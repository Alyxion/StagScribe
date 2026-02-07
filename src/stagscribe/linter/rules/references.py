"""Reference validation — ensure referenced element names exist."""

from __future__ import annotations

from stagscribe.language.ast_nodes import Document, Element
from stagscribe.linter.diagnostics import Diagnostic, Severity


def check_references(doc: Document) -> list[Diagnostic]:
    """Check that all element references point to existing names."""
    diagnostics: list[Diagnostic] = []

    # Collect all named elements
    names: set[str] = set()
    _collect_all_names(doc.elements, names)

    # Check all references
    _check_element_refs(doc.elements, names, diagnostics)

    return diagnostics


def _collect_all_names(elements: list[Element], names: set[str]) -> None:
    for el in elements:
        if el.name:
            names.add(el.name)
        _collect_all_names(el.children, names)


def _check_element_refs(
    elements: list[Element],
    names: set[str],
    diagnostics: list[Diagnostic],
) -> None:
    for el in elements:
        if el.position and el.position.reference:
            ref = el.position.reference
            if ref not in names:
                diagnostics.append(
                    Diagnostic(
                        Severity.ERROR,
                        f"Referenced element \"{ref}\" not found",
                        line=el.line,
                        rule="references",
                    )
                )
        _check_element_refs(el.children, names, diagnostics)
