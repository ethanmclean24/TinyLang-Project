from pathlib import Path
import subprocess
import sys

import pytest
from lark.exceptions import UnexpectedInput

from interpreter import Interpreter, StudyLangRuntimeError
from run import run
from semantic import SemanticError

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("expression", "expected"), [
    ("-2 + 3.5", "1.5"), ("4 - 2", "2"), ("2 * 3", "6"),
    ("6 / 2", "3.0"), ("8 % 3", "2"),
    ("2 == 2", "true"), ("2 != 2.5", "true"), ("2 < 3", "true"),
    ("2 <= 2", "true"), ("3 > 2", "true"), ("3 >= 3", "true"),
    ("not False and True or False", "true"), ('"loop" == "loop"', "true"),
    ("[True] == [1]", "false"), ("[1] == [1.0]", "true"),
])
def test_expressions(expression, expected):
    output = []
    run(f"show({expression})", Interpreter(output=output.append))
    assert output == [expected]


def test_study_session():
    answers = iter(["yes", "no"])
    prompts, output = [], []

    def answer(prompt):
        prompts.append(prompt)
        return next(answers)

    run(
        (ROOT / "examples" / "m3_m5_demo.tiny").read_text(),
        Interpreter(output=output.append, input_fn=answer),
    )
    assert prompts == ["declaration", "loop"]
    assert output == ["Review this term", "Practice again", "50.0", "14"]


def test_nested_scopes_through_cli():
    result = subprocess.run(
        [sys.executable, str(ROOT / "run.py"), str(ROOT / "examples" / "m8_scope.tiny")],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["12", "1", "12", "2"]


def test_recursion_and_return_from_loop():
    output = []
    run("""
function factorial(n):
    while n > 0:
        return n * factorial(n - 1)
    return 1
show(factorial(5))
""", Interpreter(output=output.append))
    assert output == ["120"]


def test_array_writes_and_aliases():
    output = []
    run("""
let terms = [["loop", 1], []]
let alias = terms[0]
terms[0][1] = "done"
for item in alias:
    show(item)
""", Interpreter(output=output.append))
    assert output == ["loop", "done"]


def test_short_circuit():
    output = []

    def unexpected_input(prompt):
        pytest.fail(f"Unexpected prompt: {prompt}")

    run("""
show(False and ask("Skipped") == "yes")
show(True or 1 / 0 == 0)
""", Interpreter(output=output.append, input_fn=unexpected_input))
    assert output == ["false", "true"]


@pytest.mark.parametrize(("source", "message"), [
    ("show(1 / 0)", "Division by zero"),
    ("show(1 % 0)", "Modulo by zero"),
    ("let x = []\nshow(x[0])", "out of bounds"),
    ("let x = [1]\nx[-1] = 2", "out of bounds"),
    ("let x = [1]\nlet flags = [True]\nshow(x[flags[0]])", "Array index requires integer"),
    ("let x = [1, True]\nshow(x[0] + x[1])", "requires integer or float"),
    ("let x = [1]\nif x[0]:\n    show(1)", "If condition requires boolean"),
    ("let x = 1\nlet flags = [True]\nx = flags[0]", "Assignment to 'x' requires integer"),
    ("let x = [1]\nx = x[0]", "Assignment to 'x' requires array"),
    ("function f():\n    let x = 1\nshow(f())", "ended without returning"),
    ("while True:\n    let x = 1", "Loop iteration safety limit exceeded"),
])
def test_runtime_errors(source, message):
    with pytest.raises(StudyLangRuntimeError, match=message):
        run(source, Interpreter(max_loop_iterations=2))


@pytest.mark.parametrize(("source", "error"), [
    ("show(1)\nshow(", UnexpectedInput),
    ('show(ask("Skipped"))\nshow(missing)', SemanticError),
])
def test_invalid_program_stops_before_execution(source, error):
    output, prompts = [], []
    with pytest.raises(error):
        run(source, Interpreter(output=output.append, input_fn=prompts.append))
    assert output == prompts == []


def test_cli_reports_runtime_error(tmp_path):
    source = tmp_path / "division.tiny"
    source.write_text("show(1 / 0)")
    result = subprocess.run(
        [sys.executable, str(ROOT / "run.py"), str(source)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.strip() == "Runtime error: Division by zero"


@pytest.mark.parametrize(("source", "expected"), [
    ("let x = 5\nlet y = 10\nshow(x + y * 2)", ["25"]),
    ("let x = 4\nlet ok = x % 2 == 0\nif ok and not False:\n    show(x)\nelse:\n    show(0)", ["4"]),
    ("let x = 5 / 2\nshow(x)\nshow(x + 1.25)", ["2.5", "3.75"]),
    ("let x = 10\nif True:\n    x = 15\nshow(x)", ["15"]),
    ("let x = 10\nif True:\n    let x = 20\n    show(x)\nshow(x)", ["20", "10"]),
    ("let i = 0\nwhile i < 4:\n    show(i)\n    i = i + 1", ["0", "1", "2", "3"]),
])
def test_instructor_examples_in_studylang_syntax(source, expected):
    # Expected output was checked against the supplied instructor interpreter.
    output = []
    run(source, Interpreter(output=output.append))
    assert output == expected


def test_captured_bindings_observe_updates_and_ignore_callers_locals():
    output = []
    run("""
let score = 1
function read_score():
    return score
score = 2
function caller(score):
    return read_score()
show(caller(99))
function increment():
    score = score + 1
    return score
show(increment())
show(read_score())
""", Interpreter(output=output.append))
    assert output == ["2", "3", "3"]


def test_loop_scopes_and_else_branch():
    output = []
    run("""
let total = 0
for item in [1, 2]:
    let local = item
    total = total + local
while total < 5:
    let local = total
    total = local + 1
if False:
    show(0)
else:
    let total = total + 1
    show(total)
for item in []:
    show(0)
while False:
    show(0)
show(total)
""", Interpreter(output=output.append))
    assert output == ["6", "5"]


def test_interpreter_starts_each_execution_with_fresh_globals():
    output = []
    interpreter = Interpreter(output=output.append)
    run("let score = 1\nshow(score)", interpreter)
    run("let score = 2\nshow(score)", interpreter)
    assert output == ["1", "2"]


@pytest.mark.parametrize(("source", "message"), [
    ("function double(x):\n    return x * 2\nshow(double(True))", "requires integer or float"),
    ("function f():\n    return True\nshow(f() + 1)", "requires integer or float"),
    ("function f(x):\n    for item in x:\n        show(item)\n    return 0\nshow(f(1))", "For iterable requires array"),
    ("function f(x):\n    while x:\n        return 1\n    return 0\nshow(f(1))", "While condition requires boolean"),
    ("function f(x):\n    return not x\nshow(f(1))", "'not' operand requires boolean"),
    ("function f(x):\n    return x == True\nshow(f(1))", "Cannot compare integer and boolean"),
    ("let x = [1]\nshow(x[0][0])", "Index target requires array"),
    ("function f():\n    return f()\nshow(f())", "Maximum function or expression depth exceeded"),
])
def test_deferred_checks_and_recursion_errors(source, message):
    with pytest.raises(StudyLangRuntimeError, match=message):
        run(source)


def test_input_end_is_reported_as_runtime_error():
    def exhausted_input(prompt):
        raise EOFError

    with pytest.raises(StudyLangRuntimeError, match="Input ended"):
        run('show(ask("Ready?"))', Interpreter(input_fn=exhausted_input))


def test_self_referencing_arrays_can_be_compared():
    output = []
    run("""
let a = [0]
let b = [0]
a[0] = a
b[0] = b
show(a == b)
""", Interpreter(output=output.append))
    assert output == ["true"]
