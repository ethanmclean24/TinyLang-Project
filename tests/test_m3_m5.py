"""M3-M5: Lexical and Structural Tests."""
from dataclasses import fields, is_dataclass
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lark import Token, Tree, UnexpectedInput
from lark.indenter import DedentError
from ast_nodes import (Array, Ask, Assignment, BinaryOp, Block, Boolean, Call,
                       For, Function, If, Index, Let, Not, Number, Program,
                       Return, Show, String, Variable, While)
from frontend import ToAST, create_parser, is_valid, parse, parse_tree
from test_parser import positive_tests, negative_tests

# M3: at least 3 lexical edge/negative cases (5 below).
# M4: these also cover at least 2 lexical/token-boundary negatives.
LEXICAL_NEGATIVES = [
    ("Illegal character", "show(@score)\n"),
    ("Identifier starts with a number", "let 2score = 1\n"),
    ("Reserved keyword as name", "let show = 1\n"),
    ("Unsupported operator", "show(2 ** 3)\n"),
    ("Unsupported string escape", 'show("bad\\q")\n'),
]


class StudyLangM3M5Tests(unittest.TestCase):
    def test_syntax_regression_and_lexical_errors(self):
        # M4: at least 4 positive parser cases; reuse all 7 M2 positives.
        for name, source in positive_tests:
            with self.subTest(name=name):
                self.assertTrue(is_valid(source))
                print(f"{name}: expected ACCEPT; actual ACCEPT")
        # M4: at least 4 negative parser cases; 12 M2 negatives + 5 lexical negatives.
        for name, source in negative_tests + LEXICAL_NEGATIVES:
            with self.subTest(name=name):
                self.assertFalse(is_valid(source))
                # M4: record expected/actual rejection and error type/location when available.
                try:
                    parse_tree(source)
                except (UnexpectedInput, DedentError) as error:
                    print(f"{name}: expected REJECT; actual REJECT; "
                          f"{type(error).__name__} line={getattr(error, 'line', None)} "
                          f"col={getattr(error, 'column', None)}")
                else:
                    self.fail("Invalid input accepted")

    # M5 valid AST case 1: declaration/assignment, arithmetic precedence, output, order.
    def test_declaration_assignment_output_precedence(self):
        source = "let score = 2 + 3 * 4\nscore = 10-3-2\nshow(score)\n"
        self.assertIsInstance(parse_tree(source), Tree)
        # M5: dataclass equality checks node types, fields, and nested structure.
        self.assertEqual(parse(source), Program([
            Let("score", BinaryOp("+", Number(2), BinaryOp("*", Number(3), Number(4)))),
            Assignment(Variable("score"), BinaryOp("-", BinaryOp("-", Number(10), Number(3)), Number(2))),
            Show(Variable("score")),
        ]))

    # M5 valid AST case 2: study input/output and nested Boolean precedence.
    def test_input_strings_boolean_precedence(self):
        self.assertEqual(parse('let answer = ask("Café\\n")\nshow(not False and True or False)\n'),
                         Program([Let("answer", Ask(String("Café\n"))),
                                  Show(BinaryOp("or", BinaryOp("and", Not(Boolean(False)), Boolean(True)), Boolean(False)))]))

    # M5 valid AST case 3: required control flow, nested blocks, optional else.
    def test_nested_control_flow(self):
        source = """while score < 3:
    if score == 1:
        show(score)
    else:
        score = score + 1
if True:
    show(0)
"""
        self.assertEqual(parse(source), Program([
            While(BinaryOp("<", Variable("score"), Number(3)), Block([
                If(BinaryOp("==", Variable("score"), Number(1)),
                   Block([Show(Variable("score"))]),
                   Block([Assignment(Variable("score"), BinaryOp("+", Variable("score"), Number(1)))]))])),
            If(Boolean(True), Block([Show(Number(0))])),
        ]))

    # M5 valid AST case 4: arrays, indexed assignment, and for-loop structure.
    def test_arrays_index_assignment_for(self):
        source = """let scores = [[1], []]
scores[0][0] = -5
for score in scores[0]:
    show(score)
"""
        self.assertEqual(parse(source), Program([
            Let("scores", Array([Array([Number(1)]), Array([])])),
            Assignment(Index(Index(Variable("scores"), Number(0)), Number(0)), Number(-5)),
            For("score", Index(Variable("scores"), Number(0)), Block([Show(Variable("score"))])),
        ]))

    # M5 additional M2 coverage: function/call/return fields and empty parameter lists.
    def test_functions_calls_returns(self):
        source = """function base():
    return 1
function add(a, b):
    return a + b
show(add(base(), 2))
"""
        self.assertEqual(parse(source), Program([
            Function("base", [], Block([Return(Number(1))])),
            Function("add", ["a", "b"], Block([Return(BinaryOp("+", Variable("a"), Variable("b")))])),
            Show(Call("add", [Call("base", []), Number(2)])),
        ]))

    # M5: operator fields and grouping; M3/M4: accepted numeric literal forms.
    def test_operators_and_number_forms(self):
        for op in ["+", "-", "*", "/", "%", "==", "!=", "<=", ">=", "<", ">"]:
            with self.subTest(op=op):
                self.assertEqual(parse(f"show(2 {op} 3)\n"), Program([Show(BinaryOp(op, Number(2), Number(3)))]))
        for literal, value in [(".5", .5), ("5.", 5), ("1e3", 1000), ("-5", -5)]:
            self.assertEqual(parse(f"show({literal})\n"), Program([Show(Number(value))]))
        self.assertEqual(parse("show((2 + 3) * 4)\n"), Program([Show(BinaryOp("*", BinaryOp("+", Number(2), Number(3)), Number(4)))]))

    # M3/M4: keyword-prefix identifiers and negative-literal/subtraction boundaries.
    def test_contextual_token_boundaries(self):
        interactive = create_parser().parse_interactive("let shower = -3\nshow(10-3)\n")
        tokens = list(interactive.iter_parse())
        interactive.feed_eof()
        self.assertIn(("NAME", "shower"), [(t.type, str(t)) for t in tokens])
        self.assertEqual([t.type for t in tokens if str(t).startswith('-')], ["NEGATIVE_NUMBER", "MINUS"])

    # M5: at least 2 invalid programs rejected before AST construction (3 below).
    def test_invalid_rejected_before_transform(self):
        for source in ["let x =\n", "show(@x)\n", "if True:\n  show(1)\n"]:
            with self.subTest(source=source), patch.object(ToAST, "transform") as transform:
                with self.assertRaises((UnexpectedInput, DedentError)):
                    parse(source)
                transform.assert_not_called()

    # M4: retest M2 examples; M5: at least 4 valid parse-tree-to-AST cases (9 below).
    def test_complete_ast_for_existing_examples(self):
        def check(value):
            self.assertNotIsInstance(value, (Tree, Token))
            if is_dataclass(value):
                for field in fields(value):
                    check(getattr(value, field.name))
            elif isinstance(value, list):
                for item in value:
                    check(item)
        sources = [source for _, source in positive_tests]
        for name in ["milestone1_examples.tiny", "m3_m5_demo.tiny"]:
            sources.append((ROOT / "examples" / name).read_text(encoding="utf-8"))
        for source in sources:
            with self.subTest(source=source):
                tree = parse_tree(source)
                result = parse(source)
                self.assertIsInstance(result, Program)
                self.assertEqual(len(result.statements), len(tree.children))
                # M5: no untransformed Lark trees/tokens left inside the AST.
                check(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
