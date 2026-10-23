"""AST Nodes matching grammar."""
from dataclasses import dataclass
from typing import List, Optional


class Node:
    pass


@dataclass
class Program(Node):
    statements: List[Node]


@dataclass
class Number(Node):
    value: float


@dataclass
class String(Node):
    value: str


@dataclass
class Boolean(Node):
    value: bool


@dataclass
class Variable(Node):
    name: str


@dataclass
class BinaryOp(Node):
    op: str
    left: Node
    right: Node


@dataclass
class Not(Node):
    operand: Node


@dataclass
class Let(Node):
    name: str
    value: Node


@dataclass
class Assignment(Node):
    target: Node
    value: Node


@dataclass
class Show(Node):
    expression: Node


@dataclass
class Ask(Node):
    prompt: Node


@dataclass
class Block(Node):
    statements: List[Node]


@dataclass
class If(Node):
    condition: Node
    then_branch: Block
    else_branch: Optional[Block] = None


@dataclass
class While(Node):
    condition: Node
    body: Block


@dataclass
class For(Node):
    variable: str
    iterable: Node
    body: Block


@dataclass
class Function(Node):
    name: str
    parameters: List[str]
    body: Block


@dataclass
class Return(Node):
    expression: Node


@dataclass
class Call(Node):
    name: str
    arguments: List[Node]


@dataclass
class Array(Node):
    elements: List[Node]


@dataclass
class Index(Node):
    target: Node
    index: Node
