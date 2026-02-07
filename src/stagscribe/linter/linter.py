"""StagScribe linter — orchestrates validation rules on AST."""

from __future__ import annotations

from stagscribe.language.ast_nodes import Document
from stagscribe.linter.diagnostics import Diagnostic, Severity
from stagscribe.linter.rules.colors_rule import check_colors
from stagscribe.linter.rules.references import check_references
from stagscribe.linter.rules.structure import check_structure
from stagscribe.linter.rules.style import check_style


def lint(doc: Document) -> list[Diagnostic]:
    """Run all linter rules on a parsed document. Returns diagnostics sorted by severity."""
    diagnostics: list[Diagnostic] = []

    diagnostics.extend(check_structure(doc))
    diagnostics.extend(check_references(doc))
    diagnostics.extend(check_colors(doc))
    diagnostics.extend(check_style(doc))

    # Sort: errors first, then warnings, then info
    severity_order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}
    diagnostics.sort(key=lambda d: severity_order.get(d.severity, 3))

    return diagnostics


def has_errors(diagnostics: list[Diagnostic]) -> bool:
    """Check if any diagnostics are errors."""
    return any(d.severity == Severity.ERROR for d in diagnostics)
