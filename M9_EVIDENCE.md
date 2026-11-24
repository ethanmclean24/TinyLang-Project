# M9 — LLVM IR generation

## Changes and supported subset

M9 builds on the committed M8 implementation at `958c702`. The initial
regression suite passed 128 tests and 47 subtests. The new compiler uses
the same grammar, AST, structural validator, and semantic analyzer.

`codegen.Compiler.compile(program)` generates and verifies LLVM IR.
`compile_run.compile_source(source)` parses source and calls the compiler.
`jit.run_ir(ir_text, output=print)` verifies the generated module again,
creates a native target machine and MCJIT engine, and calls its `main`.
`compile_run.py` is the executable compiler entry point.

| StudyLang construct | LLVM representation or instruction |
| --- | --- |
| Whole-number literals | `i64` constants |
| Fractional literals | `double` constants |
| Boolean literals | `i1` constants |
| Declarations | Entry-block `alloca`, followed by `store` at declaration |
| Variable reads and assignments | `load` and `store` using the nearest lexical scope |
| Integer `+`, `-`, `*` | Signed arithmetic-with-overflow intrinsics and checked error branches |
| Floating arithmetic and `/` | `sitofp` when needed, then `fadd`, `fsub`, `fmul`, or `fdiv` |
| `%` | `srem` with zero/overflow guards and sign correction |
| Comparisons | `icmp` or `fcmp`, producing `i1` |
| Mixed integer/float comparisons | Checked float-to-integer comparison that preserves large integer precision |
| `not` | Boolean inversion |
| `and`, `or` | Conditional branches and a `phi` value at the merge |
| `show` | Typed host output call, with checked output status |
| `if`/`else` | Then, else, and merge blocks |
| `while` | Test, body, and exit blocks, plus a loop counter |

The compiler's scope stack resolves shadowed names during code generation.
Each declared variable has a distinct storage location. Loop-local storage
is allocated once in the function entry block and initialized on each
execution of the declaration. Nested blocks can update outer variables.

## Annotated source, AST, and generated IR

This small program demonstrates a variable, numeric conversion, division,
and output. Expected interpreter and actual native output are both `2.0`.

```text
let correct = 6
show(correct / 3)
```

The existing frontend produces this AST.

```python
Program(statements=[Let(name='correct', value=Number(value=6.0)),
                    Show(expression=BinaryOp(op='/',
                                             left=Variable(name='correct'),
                                             right=Number(value=3.0)))])
```

The following is the generated `main` function, copied from verified IR.
The module also declares the three host output functions.

```llvm
define i32 @"main"()
{
entry:
  %"var_correct" = alloca i64
  br label %"program"
program:
  store i64 6, i64* %"var_correct"
  %"load_correct" = load i64, i64* %"var_correct"
  %"as_float" = sitofp i64 %"load_correct" to double
  %"as_float.1" = sitofp i64 3 to double
  %".4" = fcmp une double %"as_float.1",              0x0
  br i1 %".4", label %"check_ok", label %"runtime_error"
check_ok:
  %"arithmetic" = fdiv double %"as_float", %"as_float.1"
  %"output_status" = call i32 @"studylang_show_float"(double %"arithmetic")
  %".7" = icmp eq i32 %"output_status", 0
  br i1 %".7", label %"check_ok.1", label %"runtime_error.1"
runtime_error:
  ret i32 1
check_ok.1:
  ret i32 0
runtime_error.1:
  ret i32 %"output_status"
}
```

- `alloca i64` reserves storage for `correct`, and `store i64 6` initializes it.
- `load` reads the variable. `sitofp` converts the two integers to `double`,
  since StudyLang division produces a float.
- The `fcmp` and conditional branch guard against a zero divisor. The error
  block returns status 1, which the JIT runner turns into `Division by zero`.
- `fdiv` computes the result in native code. `studylang_show_float` delivers
  its formatted value through the configured output function.
- The output-status branch propagates failures from the output function.
  The final `ret i32 0` indicates successful execution.

Run `python3 compile_run.py examples/m9_demo.tiny --emit-ir` to inspect a
larger program's verified IR, including a while loop and a short-circuit
condition. Running the same command without `--emit-ir` prints the following.

```text
6
2.0
true
```

`python3 run.py examples/m9_demo.tiny` produces the same output.

## Instructor example and design decisions

The compiler follows the supplied `Compiler/compiler.py`: `i64`, `double`,
and `i1` types, a stack of lexical scopes, entry-block variable storage,
loads/stores, branching for conditionals and loops, and phi nodes for
short-circuit Boolean expressions. `jit.py` follows the instructor's
native-target and MCJIT execution approach.

StudyLang keeps its existing `codegen.py` module name and `Program` AST
wrapper. Each compilation starts with a fresh module so a compiler object
can be reused. The public compiler entry point runs structural and semantic
validation before generating IR.

The host output callbacks preserve StudyLang's established display format.
The instructor uses C `printf` with `%g`, which would print a whole-valued
float such as `2.0` as `2`. The typed callbacks keep the interpreter's
observable output. They are mapped per execution engine and kept alive
until the native call finishes. Arithmetic and control flow are compiled
to native instructions.

Native error branches handle zero division, zero modulo, integer overflow,
and the 100,000-iteration while limit. Modulo adjusts LLVM's truncated
remainder to match the interpreter for negative operands. Mixed comparisons
avoid rounding large integers to double before comparing them.

## Backend limitations

The numeric and Boolean compiler subset is the chosen scope for this project.
It follows the instructor's compiler and covers the M9 goals of lowering AST
nodes to LLVM types and instructions, verifying IR, and executing native code.
The guide explicitly permits a supported subset and requires clear reporting
of features that cannot be compiled. The M8 interpreter provides execution
for the full StudyLang language.

| Limitation | Reason for the chosen scope |
| --- | --- |
| Strings and `ask` | Native string representation, content comparison, input buffers, and storage lifetime would add a string runtime beyond the instructor's numeric and Boolean example. |
| Mixed-type arrays and indexing | Elements can contain different types, nested arrays, and shared or self-referencing arrays. Native support would need runtime type information, bounds checks, and a memory-management strategy. |
| `for` loops | StudyLang iterates over arrays. Native iteration depends on the array representation and element-access support. |
| Functions, calls, and returns | Untyped parameters and results need a native value representation and calling convention. Nested functions also need captured environments that preserve lexical scope and shared variable bindings. |
| Signed 64-bit integers | This matches the instructor's `i64` representation and maps directly to LLVM arithmetic. Arbitrary-precision integers would require additional runtime support. Explicit range and overflow errors enforce this boundary. |
| Host JIT execution | The backend demonstrates execution with the instructor's MCJIT approach. Output callbacks preserve StudyLang formatting and require the Python runner. Standalone executables and cross-compilation would need separate runtime linking and target configuration. |

These choices keep the compiler small enough to inspect and explain while
covering declarations, assignment, expressions, scope, branches, and loops.
Compiling all StudyLang features would expand both the compiler and its
runtime substantially. Additional language features remain available through
`python3 run.py path/to/program.tiny`.

- Strings, input, arrays/indexing, for loops, and functions/returns are
  outside this M9 subset. Their AST nodes raise `CompilationError` before
  execution, including in an unreachable branch. The M8 interpreter
  implements those features.
- Integers are signed 64-bit values. Out-of-range integer literals are
  compilation errors, and overflowing integer operations are runtime errors.
  This is a smaller integer range than the interpreter's Python integers.
- Floats use 64-bit IEEE doubles. Numeric literals retain the frontend's
  float-based parsing, and nonfinite literals are rejected by this backend.
- Generated IR depends on the output functions supplied by `jit.run_ir`.
  The module targets the current machine and is intended for this JIT runner.
- The compiler command provides IR inspection and execution. The guide's
  combined launcher and optimization work belong to M10.

## Verification and guide coverage

Tested on Apple Silicon macOS with Python 3.12, llvmlite 0.50.0, and LLVM
22.1.0. The dependency range is recorded in `requirements.txt`. Modern
llvmlite initializes LLVM core automatically; native target and assembly
printer initialization are performed before JIT execution.

`python3 -m pytest -q` passed 200 tests and 47 subtests, including 72 new M9
tests. These verify IR, all six adapted instructor examples, interpreter/native
output equivalence, nested scopes/loops, short-circuiting, runtime errors,
unsupported constructs, compiler reuse, and the command-line entry point.
An additional manual batch compared 486 mixed numeric boundary comparisons
with the interpreter. All matched. Infinity/NaN results from floating-point
arithmetic were also checked against interpreter comparisons and matched.

| M9 requirement | Evidence | Status |
| --- | --- | --- |
| Map AST nodes to LLVM types and instructions | Mapping table and `codegen.py` | Complete for documented subset |
| Generate valid IR and report unsupported features | `Compiler.compile`, LLVM verification, negative tests | Complete |
| Show source and readable IR with an explanation | Annotated source/AST/IR example above | Complete |
| Verify IR and demonstrate JIT execution | `jit.py`, `compile_run.py`, example and execution tests | Complete |
| Document backend limitations | Limitations above and README | Complete |

References for the LLVM Python APIs and binary installation are available
in the [llvmlite execution engine documentation](https://llvmlite.readthedocs.io/en/v0.50.0/user-guide/binding/execution-engine.html),
[initialization documentation](https://llvmlite.readthedocs.io/en/v0.50.0/user-guide/binding/initialization-finalization.html),
and [installation documentation](https://llvmlite.readthedocs.io/en/v0.50.0/admin-guide/install.html).
