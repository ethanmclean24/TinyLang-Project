from pathlib import Path

import pytest

from frontend import parse
from m6_ast_tool import validate_ast
from semantic import SemanticAnalyzer, SemanticError


def analyze(source):
    program = parse(source.rstrip("\n") + "\n")
    validate_ast(program)
    assert SemanticAnalyzer().analyze(program) is program


def test_study_session_example():
    example = Path(__file__).resolve().parents[1] / "examples" / "m3_m5_demo.tiny"
    analyze(example.read_text(encoding="utf-8"))


def test_shadowing_and_recursive_calls():
    analyze("""
let score = 1
function count(n):
    if n <= 0:
        return score
    return count(n - 1)
if True:
    let score = "local"
    show(score == "local")
else:
    score = score + 1
show(count(score))
""")


def test_nested_arrays_and_unknown_element_types():
    analyze("""
let terms = [["loop", 1], []]
terms[0][1] = ask("What is a loop?")
for term in terms[0]:
    show(term)
show(terms[0][1])
""")


@pytest.mark.parametrize("expression", [
    "-2 + 3.5", "4 - 2", "2 * 3", "6 / 2", "8 % 3",
    "2 == 2.5", "2 != 2.5", "2 < 3", "2 <= 3", "3 > 2", "3 >= 2",
    "not False and True or False", '"loop" == "loop"',
])
def test_supported_operators(expression):
    analyze(f"show({expression})")


@pytest.mark.parametrize(("source", "message"), [
    ("show(missing)", "Undefined variable: missing"),
    ("score = 1", "Undefined variable: score"),
    ("let score = score + 1", "Undefined variable: score"),
    ("let score = 1\nlet score = 2", "already declared"),
    ("let score = 1\nscore = missing", "Undefined variable: missing"),
    ('let score = 1\nscore = "one"', "Assignment requires integer"),
    ("if True:\n    let x = 1\nelse:\n    let x = 2\nshow(x)", "Undefined variable: x"),
    ("if True:\n    let x = 1\nelse:\n    show(x)", "Undefined variable: x"),
    ("while False:\n    let x = 1\nshow(x)", "Undefined variable: x"),
    ("for x in []:\n    show(x)\nshow(x)", "Undefined variable: x"),
    ("for x in x:\n    show(x)", "Undefined variable: x"),
    ("if 1:\n    show(1)", "If condition requires boolean"),
    ("while 1:\n    show(1)", "While condition requires boolean"),
    ("for x in 1:\n    show(x)", "For iterable requires array"),
    ("show(not 1)", "'not' operand requires boolean"),
    ("show(True and 1)", "Right operand of 'and' requires boolean"),
    ("show(1 + False)", "Right operand of"),
    ("show(1 == True)", "Cannot compare integer and boolean"),
    ("show(5 % 2.5)", "Right operand of '%' requires integer"),
    ("show(ask(missing))", "Undefined variable: missing"),
    ("let items = [missing]", "Undefined variable: missing"),
    ("let x = 1\nshow(x[0])", "Index target requires array"),
    ("let x = []\nx[0.5] = 1", "Array index requires integer"),
    ("let x = []\nx[0] = missing", "Undefined variable: missing"),
    ("return 1", "Return is only allowed inside a function"),
    ("function f(x, x):\n    return x", "already declared"),
    ("show(f())\nfunction f():\n    return 1", "Undefined function: f"),
    ("function f(x):\n    return x\nshow(f())", "expects 1 arguments"),
    ("function f(x):\n    return x\nshow(f(missing))", "Undefined variable: missing"),
    ("function f():\n    let local = 1\n    return local\nshow(local)", "Undefined variable: local"),
    ("let f = 1\nshow(f())", "is not a function"),
    ("function f():\n    return 1\nshow(f)", "is a function"),
])
def test_semantic_errors(source, message):
    with pytest.raises(SemanticError) as error:
        analyze(source)
    assert message in str(error.value)


def test_analyzer_resets_between_programs():
    analyzer = SemanticAnalyzer()
    analyzer.analyze(parse("let score = 1\n"))
    with pytest.raises(SemanticError, match="Undefined variable: score"):
        analyzer.analyze(parse("show(score)\n"))
