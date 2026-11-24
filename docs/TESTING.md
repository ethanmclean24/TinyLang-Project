# Testing and troubleshooting

## Verification commands

From the project directory, run the complete suite with Python 3.10 or newer.
VS Code's pytest configuration selects `tests/`.

```sh
python3 -m pip install -r requirements.txt
python3 -m pytest -q
```

The latest verification passed **266 tests and 47 subtests** on Python 3.12
with Lark 1.3.1, llvmlite 0.50.0, and LLVM 22.1.0 on Apple Silicon macOS.
The suite includes the M0–M9 regressions and M10 integration tests. Current
verification results are recorded here so milestone documents can focus on
their implementation and evidence.

For individual stages and demonstrations:

```sh
python3 tests/check_milestone1.py
python3 tests/test_parser.py
python3 -m unittest discover -s tests -p 'test_m3_m5.py' -v
python3 -m Shared.frontend
python3 -m tools.inspect_tokens
python3 -m tools.demo1_validate
python3 -m Shared.semantic
python3 -m pytest -q tests/test_interpreter.py
python3 -m pytest -q tests/test_codegen.py
python3 -m pytest -q tests/test_integration.py
```

`Shared.frontend` prints source, parse tree, and AST. Token inspection prints
contextual tokens and indentation markers. The M6 demonstration validates AST
shape, traversal, metrics, and precedence. The semantic demonstration checks
positive and negative programs. These tools inspect or validate source without
executing its StudyLang statements.

## Executable smoke checks

```sh
python3 main.py --mode interpreter --file Examples/m9_demo.tiny
python3 main.py --mode compiler --file Examples/m9_demo.tiny --opt 2
python3 -m Interpreter.run Examples/m9_demo.tiny
python3 -m Compiler.run Examples/m9_demo.tiny --opt 2
python3 Compiler/run.py Examples/m9_demo.tiny --emit-ir
```

Every execution command above prints `6`, `2.0`, and `true` on separate lines.
The final command prints verified LLVM IR without executing the program.
Integration tests also launch both runner scripts from a different working
directory using absolute source paths, and exercise the interactive launcher.
The [M10 comparison matrix](M10_EVIDENCE.md#comparison-matrix) records expected
and actual behavior for both execution modes.

## Troubleshooting

| Symptom | Explanation and action |
| --- | --- |
| Import failure after the reorganization | Use imports such as `Shared.frontend`, `Interpreter.run`, and `Compiler.compiler`. Start module commands from the project directory. |
| Compilation error for strings, arrays, input, or functions | The compiler implements the agreed numeric and Boolean subset. Select interpreter mode for full-language programs. |
| LLVM options rejected in interpreter mode | Select compiler mode for `--opt`, `--show-ir`, and `--show-optimized-ir`. |
| File error | Check `--file` or the entered path, including the capitalized `Examples/` directory. Explicit relative paths use the working directory; default and numbered examples use the project directory. |
| Missing llvmlite dependency | Run `python3 -m pip install -r requirements.txt` using Python 3.10 or newer. Official binary wheels include the LLVM runtime. |
| Extra IR in captured output | Omit IR display flags when comparing program output. Use `python3 -m Compiler.run ... --emit-ir` to inspect IR separately. |
| Integer overflow in compiler mode | The signed 64-bit backend reports overflow. Interpreter mode provides Python integer arithmetic. |
| Different IR block/declaration counts | Optimization folds constants and removes unused code. Compare O0 and O2 while checking observable results. |
| Menu cancelled at end of input or with Ctrl+C | The launcher reports cancellation and exits with status 130. |

Runtime, source, and file failures return status 1. Invalid CLI arguments
return status 2. Successful execution and selecting exit return status 0.
Lark may list expected tokens in a different order between processes; the
integration tests compare the error content without relying on that order.

The [llvmlite installation documentation](https://llvmlite.readthedocs.io/en/v0.50.0/admin-guide/install.html)
provides details about binary packages and their LLVM dependency.
