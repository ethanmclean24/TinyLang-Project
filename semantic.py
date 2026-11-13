"""Check names, scopes, and types in a structurally valid StudyLang AST."""

from dataclasses import dataclass
from typing import Optional

from ast_nodes import (
    Array, Ask, Assignment, BinaryOp, Block, Boolean, Call, For, Function,
    If, Index, Let, Node, Not, Number, Program, Return, Show, String, Variable, While,
)

NUMERIC = {"integer", "float"}
UNKNOWN = "unknown"


class SemanticError(Exception):
    """The program breaks a StudyLang semantic rule."""


@dataclass
class Symbol:
    value_type: str
    arity: Optional[int] = None


class SemanticAnalyzer:
    def __init__(self):
        self.scopes: list[dict[str, Symbol]] = []
        self.function_depth = 0

    def analyze(self, program: Program) -> Program:
        # Each program starts with an empty global scope.
        self.scopes = [{}]
        self.function_depth = 0
        for statement in program.statements:
            self._check_statement(statement)
        return program

    def _declare(self, name: str, symbol: Symbol) -> None:
        current = self.scopes[-1]
        if name in current:
            raise SemanticError(f"'{name}' is already declared in this scope")
        current[name] = symbol

    def _lookup(self, name: str, kind: str) -> Symbol:
        # Start with the innermost scope so local names can shadow outer ones.
        for scope in reversed(self.scopes):
            if name in scope:
                symbol = scope[name]
                if kind == "function" and symbol.arity is None:
                    raise SemanticError(f"'{name}' is not a function")
                if kind == "variable" and symbol.arity is not None:
                    raise SemanticError(f"'{name}' is a function, not a variable")
                return symbol
        raise SemanticError(f"Undefined {kind}: {name}")

    def _check_block(self, block: Block, bindings: tuple[str, ...] = ()) -> None:
        self.scopes.append({})
        try:
            for name in bindings:
                self._declare(name, Symbol(UNKNOWN))
            for statement in block.statements:
                self._check_statement(statement)
        finally:
            self.scopes.pop()

    def _check_statement(self, node: Node) -> None:
        if isinstance(node, Let):
            # The initializer sees the names available before this declaration.
            value_type = self._check_expression(node.value)
            self._declare(node.name, Symbol(value_type))
        elif isinstance(node, Assignment):
            target_type = self._check_expression(node.target)
            value_type = self._check_expression(node.value)
            if target_type != UNKNOWN:
                self._require_type(value_type, {target_type}, "Assignment")
        elif isinstance(node, Show):
            self._check_expression(node.expression)
        elif isinstance(node, If):
            self._require_type(self._check_expression(node.condition), {"boolean"}, "If condition")
            self._check_block(node.then_branch)
            if node.else_branch is not None:
                self._check_block(node.else_branch)
        elif isinstance(node, While):
            self._require_type(self._check_expression(node.condition), {"boolean"}, "While condition")
            self._check_block(node.body)
        elif isinstance(node, For):
            self._require_type(self._check_expression(node.iterable), {"array"}, "For iterable")
            self._check_block(node.body, (node.variable,))
        elif isinstance(node, Function):
            # Register the signature first so the body can call itself.
            self._declare(node.name, Symbol("function", len(node.parameters)))
            self.function_depth += 1
            try:
                self._check_block(node.body, tuple(node.parameters))
            finally:
                self.function_depth -= 1
        elif isinstance(node, Return):
            if self.function_depth == 0:
                raise SemanticError("Return is only allowed inside a function")
            self._check_expression(node.expression)
        else:
            raise SemanticError(f"Unsupported statement: {type(node).__name__}")

    def _check_expression(self, node: Node) -> str:
        if isinstance(node, Number):
            # The parser stores all numbers as floats, including whole numbers.
            return "integer" if float(node.value).is_integer() else "float"
        if isinstance(node, String):
            return "string"
        if isinstance(node, Boolean):
            return "boolean"
        if isinstance(node, Variable):
            return self._lookup(node.name, "variable").value_type
        if isinstance(node, BinaryOp):
            return self._check_binary(node)
        if isinstance(node, Not):
            self._require_type(self._check_expression(node.operand), {"boolean"}, "'not' operand")
            return "boolean"
        if isinstance(node, Ask):
            self._check_expression(node.prompt)
            return "string"
        if isinstance(node, Array):
            for element in node.elements:
                self._check_expression(element)
            return "array"
        if isinstance(node, Index):
            self._require_type(self._check_expression(node.target), {"array"}, "Index target")
            self._require_type(self._check_expression(node.index), {"integer"}, "Array index")
            # Arrays can hold mixed types, and writes can change their contents.
            return UNKNOWN
        if isinstance(node, Call):
            symbol = self._lookup(node.name, "function")
            if len(node.arguments) != symbol.arity:
                raise SemanticError(
                    f"Function '{node.name}' expects {symbol.arity} arguments, "
                    f"got {len(node.arguments)}"
                )
            for argument in node.arguments:
                self._check_expression(argument)
            return UNKNOWN
        raise SemanticError(f"Unsupported expression: {type(node).__name__}")

    def _check_binary(self, node: BinaryOp) -> str:
        left = self._check_expression(node.left)
        right = self._check_expression(node.right)
        op = node.op
        if op in {"==", "!="}:
            if UNKNOWN not in (left, right) and left != right and not {left, right} <= NUMERIC:
                raise SemanticError(f"Cannot compare {left} and {right} with '{op}'")
            return "boolean"
        if op in {"and", "or"}:
            allowed, result = {"boolean"}, "boolean"
        elif op in {"<", "<=", ">", ">="}:
            allowed, result = NUMERIC, "boolean"
        elif op == "%":
            allowed, result = {"integer"}, "integer"
        elif op == "/":
            allowed, result = NUMERIC, "float"
        elif op in {"+", "-", "*"}:
            allowed = NUMERIC
            if "float" in (left, right):
                result = "float"
            elif UNKNOWN in (left, right):
                result = UNKNOWN
            else:
                result = "integer"
        else:
            raise SemanticError(f"Unsupported binary operator: {op}")
        self._require_type(left, allowed, f"Left operand of '{op}'")
        self._require_type(right, allowed, f"Right operand of '{op}'")
        return result

    @staticmethod
    def _require_type(actual: str, allowed: set[str], context: str) -> None:
        # Untyped parameters, call results, and array items may need runtime checks.
        if actual != UNKNOWN and actual not in allowed:
            expected = " or ".join(sorted(allowed))
            raise SemanticError(f"{context} requires {expected}, got {actual}")


def run_demo() -> bool:
    from frontend import parse
    from m6_ast_tool import validate_ast

    cases = [
        ("arithmetic and reassignment", "let score = -1\nscore = score + 2\nshow(score)", True),
        ("input and branching", 'if ask("Ready?") == "yes":\n    show(True)', True),
        ("array and loop", "let scores = [1, 2]\nfor score in scores:\n    show(score)", True),
        ("undefined variable", "show(missing)", False),
        ("invalid assignment", 'let score = 0\nscore = "zero"', False),
        ("branch-local variable", "if True:\n    let score = 1\nshow(score)", False),
    ]
    passed = 0
    for name, source, expected in cases:
        program = parse(source + "\n")
        validate_ast(program)
        try:
            SemanticAnalyzer().analyze(program)
        except SemanticError as error:
            valid, reason = False, str(error)
        else:
            valid, reason = True, "No semantic errors found"
        matched = valid == expected
        passed += matched
        print(f"{name}: {'PASS' if matched else 'FAIL'} ({reason})")
    print(f"{passed}/{len(cases)} semantic cases passed")
    return passed == len(cases)


if __name__ == "__main__":
    raise SystemExit(0 if run_demo() else 1)
