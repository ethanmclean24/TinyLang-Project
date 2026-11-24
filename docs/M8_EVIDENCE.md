# M8 — Interpreter and runtime environments

The interpreter executes all constructs accepted by the shared grammar and
semantic analyzer. Its public APIs are `Interpreter.run.run(source)` and
`Interpreter.interpreter.Interpreter.execute(program)`.

The `m7-baseline` tag retains the pre-M8 snapshot required by the guide.
Verification commands and current results are maintained in
[TESTING.md](TESTING.md).

## Supported AST nodes

| AST nodes | Execution |
| --- | --- |
| `Program`, `Block` | Execute statements in order in the supplied scope |
| `Number`, `Boolean`, `String` | Produce literal values |
| `Variable` | Look up the closest visible binding |
| `BinaryOp`, `Not` | Arithmetic, comparisons, and Boolean operations with short-circuiting |
| `Conditional` (M11) | Evaluate the Boolean condition and the selected alternative |
| `Array`, `Index` | Build arrays and read checked indices, including nested indices |
| `Ask` | Evaluate the prompt and read a line of input |
| `Call` | Evaluate arguments and execute a function in its lexical scope |
| Built-in `Call` (M12) | Query array length or membership through a resolved predefined function |
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

Run `python3 Interpreter/run.py Examples/m8_scope.tiny`. The runner parses the source,
validates its AST, and checks names and types before interpreting the blocks.

| Source event | Expected | Actual |
| --- | --- | --- |
| Inner branch updates the enclosing local `score` from 10 to 12 | `12` | `12` |
| `read_score()` reads the global `score` visible at declaration | `1` | `1` |
| Enclosing branch prints its updated local `score` | `12` | `12` |
| Final branch updates the global `score` and the program prints it | `2` | `2` |

With answers `yes` and `no`, `Examples/m3_m5_demo.tiny` prompts for
`declaration` and `loop`. Expected and actual `show` output match,
in order: `Review this term`, `Practice again`, `50.0`, and `14`.
The CLI displays `ask` prompts inline.

A file containing `show(1 / 0)` passes semantic analysis because both
operands are numbers. The interpreter detects the zero divisor before
dividing. Expected and actual CLI results are exit status 1, empty stdout,
and `Runtime error: Division by zero` on stderr.

## Verification and guide coverage

The interpreter tests exercise every supported operator and statement,
scripted input/output, recursion, return propagation, captured bindings,
array aliasing, loop scopes, and invalid programs. They also check that
syntax or semantic errors prevent execution and input/output.
Runtime errors include invalid operand types, array bounds, zero divisors,
input exhaustion, recursion exhaustion, and the while-loop limit.

The shared both-mode instructor comparisons are recorded in
[M10_EVIDENCE.md](M10_EVIDENCE.md#comparison-matrix).

| M8 requirement | Evidence | Status |
| --- | --- | --- |
| Pre-M8 snapshot | `m7-baseline` tag | Complete |
| Tree-walking execution of grammar constructs | `Interpreter/interpreter.py`, supported-node table above | Complete |
| Runtime scopes, shadowing, and outer assignment | `Environment`, captured bindings, scope trace | Complete |
| Arithmetic, logic, output, branches, and loops | Interpreter tests and study-session example | Complete |
| Semantic validation before execution | `Interpreter/run.py`, invalid-program tests | Complete |
| Positive, negative, and nested-scope demonstrations | `tests/test_interpreter.py`, `Examples/m8_scope.tiny` | Complete |
| Design decision, handled error, and source/output evidence | Sections above | Complete |
