# StudyLang

**Version** 0.1

**Author** Ethan McLean

**Current milestone** M10 — Integration, Testing, and Debugging

A simple language with easy inputs and outputs that makes it easy for students
to add course materials, such as terms or questions, and study using console
input/output. StudyLang is intended for students with little prior programming
experience. Its design emphasizes simplicity, readability, built-in input/output,
and explicit variable declarations.

## Setup and execution

Use Python 3.10 or newer. From the project directory:

```sh
python3 -m pip install -r requirements.txt
python3 main.py
```

The launcher offers interpreter or compiler mode, a numbered example list,
and custom file paths. Use `B` in the file chooser to return to mode selection
or `Q` at mode selection to exit. Compiler mode also offers optimization and
IR display options. The selected program runs once and then the launcher exits.
VS Code's Run Python File button works with `main.py`.

For direct command-line execution:

```sh
python3 main.py --mode interpreter --file Examples/m3_m5_demo.tiny
python3 main.py --mode compiler --file Examples/m9_demo.tiny --opt 2
python3 main.py --mode compiler --file Examples/m10_scope.tiny --opt 2 --show-ir --show-optimized-ir
```

The study-session example prompts twice. Try answering `yes` and then `no`.
The compiler demo prints `6`, `2.0`, and `true` on separate lines.

Explicit `--mode` skips menu prompts and uses `Examples/m9_demo.tiny` if no
file is supplied. Compiler CLI execution defaults to O0. Interactive compiler
mode defaults to O2, following the instructor menu. O0 verifies IR without
an optimization pipeline; O1–O3 run LLVM's corresponding pipelines.
`--show-ir` and `--show-optimized-ir` display IR and then execute the program.

The individual runners also support module and direct-script execution:

```sh
python3 -m Interpreter.run Examples/m8_scope.tiny
python3 -m Compiler.run Examples/m9_demo.tiny --opt 2
python3 -m Compiler.run Examples/m9_demo.tiny --opt 2 --emit-ir
```

Use `Interpreter/run.py` or `Compiler/run.py` as the script path for direct
execution. `--emit-ir` prints verified IR without executing it. The compiler
and interpreter runners perform structural and semantic checks before execution.

## Project layout

| Path | Purpose |
| --- | --- |
| `main.py` | Interactive and command-line launcher |
| `Compiler/` | LLVM compiler, optimizer, JIT, and standalone runner |
| `Interpreter/` | Tree-walking runtime and standalone runner |
| `Shared/` | Grammar, AST, frontend, validation, semantics, project identity, and shared runtime error |
| `Examples/` | StudyLang source examples |
| `tools/` | Token inspection and AST validation demonstrations |
| `tests/` | Parser, semantic, interpreter, compiler, and integration tests |
| `docs/` | Architecture, language reference, milestone evidence, and testing notes |
| `requirements.txt` | Python dependencies |

Both modes use one shared frontend and AST. Python imports use package names
such as `Shared.frontend`, `Interpreter.run`, and `Compiler.compiler`.
See [the architecture](docs/ARCHITECTURE.md) for the integration diagram.

## Language and execution modes

| Feature | Interpreter | Compiler |
| --- | --- | --- |
| Numbers, Booleans, variables, and assignment | Supported | Supported |
| Arithmetic, comparison, and logical operators | Supported | Supported |
| `show`, `if`/`else`, and `while` | Supported | Supported |
| Strings and `ask` | Supported | Compilation error |
| Mixed/nested arrays, indexing, and `for` | Supported | Compilation error |
| Functions, recursion, and captured scopes | Supported | Compilation error |

The compiler's numeric and Boolean subset is a deliberate scope decision,
following the instructor example and the guide's supported-subset allowance.
Full-language compilation would require a substantially larger runtime for
mixed values, memory management, and captured environments. Signed 64-bit
integer limits and host JIT dependencies also apply. The detailed boundaries
and reasoning are in [the compiler notes](docs/M9_EVIDENCE.md#backend-limitations).

M0–M7 language/frontend/validation work, the M8 interpreter, M9 compiler subset,
and M10 integration and optimization are implemented. M11–M12 extensions are
upcoming milestones.

## Testing and documentation

Run the full suite with `python3 -m pytest -q`.

| Document | Contents |
| --- | --- |
| [FRONTEND.md](docs/FRONTEND.md) | Language syntax, tokens, AST, structural validation, and semantic rules |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Current module layout and execution paths |
| [M8_EVIDENCE.md](docs/M8_EVIDENCE.md) | Runtime scopes, function capture, and source/output traces |
| [M9_EVIDENCE.md](docs/M9_EVIDENCE.md) | LLVM mappings, annotated IR, and compiler limitations with reasoning |
| [M10_EVIDENCE.md](docs/M10_EVIDENCE.md) | Both-mode comparison matrix and optimization evidence |
| [TESTING.md](docs/TESTING.md) | Verification commands, current results, and troubleshooting |
