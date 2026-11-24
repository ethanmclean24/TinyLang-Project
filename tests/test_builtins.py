from pathlib import Path
import subprocess
import sys

import pytest

from Compiler.compiler import CompilationError
from Interpreter.interpreter import Interpreter
from Interpreter.run import run
from Shared.errors import StudyLangRuntimeError
from Shared.semantic import SemanticError
from main import run_program

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("expression", "expected"), [
    ("len([])", "0"),
    ('len([1, [2, 3], "term"])', "3"),
    ('contains(["let", "while"], "let")', "true"),
    ('contains(["let"], "Let")', "false"),
    ('contains([], "anything")', "false"),
    ("contains([True], 1)", "false"),
    ("contains([2], 4 / 2)", "true"),
    ("contains([1, [2, 3]], [2, 3])", "true"),
    ("contains([[True]], [1])", "false"),
])
def test_array_queries(expression, expected):
    output = []
    run_program(f"show({expression})", "interpreter", output=output.append)
    assert output == [expected]


@pytest.mark.parametrize("mode", ["interpreter", "compiler"])
@pytest.mark.parametrize(("source", "message"), [
    ("show(len())", "expects 1 arguments"),
    ("show(len([], 1))", "expects 1 arguments"),
    ("show(contains([]))", "expects 2 arguments"),
    ("show(contains([], 1, 2))", "expects 2 arguments"),
    ('show(len("text"))', "First argument of 'len' requires array"),
    ("show(contains(1, 1))", "First argument of 'contains' requires array"),
    ("if len([]):\n    show(1)", "If condition requires boolean"),
    ("show(contains([], 1) + 1)", "Left operand of"),
])
def test_builtin_semantic_errors_prevent_execution(mode, source, message):
    output = []
    with pytest.raises(SemanticError, match=message):
        run_program("show(99)\n" + source, mode, output=output.append)
    assert output == []


@pytest.mark.parametrize(("call", "name"), [("len(value)", "len"), ("contains(value, 1)", "contains")])
def test_unknown_argument_types_are_checked_at_runtime(call, name):
    source = f"function query(value):\n    return {call}\nshow(query(1))"
    with pytest.raises(StudyLangRuntimeError, match=f"First argument of '{name}' requires array"):
        run_program(source, "interpreter")


def test_arguments_run_left_to_right_once():
    output = []
    run_program("""
let trace = 0
function items():
    trace = trace * 10 + 1
    return [1]
function needle():
    trace = trace * 10 + 2
    return 1
show(contains(items(), needle()))
show(trace)
""", "interpreter", output=output.append)
    assert output == ["true", "12"]


def test_queries_observe_writes_without_modifying_arrays():
    output = []
    run_program("""
let items = [1, 2]
let alias = items
show(contains(items, 1))
alias[0] = 3
show(contains(items, 1))
show(contains(items, 3))
show(len(items))
show(items == [3, 2])
""", "interpreter", output=output.append)
    assert output == ["true", "false", "true", "2", "true"]


def test_nested_queries_handle_self_referencing_arrays():
    output = []
    run_program("""
let a = [0]
let b = [0]
a[0] = a
b[0] = b
show(len(a))
show(contains(a, b))
show(contains(a, 1))
""", "interpreter", output=output.append)
    assert output == ["1", "true", "false"]


def test_builtin_shadowing_and_lexical_capture():
    output = []
    run_program("""
function original():
    return len([1, 2])
let len = len([1, 2, 3])
show(len)
show(original())
if True:
    function contains(value):
        return value + 1
    show(contains(4))
show(contains([1], 1))
""", "interpreter", output=output.append)
    assert output == ["3", "2", "5", "true"]


def test_user_function_can_shadow_a_builtin_globally():
    output = []
    run_program("function len(value):\n    return value + 1\nshow(len(4))",
                "interpreter", output=output.append)
    assert output == ["5"]
    with pytest.raises(SemanticError, match="is not a function"):
        run_program("let len = 1\nshow(len([]))", "interpreter")


def test_reused_interpreter_restores_predefined_functions():
    output = []
    interpreter = Interpreter(output=output.append)
    run("let len = 9\nshow(len)", interpreter)
    run("show(len([1]))", interpreter)
    assert output == ["9", "1"]


@pytest.mark.parametrize(("expression", "name"), [("len([])", "len"), ("contains([], 1)", "contains")])
def test_compiler_rejects_array_queries_before_execution(expression, name):
    output = []
    with pytest.raises(CompilationError, match=f"does not support builtin '{name}'; use interpreter mode"):
        run_program(f"show(99)\nshow({expression})", "compiler", output=output.append)
    assert output == []


@pytest.mark.parametrize(("answers", "expected"), [
    ("let\nwhile loop\n", ["Correct!", "Correct!", "2", "2", "100.0"]),
    ("wrong\nwhile\n", ["Review this topic", "Correct!", "1", "2", "50.0"]),
])
def test_quiz_example(answers, expected):
    prompts, output = [], []
    responses = iter(answers.splitlines())

    def answer(prompt):
        prompts.append(prompt)
        return next(responses)

    run_program((ROOT / "Examples" / "m12_quiz.tiny").read_text(), "interpreter",
                input_fn=answer, output=output.append)
    assert output == expected
    assert prompts == ["What declares a variable? ", "What repeats while a condition is true? "]


def test_quiz_and_compiler_diagnostic_through_launcher(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--mode", "interpreter", "--file",
         str(ROOT / "Examples" / "m12_quiz.tiny")],
        input="let\nwhile\n", text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.endswith("Correct!\n2\n2\n100.0\n")
    file = tmp_path / "builtin.tiny"
    file.write_text("show(len([]))")
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--mode", "compiler", "--file", str(file)],
        text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "does not support builtin 'len'; use interpreter mode" in result.stderr
