from pathlib import Path
import subprocess
import sys

from llvmlite import binding as llvm
import pytest

from Compiler.compiler import CompilationError, Compiler
from Compiler.run import compile_source
from Shared.frontend import parse
from Interpreter.interpreter import Interpreter, StudyLangRuntimeError
from Compiler.jit import run_ir
from Interpreter.run import run
from Shared.semantic import SemanticError

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('expression', [
    '-2 + 3.5', '4 - 2', '2 * 3', '6 / 2', '8 % 3',
    '-8 % 3', '8 % -3', '-8 % -3', '-9 % 3',
    '1.5 + 2.25', '3.5 - 1', '2.5 * 2',
    '2 == 2', '2 != 2.5', '2 < 3', '2 <= 2', '3 > 2', '3 >= 3',
    '2.5 < 3', '2.5 <= 2', '2.5 > 2', '2.5 >= 3',
    '2 < 2.5', '2 <= 2.5', '2 > 2.5', '2 >= 2.5', '2 == 2.5',
    '2.5 != 2', '2.5 == 2', '2 != 2.5', '2.5 < 3.5',
    'True == False', 'True != False', 'not False and True or False',
    'False and 1 / 0 == 0', 'True or 1 % 0 == 0',
    '(True and False) or (not False and True)',
    '-9223372036854775808 % -1',
    '(9007199254740992 + 1) == (9007199254740992 / 1)',
    '(9007199254740992 + 1) > (9007199254740992 / 1)',
    '(9007199254740992 / 1) < (9007199254740992 + 1)',
    '(9007199254740992 + 1) != (9007199254740992 / 1)',
    '1 < -9223372036854775808 / 1',
    '1 < (4611686018427387904 / 1) * 2',
])
def test_native_expressions_match_interpreter(expression):
    source = f'show({expression})'
    expected, actual = [], []
    run(source, Interpreter(output=expected.append))
    text = compile_source(source)
    with llvm.parse_assembly(text) as module:
        module.verify()
    assert run_ir(text, output=actual.append) == 0
    assert actual == expected


@pytest.mark.parametrize(('source', 'expected'), [
    ('let x = 5\nlet y = 10\nshow(x + y * 2)', ['25']),
    ('let x = 4\nlet ok = x % 2 == 0\nif ok and not False:\n    show(x)\nelse:\n    show(0)', ['4']),
    ('let x = 5 / 2\nshow(x)\nshow(x + 1.25)', ['2.5', '3.75']),
    ('let x = 10\nif True:\n    x = 15\nshow(x)', ['15']),
    ('let x = 10\nif True:\n    let x = 20\n    show(x)\nshow(x)', ['20', '10']),
    ('let i = 0\nwhile i < 4:\n    show(i)\n    i = i + 1', ['0', '1', '2', '3']),
])
def test_instructor_examples(source, expected):
    actual = []
    run_ir(compile_source(source), output=actual.append)
    assert actual == expected


def test_nested_loops_shadowing_and_branch_assignments():
    source = '''
let score = 1
let i = 0
while i < 2:
    let score = score + 1
    let j = 0
    while j < 2:
        let local = j
        score = score + local
        j = j + 1
    if i == 0:
        show(score)
    else:
        let score = False
        show(score)
    i = i + 1
show(score)
if False:
    show(999)
while False:
    show(999)
'''
    actual, expected = [], []
    run(source, Interpreter(output=expected.append))
    run_ir(compile_source(source), output=actual.append)
    assert actual == expected == ['3', 'false', '1']


@pytest.mark.parametrize(('source', 'message'), [
    ('show(1 / 0)', 'Division by zero'),
    ('show(1 % 0)', 'Modulo by zero'),
    ('show(4611686018427387904 * 2)', 'signed 64-bit range'),
    ('show(-9223372036854775808 - 1)', 'signed 64-bit range'),
    ('show(4611686018427387904 + 4611686018427387904)', 'signed 64-bit range'),
    ('while True:\n    show(1)', 'Loop iteration safety limit exceeded'),
])
def test_native_runtime_errors_stop_execution(source, message):
    output = []
    compiler = Compiler(max_loop_iterations=2)
    text = compiler.compile(parse(source + '\nshow(999)\n'))
    with pytest.raises(StudyLangRuntimeError, match=message):
        run_ir(text, output=output.append)
    assert '999' not in output


@pytest.mark.parametrize('source', [
    'show("hello")', 'show(ask("Ready?"))', 'let items = [1]',
    'for item in []:\n    show(item)',
    'function f():\n    return 1\nshow(f())',
    'if False:\n    show("unsupported")',
])
def test_unsupported_constructs_fail_during_compilation(source):
    with pytest.raises(CompilationError, match='LLVM backend does not support'):
        compile_source('show(1)\n' + source)


@pytest.mark.parametrize('source', ['show(9223372036854775808)', 'show(' + '9' * 400 + ')'])
def test_literals_outside_backend_range_are_rejected(source):
    with pytest.raises(CompilationError):
        compile_source(source)


def test_semantic_validation_and_compiler_reuse():
    compiler = Compiler()
    with pytest.raises(SemanticError, match='Undefined variable'):
        compiler.compile(parse('show(missing)\n'))
    for value in [1, 2]:
        output = []
        text = compiler.compile(parse(f'let score = {value}\nshow(score)\n'))
        run_ir(text, output=output.append)
        assert output == [str(value)]


def test_loop_limit_allows_exactly_the_configured_iterations():
    text = Compiler(max_loop_iterations=2).compile(parse(
        'let i = 0\nwhile i < 2:\n    i = i + 1\nshow(i)\n'
    ))
    output = []
    run_ir(text, output=output.append)
    assert output == ['2']


def test_output_exception_is_propagated_and_stops_native_execution():
    calls = []

    def fail(value):
        calls.append(value)
        raise ValueError('output unavailable')

    with pytest.raises(ValueError, match='output unavailable'):
        run_ir(compile_source('show(1)\nshow(2)'), output=fail)
    assert calls == ['1']


def test_verified_ir_and_jit_through_cli():
    sample = ROOT / 'Examples' / 'm9_demo.tiny'
    emitted = subprocess.run(
        [sys.executable, str(ROOT / 'Compiler' / 'run.py'), str(sample), '--emit-ir'],
        text=True, capture_output=True, timeout=20,
    )
    assert emitted.returncode == 0, emitted.stderr
    with llvm.parse_assembly(emitted.stdout) as module:
        module.verify()
    executed = subprocess.run(
        [sys.executable, str(ROOT / 'Compiler' / 'run.py'), str(sample)],
        text=True, capture_output=True, timeout=20,
    )
    assert executed.returncode == 0, executed.stderr
    assert executed.stdout.splitlines() == ['6', '2.0', 'true']


@pytest.mark.parametrize(('source', 'message'), [
    ('show(1 / 0)', 'Runtime error: Division by zero'),
    ('show(missing)', 'Compilation error: Undefined variable'),
    ('show("hello")', 'Compilation error: LLVM backend does not support'),
])
def test_cli_error_reporting(tmp_path, source, message):
    file = tmp_path / 'invalid.tiny'
    file.write_text(source)
    result = subprocess.run(
        [sys.executable, str(ROOT / 'Compiler' / 'run.py'), str(file)],
        text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 1
    assert result.stdout == ''
    assert message in result.stderr
