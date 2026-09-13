# StudyLang
**Version:** 0.1  
**Author:** Ethan McLean  
**Current Milestone:** Milestone 1 — Initial Language Specification

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

## 6. Statement Forms
- Declaration- `let`
- Assigment- simple `=`. Automatic memory management. 
- Output- `show`
- Input- `ask`. Simple built in function to make it easy to get inputs. 
- Conditionals- `if bool` or `if (conditional statement)` or `if variable`
- repitition- `while (condition)` or `for item in [list]`
- blocks- (indentation, new lines). Similiar to python for simplicity
    ```
    let this = "a statement"

    if (this = "a statement"):
        return
    ```


## 7. Expression Forms
TODO: Describe arithmetic, comparison, logical, literal, and variable-reference expressions.
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
- [ ] Formal grammar — later
- [ ] Frontend/lexer/parser — later
- [ ] AST — later
- [ ] Semantic analysis — later
- [ ] Interpreter — later
- [ ] LLVM backend/JIT — later
