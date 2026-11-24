# StudyLang

**Version** 0.1

**Author** Ethan McLean

**Current milestone** M12 — Built-in Collection Queries

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

`requirements.txt` specifies Lark 1.3.1, pytest 7 or newer, and llvmlite
0.47 through 0.50. Lark supplies the parser; llvmlite supplies LLVM code
generation, optimization, and MCJIT. Official llvmlite binary wheels include
the required LLVM runtime. The verified environment is Python 3.12 with
llvmlite 0.50.0 and LLVM 22.1.0 on Apple Silicon macOS. Verification details
are maintained in [TESTING.md](docs/TESTING.md).

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

## Example programs

| File in `Examples/` | Execution mode | Demonstrates |
| --- | --- | --- |
| `m3_m5_demo.tiny` | Interpreter | Study prompts, arrays, loops, functions, and scoring; try `yes`, then `no` |
| `m8_scope.tiny` | Interpreter | Nested scope, captured bindings, and outer assignment |
| `m9_demo.tiny` | Both | Numeric/Boolean core and LLVM execution |
| `m10_scope.tiny` | Both | Nested scopes and loop-local declarations |
| `m11_numeric.tiny` | Both | Conditional expressions and safe branch selection |
| `m11_study.tiny` | Interpreter | Conditional feedback and term selection; try `let` |
| `m12_quiz.tiny` | Interpreter | Multiple accepted answers and data-derived scores; try `let`, then `while loop` |
| `milestone1_examples.tiny` | Syntax/AST inspection | Original M1 design sketches; mixed string/number additions are rejected by semantic analysis |

## Language and execution modes

Blocks use a colon and exactly four additional spaces of indentation.
Comments start with `#`, and Boolean literals are `True` and `False`.
Declarations use `let name = expression`; assignment uses `name = expression`.
Expressions include `+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `<=`, `>`, `>=`,
`and`, `or`, and `not`. Input and output use `ask(prompt)` and `show(expression)`.
Complete statement syntax, token rules, and semantic checks are in
[FRONTEND.md](docs/FRONTEND.md).

| Feature | Interpreter | Compiler |
| --- | --- | --- |
| Numbers, Booleans, variables, and assignment | Supported | Supported |
| Arithmetic, comparison, and logical operators | Supported | Supported |
| `show`, `if`/`else`, and `while` | Supported | Supported |
| Conditional expressions | Supported | Numeric and Boolean alternatives |
| Strings and `ask` | Supported | Compilation error |
| Mixed/nested arrays, indexing, and `for` | Supported | Compilation error |
| `len(array)` and `contains(array, value)` | Supported | Compilation error |
| Functions, recursion, and captured scopes | Supported | Compilation error |

The compiler's numeric and Boolean subset is a deliberate scope decision,
following the instructor example and the guide's supported-subset allowance.
Full-language compilation would require a substantially larger runtime for
mixed values, memory management, and captured environments. Signed 64-bit
integer limits and host JIT dependencies also apply. The detailed boundaries
and reasoning are in [the compiler notes](docs/M9_EVIDENCE.md#backend-limitations).

M0–M7 language/frontend/validation work, the M8 interpreter, M9 compiler subset,
M10 integration and optimization, M11 conditional expressions, and M12
built-in collection queries are implemented.

## Conditional expressions

Choose a value directly inside an expression:

```text
let correct = True
let points = 1 if correct else 0
show(points)
```

The condition requires a Boolean and only the selected alternative executes.
Known alternative types must match. Conditional expressions have lower
precedence than `or`, and nesting in the `else` alternative associates to the
right. See [the M11 notes](docs/M11_EVIDENCE.md) for the full rules and examples.

```sh
python3 main.py --mode compiler --file Examples/m11_numeric.tiny --opt 2
python3 main.py --mode interpreter --file Examples/m11_study.tiny
```

## Built-in collection queries

`len(array)` counts top-level elements. `contains(array, value)` returns a
Boolean indicating whether an element matches the value. These array-only
functions let quizzes calculate their total and accept multiple correct answers.

```text
let accepted = ["let", "variable declaration"]
let answer = ask("What declares a variable? ")
show("Correct!" if contains(accepted, answer) else "Review this topic")
show(len(accepted))
```

The names are predefined functions that follow lexical shadowing rules.
Known non-array arguments and incorrect argument counts are semantic errors;
unknown argument types are checked at runtime. String matching is exact and
case-sensitive. The compiler reports an interpreter-only diagnostic for
these queries.

```sh
python3 main.py --mode interpreter --file Examples/m12_quiz.tiny
```

See [the M12 notes](docs/M12_EVIDENCE.md) for query semantics, the complete
quiz example, implementation decisions, and remaining limitations.

## Testing and documentation

Run the full suite with `python3 -m pytest -q`.

| Document | Contents |
| --- | --- |
| [FRONTEND.md](docs/FRONTEND.md) | Language syntax, tokens, AST, structural validation, and semantic rules |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Current module layout and execution paths |
| [M8_EVIDENCE.md](docs/M8_EVIDENCE.md) | Runtime scopes, function capture, and source/output traces |
| [M9_EVIDENCE.md](docs/M9_EVIDENCE.md) | LLVM mappings, annotated IR, and compiler limitations with reasoning |
| [M10_EVIDENCE.md](docs/M10_EVIDENCE.md) | Both-mode comparison matrix and optimization evidence |
| [M11_EVIDENCE.md](docs/M11_EVIDENCE.md) | Conditional expression specification, examples, tests, and trade-offs |
| [M12_EVIDENCE.md](docs/M12_EVIDENCE.md) | Built-in collection queries, quiz demonstration, review, and final limitations |
| [TESTING.md](docs/TESTING.md) | Verification commands, current results, and troubleshooting |
