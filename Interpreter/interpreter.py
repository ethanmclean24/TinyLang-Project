"""Execute a semantically validated StudyLang AST."""

from dataclasses import dataclass
import operator

from Shared.ast_nodes import (
    Array, Ask, Assignment, BinaryOp, Block, Boolean, Call, For, Function,
    If, Index, Let, Node, Not, Number, Program, Return, Show, String, Variable, While,
)
from Shared.errors import StudyLangRuntimeError


@dataclass
class Binding:
    """A shared variable slot so captured scopes see later assignments."""
    value: object


class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.values: dict[str, Binding] = {}

    def define(self, name, value):
        if name in self.values:
            raise StudyLangRuntimeError(f"Duplicate declaration: {name}")
        self.values[name] = Binding(value)

    def _find(self, name):
        scope = self
        while scope is not None:
            if name in scope.values:
                return scope.values[name]
            scope = scope.parent
        raise StudyLangRuntimeError(f"Undefined name: {name}")

    def lookup(self, name):
        return self._find(name).value

    def assign(self, name, value):
        binding = self._find(name)
        _require_type(value, (type(binding.value),), f"Assignment to '{name}'")
        binding.value = value

    def capture(self):
        # Keep the names visible now and share their bindings with the live scopes.
        parent = self.parent.capture() if self.parent is not None else None
        captured = Environment(parent)
        captured.values = self.values.copy()
        return captured


@dataclass
class FunctionValue:
    declaration: Function
    closure: Environment


class _ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


_TYPE_NAMES = {
    int: "integer", float: "float", bool: "boolean", str: "string",
    list: "array", FunctionValue: "function",
}
_NUMBERS = (int, float)
_NUMERIC_OPERATORS = {
    "+": operator.add, "-": operator.sub, "*": operator.mul,
    "/": operator.truediv, "%": operator.mod,
    "<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge,
}


def _require_type(value, allowed, context):
    actual = type(value)
    if actual not in allowed:
        expected = " or ".join(_TYPE_NAMES[kind] for kind in allowed)
        raise StudyLangRuntimeError(
            f"{context} requires {expected}, got {_TYPE_NAMES[actual]}"
        )
    return value


def _display(value):
    return str(value).lower() if type(value) is bool else str(value)


def _equal(left, right):
    # Array comparisons can revisit the same pair when arrays contain cycles.
    pending = [(left, right)]
    seen = set()
    while pending:
        left, right = pending.pop()
        if type(left) is not type(right) and not (
            type(left) in _NUMBERS and type(right) in _NUMBERS
        ):
            return False
        if type(left) is list:
            if len(left) != len(right):
                return False
            pair = (id(left), id(right))
            if pair not in seen:
                seen.add(pair)
                pending.extend(zip(left, right))
        elif left != right:
            return False
    return True


class Interpreter:
    def __init__(self, output=print, input_fn=input, max_loop_iterations=100_000):
        self.output = output
        self.input = input_fn
        self.max_loop_iterations = max_loop_iterations

    def execute(self, program: Program) -> None:
        """Run a validated AST with fresh global bindings."""
        environment = Environment()
        try:
            for statement in program.statements:
                self._execute_statement(statement, environment)
        except RecursionError as error:
            raise StudyLangRuntimeError("Maximum function or expression depth exceeded") from error

    def _execute_block(self, block: Block, environment: Environment) -> None:
        for statement in block.statements:
            self._execute_statement(statement, environment)

    def _execute_statement(self, node: Node, environment: Environment) -> None:
        if isinstance(node, Let):
            environment.define(node.name, self._evaluate(node.value, environment))
        elif isinstance(node, Assignment):
            if isinstance(node.target, Variable):
                environment.assign(node.target.name, self._evaluate(node.value, environment))
            else:
                array, index = self._index_location(node.target, environment)
                array[index] = self._evaluate(node.value, environment)
        elif isinstance(node, Show):
            self.output(_display(self._evaluate(node.expression, environment)))
        elif isinstance(node, If):
            condition = self._condition(node.condition, environment, "If condition")
            branch = node.then_branch if condition else node.else_branch
            if branch is not None:
                self._execute_block(branch, Environment(environment))
        elif isinstance(node, While):
            count = 0
            while self._condition(node.condition, environment, "While condition"):
                count += 1
                if count > self.max_loop_iterations:
                    raise StudyLangRuntimeError("Loop iteration safety limit exceeded")
                self._execute_block(node.body, Environment(environment))
        elif isinstance(node, For):
            items = self._evaluate(node.iterable, environment)
            _require_type(items, (list,), "For iterable")
            for item in items:
                local = Environment(environment)
                local.define(node.variable, item)
                self._execute_block(node.body, local)
        elif isinstance(node, Function):
            closure = environment.capture()
            function = FunctionValue(node, closure)
            # The function can look itself up when it calls itself.
            closure.define(node.name, function)
            environment.define(node.name, function)
        elif isinstance(node, Return):
            raise _ReturnSignal(self._evaluate(node.expression, environment))
        else:
            raise StudyLangRuntimeError(f"Unsupported statement: {type(node).__name__}")

    def _evaluate(self, node: Node, environment: Environment):
        if isinstance(node, Number):
            value = float(node.value)
            return int(value) if value.is_integer() else value
        if isinstance(node, (Boolean, String)):
            return node.value
        if isinstance(node, Variable):
            return environment.lookup(node.name)
        if isinstance(node, BinaryOp):
            return self._evaluate_binary(node, environment)
        if isinstance(node, Not):
            return not self._condition(node.operand, environment, "'not' operand")
        if isinstance(node, Ask):
            prompt = _display(self._evaluate(node.prompt, environment))
            try:
                return self.input(prompt)
            except EOFError as error:
                raise StudyLangRuntimeError("Input ended while waiting for ask()") from error
        if isinstance(node, Array):
            return [self._evaluate(item, environment) for item in node.elements]
        if isinstance(node, Index):
            array, index = self._index_location(node, environment)
            return array[index]
        if isinstance(node, Call):
            return self._call(node, environment)
        raise StudyLangRuntimeError(f"Unsupported expression: {type(node).__name__}")

    def _condition(self, node, environment, context):
        return _require_type(self._evaluate(node, environment), (bool,), context)

    def _index_location(self, node: Index, environment: Environment):
        array = _require_type(self._evaluate(node.target, environment), (list,), "Index target")
        index = _require_type(self._evaluate(node.index, environment), (int,), "Array index")
        if not 0 <= index < len(array):
            raise StudyLangRuntimeError(f"Array index {index} out of bounds for length {len(array)}")
        return array, index

    def _call(self, node: Call, environment: Environment):
        function = environment.lookup(node.name)
        local = Environment(function.closure)
        for name, argument in zip(function.declaration.parameters, node.arguments):
            local.define(name, self._evaluate(argument, environment))
        try:
            self._execute_block(function.declaration.body, local)
        except _ReturnSignal as result:
            return result.value
        raise StudyLangRuntimeError(f"Function '{node.name}' ended without returning a value")

    def _evaluate_binary(self, node: BinaryOp, environment: Environment):
        op = node.op
        left = self._evaluate(node.left, environment)
        # Skip the right operand when the left already determines the result.
        if op == "and":
            return _require_type(left, (bool,), "Left operand of 'and'") and self._condition(
                node.right, environment, "Right operand of 'and'"
            )
        if op == "or":
            return _require_type(left, (bool,), "Left operand of 'or'") or self._condition(
                node.right, environment, "Right operand of 'or'"
            )

        right = self._evaluate(node.right, environment)
        if op in {"==", "!="}:
            if type(left) is not type(right) and not (
                type(left) in _NUMBERS and type(right) in _NUMBERS
            ):
                raise StudyLangRuntimeError(
                    f"Cannot compare {_TYPE_NAMES[type(left)]} and "
                    f"{_TYPE_NAMES[type(right)]} with '{op}'"
                )
            equal = _equal(left, right)
            return equal if op == "==" else not equal

        allowed = (int,) if op == "%" else _NUMBERS
        _require_type(left, allowed, f"Left operand of '{op}'")
        _require_type(right, allowed, f"Right operand of '{op}'")
        if op == "/" and right == 0:
            raise StudyLangRuntimeError("Division by zero")
        if op == "%" and right == 0:
            raise StudyLangRuntimeError("Modulo by zero")
        try:
            return _NUMERIC_OPERATORS[op](left, right)
        except OverflowError as error:
            raise StudyLangRuntimeError("Numeric result exceeds the supported range") from error
