# M8 — Interpreter and runtime environments

## M7 baseline

Local tag `m7-baseline` points to `76d19f9`. Before editing, pytest reported
75 passing tests and 47 passing subtests. The standalone parser suite passed
19/19 cases, the M3–M5 unittest suite passed 10/10, and the M1 readiness check,
M6 demonstration, and M7 semantic demonstration passed.

M7 leaves types unknown for function parameters, call results, and array
elements. M8 checks their concrete types when evaluating
those operations. The existing grammar, AST definitions, parser API, and
semantic analyzer carry forward without edits. M8 adds `run.run(source)`
and `Interpreter.execute(program)`.

## Supported AST nodes

| AST nodes | Execution |
| --- | --- |
| `Program`, `Block` | Execute statements in order in the supplied scope |
| `Number`, `Boolean`, `String` | Produce literal values |
| `Variable` | Look up the closest visible binding |
| `BinaryOp`, `Not` | Arithmetic, comparisons, and Boolean operations with short-circuiting |
| `Array`, `Index` | Build arrays and read checked indices, including nested indices |
| `Ask` | Evaluate the prompt and read a line of input |
| `Call` | Evaluate arguments and execute a function in its lexical scope |
| `Let`, `Assignment` | Declare a local value or update an existing binding or array slot |
| `Show` | Print the evaluated value |
| `If`, `While`, `For` | Select a branch or repeat a body, using a fresh scope for each block execution |
| `Function`, `Return` | Register a function and return a value to its caller |

## Design decision

Like the instructor example, the interpreter walks the validated AST and
uses parent-linked runtime environments. The semantic symbol table stores
type and arity information. Runtime bindings store the actual values.
Assignment finds the nearest existing binding, and a declaration can
introduce a shadowing binding in the current scope.

StudyLang functions capture the bindings visible at their declaration.
The function observes later assignments to those bindings because they
are shared. A declaration appearing later in the same block cannot
redirect a name that the semantic analyzer already resolved.

## Source-to-output traces

Run `python3 run.py examples/m8_scope.tiny`. The runner parses the source,
validates its AST, and checks names and types before interpreting the blocks.

| Source event | Expected | Actual |
| --- | --- | --- |
| Inner branch updates the enclosing local `score` from 10 to 12 | `12` | `12` |
| `read_score()` reads the global `score` visible at declaration | `1` | `1` |
| Enclosing branch prints its updated local `score` | `12` | `12` |
| Final branch updates the global `score` and the program prints it | `2` | `2` |

With answers `yes` and `no`, `examples/m3_m5_demo.tiny` prompts for
`declaration` and `loop`. Expected and actual `show` output match,
in order: `Review this term`, `Practice again`, `50.0`, and `14`.
The CLI displays `ask` prompts inline.

A file containing `show(1 / 0)` passes semantic analysis because both
operands are numbers. The interpreter detects the zero divisor before
dividing. Expected and actual CLI results are exit status 1, empty stdout,
and `Runtime error: Division by zero` on stderr.

## Test results

`python3 -m pytest -q` reported 128 passing tests and 47 passing subtests
on November 24, 2026, including 53 M8 tests.
The M8 tests cover operators, short-circuiting, scripted input and output,
scope and shadowing through the CLI, recursion, return from inside a loop,
nested array assignment, and syntax, semantic, and runtime failures.
Additional checks cover captured bindings after assignment, lexical scope
across function calls, fresh globals between executions, fresh loop scopes,
the else branch, empty loops, input exhaustion, recursion exhaustion, and
comparisons of self-referencing arrays. The standalone M1, M3–M5, M6, and
M7 checks also passed during this review.

## Instructor example comparison

All six supplied instructor examples were executed with the instructor's
interpreter. Equivalent programs using StudyLang syntax produced the same
output. The expected outputs are retained in `tests/test_interpreter.py`.

| Instructor example | Instructor output | StudyLang output |
| --- | --- | --- |
| arithmetic | `25` | `25` |
| boolean | `4` | `4` |
| fractional | `2.5`, `3.75` | `2.5`, `3.75` |
| outer_assignment | `15` | `15` |
| shadowing | `20`, `10` | `20`, `10` |
| while | `0`, `1`, `2`, `3` | `0`, `1`, `2`, `3` |

The common runtime behavior follows the instructor example, including
numeric literals, true division, lowercase Boolean output, lexical blocks,
outer assignment, short-circuiting, and the 100,000-iteration while limit.
StudyLang also executes its existing strings, input, arrays, for loops,
and functions. These features require input injection, checked indices,
captured bindings, and return propagation. Runtime type checks enforce
StudyLang's M7 rules where types were unknown during analysis.

The runner is `run.py`, following the instructor's interpreter entry point.
The combined interpreter/compiler launcher is addressed in M10 of the guide.
StudyLang-specific runtime choices are zero-based, nonnegative array indices,
preserving a variable's initial runtime type during reassignment, and an
error when a called function finishes without a return value.

## Guide coverage through M8

| Requirement | Evidence | Status |
| --- | --- | --- |
| Preserve earlier language and document interface changes | M7 baseline and supported nodes above, existing regression suite | Complete |
| Baseline snapshot and pre-M8 tests | Local `m7-baseline` tag and recorded results | Complete |
| Tree-walking execution of all grammar constructs | `interpreter.py` and interpreter tests | Complete |
| Runtime environments, shadowing, and outer assignment | `Environment`, captured bindings, scope demo and tests | Complete |
| Arithmetic, Boolean logic, output, branches, and loops | Operator tests, instructor comparisons, study-session demo | Complete |
| Separate semantic metadata and runtime values | `semantic.Symbol` and `interpreter.Binding` | Complete |
| Semantic validation before execution | `run.run` and invalid-program tests that check no I/O occurred | Complete |
| Positive and invalid programs and nested-scope demonstration | `tests/test_interpreter.py`, `examples/m8_scope.tiny` | Complete |
| Executable entry point, source/output traces, and results | `run.py` and traces above | Complete |
| Explain a design decision and an error handled | Captured bindings and division-by-zero discussion above | Complete |
