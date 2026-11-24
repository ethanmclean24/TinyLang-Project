"""Compile a StudyLang file to verified LLVM IR and optionally execute it."""

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lark.exceptions import UnexpectedInput
from lark.indenter import DedentError

from Compiler.compiler import CompilationError, Compiler
from Shared.frontend import parse
from Shared.errors import StudyLangRuntimeError
from Compiler.jit import run_ir
from Shared.m6_ast_tool import ASTValidationError
from Compiler.optimizer import optimize_ir
from Shared.semantic import SemanticError


def compile_source(source: str) -> str:
    program = parse(source if source.endswith("\n") else source + "\n")
    return Compiler().compile(program)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile StudyLang with LLVM and run with MCJIT.")
    parser.add_argument("file", type=Path, help="path to a .tiny source file")
    parser.add_argument("--emit-ir", action="store_true", help="print verified IR without executing")
    parser.add_argument("--opt", type=int, choices=(0, 1, 2, 3), default=0,
                        help="LLVM optimization level; default is 0")
    args = parser.parse_args()
    try:
        ir_text = optimize_ir(compile_source(args.file.read_text(encoding="utf-8")), args.opt)
        if args.emit_ir:
            print(ir_text)
        else:
            run_ir(ir_text)
    except (OSError, UnicodeError) as error:
        print(f"File error: {error}", file=sys.stderr)
    except (UnexpectedInput, DedentError, ASTValidationError, SemanticError, CompilationError) as error:
        print(f"Compilation error: {error}", file=sys.stderr)
    except StudyLangRuntimeError as error:
        print(f"Runtime error: {error}", file=sys.stderr)
    except RuntimeError as error:
        print(f"LLVM error: {error}", file=sys.stderr)
    else:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
