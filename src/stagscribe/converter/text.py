"""Text rendering for SVG output."""

from __future__ import annotations

from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import SubElement

from stagscribe.converter.layout import ResolvedBox
from stagscribe.converter.styles import build_style_attrs, build_text_attrs
from stagscribe.language.ast_nodes import Element


def render_text(el: Element, box: ResolvedBox, parent: XmlElement) -> XmlElement:
    """Render a text AST element as an SVG <text> element."""
    # Position text at center of its box by default
    x = box.x + box.width / 2
    y = box.y + box.height / 2

    attrs: dict[str, str] = {
        "x": _fmt(x),
        "y": _fmt(y),
        "text-anchor": "middle",
        "dominant-baseline": "central",
    }

    # Apply text style
    text_attrs = build_text_attrs(el.text_style)
    attrs.update(text_attrs)

    # Apply general style (but fill comes from text_style color if set)
    style_attrs = build_style_attrs(el)
    # Don't override text fill with element fill
    if "fill" in style_attrs and "fill" in attrs:
        del style_attrs["fill"]
    attrs.update(style_attrs)

    svg_text = SubElement(parent, "text", attrib=attrs)
    svg_text.text = el.name or ""

    return svg_text


def _fmt(n: float) -> str:
    if n == int(n):
        return str(int(n))
    return f"{n:.2f}"
