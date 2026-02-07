"""Color validation — ensure all color values resolve."""

from __future__ import annotations

from stagscribe.language.ast_nodes import Document, Element
from stagscribe.language.colors import resolve_color
from stagscribe.linter.diagnostics import Diagnostic, Severity


def check_colors(doc: Document) -> list[Diagnostic]:
    """Validate all color values in the document."""
    diagnostics: list[Diagnostic] = []
    _check_element_colors(doc.elements, diagnostics)
    return diagnostics


def _check_element_colors(
    elements: list[Element],
    diagnostics: list[Diagnostic],
) -> None:
    for el in elements:
        _validate_color(el.fill, "fill", el, diagnostics)
        _validate_color(el.background, "background", el, diagnostics)
        if el.stroke and el.stroke.color:
            _validate_color(el.stroke.color, "stroke color", el, diagnostics)
        if el.text_style and el.text_style.color:
            _validate_color(el.text_style.color, "text color", el, diagnostics)
        _check_element_colors(el.children, diagnostics)


def _validate_color(
    color: str | None,
    prop_name: str,
    el: Element,
    diagnostics: list[Diagnostic],
) -> None:
    if color is None:
        return
    # Already resolved by the parser (hex values, etc.)
    if color.startswith("#") or color.startswith("rgb") or color == "none":
        return
    if resolve_color(color) is None:
        diagnostics.append(
            Diagnostic(
                Severity.ERROR,
                f"Unknown color \"{color}\" in {prop_name}",
                line=el.line,
                rule="colors",
            )
        )
