"""Readable preorder AST walk, adapted from the M6 example."""
from ast_nodes import BinaryOp, Boolean, Call, For, Function, Let, Number, String, Variable
from metric import children


def walk(node, depth=0):
    kids = children(node)  # Reject unsupported nodes instead of skipping them.
    label = type(node).__name__
    if type(node) is Number:
        label += f"({node.value:g})"
    elif type(node) in (String, Boolean):
        label += f"({node.value!r})"
    elif type(node) is BinaryOp:
        label += f"({node.op})"
    elif type(node) in (Variable, Let, Call):
        label += f"({node.name})"
    elif type(node) is For:
        label += f"({node.variable})"
    elif type(node) is Function:
        label += f"({node.name}, parameters={node.parameters!r})"
    print("  " * depth + label)
    for child in kids:
        walk(child, depth + 1)
