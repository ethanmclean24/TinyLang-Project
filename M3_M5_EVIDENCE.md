# M3–M5 Implementation and Test Evidence

## Language identity and M0–M2 continuity
StudyLang (Ethan McLean, version 0.1) is a beginner-friendly console study language.
Milestones 0-2, the language vision, specification, and grammar has been preserved. The M2 test inputs are unchanged and now use the shared frontend parser.

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

No M2 syntax feature is deferred from AST construction. Runtime semantics remain
outside this assignment. There was an M2 revision that made show/ask parentheses
explicit for clarity; the M1 sketches are preserved and still parse.

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

## Test commands and actual results
Validated on 2026-10-19 with Python and Lark 1.3.1. Setup command for a new environment:
`python3 -m pip install -r requirements.txt`. 

M2: 7 positive + 12 negative cases, all passed. M3/M4: those cases plus 5 lexical
negatives, all matched expectations. M5: 10 unittest methods cover structural
comparisons, operators, nested blocks, optional lists/branches, token boundaries,
three invalid programs before transformation, and complete ASTs for all seven
M2 positive programs plus both example files.

### python3 tests/test_parser.py
```text
POSITIVE TESTS
PASS: Declarations and assignment
PASS: Arithmetic and grouping
PASS: Input, output, and strings
PASS: Comparisons and conditionals
PASS: Functions and return values
PASS: Arrays and indexing
PASS: While and for loops

NEGATIVE TESTS
PASS (rejected): Missing initializer
PASS (rejected): Missing output argument
PASS (rejected): Missing call parentheses
PASS (rejected): Incorrect indentation
PASS (rejected): Empty program
PASS (rejected): Empty block
PASS (rejected): Unary expression
PASS (rejected): Trailing array comma
PASS (rejected): Missing array index
PASS (rejected): Missing loop iterable
PASS (rejected): Missing return value
PASS (rejected): Single quoted string

EXAMPLE PARSE TREE
start
  show_stmt
    add
      number	2
      multiply
        number	3
        number	4

Tests: 19 | Passed: 19 | Failed: 0
```

### python3 -m unittest discover -s tests -p test_m3_m5.py -v
```text
test_arrays_index_assignment_for (test_m3_m5.StudyLangM3M5Tests.test_arrays_index_assignment_for) ... ok
test_complete_ast_for_existing_examples (test_m3_m5.StudyLangM3M5Tests.test_complete_ast_for_existing_examples) ... ok
test_contextual_token_boundaries (test_m3_m5.StudyLangM3M5Tests.test_contextual_token_boundaries) ... ok
test_declaration_assignment_output_precedence (test_m3_m5.StudyLangM3M5Tests.test_declaration_assignment_output_precedence) ... ok
test_functions_calls_returns (test_m3_m5.StudyLangM3M5Tests.test_functions_calls_returns) ... ok
test_input_strings_boolean_precedence (test_m3_m5.StudyLangM3M5Tests.test_input_strings_boolean_precedence) ... ok
test_invalid_rejected_before_transform (test_m3_m5.StudyLangM3M5Tests.test_invalid_rejected_before_transform) ... ok
test_nested_control_flow (test_m3_m5.StudyLangM3M5Tests.test_nested_control_flow) ... ok
test_operators_and_number_forms (test_m3_m5.StudyLangM3M5Tests.test_operators_and_number_forms) ... ok
test_syntax_regression_and_lexical_errors (test_m3_m5.StudyLangM3M5Tests.test_syntax_regression_and_lexical_errors) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.043s

OK
Declarations and assignment: expected ACCEPT; actual ACCEPT
Arithmetic and grouping: expected ACCEPT; actual ACCEPT
Input, output, and strings: expected ACCEPT; actual ACCEPT
Comparisons and conditionals: expected ACCEPT; actual ACCEPT
Functions and return values: expected ACCEPT; actual ACCEPT
Arrays and indexing: expected ACCEPT; actual ACCEPT
While and for loops: expected ACCEPT; actual ACCEPT
Missing initializer: expected REJECT; actual REJECT; UnexpectedToken line=1 col=12
Missing output argument: expected REJECT; actual REJECT; UnexpectedToken line=1 col=6
Missing call parentheses: expected REJECT; actual REJECT; UnexpectedToken line=1 col=6
Incorrect indentation: expected REJECT; actual REJECT; DedentError line=None col=None
Empty program: expected REJECT; actual REJECT; UnexpectedToken line=1 col=1
Empty block: expected REJECT; actual REJECT; UnexpectedToken line=2 col=9
Unary expression: expected REJECT; actual REJECT; UnexpectedToken line=1 col=6
Trailing array comma: expected REJECT; actual REJECT; UnexpectedToken line=1 col=20
Missing array index: expected REJECT; actual REJECT; UnexpectedToken line=1 col=13
Missing loop iterable: expected REJECT; actual REJECT; UnexpectedToken line=2 col=13
Missing return value: expected REJECT; actual REJECT; UnexpectedToken line=3 col=11
Single quoted string: expected REJECT; actual REJECT; UnexpectedCharacters line=1 col=6
Illegal character: expected REJECT; actual REJECT; UnexpectedCharacters line=1 col=6
Identifier starts with a number: expected REJECT; actual REJECT; UnexpectedToken line=1 col=5
Reserved keyword as name: expected REJECT; actual REJECT; UnexpectedToken line=1 col=5
Unsupported operator: expected REJECT; actual REJECT; UnexpectedToken line=1 col=9
Unsupported string escape: expected REJECT; actual REJECT; UnexpectedCharacters line=1 col=6
```

### python3 tests/check_milestone1.py
```text
TinyLang Milestone 1 readiness check
=======================================
[PASS]  config.py
[PASS]  main.py
[PASS]  README.md
[PASS]  ARCHITECTURE.md
[PASS]  examples/milestone1_examples.tiny
[PASS]  grammar.lark
[PASS]  frontend.py
[PASS]  ast_nodes.py
[PASS]  semantic.py
[PASS]  interpreter.py
[PASS]  codegen.py
[PASS]  jit.py

Week 2 editable-file placeholder check
---------------------------------------
[PASS]  README specification
[PASS]  architecture
[PASS]  informal examples

Interpretation
---------------------------------------
Basic Week 2 package checks pass.
This script checks package readiness only; it does NOT grade design quality.
Review START_HERE.md, the Guided Development Workbook, and Moodle before submitting.
```


## Token inspection output
`python3 inspect_tokens.py` (complete captured output):

```text
_NEWLINE           '# StudyLang: inspect the structure of a short study session.\n' line=1 col=1
FUNCTION           'function' line=2 col=1
NAME               'percent' line=2 col=10
LPAR               '(' line=2 col=17
NAME               'correct' line=2 col=18
COMMA              ',' line=2 col=25
NAME               'total' line=2 col=27
RPAR               ')' line=2 col=32
COLON              ':' line=2 col=33
_NEWLINE           '\n    ' line=2 col=34
_INDENT            '    ' line=2 col=34
RETURN             'return' line=3 col=5
NAME               'correct' line=3 col=12
STAR               '*' line=3 col=20
NUMBER             '100' line=3 col=22
SLASH              '/' line=3 col=26
NAME               'total' line=3 col=28
_NEWLINE           '\n' line=3 col=33
_DEDENT            '' line=3 col=33
LET                'let' line=4 col=1
NAME               'terms' line=4 col=5
EQUAL              '=' line=4 col=11
LSQB               '[' line=4 col=13
STRING             '"declaration"' line=4 col=14
COMMA              ',' line=4 col=27
STRING             '"loop"' line=4 col=29
RSQB               ']' line=4 col=35
_NEWLINE           '\n' line=4 col=36
LET                'let' line=5 col=1
NAME               'correct' line=5 col=5
EQUAL              '=' line=5 col=13
NUMBER             '0' line=5 col=15
_NEWLINE           '\n' line=5 col=16
FOR                'for' line=6 col=1
NAME               'term' line=6 col=5
IN                 'in' line=6 col=10
NAME               'terms' line=6 col=13
COLON              ':' line=6 col=18
_NEWLINE           '\n    ' line=6 col=19
_INDENT            '    ' line=6 col=19
LET                'let' line=7 col=5
NAME               'answer' line=7 col=9
EQUAL              '=' line=7 col=16
ASK                'ask' line=7 col=18
LPAR               '(' line=7 col=21
NAME               'term' line=7 col=22
RPAR               ')' line=7 col=26
_NEWLINE           '\n    ' line=7 col=27
IF                 'if' line=8 col=5
NAME               'answer' line=8 col=8
COMP_OP            '==' line=8 col=15
STRING             '"yes"' line=8 col=18
AND                'and' line=8 col=24
NOT                'not' line=8 col=28
FALSE              'False' line=8 col=32
COLON              ':' line=8 col=37
_NEWLINE           '\n        ' line=8 col=38
_INDENT            '        ' line=8 col=38
NAME               'correct' line=9 col=9
EQUAL              '=' line=9 col=17
NAME               'correct' line=9 col=19
PLUS               '+' line=9 col=27
NUMBER             '1' line=9 col=29
_NEWLINE           '\n    ' line=9 col=30
_DEDENT            '    ' line=9 col=30
ELSE               'else' line=10 col=5
COLON              ':' line=10 col=9
_NEWLINE           '\n        ' line=10 col=10
_INDENT            '        ' line=10 col=10
SHOW               'show' line=11 col=9
LPAR               '(' line=11 col=13
STRING             '"Review this term"' line=11 col=14
RPAR               ')' line=11 col=32
_NEWLINE           '\n' line=11 col=33
_DEDENT            '' line=11 col=33
_DEDENT            '' line=11 col=33
LET                'let' line=12 col=1
NAME               'remaining' line=12 col=5
EQUAL              '=' line=12 col=15
NUMBER             '2' line=12 col=17
MINUS              '-' line=12 col=18
NAME               'correct' line=12 col=19
_NEWLINE           '\n' line=12 col=26
WHILE              'while' line=13 col=1
NAME               'remaining' line=13 col=7
COMP_OP            '>' line=13 col=17
NUMBER             '0' line=13 col=19
COLON              ':' line=13 col=20
_NEWLINE           '\n    ' line=13 col=21
_INDENT            '    ' line=13 col=21
SHOW               'show' line=14 col=5
LPAR               '(' line=14 col=9
STRING             '"Practice again"' line=14 col=10
RPAR               ')' line=14 col=26
_NEWLINE           '\n    ' line=14 col=27
NAME               'remaining' line=15 col=5
EQUAL              '=' line=15 col=15
NAME               'remaining' line=15 col=17
MINUS              '-' line=15 col=27
NUMBER             '1' line=15 col=29
_NEWLINE           '\n' line=15 col=30
_DEDENT            '' line=15 col=30
NAME               'terms' line=16 col=1
LSQB               '[' line=16 col=6
NUMBER             '0' line=16 col=7
RSQB               ']' line=16 col=8
EQUAL              '=' line=16 col=10
STRING             '"let"' line=16 col=12
_NEWLINE           '\n' line=16 col=17
SHOW               'show' line=17 col=1
LPAR               '(' line=17 col=5
NAME               'percent' line=17 col=6
LPAR               '(' line=17 col=13
NAME               'correct' line=17 col=14
COMMA              ',' line=17 col=21
NUMBER             '2' line=17 col=23
RPAR               ')' line=17 col=24
RPAR               ')' line=17 col=25
_NEWLINE           '\n' line=17 col=26
SHOW               'show' line=18 col=1
LPAR               '(' line=18 col=5
NUMBER             '2' line=18 col=6
PLUS               '+' line=18 col=8
NUMBER             '3' line=18 col=10
STAR               '*' line=18 col=12
NUMBER             '4' line=18 col=14
RPAR               ')' line=18 col=15
_NEWLINE           '\n' line=18 col=16
```


## Parse-tree and AST evidence
`python3 frontend.py` successfully printed the full demo source, parse tree and
AST. The following four focused cases were captured using parse_tree(source).pretty()
and parse(source); corresponding structural assertions are in test_m3_m5.py.

### Declaration and assignment
```text
let score = 1
score = 2
```
```text
start
  declaration
    score
    number	1
  assignment
    variable	score
    number	2
Program(statements=[Let(name='score', value=Number(value=1.0)),
                    Assignment(target=Variable(name='score'),
                               value=Number(value=2.0))])
```

### Arithmetic precedence
```text
show(2 + 3 * 4)
```
```text
start
  show_stmt
    add
      number	2
      multiply
        number	3
        number	4
Program(statements=[Show(expression=BinaryOp(op='+',
                                             left=Number(value=2.0),
                                             right=BinaryOp(op='*',
                                                            left=Number(value=3.0),
                                                            right=Number(value=4.0))))])
```

### Study input/output
```text
let answer = ask("Term?")
show(answer)
```
```text
start
  declaration
    answer
    ask
      string	"Term?"
  show_stmt
    variable	answer
Program(statements=[Let(name='answer', value=Ask(prompt=String(value='Term?'))),
                    Show(expression=Variable(name='answer'))])
```

### Conditional
```text
if True:
    show(1)
else:
    show(0)
```
```text
start
  if_stmt
    true
    block
      show_stmt
        number	1
    block
      show_stmt
        number	0
Program(statements=[If(condition=Boolean(value=True),
                       then_branch=Block(statements=[Show(expression=Number(value=1.0))]),
                       else_branch=Block(statements=[Show(expression=Number(value=0.0))]))])
```

## Limitations and packaging
Only syntax and AST construction are implemented. No further Milestones have been implemented. 
Numbers are represented as Python floats. Historical examples mixing strings/numbers establish syntax only.
M2 restrictions remain intentional.

The up-to-date project is on [GitHub](https://github.com/ethanmclean24/TinyLang-Project).

## Attribution and customization statement
The instructor's Project3 M3–M5 guide controls scope. The supplemental evidence
outline and token-inspector/test scaffolds informed these four new support files.
The in-class frontend supplied the Lark factory, parse_tree/parse/is_valid,
Transformer, and dataclass architectural patterns; these were adapted to
StudyLang's existing grammar rather than copied as a replacement language.
The M2 indenter and regression cases are carried forward from this project.
The concrete customizations and design mappings above distinguish this project from the demo.
