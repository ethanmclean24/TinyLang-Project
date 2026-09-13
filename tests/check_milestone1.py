"""Milestone 1 completion aid — not a design-quality autograder."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required_files = [
    "config.py", "main.py", "README.md", "ARCHITECTURE.md",
    "examples/milestone1_examples.tiny", "grammar.lark", "frontend.py",
    "ast_nodes.py", "semantic.py", "interpreter.py", "codegen.py", "jit.py",
]

editable_week2 = [
    ("README.md", "README specification"),
    ("ARCHITECTURE.md", "architecture"),
    ("examples/milestone1_examples.tiny", "informal examples"),
]

print("TinyLang Milestone 1 readiness check")
print("=" * 39)

missing = 0
for rel in required_files:
    ok = (ROOT / rel).exists()
    print(("[PASS]  " if ok else "[CHECK] ") + rel)
    missing += 0 if ok else 1

print("\nWeek 2 editable-file placeholder check")
print("-" * 39)
todo_count = 0
for rel, label in editable_week2:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    ok = path.exists() and "TODO" not in text
    print(("[PASS]  " if ok else "[CHECK] ") + label)
    todo_count += 0 if ok else 1

print("\nInterpretation")
print("-" * 39)
if missing == 0 and todo_count == 0:
    print("Basic Week 2 package checks pass.")
else:
    print("Complete the items marked [CHECK] before submission.")

print("This script checks package readiness only; it does NOT grade design quality.")
print("Review START_HERE.md, the Guided Development Workbook, and Moodle before submitting.")
