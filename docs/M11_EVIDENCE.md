# M11 — Conditional expressions

## Purpose and syntax

Study programs often select a score, feedback message, or next set of terms
based on an answer. A conditional expression produces that value directly.
The syntax builds on StudyLang's existing `if` and `else` keywords and adds
one expression form.

```text
then_expression if condition else else_expression
```

The grammar uses the following rule.

```text
?expression: or_expr "if" or_expr "else" expression -> conditional
           | or_expr
```

Conditional expressions have lower precedence than `or`. The else alternative
associates to the right, so `a if p else b if q else c` means
`a if p else (b if q else c)`. Parentheses allow nested conditionals inside
the condition or then alternative. The expression can be used in declaration
initializers, assignment values, output, arguments, returns, array elements,
indices, and other expression positions.

## Intended semantics and type rules

1. Evaluate the condition first. It must produce a Boolean.
2. Evaluate the then expression if the condition is true, or the else
   expression if it is false. The other alternative receives no runtime
   evaluation or input/output.
3. Return the selected value to the enclosing expression. Selecting an array
   preserves the existing reference to that array.

Static analysis checks names, operators, and types in both alternatives,
including the alternative that will be skipped. When both result types are
known, they must match exactly. For example, two integer alternatives, two
float alternatives, two Booleans, two strings, or two arrays are accepted.
An integer paired with a float is rejected, following the existing strict
assignment policy. `1 if True else 2.5` is an example of a rejected program.
Numeric literals retain StudyLang's existing whole-value classification.

When either alternative has an unknown type, the expression's inferred type
is unknown. This follows the existing treatment of parameters, call results,
and array elements. Operations consuming the selected value apply runtime
type checks. Unknown conditions also receive a runtime Boolean check.

Conditional expressions introduce no scope of their own. Function calls and
other existing expressions in an alternative retain their normal scope and
side-effect behavior.

## Example 1 — Scoring and safe division in both modes

`Examples/m11_numeric.tiny` is executable with the interpreter and compiler.

```text
let correct = True
let points = 1 if correct else 0
show(points)
let denominator = 0
show(10 / denominator if denominator != 0 else 0 / 1)
let score = 75
let grade = 2 if score >= 90 else 1 if score >= 70 else 0
show(grade)
show(True if points > 0 else False)
```

Expected and actual output match in interpreter mode and compiler modes O0–O3.

```text
1
0.0
1
true
```

Both division alternatives produce floats. The zero divisor is in the skipped
alternative, so execution selects the safe result. The nested expression
chooses a grade through the right-associated else alternative.

```sh
python3 main.py --mode interpreter --file Examples/m11_numeric.tiny
python3 main.py --mode compiler --file Examples/m11_numeric.tiny --opt 2
```

## Example 2 — Study feedback in interpreter mode

`Examples/m11_study.tiny` selects a feedback string and an array of terms.

```text
let answer = ask("What keyword declares a variable? ")
let correct = answer == "let"
let feedback = "Correct!" if correct else "Review let"
show(feedback)
let terms = ["loop"] if correct else ["let", "loop"]
for term in terms:
    show(term)
```

With input `let`, expected and actual show output are `Correct!` and `loop`.
With input `wrong`, they are `Review let`, `let`, and `loop`.
The input prompt appears before this output.

```sh
python3 main.py --mode interpreter --file Examples/m11_study.tiny
```

The compiler implements conditional expressions for its existing numeric and
Boolean subset. String/array results and input remain interpreter features,
with explicit compilation errors under the documented backend limitations.

## Pipeline changes

| Layer | Implementation |
| --- | --- |
| Grammar/tokens | `Shared/grammar.lark` reuses `if`/`else` and defines conditional precedence and associativity |
| AST | `Shared.ast_nodes.Conditional` stores `condition`, `then_expression`, and `else_expression` |
| Transformer | `Shared.frontend.ToAST.conditional` maps source order to AST fields |
| Structural validation | `Shared.m6_ast_tool` validates all three required expression children |
| Traversal/metrics | `Shared.metric.children` visits the then expression, condition, and else expression in source order; the existing walker displays the new node |
| Semantic analysis | `Shared.semantic` checks the Boolean condition and matching known alternative types |
| Interpreter | `Interpreter/interpreter.py` evaluates the condition and selected alternative |
| LLVM compiler | `Compiler/compiler.py` emits two branch blocks and a merge with a typed phi node |

This small source demonstrates the generated LLVM control flow.

```text
let correct = True
show(1 if correct else 0)
```

The following excerpt is copied from its verified unoptimized IR.

```llvm
%"load_correct" = load i1, i1* %"var_correct"
  br i1 %"load_correct", label %"conditional_then", label %"conditional_else"
conditional_then:
  br label %"conditional_merge"
conditional_else:
  br label %"conditional_merge"
conditional_merge:
  %"conditional_result" = phi  i64 [1, %"conditional_then"], [0, %"conditional_else"]
```

The conditional branch directs execution to one alternative. The phi node
receives the value from the predecessor that actually executed. Alternative
expressions can themselves create blocks for runtime guards or nested
conditionals, so the compiler records their actual exit blocks for the phi.
LLVM optimization can fold a constant condition while retaining the same
observable result.

## Functional-programming comparison and trade-offs

Functional-style code composes expressions that produce values. This feature
lets a conditional directly initialize a binding or supply a function result,
reducing the need for a temporary variable followed by branch assignments.
It corresponds to the value-producing if expressions used in functional
programming. StudyLang uses familiar Python-like ordering for readability.

The matching-type rule keeps the result predictable for semantic analysis
and gives LLVM's phi node one concrete type. Its cost is requiring consistent
numeric types on both sides, even if a constant condition selects only one.
Unknown function and collection types retain the existing deferred checks.

Deeply nested conditionals can be harder to read than statement blocks.
The existing if statement remains useful for multi-statement branches.
Alternatives can call input or functions with side effects, and evaluation
is restricted to the selected alternative. This feature provides expression
composition within StudyLang's established execution model.

## Positive and negative evidence

| Case | Expected and actual behavior |
| --- | --- |
| Numeric/Boolean examples and nested expressions | Interpreter and O0–O3 compiler outputs agree |
| Skipped zero division/modulo | No runtime error from the unselected alternative |
| Selected zero division | Runtime error in both modes at O0–O3 |
| Conditional input | Condition prompt occurs first, followed by only the selected alternative's prompt |
| Function calls/returns and selected arrays | Selected function runs once; selected array retains aliasing |
| Missing condition, else keyword, or else value | Syntax rejection |
| Non-Boolean known condition | Semantic rejection before execution |
| Non-Boolean unknown condition | Runtime Boolean-type error |
| Mismatched known alternative types | Semantic rejection before execution |
| Undefined name in an unselected alternative | Semantic rejection before execution |
| Incompatible known assignment result | Semantic rejection before execution |
| Unknown selected value used in invalid arithmetic | Runtime operand-type error |
| String result compiled with LLVM | Explicit unsupported-expression compilation error |
| Missing AST child | Structural validation rejection |

The cases are implemented in `tests/test_conditional.py`. Current full-suite
results and commands are maintained in [TESTING.md](TESTING.md).

| M11 requirement | Evidence | Status |
| --- | --- | --- |
| Purpose, syntax, semantics, and two examples | Specification and runnable examples above | Complete |
| Update relevant pipeline layers | Shared AST/frontend/validation, interpreter, compiler, and metrics | Complete |
| Identify unsupported execution modes | String/array/input examples use interpreter mode | Complete |
| Positive and negative tests | `tests/test_conditional.py`, earlier regression suite | Complete |
| Compare to a course paradigm | Functional expression composition discussion above | Complete |
| Demonstration and reasoned trade-offs | Both source files, IR excerpt, traces, and type/readability discussion | Complete |
