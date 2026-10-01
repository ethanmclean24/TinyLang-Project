from pathlib import Path

from lark import Lark, UnexpectedInput
from lark.indenter import DedentError, PythonIndenter


ROOT = Path(__file__).resolve().parents[1]


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


parser = Lark.open(
    str(ROOT / "grammar.lark"),
    start="start",
    parser="lalr",
    postlex=StudyLangIndenter(),
    maybe_placeholders=False,
)

positive_tests = [
    ("Declarations and assignment", """
let score = -5
let total_score = 10
score = score + total_score
show(score)
"""),
    ("Arithmetic and grouping", """
let result = (2 + 3) * 4 - 10 / 2
show(result % 3)
show(2 + 3 * 4)
show(10 - 3 - 2)
show(.5 + 5. + 1e3)
"""),
    ("Input, output, and strings", r'''
let answer = ask("What keyword declares a variable?")
show(answer)
show("Quotes: \"yes\", backslash: \\, newline:\n tab:\t return:\r")
# This line tests comments.
show("# inside a string")
'''),
    ("Comparisons and conditionals", """
let score = 7
if score >= 0 and score <= 10 and not False or True:
    if score == 10:
        show("Perfect")
    else:
        show("Keep studying")
show(score != 0)
show(score < 10)
show(score > 0)
"""),
    ("Functions and return values", """
function starting_score():
    return -5
function same(value):
    return value
function add(a, b):
    return a + b
show(add(starting_score(), same(10)))
"""),
    ("Arrays and indexing", """
function scores():
    return [1, 2 + 3, -5]
let empty = []
let single = [1]
let values = scores()
values[0] = values[1] + 1
let matrix = [[1, 2], [3, 4]]
matrix[0][1] = values[0]
show(matrix[0][1])
show(matrix)
"""),
    ("While and for loops", """
let scores = [1, 2, 3]
let current = 0
while current < 3:
    scores[current] = scores[current] + 1
    current = current + 1
for row in [[1, 2], [3, 4]]:
    for score in row:
        if score > 0:
            show(score)
show(scores)
"""),
]

negative_tests = [
    ("Missing initializer", "let score =\n"),
    ("Missing output argument", "show()\n"),
    ("Missing call parentheses", "show 1\n"),
    ("Incorrect indentation", """
if True:
  show(1)
"""),
    ("Empty program", ""),
    ("Empty block", """
if True:

"""),
    ("Unary expression", "show(-score)\n"),
    ("Trailing array comma", "let scores = [1, 2,]\n"),
    ("Missing array index", "show(scores[])\n"),
    ("Missing loop iterable", """
for score in:
    show(score)
"""),
    ("Missing return value", """
function score():
    return
"""),
    ("Single quoted string", "show('hello')\n"),
]

if __name__ == "__main__":
    passed = 0
    print("POSITIVE TESTS")
    for description, source in positive_tests:
        try:
            parser.parse(source)
            print("PASS:", description)
            passed += 1
        except (UnexpectedInput, DedentError) as error:
            print("FAIL:", description, type(error).__name__)

    print("\nNEGATIVE TESTS")
    for description, source in negative_tests:
        try:
            parser.parse(source)
            print("FAIL (accepted):", description)
        except (UnexpectedInput, DedentError):
            print("PASS (rejected):", description)
            passed += 1

    print("\nEXAMPLE PARSE TREE")
    print(parser.parse("show(2 + 3 * 4)\n").pretty())

    total = len(positive_tests) + len(negative_tests)
    failed = total - passed
    print(f"Tests: {total} | Passed: {passed} | Failed: {failed}")
    if failed:
        raise SystemExit(1)
