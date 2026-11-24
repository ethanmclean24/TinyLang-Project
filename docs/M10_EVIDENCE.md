# M10 — Integration, testing, and debugging

The launcher selects the interpreter or compiler, including source selection,
optimization, and IR display controls. User-facing commands and defaults are
maintained in the [README](../README.md#setup-and-execution).

## Shared modules and integration

The integration diagram and package responsibilities are in
[ARCHITECTURE.md](ARCHITECTURE.md).
Both paths use one copy of `Shared/grammar.lark`, `Shared/ast_nodes.py`, `Shared/frontend.py`,
`Shared/m6_ast_tool.py`, and `Shared/semantic.py`. Grammar, AST, and semantic rules have a
single implementation. Interpreter mode delegates to the existing `Interpreter.run.run`
API. Compiler mode delegates to `Compiler.run.compile_source`, then runs
optimization and JIT execution. Existing standalone runners remain usable.

The validation calls live in the existing runners and compiler API, so direct
callers also receive their established checks. Integration tests exercise
both paths through the root launcher and compare output and diagnostics.
This makes changes to shared rules visible in both modes.

## Comparison matrix

All listed expected results matched actual results during verification.
For supported examples, compiler output matched interpreter output at every
optimization level O0–O3.

| Program or behavior | Interpreter | Compiler | Verification |
| --- | --- | --- | --- |
| Instructor arithmetic example | `25` | `25` | O0–O3 |
| Instructor Boolean example | `4` | `4` | O0–O3 |
| Instructor fractional example | `2.5`, `3.75` | `2.5`, `3.75` | O0–O3 |
| Instructor outer assignment | `15` | `15` | O0–O3 |
| Instructor shadowing example | `20`, `10` | `20`, `10` | O0–O3 |
| Instructor while example | `0`, `1`, `2`, `3` | `0`, `1`, `2`, `3` | O0–O3 |
| `m9_demo.tiny` | `6`, `2.0`, `true` | Same | CLI, O0–O3 |
| `m10_scope.tiny` | `12`, `12`, `1`, `7` | Same | CLI, O0–O3 |
| Negative modulo and short-circuit guards | Same expected values | Same | O0–O3 |
| Syntax error after an output statement | Syntax error, no output | Same | CLI, O0/O2 |
| Undefined or escaped local variable | Semantic error, no output | Same | CLI, O0/O2 |
| Division/modulo by zero after `show(1)` | Prints `1`, then runtime error | Same | CLI, O0/O2 |
| Infinite while loop | Loop-limit runtime error | Same | CLI, O0/O2 |
| Strings | Executed | Explicit compilation error before execution | Documented subset boundary |
| Result outside signed 64-bit integer range | Python integer result | Explicit runtime overflow error | Documented numeric boundary |

The nested-scope example changes an enclosing local variable, prints that
local from its enclosing block, and then prints the original global value.
It also updates the global in a loop whose local declaration runs repeatedly.
The interpreter and compiler agree on all four outputs.

Lark represents expected tokens as a set. Its diagnostic can list those tokens
in a different order in different processes. Tests compare the same error
content, positions, and exit statuses while ignoring that ordering.

## O0 and optimized IR evidence

This source is used by the optimization test.

```text
let score = 2 + 3
show(score)
```

O0 verifies IR without applying optimization passes. Its generated code retains
variable storage, checked addition, and loading the stored value. This is an
excerpt from the verified O0 module.

```llvm
  %var_score = alloca i64, align 8
  br label %program

program:                                          ; preds = %entry
  %checked_arithmetic = call { i64, i1 } @llvm.sadd.with.overflow.i64(i64 2, i64 3)
  %arithmetic = extractvalue { i64, i1 } %checked_arithmetic, 0
  %overflow = extractvalue { i64, i1 } %checked_arithmetic, 1
  %.3 = xor i1 %overflow, true
  br i1 %.3, label %check_ok, label %runtime_error

check_ok:                                         ; preds = %program
  store i64 %arithmetic, ptr %var_score, align 4
  %load_score = load i64, ptr %var_score, align 4
  %output_status = call i32 @studylang_show_integer(i64 %load_score)
```

At O2 the same module's `main` becomes the following.

```llvm
define i32 @main() local_unnamed_addr {
entry:
  %output_status = tail call i32 @studylang_show_integer(i64 5)
  ret i32 %output_status
}
```

LLVM folds the addition to `5`, removes variable storage and the impossible
integer-overflow branch, and reduces the output-status branches to a direct
return. It preserves the host output call and its returned error status.
Both versions print `5` and finish successfully. In the tested LLVM version,
the full module shrinks from 43 lines at O0 to 12 at O2.

`Compiler.optimizer.optimize_ir` follows the instructor's new-pass-manager implementation.
It validates the optimization level and verifies IR before and after running
the selected LLVM pipeline. `Compiler.jit.run_ir` verifies the result again before
native execution. Fast-math flags are not introduced by this stage.

Optimization can remove unused output-function declarations. The JIT now maps
only functions that remain in the module. An optimized program with no output
is covered by a regression test. Output callback errors, integer overflow,
loop limits, short-circuiting, negative remainders, and large mixed numeric
comparisons are also checked with optimization enabled.

## Verification and guide coverage

The integration suite covers both mode APIs, command-line execution,
interactive input, numbered/custom file selection, back/exit behavior,
IR display, O0–O3 equivalence, errors, compiler limitations, and package
runner compatibility. Earlier milestone tests remain in the full suite.
Current results and troubleshooting are maintained in [TESTING.md](TESTING.md).

| M10 requirement | Evidence | Status |
| --- | --- | --- |
| One workflow to select interpreter or compiler | `main.py`, interactive and CLI tests | Complete |
| Consistent grammar, AST, and semantic rules | Shared modules and both-mode tests | Complete |
| Matching outputs, errors, and nested-scope behavior | Comparison matrix and `tests/test_integration.py` | Complete for supported subset |
| Earlier milestone regression coverage | Full pytest suite | Complete |
| O0 versus optimized IR and equivalent results | Verified excerpts above, O0–O3 tests | Complete |
| Launcher, integration diagram, troubleshooting, and comparison evidence | `main.py`, `ARCHITECTURE.md`, this document | Complete |

The compiler feature and numeric boundaries are documented in
`M9_EVIDENCE.md`. This milestone adds workflow integration and optimization
within that subset. The guide treats optimization as an instructional
extension within M10.
