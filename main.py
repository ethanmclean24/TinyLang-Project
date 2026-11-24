"""Select StudyLang's interpreter or LLVM compiler from one launcher."""

import argparse
from pathlib import Path
import sys

from lark.exceptions import UnexpectedInput
from lark.indenter import DedentError

from Compiler.compiler import CompilationError
from Compiler.run import compile_source
from Shared.config import AUTHOR, LANGUAGE_NAME, VERSION
from Interpreter.interpreter import Interpreter
from Shared.errors import StudyLangRuntimeError
from Compiler.jit import run_ir
from Shared.m6_ast_tool import ASTValidationError
from Compiler.optimizer import optimize_ir
from Interpreter.run import run
from Shared.semantic import SemanticError

ROOT = Path(__file__).resolve().parent


def run_program(source, mode, *, opt=0, show_ir=False, show_optimized_ir=False,
                output=print, input_fn=input):
    """Use the existing validated execution paths for the selected mode."""
    if mode not in ("interpreter", "compiler"):
        raise ValueError("Choose interpreter or compiler")
    if mode == "interpreter":
        if opt != 0 or show_ir or show_optimized_ir:
            raise ValueError("LLVM options require compiler mode")
        run(source, Interpreter(output=output, input_fn=input_fn))
        return
    raw_ir = compile_source(source)
    executable_ir = optimize_ir(raw_ir, opt)
    if show_ir:
        output("LLVM IR before optimization\n" + raw_ir)
    if show_optimized_ir:
        output(f"LLVM IR at O{opt}\n" + executable_ir)
    if show_ir or show_optimized_ir:
        output("Program output")
    run_ir(executable_ir, output=output)


def _choose_mode():
    print("1. Interpreter\n2. LLVM compiler\nQ. Exit")
    modes = {"1": "interpreter", "2": "compiler",
             "interpreter": "interpreter", "compiler": "compiler"}
    while True:
        choice = input("Choose execution mode: ").strip().lower()
        if choice == "q":
            return None
        if choice in modes:
            return modes[choice]
        print("Choose 1, 2, or Q.")


def _choose_file():
    examples = sorted((ROOT / "Examples").glob("*.tiny"))
    print("Select a StudyLang source file:")
    for index, example in enumerate(examples, 1):
        print(f"{index}. {example.name}")
    print("P. Enter another file path\nB. Back")
    while True:
        choice = input("Selection: ").strip()
        if choice.lower() == "b":
            return None
        if choice.lower() == "p":
            entered = input("Source file path: ").strip().strip('"')
            path = Path(entered).expanduser()
            if path.is_file():
                return path
            print(f"File not found: {path}")
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            return examples[int(choice) - 1]
        else:
            print("Choose a listed number, P, or B.")


def _choose_optimization():
    while True:
        choice = input("Optimization level [0-3, default 2]: ").strip() or "2"
        if choice in ("0", "1", "2", "3"):
            return int(choice)
        print("Choose 0, 1, 2, or 3.")


def _yes_no(prompt):
    while True:
        choice = input(prompt + " [y/N]: ").strip().lower()
        if choice in ("", "n", "no"):
            return False
        if choice in ("y", "yes"):
            return True
        print("Please enter y or n.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run StudyLang with the interpreter or LLVM compiler.")
    parser.add_argument("--mode", choices=("interpreter", "compiler"))
    parser.add_argument("--file", type=Path, help="source file; defaults to Examples/m9_demo.tiny in CLI mode")
    parser.add_argument("--opt", type=int, choices=(0, 1, 2, 3), help="LLVM optimization level; CLI default is 0")
    parser.add_argument("--show-ir", action="store_true", help="display IR before optimization")
    parser.add_argument("--show-optimized-ir", action="store_true", help="display IR at the selected level")
    args = parser.parse_args()
    try:
        mode = args.mode
        interactive = mode is None
        path = args.file
        if interactive:
            print(f"{LANGUAGE_NAME} {VERSION} — {AUTHOR}")
            while True:
                mode = _choose_mode()
                if mode is None:
                    return 0
                path = args.file if args.file is not None else _choose_file()
                if path is not None:
                    break
        if mode == "interpreter" and (
            args.opt is not None or args.show_ir or args.show_optimized_ir
        ):
            parser.error("--opt and IR display options require --mode compiler")
        if path is None:
            path = ROOT / "Examples" / "m9_demo.tiny"
        opt = args.opt if args.opt is not None else 0
        show_ir, show_optimized_ir = args.show_ir, args.show_optimized_ir
        if interactive and mode == "compiler":
            if args.opt is None:
                opt = _choose_optimization()
            if not show_ir:
                show_ir = _yes_no("Show IR before optimization?")
            if not show_optimized_ir:
                show_optimized_ir = _yes_no("Show IR at the selected optimization level?")
        run_program(path.expanduser().read_text(encoding="utf-8"), mode, opt=opt,
                    show_ir=show_ir, show_optimized_ir=show_optimized_ir)
    except (OSError, UnicodeError) as error:
        print(f"File error: {error}", file=sys.stderr)
    except (UnexpectedInput, DedentError) as error:
        print(f"Syntax error: {error}", file=sys.stderr)
    except ASTValidationError as error:
        print(f"AST error: {error}", file=sys.stderr)
    except SemanticError as error:
        print(f"Semantic error: {error}", file=sys.stderr)
    except CompilationError as error:
        print(f"Compilation error: {error}", file=sys.stderr)
    except StudyLangRuntimeError as error:
        print(f"Runtime error: {error}", file=sys.stderr)
    except RuntimeError as error:
        print(f"LLVM error: {error}", file=sys.stderr)
    except (EOFError, KeyboardInterrupt):
        print("\nExecution cancelled.", file=sys.stderr)
        return 130
    else:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
