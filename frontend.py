"""StudyLang M3-M5: Parser/Frontend Integration

Uses one grammar, and uses a parser to produce an AST.
"""
from pathlib import Path

from lark import Lark, UnexpectedInput
from lark.indenter import DedentError, PythonIndenter

ROOT = Path(__file__).resolve().parent


class StudyLangIndenter(PythonIndenter):
    """Use PythonIndenter class to identify correct indentation and thus correct block tokens."""

    def handle_NL(self, token):
        if not self.paren_level:
            indent = token.rsplit("\n", 1)[-1]
            if "\t" in indent:
                raise DedentError("Use four spaces for indentation; tab characters are not allowed")
            width = len(indent)
            if width % 4 or width > self.indent_level[-1] + 4:
                raise DedentError("Each block must add exactly four spaces")
        yield from super().handle_NL(token)

    def process(self, stream):
        def checked_tokens():
            first = True
            for token in stream:
                if first and token.type != self.NL_type and token.column > 1:
                    raise DedentError("The first statement must start in column 1")
                first = False
                yield token

        return super().process(checked_tokens())



def create_parser():
    return Lark.open(
        str(ROOT / "grammar.lark"), start="start", parser="lalr",
        postlex=StudyLangIndenter(), maybe_placeholders=False,
    )


parser = create_parser()


def parse_tree(source):
    return parser.parse(source)


def is_valid(source):
    """Check syntax only; undefined variables and type errors are future work."""
    try:
        parse_tree(source)
        return True
    except (UnexpectedInput, DedentError):
        return False
