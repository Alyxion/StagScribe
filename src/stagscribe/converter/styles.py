"""Style → SVG attribute mapping."""

from __future__ import annotations

from stagscribe.language.ast_nodes import Element, StrokeStyle, TextStyle


def build_style_attrs(el: Element) -> dict[str, str]:
    """Build SVG style attributes from element properties."""
    attrs: dict[str, str] = {}

    if el.fill:
        attrs["fill"] = el.fill
    if el.opacity is not None:
        attrs["opacity"] = str(el.opacity)
    if el.stroke:
        _apply_stroke(el.stroke, attrs)

    return attrs


def build_text_attrs(style: TextStyle | None) -> dict[str, str]:
    """Build SVG text attributes from TextStyle."""
    attrs: dict[str, str] = {}
    if style is None:
        return attrs

    if style.size:
        attrs["font-size"] = str(style.size.to_pixels())
    if style.color:
        attrs["fill"] = style.color
    if style.weight:
        attrs["font-weight"] = style.weight
    if style.style:
        attrs["font-style"] = style.style
    if style.font:
        attrs["font-family"] = style.font
    if style.align:
        anchor_map = {"left": "start", "center": "middle", "right": "end"}
        attrs["text-anchor"] = anchor_map.get(style.align, "middle")

    return attrs


def _apply_stroke(stroke: StrokeStyle, attrs: dict[str, str]) -> None:
    if stroke.color:
        attrs["stroke"] = stroke.color
    if stroke.width:
        attrs["stroke-width"] = str(stroke.width.to_pixels())
    if stroke.dash == "dashed":
        attrs["stroke-dasharray"] = "8,4"
    elif stroke.dash == "dotted":
        attrs["stroke-dasharray"] = "2,2"
