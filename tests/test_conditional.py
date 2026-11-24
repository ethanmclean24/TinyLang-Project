from pathlib import Path
import subprocess
import sys

from lark.exceptions import UnexpectedInput
from llvmlite import binding as llvm
import pytest

from Compiler.compiler import CompilationError
from Compiler.run import compile_source
from Shared.ast_nodes import Boolean, Conditional, Number
from Shared.errors import StudyLangRuntimeError
from Shared.frontend import parse
from Shared.m6_ast_tool import ASTValidationError, validate_ast
from Shared.metric import max_depth, node_count
from Shared.semantic import SemanticError
from Shared.walk import walk
from main import run_program

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("level", [0, 1, 2, 3])
@pytest.mark.parametrize(("expression", "expected"), [
    ("1 if True else 2", "1"),
    ("1 if False else 2", "2"),
    ("1.5 if True else 2.5", "1.5"),
    ("True if False else False", "false"),
    ("1 + 2 if 2 < 3 and not False else 4 * 5", "3"),
    ("True or False if False else False", "false"),
    ("(1 if False else 2) + 3", "5"),
    ("1 if False else 2 if True else 3", "2"),
    ("(1 if False else 2) if True else 3", "2"),
    ("1 if (True if False else False) else 2", "2"),
    ("1 / 0 if False else 2 / 1", "2.0"),
    ("7 if True else 3 % 0", "7"),
])
def test_numeric_conditionals_in_both_modes(expression, expected, level):
    interpreted, compiled = [], []
    source = f"show({expression})"
    run_program(source, "interpreter", output=interpreted.append)
    run_program(source, "compiler", opt=level, output=compiled.append)
    assert interpreted == compiled == [expected]


def test_right_associative_ast_and_source_order_walk(capsys):
    program = parse("show(1 if False else 2 if True else 3)\n")
    expression = program.statements[0].expression
    assert expression == Conditional(Boolean(False), Number(1),
                                     Conditional(Boolean(True), Number(2), Number(3)))
    validate_ast(program)
    simple = parse("show(1 if True else 2)\n")
    assert node_count(simple) == 6
    assert max_depth(simple) == 4
    walk(simple)
    assert capsys.readouterr().out == (
        "Program\n  Show\n    Conditional\n      Number(1)\n"
        "      Boolean(True)\n      Number(2)\n"
    )


@pytest.mark.parametrize("field", ["condition", "then_expression", "else_expression"])
def test_conditional_ast_requires_all_expression_children(field):
    expression = Conditional(Boolean(True), Number(1), Number(2))
    setattr(expression, field, None)
    with pytest.raises(ASTValidationError, match=field):
        validate_ast(expression)


@pytest.mark.parametrize("source", [
    "show(1 if True)",
    "show(1 if else 2)",
    "show(1 if True else)",
])
def test_incomplete_conditional_syntax(source):
    with pytest.raises(UnexpectedInput):
        parse(source + "\n")


@pytest.mark.parametrize("mode", ["interpreter", "compiler"])
@pytest.mark.parametrize(("source", "message"), [
    ("show(1 if 2 else 0)", "Conditional condition requires boolean"),
    ("show(1 if True else False)", "Conditional alternatives require matching types"),
    ("show(1 if True else 2.5)", "Conditional alternatives require matching types"),
    ("show(1 if True else missing)", "Undefined variable: missing"),
    ("show(1 if True else True + 1)", "Left operand of"),
    ("let x = 1\nx = 1.5 if True else 2.5", "Assignment requires integer"),
])
def test_semantic_rejection_precedes_all_execution(mode, source, message):
    output = []
    with pytest.raises(SemanticError, match=message):
        run_program("show(99)\n" + source, mode, output=output.append)
    assert output == []


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_nested_conditionals_in_blocks_loops_and_assignments(level):
    source = """
let i = 0
while i < 2 if True else False:
    let delta = 1 if i == 0 else 2
    i = i + delta
    show(i)
if True if i == 3 else False:
    let i = 5
    show(i if True else 0)
show(i)
"""
    interpreted, compiled = [], []
    run_program(source, "interpreter", output=interpreted.append)
    run_program(source, "compiler", opt=level, output=compiled.append)
    assert interpreted == compiled == ["1", "3", "5", "3"]


def test_condition_is_evaluated_before_only_the_selected_input():
    prompts, output = [], []
    responses = iter(["no", "done"])

    def answer(prompt):
        prompts.append(prompt)
        return next(responses)

    run_program('show(ask("then?") if ask("choose?") == "yes" else ask("else?"))',
                "interpreter", input_fn=answer, output=output.append)
    assert prompts == ["choose?", "else?"]
    assert output == ["done"]


def test_function_calls_returns_and_array_aliasing():
    output = []
    source = """
let calls = 0
function hit(n):
    calls = calls + 1
    return n if n > 0 else 0
show(hit(1) if False else hit(2))
show(calls)
let a = [1]
let b = [2]
let selected = a if True else b
selected[0] = 9
show(a[0])
show(b[0])
show(a[0 if True else 1])
"""
    run_program(source, "interpreter", output=output.append)
    assert output == ["2", "1", "9", "2", "9"]


def test_unknown_result_type_is_checked_by_its_consumer():
    source = """
function identity(value):
    return value
let result = identity("text") if True else 0
show(result + 1)
"""
    with pytest.raises(StudyLangRuntimeError, match="requires integer or float"):
        run_program(source, "interpreter")


def test_unknown_condition_requires_boolean_at_runtime():
    source = """
function choose(flag):
    return 1 if flag else 0
show(choose(1))
"""
    with pytest.raises(StudyLangRuntimeError, match="Conditional condition requires boolean"):
        run_program(source, "interpreter")


def test_generated_ir_uses_branching_and_phi():
    text = compile_source("let correct = True\nshow(1 if correct else 0)")
    with llvm.parse_assembly(text) as module:
        module.verify()
    assert "conditional_then" in text
    assert "conditional_else" in text
    assert "conditional_merge" in text
    assert 'phi  i64' in text


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_selected_runtime_failure_is_preserved(level):
    for mode in ["interpreter", "compiler"]:
        with pytest.raises(StudyLangRuntimeError, match="Division by zero"):
            run_program("show(1 / 0 if True else 2 / 1)", mode,
                        opt=level if mode == "compiler" else 0)


def test_compiler_checks_even_unselected_unsupported_alternatives():
    source = 'show("yes" if True else "no")'
    output = []
    run_program(source, "interpreter", output=output.append)
    assert output == ["yes"]
    with pytest.raises(CompilationError, match="does not support expression: String"):
        run_program(source, "compiler")


def test_numeric_example_through_launcher_at_all_levels():
    sample = ROOT / "Examples" / "m11_numeric.tiny"
    for mode, level in [("interpreter", 0), ("compiler", 0), ("compiler", 1),
                        ("compiler", 2), ("compiler", 3)]:
        command = [sys.executable, str(ROOT / "main.py"), "--mode", mode, "--file", str(sample)]
        if mode == "compiler":
            command.extend(["--opt", str(level)])
        result = subprocess.run(command, text=True, capture_output=True, timeout=20)
        assert result.returncode == 0, result.stderr
        assert result.stdout == "1\n0.0\n1\ntrue\n"


@pytest.mark.parametrize(("answer", "expected"), [
    ("let", ["Correct!", "loop"]),
    ("wrong", ["Review let", "let", "loop"]),
])
def test_study_example(answer, expected):
    output = []
    source = (ROOT / "Examples" / "m11_study.tiny").read_text()
    run_program(source, "interpreter", input_fn=lambda prompt: answer, output=output.append)
    assert output == expected
