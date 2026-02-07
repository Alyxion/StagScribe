"""Style validation — check for questionable style choices."""

from __future__ import annotations

from stagscribe.language.ast_nodes import Document, Element
from stagscribe.linter.diagnostics import Diagnostic, Severity


def check_style(doc: Document) -> list[Diagnostic]:
    """Check for style issues and best practices."""
    diagnostics: list[Diagnostic] = []
    _check_elements(doc.elements, diagnostics)
    return diagnostics


def _check_elements(
    elements: list[Element],
    diagnostics: list[Diagnostic],
) -> None:
    for el in elements:
        # Canvas should have width and height
        if el.element_type == "canvas":
            if el.width is None or el.height is None:
                diagnostics.append(
                    Diagnostic(
                        Severity.WARNING,
                        "Canvas should have explicit width and height",
                        line=el.line,
                        rule="style",
                    )
                )

        # Rectangles/circles should have dimensions or radius
        if el.element_type in ("rectangle", "rect"):
            if el.width is None and el.height is None:
                diagnostics.append(
                    Diagnostic(
                        Severity.WARNING,
                        f"Element \"{el.name or el.element_type}\" has no dimensions",
                        line=el.line,
                        rule="style",
                    )
                )

        if el.element_type == "circle" and el.radius is None:
            diagnostics.append(
                Diagnostic(
                    Severity.WARNING,
                    f"Circle \"{el.name or 'unnamed'}\" has no radius",
                    line=el.line,
                    rule="style",
                )
            )

        # Text elements should have text_style with size
        if el.element_type == "text":
            if el.text_style is None or el.text_style.size is None:
                diagnostics.append(
                    Diagnostic(
                        Severity.INFO,
                        f"Text \"{el.name or 'unnamed'}\" has no explicit size",
                        line=el.line,
                        rule="style",
                    )
                )

        _check_elements(el.children, diagnostics)
