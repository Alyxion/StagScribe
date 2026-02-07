"""Token types used in the StagScribe lexer/parser."""

from enum import StrEnum


class TokenType(StrEnum):
    # Structure
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    NEWLINE = "NEWLINE"
    COMMENT = "COMMENT"

    # Literals
    NUMBER = "NUMBER"
    STRING = "STRING"
    HEX_COLOR = "HEX_COLOR"
    PERCENTAGE = "PERCENTAGE"

    # Identifiers and keywords
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    ELEMENT_TYPE = "ELEMENT_TYPE"

    # Punctuation
    COMMA = "COMMA"

    # Special
    EOF = "EOF"
