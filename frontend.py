"""StudyLang M3-M5: Parser/Frontend Integration

Uses one grammar, and uses a parser to produce an AST.
"""
import ast
from pathlib import Path
from pprint import pprint

from lark import Lark, Transformer, UnexpectedInput
from lark.indenter import DedentError, PythonIndenter

from ast_nodes import (
    Array, Ask, Assignment, BinaryOp, Block, Boolean, Call, For, Function,
    If, Index, Let, Not, Number, Program, Return, Show, String, Variable, While,
)

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


class ToAST(Transformer):
    """Methods match the rule names and aliases in grammar.lark."""

    def start(self, items):
        return Program(list(items))

    def number(self, items):
        return Number(float(items[0]))

    def string(self, items):
        # Grammar limits escapes; literal_eval decodes them without executing code.
        return String(ast.literal_eval(str(items[0])))

    def true(self, items):
        return Boolean(True)

    def false(self, items):
        return Boolean(False)

    def variable(self, items):
        return Variable(str(items[0]))

    def add(self, items):
        return BinaryOp("+", *items)

    def subtract(self, items):
        return BinaryOp("-", *items)

    def multiply(self, items):
        return BinaryOp("*", *items)

    def divide(self, items):
        return BinaryOp("/", *items)

    def remainder(self, items):
        return BinaryOp("%", *items)

    def compare(self, items):
        left, operator, right = items
        return BinaryOp(str(operator), left, right)

    def logical_and(self, items):
        return BinaryOp("and", *items)

    def logical_or(self, items):
        return BinaryOp("or", *items)

    def logical_not(self, items):
        return Not(items[0])

    def declaration(self, items):
        return Let(str(items[0]), items[1])

    def assignment(self, items):
        return Assignment(*items)

    def show_stmt(self, items):
        return Show(items[0])

    def ask(self, items):
        return Ask(items[0])

    def block(self, items):
        return Block(list(items))

    def if_stmt(self, items):
        return If(*items)

    def while_stmt(self, items):
        return While(*items)

    def for_stmt(self, items):
        return For(str(items[0]), items[1], items[2])

    def parameters(self, items):
        return [str(item) for item in items]

    def function_decl(self, items):
        name, *rest = items
        parameters = rest[0] if len(rest) == 2 else []
        return Function(str(name), parameters, rest[-1])

    def return_stmt(self, items):
        return Return(items[0])

    def arguments(self, items):
        return list(items)

    def call(self, items):
        return Call(str(items[0]), items[1] if len(items) == 2 else [])

    def elements(self, items):
        return list(items)

    def array_literal(self, items):
        return Array(items[0] if items else [])

    def index(self, items):
        return Index(*items)


def parse_tree(source):
    return parser.parse(source)


def parse(source):
    return ToAST().transform(parse_tree(source))


def is_valid(source):
    """Check syntax only; undefined variables and type errors are future work."""
    try:
        parse_tree(source)
        return True
    except (UnexpectedInput, DedentError):
        return False


if __name__ == "__main__":
    source = (ROOT / "examples/m3_m5_demo.tiny").read_text(encoding="utf-8")
    print("SOURCE")
    print(source)
    print("PARSE TREE")
    print(parse_tree(source).pretty())
    print("AST (no execution)")
    pprint(parse(source))
