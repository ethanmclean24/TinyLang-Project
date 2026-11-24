"""Compile a StudyLang file to verified LLVM IR and optionally execute it."""

import argparse
from pathlib import Path
import sys

from lark.exceptions import UnexpectedInput
from lark.indenter import DedentError

from codegen import CompilationError, Compiler
from frontend import parse
from interpreter import StudyLangRuntimeError
from jit import run_ir
from m6_ast_tool import ASTValidationError
from semantic import SemanticError


def compile_source(source: str) -> str:
    program = parse(source if source.endswith("\n") else source + "\n")
    return Compiler().compile(program)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile StudyLang with LLVM and run with MCJIT.")
    parser.add_argument("file", type=Path, help="path to a .tiny source file")
    parser.add_argument("--emit-ir", action="store_true", help="print verified IR without executing")
    args = parser.parse_args()
    try:
        ir_text = compile_source(args.file.read_text(encoding="utf-8"))
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
    else:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
