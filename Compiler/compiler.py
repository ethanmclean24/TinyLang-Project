"""Generate verified LLVM IR for StudyLang's numeric and Boolean core.

Adapted from the instructor compiler's types, scope stack, and control flow.
"""

import math

from llvmlite import binding as llvm, ir

from Shared.ast_nodes import (
    Assignment, BinaryOp, Boolean, Conditional, If, Let, Not, Number, Program, Show,
    Variable, While,
)
from Shared.m6_ast_tool import validate_ast
from Shared.semantic import SemanticAnalyzer

I1 = ir.IntType(1)
I32 = ir.IntType(32)
I64 = ir.IntType(64)
F64 = ir.DoubleType()
MIN_INTEGER = -(2 ** 63)
MAX_INTEGER = 2 ** 63 - 1
RUNTIME_ERRORS = {
    1: "Division by zero",
    2: "Modulo by zero",
    3: "Integer result exceeds signed 64-bit range",
    4: "Loop iteration safety limit exceeded",
}
OUTPUT_FUNCTIONS = {
    "studylang_show_integer": I64,
    "studylang_show_float": F64,
    "studylang_show_boolean": I32,
}


class CompilationError(Exception):
    """The program uses a feature outside the supported LLVM subset."""


class Compiler:
    def __init__(self, max_loop_iterations=100_000):
        if type(max_loop_iterations) is not int or not 0 <= max_loop_iterations <= MAX_INTEGER:
            raise ValueError("Loop limit must be a nonnegative signed 64-bit integer")
        self.max_loop_iterations = max_loop_iterations

    def compile(self, program: Program) -> str:
        """Validate the program, build a fresh module, and verify its IR."""
        validate_ast(program)
        SemanticAnalyzer().analyze(program)
        self.module = ir.Module(name="studylang")
        self.module.triple = llvm.get_default_triple()
        self.function = ir.Function(self.module, ir.FunctionType(I32, []), name="main")
        entry = self.function.append_basic_block("entry")
        body = self.function.append_basic_block("program")
        self.builder = ir.IRBuilder(entry)
        self.builder.branch(body)
        self.builder.position_at_end(body)
        self.scopes = [{}]
        self.output_functions = {
            name: ir.Function(self.module, ir.FunctionType(I32, [kind]), name=name)
            for name, kind in OUTPUT_FUNCTIONS.items()
        }
        for statement in program.statements:
            self._statement(statement)
        self.builder.ret(ir.Constant(I32, 0))
        text = str(self.module)
        with llvm.parse_assembly(text) as module:
            module.verify()
        return text

    def _allocate(self, kind, name):
        # Storage lives in entry so loops reuse it instead of growing the stack.
        with self.builder.goto_entry_block():
            return self.builder.alloca(kind, name=name)

    def _find(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise CompilationError(f"Undeclared name: {name}")

    def _cast_float(self, value):
        if value.type == I64:
            return self.builder.sitofp(value, F64, name="as_float")
        return value

    def _guard(self, valid, status):
        # Return an error code before reaching an invalid native instruction.
        good = self.function.append_basic_block("check_ok")
        bad = self.function.append_basic_block("runtime_error")
        self.builder.cbranch(valid, good, bad)
        self.builder.position_at_end(bad)
        self.builder.ret(status)
        self.builder.position_at_end(good)

    def _expression(self, node):
        if isinstance(node, Boolean):
            return ir.Constant(I1, int(node.value))
        if isinstance(node, Number):
            value = float(node.value)
            if not math.isfinite(value):
                raise CompilationError("LLVM backend requires finite numeric literals")
            if value.is_integer():
                integer = int(value)
                if not MIN_INTEGER <= integer <= MAX_INTEGER:
                    raise CompilationError("Integer literal is outside signed 64-bit range")
                return ir.Constant(I64, integer)
            return ir.Constant(F64, value)
        if isinstance(node, Variable):
            return self.builder.load(self._find(node.name), name=f"load_{node.name}")
        if isinstance(node, Not):
            return self.builder.not_(self._expression(node.operand), name="logical_not")
        if isinstance(node, BinaryOp):
            return self._binary(node)
        if isinstance(node, Conditional):
            return self._conditional(node)
        raise CompilationError(f"LLVM backend does not support expression: {type(node).__name__}")

    def _conditional(self, node):
        condition = self._expression(node.condition)
        then_block = self.function.append_basic_block("conditional_then")
        else_block = self.function.append_basic_block("conditional_else")
        merge = self.function.append_basic_block("conditional_merge")
        self.builder.cbranch(condition, then_block, else_block)

        self.builder.position_at_end(then_block)
        then_value = self._expression(node.then_expression)
        then_end = self.builder.block
        self.builder.branch(merge)

        self.builder.position_at_end(else_block)
        else_value = self._expression(node.else_expression)
        else_end = self.builder.block
        self.builder.branch(merge)

        # The phi selects a value from the branch that actually executed.
        self.builder.position_at_end(merge)
        result = self.builder.phi(then_value.type, name="conditional_result")
        result.add_incoming(then_value, then_end)
        result.add_incoming(else_value, else_end)
        return result

    def _binary(self, node):
        op = node.op
        if op in {"and", "or"}:
            return self._logical(node)
        left = self._expression(node.left)
        right = self._expression(node.right)
        if op in {"==", "!=", "<", "<=", ">", ">="}:
            if {left.type, right.type} == {I64, F64}:
                if left.type == F64:
                    reverse = {"<": ">", "<=": ">=", ">": "<", ">=": "<=", "==": "==", "!=": "!="}
                    return self._mixed_comparison(reverse[op], right, left)
                return self._mixed_comparison(op, left, right)
            if F64 in (left.type, right.type):
                # NaN is unequal to every value, including itself.
                compare = self.builder.fcmp_unordered if op == "!=" else self.builder.fcmp_ordered
                return compare(op, left, right, name="comparison")
            return self.builder.icmp_signed(op, left, right, name="comparison")
        if op == "%":
            return self._remainder(left, right)
        if op == "/" or F64 in (left.type, right.type):
            left, right = self._cast_float(left), self._cast_float(right)
            if op == "/":
                nonzero = self.builder.fcmp_unordered("!=", right, ir.Constant(F64, 0))
                self._guard(nonzero, ir.Constant(I32, 1))
            operations = {
                "+": self.builder.fadd, "-": self.builder.fsub,
                "*": self.builder.fmul, "/": self.builder.fdiv,
            }
            return operations[op](left, right, name="arithmetic")
        operations = {
            "+": self.builder.sadd_with_overflow,
            "-": self.builder.ssub_with_overflow,
            "*": self.builder.smul_with_overflow,
        }
        checked = operations[op](left, right, name="checked_arithmetic")
        value = self.builder.extract_value(checked, 0, name="arithmetic")
        overflow = self.builder.extract_value(checked, 1, name="overflow")
        self._guard(self.builder.not_(overflow), ir.Constant(I32, 3))
        return value

    def _mixed_comparison(self, op, integer, floating):
        # Comparing after converting a large integer to double could round it.
        above = self.builder.fcmp_ordered(">=", floating, ir.Constant(F64, 2 ** 63))
        below = self.builder.fcmp_ordered("<", floating, ir.Constant(F64, MIN_INTEGER))
        in_range = self.builder.and_(
            self.builder.fcmp_ordered(">=", floating, ir.Constant(F64, MIN_INTEGER)),
            self.builder.fcmp_ordered("<", floating, ir.Constant(F64, 2 ** 63)),
        )
        safe_float = self.builder.select(in_range, floating, ir.Constant(F64, 0))
        whole = self.builder.fptosi(safe_float, I64)
        same_whole = self.builder.icmp_signed("==", integer, whole)
        fraction_zero = self.builder.fcmp_ordered("==", safe_float, self._cast_float(whole))
        equal = self.builder.and_(in_range, self.builder.and_(same_whole, fraction_zero))
        if op == "==":
            return equal
        if op == "!=":
            return self.builder.not_(equal)
        direction = "<" if op in {"<", "<="} else ">"
        whole_compare = self.builder.icmp_signed(direction, integer, whole)
        fraction_compare = self.builder.fcmp_ordered(
            ">" if direction == "<" else "<", safe_float, self._cast_float(whole)
        )
        within = self.builder.or_(whole_compare, self.builder.and_(same_whole, fraction_compare))
        result = self.builder.or_(above if direction == "<" else below,
                                  self.builder.and_(in_range, within))
        if op in {"<=", ">="}:
            return self.builder.or_(result, equal)
        return result

    def _remainder(self, left, right):
        nonzero = self.builder.icmp_signed("!=", right, ir.Constant(I64, 0))
        self._guard(nonzero, ir.Constant(I32, 2))
        # LLVM srem overflows for MIN_INTEGER % -1; the mathematical result is zero.
        minimum = self.builder.icmp_signed("==", left, ir.Constant(I64, MIN_INTEGER))
        minus_one = self.builder.icmp_signed("==", right, ir.Constant(I64, -1))
        special = self.builder.and_(minimum, minus_one)
        divisor = self.builder.select(special, ir.Constant(I64, 1), right)
        remainder = self.builder.srem(left, divisor, name="truncated_remainder")
        # StudyLang follows Python: a nonzero remainder has the divisor's sign.
        nonzero_remainder = self.builder.icmp_signed("!=", remainder, ir.Constant(I64, 0))
        negative_remainder = self.builder.icmp_signed("<", remainder, ir.Constant(I64, 0))
        negative_divisor = self.builder.icmp_signed("<", right, ir.Constant(I64, 0))
        different_signs = self.builder.xor(negative_remainder, negative_divisor)
        adjust = self.builder.and_(nonzero_remainder, different_signs)
        corrected = self.builder.add(remainder, right)
        return self.builder.select(adjust, corrected, remainder, name="remainder")

    def _logical(self, node):
        left = self._expression(node.left)
        left_end = self.builder.block
        rhs = self.function.append_basic_block("logic_rhs")
        merge = self.function.append_basic_block("logic_merge")
        if node.op == "and":
            self.builder.cbranch(left, rhs, merge)
        else:
            self.builder.cbranch(left, merge, rhs)
        self.builder.position_at_end(rhs)
        right = self._expression(node.right)
        right_end = self.builder.block
        self.builder.branch(merge)
        self.builder.position_at_end(merge)
        result = self.builder.phi(I1, name="logical_result")
        result.add_incoming(ir.Constant(I1, int(node.op == "or")), left_end)
        result.add_incoming(right, right_end)
        return result

    def _block(self, block):
        self.scopes.append({})
        try:
            for statement in block.statements:
                self._statement(statement)
        finally:
            self.scopes.pop()

    def _statement(self, node):
        if isinstance(node, Let):
            value = self._expression(node.value)
            pointer = self._allocate(value.type, f"var_{node.name}")
            self.builder.store(value, pointer)
            self.scopes[-1][node.name] = pointer
        elif isinstance(node, Assignment):
            if not isinstance(node.target, Variable):
                raise CompilationError("LLVM backend does not support indexed assignment")
            value = self._expression(node.value)
            self.builder.store(value, self._find(node.target.name))
        elif isinstance(node, Show):
            value = self._expression(node.expression)
            names = {I64: "integer", F64: "float", I1: "boolean"}
            function = self.output_functions[f"studylang_show_{names[value.type]}"]
            if value.type == I1:
                value = self.builder.zext(value, I32)
            status = self.builder.call(function, [value], name="output_status")
            self._guard(self.builder.icmp_signed("==", status, ir.Constant(I32, 0)), status)
        elif isinstance(node, If):
            condition = self._expression(node.condition)
            then = self.function.append_basic_block("if_then")
            otherwise = self.function.append_basic_block("if_else")
            merge = self.function.append_basic_block("if_end")
            self.builder.cbranch(condition, then, otherwise)
            self.builder.position_at_end(then)
            self._block(node.then_branch)
            self.builder.branch(merge)
            self.builder.position_at_end(otherwise)
            if node.else_branch is not None:
                self._block(node.else_branch)
            self.builder.branch(merge)
            self.builder.position_at_end(merge)
        elif isinstance(node, While):
            self._while(node)
        else:
            raise CompilationError(f"LLVM backend does not support statement: {type(node).__name__}")

    def _while(self, node):
        counter = self._allocate(I64, "loop_count")
        self.builder.store(ir.Constant(I64, 0), counter)
        test = self.function.append_basic_block("while_test")
        body = self.function.append_basic_block("while_body")
        done = self.function.append_basic_block("while_end")
        self.builder.branch(test)
        self.builder.position_at_end(test)
        condition = self._expression(node.condition)
        self.builder.cbranch(condition, body, done)
        self.builder.position_at_end(body)
        count = self.builder.load(counter)
        within_limit = self.builder.icmp_signed("<", count, ir.Constant(I64, self.max_loop_iterations))
        self._guard(within_limit, ir.Constant(I32, 4))
        self.builder.store(self.builder.add(count, ir.Constant(I64, 1)), counter)
        self._block(node.body)
        self.builder.branch(test)
        self.builder.position_at_end(done)
