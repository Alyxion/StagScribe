"""Lark parser wrapper for StagScribe."""

from __future__ import annotations

from pathlib import Path

from lark import Lark, Tree

from stagscribe.language.ast_nodes import Document
from stagscribe.parser.lexer import StagIndenter
from stagscribe.parser.transformer import StagTransformer

_GRAMMAR_PATH = Path(__file__).parent.parent / "language" / "grammar.lark"

_parser: Lark | None = None


def _get_parser() -> Lark:
    global _parser
    if _parser is None:
        _parser = Lark(
            _GRAMMAR_PATH.read_text(),
            parser="lalr",
            postlex=StagIndenter(),
            propagate_positions=True,
            maybe_placeholders=False,
        )
    return _parser


def parse_to_tree(source: str) -> Tree:
    """Parse StagScribe source into a Lark parse tree."""
    # Ensure trailing newline for the indenter
    if not source.endswith("\n"):
        source += "\n"
    return _get_parser().parse(source)


def parse(source: str) -> Document:
    """Parse StagScribe source into an AST Document."""
    tree = parse_to_tree(source)
    transformer = StagTransformer()
    result: Document = transformer.transform(tree)
    return result
