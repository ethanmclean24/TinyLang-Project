# Milestone 1 — Execution Architecture

## A. INITIAL execution path
```text
TinyLang Source
      |
      v
Frontend
      |
      v
AST
      |
      v
Interpreter
      |
      v
Result
```

1. **Criterion:** Simplicity — **Reason:** StudyLang is meant to help students write small, readable study programs with input, output, variables, conditionals, and loops. An interpreter-oriented path is the simplest way to execute those programs first.
2. **Criterion:** Debuggability — **Reason:** An interpreter makes program behavior easier to inspect while the language is still being learned and refined.
3. **Criterion:** Semester scope — **Reason:** This path lets the project focus first on the frontend, AST, and basic execution before adding more advanced backend pieces like LLVM code generation or JIT execution.

**Trade-off:** This path gains simplicity, readability, and easier debugging, but it postpones performance-focused execution.

## B. Possible FUTURE execution path
```text
TinyLang Source
      |
      v
Frontend
      |
      v
AST
      |
      v
Code Generation
      |
      v
LLVM IR
      |
      v
JIT
      |
      v
Native Execution
```
**Benefit:** A compiler/JIT-oriented path could make StudyLang programs execute faster and would support a more advanced implementation once the language design is stable.  
**Cost/trade-off:** This adds more complexity and makes debugging harder, so it is better as a later path rather than the initial architecture.

## C. Semester reference architecture
```text
TinyLang Source
      |
      v
grammar.lark
      |
      v
frontend.py -> Parse Tree -> AST
                         /     \
                        v       v
               interpreter.py  codegen.py
                     |             |
                   Result        LLVM IR
                                   |
                                 jit.py
                                   |
                           Native Execution
```
**Week 2 boundary:** understand and map this architecture; do not implement later components yet.
