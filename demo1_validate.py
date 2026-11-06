"""Run the M6 validation, walk, metrics, and precedence demonstration."""
from ast_nodes import BinaryOp, Number, Program, Show
from frontend import ROOT, parse, parse_tree
from m6_ast_tool import validate_ast
from metric import max_depth, node_count
from walk import walk

SOURCE = "show(3 + 5 * 2)\n"
GROUPED_SOURCE = "show((3 + 5) * 2)\n"


def inspect_source(label, source):
    print(f"\n{label}\nSOURCE:\n{source}")
    print("PARSE TREE:\n" + parse_tree(source).pretty())
    ast = parse(source)
    validate_ast(ast)
    print("AST WALK:")
    walk(ast)
    print(f"METRICS: nodes={node_count(ast)}, max_depth={max_depth(ast)}")
    return ast


def main():
    ast = inspect_source("PRECEDENCE", SOURCE)
    assert isinstance(ast, Program) and len(ast.statements) == 1
    statement = ast.statements[0]
    assert isinstance(statement, Show)
    assert statement.expression == BinaryOp("+", Number(3), BinaryOp("*", Number(5), Number(2)))
    assert (node_count(ast), max_depth(ast)) == (7, 5)

    grouped = inspect_source("GROUPING", GROUPED_SOURCE)
    assert grouped.statements[0].expression == BinaryOp("*", BinaryOp("+", Number(3), Number(5)), Number(2))
    assert (node_count(grouped), max_depth(grouped)) == (7, 5)

    source = (ROOT / "examples/m3_m5_demo.tiny").read_text(encoding="utf-8")
    study = inspect_source("STUDY SESSION", source)
    assert (node_count(study), max_depth(study)) == (68, 8)
    print("PASS: structure, precedence, grouping, and study-session regression validated")


if __name__ == "__main__":
    main()
