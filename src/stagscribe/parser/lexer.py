"""Indentation-aware preprocessor for StagScribe using Lark's Indenter."""

from __future__ import annotations

from collections.abc import Iterator

from lark import Token
from lark.indenter import Indenter


class StagIndenter(Indenter):
    """Indentation handler for StagScribe's 2-space indent syntax."""

    NL_type = "_NL"
    OPEN_PAREN_types: list[str] = []
    CLOSE_PAREN_types: list[str] = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 2  # 2-space indentation

    def handle_NL(self, token: Token) -> Iterator[Token]:  # noqa: N802
        yield from super().handle_NL(token)
