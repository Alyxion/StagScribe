"""Shape → SVG element mapping."""

from __future__ import annotations

from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import SubElement

from stagscribe.converter.layout import ResolvedBox
from stagscribe.converter.styles import build_style_attrs
from stagscribe.language.ast_nodes import Element


def render_shape(el: Element, box: ResolvedBox, parent: XmlElement) -> XmlElement:
    """Render an AST element as an SVG shape element."""
    shape_type = el.element_type
    if shape_type in ("rect", "rectangle"):
        return _render_rect(el, box, parent)
    if shape_type == "circle":
        return _render_circle(el, box, parent)
    if shape_type == "ellipse":
        return _render_ellipse(el, box, parent)
    if shape_type == "line":
        return _render_line(el, box, parent)
    if shape_type == "path":
        return _render_path(el, parent)
    if shape_type == "polygon":
        return _render_polygon(el, parent)
    if shape_type == "image":
        return _render_image(el, box, parent)
    # Default: group or unknown — render as <g>
    return _render_group(el, box, parent)


def _render_rect(el: Element, box: ResolvedBox, parent: XmlElement) -> XmlElement:
    attrs = {
        "x": _fmt(box.x),
        "y": _fmt(box.y),
        "width": _fmt(box.width),
        "height": _fmt(box.height),
    }
    if el.rounded:
        r = el.rounded.to_pixels()
        attrs["rx"] = _fmt(r)
        attrs["ry"] = _fmt(r)
    attrs.update(build_style_attrs(el))
    if el.rotate:
        cx = box.x + box.width / 2
        cy = box.y + box.height / 2
        attrs["transform"] = f"rotate({el.rotate},{_fmt(cx)},{_fmt(cy)})"
    svg_el = SubElement(parent, "rect", attrib=attrs)
    return svg_el


def _render_circle(el: Element, box: ResolvedBox, parent: XmlElement) -> XmlElement:
    r = box.width / 2
    attrs = {
        "cx": _fmt(box.x + r),
        "cy": _fmt(box.y + r),
        "r": _fmt(r),
    }
    attrs.update(build_style_attrs(el))
    return SubElement(parent, "circle", attrib=attrs)


def _render_ellipse(el: Element, box: ResolvedBox, parent: XmlElement) -> XmlElement:
    attrs = {
        "cx": _fmt(box.x + box.width / 2),
        "cy": _fmt(box.y + box.height / 2),
        "rx": _fmt(box.width / 2),
        "ry": _fmt(box.height / 2),
    }
    attrs.update(build_style_attrs(el))
    return SubElement(parent, "ellipse", attrib=attrs)


def _render_line(el: Element, box: ResolvedBox, parent: XmlElement) -> XmlElement:
    attrs: dict[str, str] = {}
    if el.line_from:
        attrs["x1"] = _fmt(el.line_from[0].to_pixels())
        attrs["y1"] = _fmt(el.line_from[1].to_pixels())
    else:
        attrs["x1"] = _fmt(box.x)
        attrs["y1"] = _fmt(box.y)
    if el.line_to:
        attrs["x2"] = _fmt(el.line_to[0].to_pixels())
        attrs["y2"] = _fmt(el.line_to[1].to_pixels())
    else:
        attrs["x2"] = _fmt(box.x + box.width)
        attrs["y2"] = _fmt(box.y + box.height)
    attrs.update(build_style_attrs(el))
    if "fill" not in attrs:
        attrs["fill"] = "none"
    return SubElement(parent, "line", attrib=attrs)


def _render_path(el: Element, parent: XmlElement) -> XmlElement:
    attrs: dict[str, str] = {}
    if el.path_data:
        attrs["d"] = el.path_data
    attrs.update(build_style_attrs(el))
    return SubElement(parent, "path", attrib=attrs)


def _render_polygon(el: Element, parent: XmlElement) -> XmlElement:
    attrs: dict[str, str] = {}
    if el.points:
        pts = " ".join(f"{_fmt(p[0].to_pixels())},{_fmt(p[1].to_pixels())}" for p in el.points)
        attrs["points"] = pts
    attrs.update(build_style_attrs(el))
    return SubElement(parent, "polygon", attrib=attrs)


def _render_image(el: Element, box: ResolvedBox, parent: XmlElement) -> XmlElement:
    attrs = {
        "x": _fmt(box.x),
        "y": _fmt(box.y),
        "width": _fmt(box.width),
        "height": _fmt(box.height),
    }
    if el.src:
        attrs["href"] = el.src
    return SubElement(parent, "image", attrib=attrs)


def _render_group(el: Element, box: ResolvedBox, parent: XmlElement) -> XmlElement:
    attrs: dict[str, str] = {}
    if el.rotate:
        cx = box.x + box.width / 2
        cy = box.y + box.height / 2
        attrs["transform"] = f"rotate({el.rotate},{_fmt(cx)},{_fmt(cy)})"
    attrs.update(build_style_attrs(el))
    return SubElement(parent, "g", attrib=attrs)


def _fmt(n: float) -> str:
    """Format a float for SVG output — strip trailing zeros."""
    if n == int(n):
        return str(int(n))
    return f"{n:.2f}"
