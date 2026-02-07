"""Structure validation rules — canvas presence, nesting, duplicates."""

from __future__ import annotations

from stagscribe.language.ast_nodes import Document, Element
from stagscribe.linter.diagnostics import Diagnostic, Severity


def check_structure(doc: Document) -> list[Diagnostic]:
    """Check document structure rules."""
    diagnostics: list[Diagnostic] = []

    # Must have at least one element
    if not doc.elements:
        diagnostics.append(
            Diagnostic(Severity.ERROR, "Document has no elements", rule="structure")
        )
        return diagnostics

    # Canvas checks
    canvases = [e for e in doc.elements if e.element_type == "canvas"]
    if len(canvases) == 0:
        diagnostics.append(
            Diagnostic(
                Severity.WARNING,
                "No canvas element — default size will be used",
                rule="structure",
            )
        )
    elif len(canvases) > 1:
        diagnostics.append(
            Diagnostic(
                Severity.ERROR,
                "Multiple canvas elements found — only one is allowed",
                line=canvases[1].line,
                rule="structure",
            )
        )

    # Canvas should be the first element
    if canvases and doc.elements[0].element_type != "canvas":
        diagnostics.append(
            Diagnostic(
                Severity.WARNING,
                "Canvas should be the first element",
                line=canvases[0].line,
                rule="structure",
            )
        )

    # Check for duplicate names
    names: dict[str, Element] = {}
    _collect_names(doc.elements, names, diagnostics)

    return diagnostics


def _collect_names(
    elements: list[Element],
    names: dict[str, Element],
    diagnostics: list[Diagnostic],
) -> None:
    for el in elements:
        if el.name:
            if el.name in names:
                diagnostics.append(
                    Diagnostic(
                        Severity.ERROR,
                        f"Duplicate element name: \"{el.name}\"",
                        line=el.line,
                        rule="structure",
                    )
                )
            else:
                names[el.name] = el
        _collect_names(el.children, names, diagnostics)
