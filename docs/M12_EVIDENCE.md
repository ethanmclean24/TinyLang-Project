# M12 — Built-in collection queries

## Feature design and purpose

M12 implements the guide's final-language-extension option by completing two
collection operations needed by study programs. `len` lets a quiz derive its
question total from its data. `contains` lets one question accept multiple
correct answers. Together they resolve the hard-coded totals and single-answer
checks in earlier examples.

The final demonstration combines arrays, indexed access, a for loop, input,
functions supplied by the language, numeric scoring, and M11 conditional
expressions. This builds on the existing language vision and pipeline.

| Function | Arguments | Result |
| --- | --- | --- |
| `len(array)` | One array | Integer count of top-level elements |
| `contains(array, value)` | One array and one value | Boolean indicating whether an element matches |

Both functions use the existing call syntax and `Call` AST. Their names are
predefined functions in an enclosing scope outside the global scope. Ordinary
variable/function declarations can shadow them. A call resolves its name using
the same lexical rules as user functions.

## Intended semantics

- Arguments are evaluated once, from left to right, before the query runs.
- Both first arguments must be arrays. Strings and other values are rejected.
  Nested arrays count as individual top-level elements for `len`.
- Empty arrays have length zero, and membership in an empty array is false.
- `contains` compares the requested value against each top-level element using
  the interpreter's existing array-element equality helper. Numeric integer/float
  values can match. Booleans have a distinct type, so `contains([True], 1)` is
  false. Strings match exactly and case-sensitively. Nested arrays are compared
  structurally, including self-referencing arrays.
- The queries observe current array contents and preserve their contents,
  order, and aliases. They return values for use in expressions.

Semantic analysis knows each builtin's argument count and result type.
Known non-array first arguments are rejected before execution. Unknown first
arguments, such as untyped parameters and function results, receive a runtime
array check. The resulting integer or Boolean type is used by normal operator,
assignment, and condition checks.

Predefined names share the existing namespace rules. A function declared before
a later `len` variable captures the original builtin binding. A local user
function named `contains` follows its own arity and parameter rules. Static
analysis marks the resolved builtin symbol explicitly, and the interpreter
checks the resolved runtime callable.

## Implementation changes

| Layer | Implementation |
| --- | --- |
| Signature definitions | `Shared/builtins.py` defines immutable `Builtin` descriptions with name, arity, and result type |
| Grammar/AST | Existing named calls represent the queries and their arguments |
| Semantic analysis | `Shared/semantic.py` installs the predefined scope, marks builtin symbols, and checks argument/result types |
| Runtime environments | `Interpreter/interpreter.py` installs the same descriptions in a parent environment on each execution |
| Query execution | The resolved builtin evaluates arguments and applies array validation; membership reuses `_equal` |
| LLVM backend | `Compiler/compiler.py` gives an explicit interpreter-only diagnostic for builtin queries |
| Demonstration and tests | `Examples/m12_quiz.tiny` and `tests/test_builtins.py` |

The shared signatures keep the semantic and runtime definitions consistent.
Using existing call nodes and equality logic keeps the extension small and
makes its behavior consistent with the language already implemented.

## Runnable demonstration

Run the following from the project directory.

```sh
python3 main.py --mode interpreter --file Examples/m12_quiz.tiny
```

The example source is below.

```text
let questions = ["What declares a variable? ", "What repeats while a condition is true? "]
let accepted = [["let", "variable declaration"], ["while", "while loop"]]
let correct = 0
let index = 0
for question in questions:
    let answer = ask(question)
    let matched = contains(accepted[index], answer)
    show("Correct!" if matched else "Review this topic")
    correct = correct + (1 if matched else 0)
    index = index + 1
show(correct)
show(len(questions))
show(correct * 100 / len(questions))
```

Expected and actual `show` output matched in both scripted test scenarios.
The corresponding input prompts appear before feedback during terminal use.

| Answers | Expected output | Actual output |
| --- | --- | --- |
| `let`, `while loop` | `Correct!`, `Correct!`, `2`, `2`, `100.0` | Same |
| `wrong`, `while` | `Review this topic`, `Correct!`, `1`, `2`, `50.0` | Same |

## Rejected programs and runtime checks

| Program | Expected and actual behavior |
| --- | --- |
| `show(len())` | Semantic error for wrong argument count |
| `show(contains([]))` | Semantic error for wrong argument count |
| `show(len("text"))` | Semantic error requiring an array |
| `show(contains(1, 1))` | Semantic error requiring an array |
| `if len([]):` with a body | Semantic error requiring a Boolean condition |
| `show(contains([], 1) + 1)` | Semantic error requiring numeric operands |
| Untyped parameter holding a number passed to either query | Runtime error requiring an array |
| `show(len([]))` in compiler mode | Compilation error directing the user to interpreter mode |

Syntax and semantic errors are detected before StudyLang execution or input/output.
In a runtime type failure, earlier executed statements retain their normal
observable effects.

## Review and regression evidence

The implementation review checked builtin lookup against ordinary functions
and variable shadowing, including captures made before a later shadowing
declaration. It also checked argument evaluation order, type-aware comparison,
cyclic arrays, interpreter reuse, and the compiler's explicit rejection path.
The tests exercise these cases and the command-line launcher.

The focused suite passed 38 new cases. The final regression run passed
388 tests and 47 subtests, including the earlier milestone tests.
Current commands and environment details are maintained in
[TESTING.md](TESTING.md).

## Remaining limitations and trade-offs

These functions operate on arrays. They preserve exact string matching, so
applications can list alternative spellings explicitly in their accepted
answer arrays. Answer normalization and automatic numeric input conversion
are possible future language capabilities.

The compiler supports the documented numeric and Boolean subset, including
M11 conditional expressions. Array queries execute in interpreter mode because
their array representation and equality operations are implemented there.
The complete backend boundaries are recorded in
[M9_EVIDENCE.md](M9_EVIDENCE.md#backend-limitations).

User-defined function parameters and results still use deferred type checks
where semantic analysis cannot determine their types. The query return types
are known because the builtins have fixed signatures.

`len` uses the array's stored length. `contains` examines elements until a match
is found or the array is exhausted; nested structural comparisons add work.
The extension focuses on read-only queries and reuses the existing array
representation and memory management.

## Guide coverage

| M12 requirement | Evidence | Status |
| --- | --- | --- |
| Complete a final capability or important feature gap | Data-derived quiz totals and multiple accepted answers | Complete |
| Explain why it fits the language | Study-session purpose and integrated example above | Complete |
| Update specifications and relevant pipeline behavior | Shared signatures, semantics, interpreter, compiler diagnostic, and documentation | Complete |
| Demonstrate successful and rejected programs | Quiz scenarios and negative-program table | Complete |
| Run final regression tests | Full suite and focused M12 tests | Complete |
| State remaining limitations | Array-only, interpreter-only queries and existing deferred typing documented above | Complete |
