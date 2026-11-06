"""AST metrics adapted from the M6 example; root depth is 1."""
from ast_nodes import (
    Array, Ask, Assignment, BinaryOp, Block, Boolean, Call, For, Function,
    If, Index, Let, Not, Number, Program, Return, Show, String, Variable, While,
)


def children(node):
    """Return immediate AST children in source order, excluding scalar fields."""
    kind = type(node)
    if kind in (Program, Block):
        return tuple(node.statements)
    if kind in (Number, String, Boolean, Variable):
        return ()
    if kind is BinaryOp:
        return (node.left, node.right)
    if kind is Not:
        return (node.operand,)
    if kind is Let:
        return (node.value,)
    if kind is Assignment:
        return (node.target, node.value)
    if kind in (Show, Return):
        return (node.expression,)
    if kind is Ask:
        return (node.prompt,)
    if kind is If:
        return ((node.condition, node.then_branch) if node.else_branch is None
                else (node.condition, node.then_branch, node.else_branch))
    if kind is While:
        return (node.condition, node.body)
    if kind is For:
        return (node.iterable, node.body)
    if kind is Function:
        return (node.body,)
    if kind is Call:
        return tuple(node.arguments)
    if kind is Array:
        return tuple(node.elements)
    if kind is Index:
        return (node.target, node.index)
    raise TypeError(f"Metrics do not support {kind.__name__}")


def node_count(node):
    return 1 + sum(node_count(child) for child in children(node))


def max_depth(node):
    kids = children(node)
    return 1 + max((max_depth(child) for child in kids), default=0)
