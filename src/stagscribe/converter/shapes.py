"""Shape → SVG element mapping."""

from __future__ import annotations

import math
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
    if shape_type == "gear":
        return _render_gear(el, box, parent)
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


def _render_gear(el: Element, box: ResolvedBox, parent: XmlElement) -> XmlElement:
    """Render a gear element as an SVG path."""
    teeth = el.teeth or 12
    module = el.tooth_module or 10.0
    cx = box.x + box.width / 2
    cy = box.y + box.height / 2
    rotation_deg = box.rotation

    d = _gear_path_data(cx, cy, teeth, module, rotation_deg)
    attrs: dict[str, str] = {"d": d}
    attrs.update(build_style_attrs(el))
    return SubElement(parent, "path", attrib=attrs)


def _gear_path_data(
    cx: float, cy: float, teeth: int, module: float, rotation_deg: float = 0.0,
) -> str:
    """Generate SVG path data for a gear profile.

    Uses trapezoidal tooth approximation: wider base, narrower tip.
    """
    pitch_r = module * teeth / 2
    outer_r = pitch_r + module
    root_r = max(pitch_r - 1.25 * module, module * 0.5)

    pitch_angle = 2 * math.pi / teeth
    # Involute approximation with 3 radii: root, pitch, outer
    # Tooth is wider at root, narrower at tip
    root_half = pitch_angle * 0.30   # half-angle at root circle
    pitch_half = pitch_angle * 0.25  # half-angle at pitch circle
    tip_half = pitch_angle * 0.18    # half-angle at outer circle
    rot = math.radians(rotation_deg)

    parts: list[str] = []
    for i in range(teeth):
        center = i * pitch_angle + rot
        gap_left = center - pitch_angle / 2

        if i == 0:
            gx = cx + root_r * math.cos(gap_left)
            gy = cy + root_r * math.sin(gap_left)
            parts.append(f"M {gx:.2f},{gy:.2f}")

        # Arc along root to left base of tooth
        bl = center - root_half
        bx = cx + root_r * math.cos(bl)
        by = cy + root_r * math.sin(bl)
        parts.append(f"A {root_r:.2f},{root_r:.2f} 0 0,1 {bx:.2f},{by:.2f}")

        # Left flank: root → pitch circle
        pl = center - pitch_half
        px = cx + pitch_r * math.cos(pl)
        py = cy + pitch_r * math.sin(pl)
        parts.append(f"L {px:.2f},{py:.2f}")

        # Left flank: pitch → tip
        tl = center - tip_half
        tx = cx + outer_r * math.cos(tl)
        ty = cy + outer_r * math.sin(tl)
        parts.append(f"L {tx:.2f},{ty:.2f}")

        # Tip arc
        tr = center + tip_half
        trx = cx + outer_r * math.cos(tr)
        try_ = cy + outer_r * math.sin(tr)
        parts.append(f"A {outer_r:.2f},{outer_r:.2f} 0 0,1 {trx:.2f},{try_:.2f}")

        # Right flank: tip → pitch circle
        pr = center + pitch_half
        prx = cx + pitch_r * math.cos(pr)
        pry = cy + pitch_r * math.sin(pr)
        parts.append(f"L {prx:.2f},{pry:.2f}")

        # Right flank: pitch → root
        br = center + root_half
        brx = cx + root_r * math.cos(br)
        bry = cy + root_r * math.sin(br)
        parts.append(f"L {brx:.2f},{bry:.2f}")

        # Arc along root to next gap
        gap_right = center + pitch_angle / 2
        ngx = cx + root_r * math.cos(gap_right)
        ngy = cy + root_r * math.sin(gap_right)
        parts.append(f"A {root_r:.2f},{root_r:.2f} 0 0,1 {ngx:.2f},{ngy:.2f}")

    parts.append("Z")
    return " ".join(parts)


def _fmt(n: float) -> str:
    """Format a float for SVG output — strip trailing zeros."""
    if n == int(n):
        return str(int(n))
    return f"{n:.2f}"
