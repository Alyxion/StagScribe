"""AST → SVG XML builder."""

from __future__ import annotations

from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import tostring

from stagscribe.converter.layout import ResolvedBox, resolve_layout
from stagscribe.converter.shapes import render_shape
from stagscribe.converter.text import render_text
from stagscribe.language.ast_nodes import Document, Element


def build_svg(doc: Document, debug: set[str] | None = None) -> str:
    """Convert a StagScribe AST Document to an SVG XML string."""
    boxes = resolve_layout(doc)

    # Determine canvas size
    canvas = doc.canvas
    canvas_w = canvas.width.to_pixels() if canvas and canvas.width else 800.0
    canvas_h = canvas.height.to_pixels() if canvas and canvas.height else 600.0

    # Create root SVG element
    svg = XmlElement("svg")
    svg.set("xmlns", "http://www.w3.org/2000/svg")
    svg.set("width", str(int(canvas_w)))
    svg.set("height", str(int(canvas_h)))
    svg.set("viewBox", f"0 0 {int(canvas_w)} {int(canvas_h)}")

    # Canvas background
    if canvas and canvas.background:
        bg = XmlElement("rect")
        bg.set("width", "100%")
        bg.set("height", "100%")
        bg.set("fill", canvas.background)
        svg.append(bg)

    # Render elements
    for el in doc.elements:
        if el.element_type == "canvas":
            continue
        _render_element(el, svg, boxes)

    # Debug overlays
    if debug:
        from stagscribe.converter.debug_overlay import apply_debug_overlays

        apply_debug_overlays(svg, doc, boxes, canvas_w, canvas_h, debug)

    # Serialize to string
    xml_bytes = tostring(svg, encoding="unicode")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_bytes}'


def _render_element(
    el: Element,
    parent: XmlElement,
    boxes: dict[str, ResolvedBox],
) -> None:
    """Render a single element and its children."""
    key = el.name or _find_key(el, boxes)
    box = boxes.get(key, ResolvedBox(0, 0, 0, 0))

    if el.element_type == "text":
        render_text(el, box, parent)
        return

    svg_el = render_shape(el, box, parent)

    # Recurse into children
    for child in el.children:
        _render_element(child, svg_el, boxes)


def _find_key(el: Element, boxes: dict[str, ResolvedBox]) -> str:
    """Find the box key for an unnamed element."""
    for key in boxes:
        if key.startswith("__element_"):
            return key
    return "__element_0"
