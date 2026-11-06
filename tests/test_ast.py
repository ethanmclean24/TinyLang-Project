"""Instructor-style M6 tests adapted to StudyLang."""
from pathlib import Path
import sys

import pytest
from lark import UnexpectedInput

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ast_nodes import BinaryOp, Block, Number, Program, Show, Variable
from frontend import parse
from m6_ast_tool import ASTValidationError, validate_ast
from metric import max_depth, node_count
from walk import walk


def test_precedence():
    ast = parse("show(3 + 5 * 2)\n")
    validate_ast(ast)
    expression = ast.statements[0].expression
    assert expression.op == "+"
    assert expression.right.op == "*"
    assert node_count(ast) == 7
    assert max_depth(ast) == 5


def test_parentheses_override_precedence():
    ast = parse("show((3 + 5) * 2)\n")
    validate_ast(ast)
    expression = ast.statements[0].expression
    assert expression.op == "*"
    assert expression.left.op == "+"


def test_invalid_syntax_rejected():
    with pytest.raises(UnexpectedInput):
        parse("show(3 + )\n")


def test_invalid_ast_shape_rejected():
    with pytest.raises(ASTValidationError, match="unsupported operator"):
        validate_ast(BinaryOp("^", Number(1), Number(2)))


@pytest.mark.parametrize("node", [
    Program([]),                   # Programs require statements.
    Block([]),                     # Blocks require statements.
    Number(True),                  # Python bool must not count as a number.
    Show(None),                    # Required expression is missing.
    Program([Number(1)]),           # An expression is not a statement.
    Variable("show"),              # Keywords cannot be identifiers.
    None,                          # Unknown node type.
])
def test_malformed_nodes_rejected(node):
    with pytest.raises(ASTValidationError):
        validate_ast(node)


@pytest.mark.parametrize("filename", ["milestone1_examples.tiny", "m3_m5_demo.tiny"])
def test_existing_examples_validate(filename):
    source = (ROOT / "examples" / filename).read_text(encoding="utf-8")
    validate_ast(parse(source))


def test_ast_walk(capsys):
    walk(parse("show(3 + 5 * 2)\n"))
    assert capsys.readouterr().out == (
        "Program\n  Show\n    BinaryOp(+)\n      Number(3)\n"
        "      BinaryOp(*)\n        Number(5)\n        Number(2)\n"
    )


def test_semantic_checks_remain_outside_m6():
    # Undeclared names, operand types, and return context belong to future milestones.
    validate_ast(parse('show(missing + "text")\nreturn 1\n'))
