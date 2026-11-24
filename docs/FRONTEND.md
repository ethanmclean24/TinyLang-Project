# Language and shared frontend — M0–M7

## Language identity and M0–M2 continuity
StudyLang (Ethan McLean, version 0.1) is a beginner-friendly console study language.
The language vision, specification, and M2 syntax are represented by the shared grammar and AST. Both execution modes use these definitions.

## Feature traceability
| M1 feature/design | M2 production | M3 tokens | M5 representation |
|---|---|---|---|
| Explicit variables | declaration, assignment, reference | LET, NAME, EQUAL | Let, Assignment, Variable |
| Arithmetic scores | add/subtract/multiply/divide/remainder | NUMBER, NEGATIVE_NUMBER, arithmetic operators | Number, BinaryOp |
| Study input/output | ask, show_stmt, string | ASK, SHOW, LPAR/RPAR, STRING | Ask, Show, String |
| Conditional feedback | if_stmt, block, compare | IF, ELSE, COLON, COMP_OP, indentation | If, Block, BinaryOp |
| Repeated practice | while_stmt | WHILE, COLON | While |
| Study collections | array_literal, index, for_stmt | LSQB/RSQB, COMMA, FOR, IN | Array, Index, For |
| Reusable functions | function_decl, parameters, call, return_stmt | FUNCTION, NAME, RETURN, parentheses | Function, Call, Return |
| Boolean decisions | logical_or/and/not, true/false | OR, AND, NOT, TRUE, FALSE | BinaryOp, Not, Boolean |

All M2 syntax features have AST representations. The grammar requires parentheses
for show/ask. The M1 sketches are retained in `Examples/milestone1_examples.tiny`
for syntax/AST inspection; use the later examples for executable demonstrations.

## Token inventory
Literal terminals receive Lark-generated names below. Keywords are case-sensitive.
NAME uses `[a-zA-Z_][a-zA-Z0-9_]*` with a negative lookahead excluding complete
reserved words; names such as `shower` remain valid. The contextual lexer selects
terminals allowed in the parser state, including subtraction versus a negative literal.

| Category/token | Pattern/literal | Example | Role/precedence |
|---|---|---|---|
| NAME | identifier pattern above | correct | Variable/function name; excludes keywords |
| NUMBER | Lark common.NUMBER | 2, .5, 5., 1e3 | Nonnegative numeric literal |
| NEGATIVE_NUMBER | `-` immediately followed by NUMBER | -5 | Signed literal, not general unary minus |
| STRING | Double quotes, no raw newline; escapes quote, backslash, n/t/r | "Review" | Text and prompts; # inside string is text |
| TRUE, FALSE | True, False | True | Boolean literals; reserved |
| LET | let | let | Declaration keyword |
| SHOW, ASK | show, ask | ask | Output/input syntax |
| IF, ELSE | if, else | if | Conditional branches |
| WHILE | while | while | Condition-controlled loop |
| FOR, IN | for, in | for | Collection iteration |
| FUNCTION, RETURN | function, return | return | Function definition/return |
| AND, OR, NOT | and, or, not | not | Word-based logical operators |
| PLUS, MINUS | +, - | + | Left-associative addition/subtraction |
| STAR, SLASH, PERCENT | *, /, % | * | Bind more tightly than addition |
| COMP_OP | ==, !=, <=, >=, <, > | >= | Non-chained comparison |
| EQUAL | = | = | Declaration/assignment delimiter |
| LPAR, RPAR | (, ) | ( | Calls, output, grouping |
| LSQB, RSQB | [, ] | [ | Arrays and indexing |
| COMMA | , | , | Elements, arguments, parameters |
| COLON | : | : | Introduces an indented block |
| _NEWLINE | Newline plus indentation or comment text | newline | Ends simple statements; final newline required |
| _INDENT, _DEDENT | Synthesized by StudyLangIndenter | four spaces | Block boundaries; no tabs |
| WS_INLINE | Lark inline whitespace | space | Ignored between tokens |
| SH_COMMENT | # through end of line | # study | Ignored or absorbed into _NEWLINE; no AST node |

Precedence, strongest to weakest: grouped/atomic expressions, multiplication/
division/remainder, addition/subtraction, one comparison, not, and, or.
Blocks require exactly four additional spaces; the first statement starts in
column one. Parentheses/brackets suppress indentation processing while open.

## Meaningful differences from the instructor demo
1. Colon/newline/four-space blocks replace braces and semicolons, following the
   M1 readability principle and submitted M2 grammar.
2. `show(expression)` requires parentheses and `ask(prompt)` represents study
   input, matching the explicit M2 revision and M1 console-study workflow.
3. Arrays, indexed assignment, and for-loops represent collections of study terms
   already specified in README/M2, beyond the demo's scalar statements.
4. Functions, calls, and returns represent the reusable study logic already in M2.

Shared let/if/while and arithmetic syntax serves the common course core.
Independent mappings retain indexed assignment targets, distinct Ask nodes,
StudyLang aliases, and indentation-aware blocks. Boolean case is True/False.


## Values and statements

StudyLang supports numeric and Boolean values, strings, and arrays containing
mixed or nested values. `let name = expression` declares a variable, and
`name = expression` updates an existing binding. Indexed assignment updates
an existing array element. Blocks use a colon, newline, and exactly four
additional spaces per level.

`show(expression)` produces output and `ask(prompt)` reads text. Conditions
use `if expression:` with an optional `else:`. Repetition uses
`while expression:` or `for item in array_expression:`. Reusable logic uses
`function name(parameters):` and `return expression`. The interpreter's
runtime rules and examples are documented in [M8_EVIDENCE.md](M8_EVIDENCE.md).

The compiler implements the numeric and Boolean subset described in
[M9_EVIDENCE.md](M9_EVIDENCE.md).

## Parser and AST API

Import the frontend from `Shared.frontend`.

- `create_parser()` returns the Lark LALR parser with StudyLang indentation handling.
- `parse_tree(source)` returns a parse tree and `parse(source)` returns a `Program` AST.
- `is_valid(source)` checks syntax and indentation. Names and operand types are
  checked by semantic analysis.
- Direct parser calls require a final newline. Both program runners add one
  when needed. Invalid syntax or indentation raises Lark `UnexpectedInput`
  or `DedentError` before AST transformation.

`Shared.ast_nodes` contains the dataclasses used by every stage. Whole-valued
numbers are stored as floats in the AST and classified as integers during
semantic analysis and execution. String escapes are decoded by the transformer.

## M6 structural validation and inspection

`Shared.m6_ast_tool.validate_ast(program)` checks node types, required fields,
identifiers, operators, and child structure. Malformed trees raise
`ASTValidationError`. Structural validation accepts references whose declarations
or operand types are checked later by semantic analysis.

`Shared.walk.walk(program)` prints the tree. `Shared.metric.node_count(program)`
counts nodes and `max_depth(program)` measures depth with the root at depth 1.
The `tools.demo1_validate` demonstration checks precedence, parentheses,
structure, traversal, and metrics. `tools.inspect_tokens` uses interactive
parsing to print the actual contextual tokens and indentation markers.

## M7 semantic rules

`Shared.semantic.SemanticAnalyzer().analyze(program)` returns the same AST on
success or raises `SemanticError` for a violation. Variables and functions
share a namespace and must be declared before use. Branches, loops, and
functions have local scopes. Inner names can shadow outer names, and a
function's body can call itself.

Assignments preserve a variable's inferred type when both types are known.
Arithmetic takes numbers, `%` takes integers, and logical operations and
if/while conditions take Booleans. Equality accepts matching types or two
numbers. Arrays can contain mixed values and require integer indices.
`ask` returns a string. Function arity is checked before execution.

Function parameters, call results, and array elements may have unknown types
during analysis. Operations involving these values receive concrete type
checks during interpretation. Calling a function that finishes without a
return value raises a runtime error.

Current commands and verification results are in [TESTING.md](TESTING.md).
