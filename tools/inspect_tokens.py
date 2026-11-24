"""Print actual contextual parser tokens, including indentation markers.

Interactive parsing used to add context. Positive/cases are handled in test_m3_m5.py for efficiency (can test all stages in one place).
"""
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Shared.frontend import ROOT, create_parser


def main():
    source = (ROOT / "Examples/m3_m5_demo.tiny").read_text(encoding="utf-8")
    interactive = create_parser().parse_interactive(source)
    for token in interactive.iter_parse():
        print(f"{token.type:<18} {token.value!r} line={token.line} col={token.column}")
    interactive.feed_eof()  # Also reject incomplete programs at end of input.


if __name__ == "__main__":
    main()
