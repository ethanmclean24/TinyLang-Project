from pathlib import Path
import subprocess
import sys

from llvmlite import binding as llvm
import pytest

from Compiler.compiler import Compiler
from Compiler.run import compile_source
from Shared.frontend import parse
from Interpreter.interpreter import StudyLangRuntimeError
from Compiler.jit import run_ir
from main import run_program
from Compiler.optimizer import optimize_ir

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def launch(mode, file, *options, input_text=None):
    return subprocess.run(
        [sys.executable, str(MAIN), "--mode", mode, "--file", str(file), *options],
        text=True, input=input_text, capture_output=True, timeout=20,
    )


@pytest.mark.parametrize("level", [0, 1, 2, 3])
@pytest.mark.parametrize(("source", "expected"), [
    ("let x = 5\nlet y = 10\nshow(x + y * 2)", ["25"]),
    ("let x = 4\nlet ok = x % 2 == 0\nif ok and not False:\n    show(x)\nelse:\n    show(0)", ["4"]),
    ("let x = 5 / 2\nshow(x)\nshow(x + 1.25)", ["2.5", "3.75"]),
    ("let x = 10\nif True:\n    x = 15\nshow(x)", ["15"]),
    ("let x = 10\nif True:\n    let x = 20\n    show(x)\nshow(x)", ["20", "10"]),
    ("let i = 0\nwhile i < 4:\n    show(i)\n    i = i + 1", ["0", "1", "2", "3"]),
])
def test_instructor_examples_in_both_modes_at_all_levels(source, expected, level):
    interpreted, compiled = [], []
    run_program(source, "interpreter", output=interpreted.append)
    run_program(source, "compiler", opt=level, output=compiled.append)
    assert interpreted == compiled == expected


@pytest.mark.parametrize(("filename", "expected"), [
    ("m9_demo.tiny", ["6", "2.0", "true"]),
    ("m10_scope.tiny", ["12", "12", "1", "7"]),
])
def test_shared_examples_through_both_cli_modes(filename, expected):
    file = ROOT / "Examples" / filename
    interpreted = launch("interpreter", file)
    assert interpreted.returncode == 0, interpreted.stderr
    assert interpreted.stdout.splitlines() == expected
    for level in range(4):
        compiled = launch("compiler", file, "--opt", str(level))
        assert compiled.returncode == 0, compiled.stderr
        assert compiled.stdout == interpreted.stdout
        assert compiled.stderr == interpreted.stderr == ""


@pytest.mark.parametrize(("source", "prefix", "stdout"), [
    ("show(1)\nshow(", "Syntax error:", ""),
    ("show(1)\nshow(missing)", "Semantic error: Undefined variable: missing", ""),
    ("show(1)\nif True:\n    let local = 2\nshow(local)", "Semantic error: Undefined variable: local", ""),
    ("show(1)\nshow(1 / 0)", "Runtime error: Division by zero", "1\n"),
    ("show(1)\nshow(1 % 0)", "Runtime error: Modulo by zero", "1\n"),
    ("show(1)\nwhile True:\n    let local = 0", "Runtime error: Loop iteration safety limit exceeded", "1\n"),
])
def test_matching_cli_errors(tmp_path, source, prefix, stdout):
    file = tmp_path / "invalid.tiny"
    file.write_text(source)
    interpreted = launch("interpreter", file)
    assert interpreted.returncode == 1
    assert interpreted.stdout == stdout
    assert interpreted.stderr.startswith(prefix)
    for level in (0, 2):
        compiled = launch("compiler", file, "--opt", str(level))
        assert compiled.returncode == 1
        assert compiled.stdout == interpreted.stdout
        # Lark's expected-token set can print in a different order per process.
        assert sorted(compiled.stderr.splitlines()) == sorted(interpreted.stderr.splitlines())


def test_full_language_program_has_an_explicit_compiler_boundary(tmp_path):
    file = tmp_path / "strings.tiny"
    file.write_text('show(1)\nshow("hello")')
    interpreted = launch("interpreter", file)
    compiled = launch("compiler", file)
    assert interpreted.returncode == 0
    assert interpreted.stdout == "1\nhello\n"
    assert compiled.returncode == 1
    assert compiled.stdout == ""
    assert "Compilation error: LLVM backend does not support expression: String" in compiled.stderr


def test_integer_range_difference_is_reported(tmp_path):
    file = tmp_path / "overflow.tiny"
    file.write_text("show(4611686018427387904 * 2)")
    interpreted = launch("interpreter", file)
    compiled = launch("compiler", file, "--opt", "2")
    assert interpreted.returncode == 0
    assert interpreted.stdout == "9223372036854775808\n"
    assert compiled.returncode == 1
    assert "Integer result exceeds signed 64-bit range" in compiled.stderr


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_optimization_preserves_edge_cases_and_short_circuiting(level):
    source = """
show(-8 % 3)
show(8 % -3)
show(-9223372036854775808 % -1)
show(False and 1 / 0 == 0)
show(True or 1 % 0 == 0)
show((9007199254740992 + 1) > (9007199254740992 / 1))
show(((True and False) or True) and not False)
"""
    interpreted, compiled = [], []
    run_program(source, "interpreter", output=interpreted.append)
    run_program(source, "compiler", opt=level, output=compiled.append)
    assert compiled == interpreted == ["1", "-1", "0", "false", "true", "true", "true"]


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_optimizer_can_remove_unused_output_functions(level):
    text = optimize_ir(compile_source("let x = 1"), level)
    assert run_ir(text) == 0


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_optimization_preserves_runtime_guards_and_output_failures(level):
    overflow = compile_source("show(4611686018427387904 * 2)")
    with pytest.raises(StudyLangRuntimeError, match="signed 64-bit range"):
        run_ir(optimize_ir(overflow, level))
    loop = Compiler(max_loop_iterations=2).compile(parse("while True:\n    let x = 1\n"))
    with pytest.raises(StudyLangRuntimeError, match="Loop iteration safety limit exceeded"):
        run_ir(optimize_ir(loop, level))
    calls = []

    def fail(value):
        calls.append(value)
        raise ValueError("output unavailable")

    with pytest.raises(ValueError, match="output unavailable"):
        run_ir(optimize_ir(compile_source("show(1)\nshow(2)"), level), output=fail)
    assert calls == ["1"]


def test_o0_and_optimized_ir_are_verified_and_different():
    raw = compile_source("let score = 2 + 3\nshow(score)")
    o0 = optimize_ir(raw, 0)
    o2 = optimize_ir(raw, 2)
    for text in (o0, o2):
        with llvm.parse_assembly(text) as module:
            module.verify()
    assert "alloca" in o0
    assert "alloca" not in o2
    assert "studylang_show_integer(i64 5)" in o2
    actual = []
    run_ir(o2, output=actual.append)
    assert actual == ["5"]


@pytest.mark.parametrize("level", [-1, 4, True])
def test_invalid_optimization_levels_are_rejected(level):
    with pytest.raises(ValueError, match="Optimization level"):
        optimize_ir(compile_source("show(1)"), level)


def test_interactive_interpreter(tmp_path):
    file = tmp_path / "interactive.tiny"
    file.write_text('show(ask("Ready?"))')
    result = subprocess.run(
        [sys.executable, str(MAIN)], input=f"1\nP\n{file}\nyes\n",
        text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "Ready?yes\n" in result.stdout


def test_interactive_compiler():
    file = ROOT / "Examples" / "m9_demo.tiny"
    result = subprocess.run(
        [sys.executable, str(MAIN)], input=f"2\nP\n{file}\n\nn\nn\n",
        text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.endswith("6\n2.0\ntrue\n")


def test_interactive_numbered_file_selection_and_ir_options():
    examples = sorted((ROOT / "Examples").glob("*.tiny"))
    selection = examples.index(ROOT / "Examples" / "m10_scope.tiny") + 1
    result = subprocess.run(
        [sys.executable, str(MAIN)], input=f"2\n{selection}\n2\ny\ny\n",
        text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "LLVM IR before optimization" in result.stdout
    assert "LLVM IR at O2" in result.stdout
    assert result.stdout.endswith("Program output\n12\n12\n1\n7\n")


def test_interactive_back_and_exit():
    result = subprocess.run(
        [sys.executable, str(MAIN)], input="invalid\n1\nB\nQ\n",
        text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 0
    assert "Choose 1, 2, or Q." in result.stdout
    assert result.stdout.count("Choose execution mode:") == 3


def test_ir_display_and_execution():
    result = launch("compiler", ROOT / "Examples" / "m9_demo.tiny", "--opt", "2",
                    "--show-ir", "--show-optimized-ir")
    assert result.returncode == 0, result.stderr
    assert "LLVM IR before optimization" in result.stdout
    assert "LLVM IR at O2" in result.stdout
    assert result.stdout.endswith("Program output\n6\n2.0\ntrue\n")


def test_default_example_is_resolved_independently_of_working_directory(tmp_path):
    result = subprocess.run(
        [sys.executable, str(MAIN), "--mode", "compiler"], cwd=tmp_path,
        text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "6\n2.0\ntrue\n"


@pytest.mark.parametrize("options", [
    ["--mode", "interpreter", "--opt", "2"],
    ["--mode", "interpreter", "--show-ir"],
    ["--mode", "compiler", "--opt", "4"],
])
def test_invalid_cli_options(options):
    result = subprocess.run([sys.executable, str(MAIN), *options],
                            text=True, capture_output=True, timeout=20)
    assert result.returncode == 2
    assert "error:" in result.stderr


@pytest.mark.parametrize("mode", ["interpreter", "compiler"])
def test_missing_files_are_reported(tmp_path, mode):
    result = launch(mode, tmp_path / "missing.tiny")
    assert result.returncode == 1
    assert "File error:" in result.stderr


def test_legacy_compiler_runner_accepts_optimization():
    result = subprocess.run(
        [sys.executable, str(ROOT / "Compiler" / "run.py"),
         str(ROOT / "Examples" / "m9_demo.tiny"), "--opt", "2"],
        text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "6\n2.0\ntrue\n"


@pytest.mark.parametrize("package", ["Interpreter", "Compiler"])
@pytest.mark.parametrize("entry_point", ["module", "script"])
def test_reorganized_package_entry_points(tmp_path, package, entry_point):
    sample = ROOT / "Examples" / "m9_demo.tiny"
    if entry_point == "module":
        command = [sys.executable, "-m", f"{package}.run", str(sample)]
        directory = ROOT
    else:
        command = [sys.executable, str(ROOT / package / "run.py"), str(sample)]
        directory = tmp_path
    result = subprocess.run(command, cwd=directory, text=True,
                            capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "6\n2.0\ntrue\n"
