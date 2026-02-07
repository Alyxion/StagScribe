"""Diagnostic types for the StagScribe linter."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Diagnostic:
    """A linter diagnostic (error, warning, or info)."""

    severity: Severity
    message: str
    line: int | None = None
    column: int | None = None
    rule: str | None = None

    def __str__(self) -> str:
        loc = ""
        if self.line is not None:
            loc = f":{self.line}"
            if self.column is not None:
                loc += f":{self.column}"
        rule_tag = f" [{self.rule}]" if self.rule else ""
        return f"{self.severity.value}{loc}{rule_tag}: {self.message}"
