"""Signatures shared by semantic analysis and the interpreter's array queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Builtin:
    name: str
    arity: int
    result_type: str


BUILTINS = {
    "len": Builtin("len", 1, "integer"),
    "contains": Builtin("contains", 2, "boolean"),
}
