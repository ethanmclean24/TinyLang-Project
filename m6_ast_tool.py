"""StudyLang AST shape checks, adapted from the instructor's M6 example."""
import re

from ast_nodes import (
    Array, Ask, Assignment, BinaryOp, Block, Boolean, Call, For, Function,
    If, Index, Let, Not, Number, Program, Return, Show, String, Variable, While,
)

EXPRESSIONS = (Number, String, Boolean, Variable, BinaryOp, Not, Ask, Call, Array, Index)
STATEMENTS = (Let, Assignment, Show, If, While, For, Function, Return)
OPERATORS = {"+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "and", "or"}
KEYWORDS = {"let", "show", "ask", "if", "else", "while", "for", "in", "function",
            "return", "True", "False", "and", "or", "not"}


class ASTValidationError(ValueError):
    pass


def validate_ast(node) -> None:
    """Validate a whole AST or subtree; names and operand types are M7 concerns."""
    _validate(node, type(node).__name__)


def _require(condition, path, message):
    if not condition:
        raise ASTValidationError(f"{path}: {message}")


def _identifier(value, path):
    _require(type(value) is str and re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", value)
             and value not in KEYWORDS, path, "expected a nonreserved identifier")


def _child(value, allowed, path):
    _require(type(value) in allowed, path, "unexpected child type " + type(value).__name__)
    _validate(value, path)


def _sequence(values, path, nonempty=False):
    _require(type(values) in (list, tuple), path, "expected a list or tuple")
    _require(not nonempty or bool(values), path, "must not be empty")


def _validate(node, path):
    kind = type(node)
    if kind in (Program, Block):
        _sequence(node.statements, path + ".statements", nonempty=True)
        for i, statement in enumerate(node.statements):
            _child(statement, STATEMENTS, f"{path}.statements[{i}]")
    elif kind is Number:
        _require(isinstance(node.value, (int, float)) and not isinstance(node.value, bool),
                 path + ".value", "expected a number (not bool)")
    elif kind is String:
        _require(type(node.value) is str, path + ".value", "expected a string")
    elif kind is Boolean:
        _require(type(node.value) is bool, path + ".value", "expected a Boolean")
    elif kind is Variable:
        _identifier(node.name, path + ".name")
    elif kind is BinaryOp:
        _require(type(node.op) is str and node.op in OPERATORS,
                 path + ".op", "unsupported operator " + repr(node.op))
        _child(node.left, EXPRESSIONS, path + ".left")
        _child(node.right, EXPRESSIONS, path + ".right")
    elif kind is Not:
        _child(node.operand, EXPRESSIONS, path + ".operand")
    elif kind is Let:
        _identifier(node.name, path + ".name")
        _child(node.value, EXPRESSIONS, path + ".value")
    elif kind is Assignment:
        _child(node.target, (Variable, Index), path + ".target")
        _child(node.value, EXPRESSIONS, path + ".value")
    elif kind in (Show, Return):
        _child(node.expression, EXPRESSIONS, path + ".expression")
    elif kind is Ask:
        _child(node.prompt, EXPRESSIONS, path + ".prompt")
    elif kind is If:
        _child(node.condition, EXPRESSIONS, path + ".condition")
        _child(node.then_branch, (Block,), path + ".then_branch")
        if node.else_branch is not None:
            _child(node.else_branch, (Block,), path + ".else_branch")
    elif kind is While:
        _child(node.condition, EXPRESSIONS, path + ".condition")
        _child(node.body, (Block,), path + ".body")
    elif kind is For:
        _identifier(node.variable, path + ".variable")
        _child(node.iterable, EXPRESSIONS, path + ".iterable")
        _child(node.body, (Block,), path + ".body")
    elif kind is Function:
        _identifier(node.name, path + ".name")
        _sequence(node.parameters, path + ".parameters")
        for i, parameter in enumerate(node.parameters):
            _identifier(parameter, f"{path}.parameters[{i}]")
        _child(node.body, (Block,), path + ".body")
    elif kind is Call:
        _identifier(node.name, path + ".name")
        _sequence(node.arguments, path + ".arguments")
        for i, argument in enumerate(node.arguments):
            _child(argument, EXPRESSIONS, f"{path}.arguments[{i}]")
    elif kind is Array:
        _sequence(node.elements, path + ".elements")
        for i, element in enumerate(node.elements):
            _child(element, EXPRESSIONS, f"{path}.elements[{i}]")
    elif kind is Index:
        _child(node.target, (Variable, Index), path + ".target")
        _child(node.index, EXPRESSIONS, path + ".index")
    else:
        raise ASTValidationError(f"{path}: unknown AST node {kind.__name__}")
