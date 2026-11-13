# StudyLang
**Version:** 0.1  
**Author:** Ethan McLean  
**Current Milestone:** M7 — Semantic Analysis

## 1. Language Purpose
A simple language with easy inputs and outputs that makes it easy for students to add course materials (like terms or questions) and study using simple console input/output.

## 2. Target Users
Students looking for a way to study their course material. Little to none prior knowledge needed.

## 3. Design Principles
1. Simplicity
2. Readability
3. Built in functions

## 4. Required Common-Core Direction
Your TinyLang will eventually support numeric and Boolean values; variables,
declaration and assignment; arithmetic/comparison/logical expressions; output;
conditional execution with optional else; while-style repetition; blocks; and comments.

## 5. Initial Data and Value Categories
- Boolean values- True/False is very important for study workflow
- Numeric values- Keeps track of things like answers and question counts
- Strings- Input, Output, store questions or answers or other messages
- Arrays- Store sequences of study terms, scores, or nested arrays.

## 6. Statement Forms
- Declaration- `let`
- Assigment- simple `=`. Automatic memory management. 
- Output- `show(expression)`
- Input- `ask(prompt)`. A built-in function taking one prompt expression.
- Conditionals- `if bool` or `if (conditional statement)` or `if variable`
- Repetition- `while condition:` and `for item in array_expression:`.
- Functions- `function name(parameters):` with an indented body and `return expression`.
- Blocks- colon, newline, and exactly four additional spaces per level; no indentation tabs.
    ```
    let this = "a statement"

    if (this == "a statement"):
        show(this)
    ```


## 7. Expression Forms
- Arithmetic- `+`, `-`, `*`, `/`, `%`
- Comparison- `==`, `!=`, `<`, `>`, `<=`, `>=`
- Logical- `and`, `or`, `not` (avoids symbols for simplicity)
- Literal- Numbers, strings, and booleans
- Variable-reference- Using the name of a variable to access its value

## 8. Individual Innovation
1. Built in functions for input and output to make it easy for students to use the language for studying.
2. Simple syntax and indentation-based blocks to make it easy to read and write code. Similar to Python, but with a focus on simplicity and readability for students.
3. Simple, but explicit variable declaration and assignment to make it easy for students to understand how variables work.

## 9. Execution Architecture
See `ARCHITECTURE.md`.

## 10. Informal Examples
See `examples/milestone1_examples.tiny`.

> These are design sketches, not formal grammar.

## 11. Implementation Status
- [x] Project identity scaffold
- [x] Initial language specification — Milestone 1
- [x] Formal grammar — M2
- [x] Frontend/lexer/parser — M3–M5
- [x] AST — M5
- [x] AST structural validation, walk, and metrics — M6
- [x] Semantic analysis
- [ ] Interpreter — later
- [ ] LLVM backend/JIT — later

## 12. Setup and verification
Use Python 3.9 or newer. From the project root:

```sh
python3 -m pip install -r requirements.txt
python3 inspect_tokens.py
python3 frontend.py
python3 demo1_validate.py
python3 semantic.py
python3 -m pytest -q
python3 tests/test_parser.py
python3 -m unittest discover -s tests -p 'test_m3_m5.py' -v
python3 tests/check_milestone1.py
```

`frontend.py` displays the new study-session source, parse tree, and AST.
`inspect_tokens.py` displays the contextual tokens consumed by the same parser,
including their positions and generated indentation markers. Neither executes
StudyLang statements or asks for input. `main.py` remains the historical M1
identity entry point; use `frontend.py` for this milestone's demonstration.

## 13. Frontend API and boundaries
- `create_parser()` returns a Lark LALR parser with StudyLang indentation handling.
- `parse_tree(source)` returns the Lark tree; `parse(source)` returns a `Program` AST.
- `is_valid(source)` checks syntax and indentation only.
- Invalid input raises Lark `UnexpectedInput` or `DedentError` before transformation.

See `M3_M5_EVIDENCE.md` for the token inventory, mappings, captured results,
customizations, and attribution.

M6: call `validate_ast(parse(source))` from `m6_ast_tool` to check AST shape;
malformed nodes raise `ASTValidationError`. `walk.walk(ast)` prints the AST;
`metric.node_count(ast)` and `metric.max_depth(ast)` measure it (root depth 1).

M7: pass a structurally valid `Program` to
`SemanticAnalyzer().analyze(program)` from `semantic`. It returns the same
AST on success and raises `SemanticError` for a semantic violation.

- Variables and functions share a namespace and must be declared before use.
  Branches, loops, and functions have local scopes. Inner declarations can
  shadow outer names. A function can call itself.
- Assignments preserve a variable's inferred type when both types are known.
  Arithmetic takes numbers, `%` takes whole numbers, and logical operators and
  `if`/`while` conditions take Booleans. Equality accepts matching types or
  two numbers.
- `ask` returns a string. Arrays can hold mixed values and take whole-number
  indices. Function parameters, call results, and array elements can have
  unknown types during analysis. Operations that depend on those types need
  runtime checks.

Run `python3 semantic.py` for positive and negative examples.
