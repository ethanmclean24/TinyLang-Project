"""Run a StudyLang source file through the interpreter."""

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lark.exceptions import UnexpectedInput
from lark.indenter import DedentError

from Shared.frontend import parse
from Interpreter.interpreter import Interpreter, StudyLangRuntimeError
from Shared.m6_ast_tool import ASTValidationError, validate_ast
from Shared.semantic import SemanticAnalyzer, SemanticError


def run(source: str, interpreter=None) -> None:
    # Finish all frontend checks before executing any statement.
    program = parse(source if source.endswith("\n") else source + "\n")
    validate_ast(program)
    SemanticAnalyzer().analyze(program)
    if interpreter is None:
        interpreter = Interpreter()
    interpreter.execute(program)


def main() -> int:
    parser = argparse.ArgumentParser(description="Interpret a StudyLang source file.")
    parser.add_argument("file", type=Path, help="path to a .tiny source file")
    args = parser.parse_args()

    try:
        run(args.file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as error:
        print(f"File error: {error}", file=sys.stderr)
    except (UnexpectedInput, DedentError) as error:
        print(f"Syntax error: {error}", file=sys.stderr)
    except ASTValidationError as error:
        print(f"AST error: {error}", file=sys.stderr)
    except SemanticError as error:
        print(f"Semantic error: {error}", file=sys.stderr)
    except StudyLangRuntimeError as error:
        print(f"Runtime error: {error}", file=sys.stderr)
    else:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
