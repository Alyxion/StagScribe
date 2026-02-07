"""Debug overlay system for AI-assisted visual debugging of .stag scenes."""

from __future__ import annotations

from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import SubElement

from stagscribe.converter.layout import ResolvedBox
from stagscribe.language.ast_nodes import Document, Element

# Kelly's 22 maximally-distinct colors (hex), good perceptual contrast
KELLY_COLORS: list[str] = [
    "#F2F3F4",  # white
    "#222222",  # black
    "#F3C300",  # yellow
    "#875692",  # purple
    "#F38400",  # orange
    "#A1CAF1",  # light blue
    "#BE0032",  # red
    "#C2B280",  # buff
    "#848482",  # gray
    "#008856",  # green
    "#E68FAC",  # purplish pink
    "#0067A5",  # blue
    "#F99379",  # yellowish pink
    "#604E97",  # violet
    "#F6A600",  # orange yellow
    "#B3446C",  # purplish red
    "#DCD300",  # greenish yellow
    "#882D17",  # reddish brown
    "#8DB600",  # yellow green
    "#654522",  # yellowish brown
    "#E25822",  # reddish orange
    "#2B3D26",  # olive green
]

ALL_MODES = {"labels", "colors", "grid", "boxes", "markers"}


def apply_debug_overlays(
    svg: XmlElement,
    doc: Document,
    boxes: dict[str, ResolvedBox],
    canvas_w: float,
    canvas_h: float,
    modes: set[str],
) -> None:
    """Append debug overlay elements on top of the rendered SVG scene.

    Modes: labels, colors, grid, boxes, markers, or 'all' for everything.
    Modifies `svg` in place.
    """
    if "all" in modes:
        modes = ALL_MODES.copy()

    flat = _flatten_elements(doc)

    if "grid" in modes:
        _add_grid(svg, canvas_w, canvas_h)

    if "colors" in modes:
        _add_color_overlays(svg, flat, boxes)

    if "boxes" in modes:
        _add_box_outlines(svg, flat, boxes)

    if "markers" in modes:
        _add_origin_markers(svg, flat, boxes)

    if "labels" in modes:
        _add_labels(svg, flat, boxes)


def _flatten_elements(
    doc: Document,
) -> list[tuple[str, str, int]]:
    """Flatten document elements into (name, element_type, index) tuples.

    Skips canvas elements. Uses element name or generated key.
    """
    result: list[tuple[str, str, int]] = []
    counter = 0

    for el in doc.elements:
        if el.element_type == "canvas":
            continue
        counter = _flatten_recurse(el, result, counter)

    return result


def _flatten_recurse(
    el: Element,
    result: list[tuple[str, str, int]],
    counter: int,
) -> int:
    name = el.name or f"__element_{counter}"
    result.append((name, el.element_type, len(result)))
    counter += 1

    for child in el.children:
        counter = _flatten_recurse(child, result, counter)

    return counter


def _add_grid(svg: XmlElement, canvas_w: float, canvas_h: float) -> None:
    """Add a 50px grid with coordinate labels."""
    g = SubElement(svg, "g", attrib={"class": "debug-grid", "opacity": "0.4"})
    step = 50

    # Vertical lines
    x = 0
    while x <= canvas_w:
        SubElement(
            g, "line",
            attrib={
                "x1": str(x), "y1": "0",
                "x2": str(x), "y2": str(int(canvas_h)),
                "stroke": "#999999", "stroke-width": "0.5",
            },
        )
        # Label at top
        label = SubElement(
            g, "text",
            attrib={
                "x": str(x + 2), "y": "10",
                "font-size": "8", "font-family": "monospace",
                "fill": "#666666",
            },
        )
        label.text = str(x)
        x += step

    # Horizontal lines
    y = 0
    while y <= canvas_h:
        SubElement(
            g, "line",
            attrib={
                "x1": "0", "y1": str(y),
                "x2": str(int(canvas_w)), "y2": str(y),
                "stroke": "#999999", "stroke-width": "0.5",
            },
        )
        # Label at left
        label = SubElement(
            g, "text",
            attrib={
                "x": "2", "y": str(y - 2),
                "font-size": "8", "font-family": "monospace",
                "fill": "#666666",
            },
        )
        label.text = str(y)
        y += step


def _add_color_overlays(
    svg: XmlElement,
    flat: list[tuple[str, str, int]],
    boxes: dict[str, ResolvedBox],
) -> None:
    """Add semi-transparent colored rectangles per element."""
    g = SubElement(svg, "g", attrib={"class": "debug-colors"})

    for name, _etype, idx in flat:
        box = boxes.get(name)
        if not box or (box.width == 0 and box.height == 0):
            continue
        color = KELLY_COLORS[idx % len(KELLY_COLORS)]
        SubElement(
            g, "rect",
            attrib={
                "x": str(box.x), "y": str(box.y),
                "width": str(box.width), "height": str(box.height),
                "fill": color, "opacity": "0.25",
            },
        )


def _add_box_outlines(
    svg: XmlElement,
    flat: list[tuple[str, str, int]],
    boxes: dict[str, ResolvedBox],
) -> None:
    """Add dashed outline rectangles per element."""
    g = SubElement(svg, "g", attrib={"class": "debug-boxes"})

    for name, _etype, idx in flat:
        box = boxes.get(name)
        if not box or (box.width == 0 and box.height == 0):
            continue
        color = KELLY_COLORS[idx % len(KELLY_COLORS)]
        SubElement(
            g, "rect",
            attrib={
                "x": str(box.x), "y": str(box.y),
                "width": str(box.width), "height": str(box.height),
                "fill": "none",
                "stroke": color, "stroke-width": "1.5",
                "stroke-dasharray": "6,3",
            },
        )


def _add_origin_markers(
    svg: XmlElement,
    flat: list[tuple[str, str, int]],
    boxes: dict[str, ResolvedBox],
) -> None:
    """Add small crosshair at each element's origin (top-left)."""
    g = SubElement(svg, "g", attrib={"class": "debug-markers"})
    arm = 6  # crosshair arm length

    for name, _etype, _idx in flat:
        box = boxes.get(name)
        if not box:
            continue
        cx, cy = box.x, box.y
        SubElement(
            g, "line",
            attrib={
                "x1": str(cx - arm), "y1": str(cy),
                "x2": str(cx + arm), "y2": str(cy),
                "stroke": "#FF0000", "stroke-width": "1.5",
            },
        )
        SubElement(
            g, "line",
            attrib={
                "x1": str(cx), "y1": str(cy - arm),
                "x2": str(cx), "y2": str(cy + arm),
                "stroke": "#FF0000", "stroke-width": "1.5",
            },
        )


def _add_labels(
    svg: XmlElement,
    flat: list[tuple[str, str, int]],
    boxes: dict[str, ResolvedBox],
) -> None:
    """Add element name as white-on-black text centered on each bounding box."""
    g = SubElement(svg, "g", attrib={"class": "debug-labels"})

    for name, etype, _idx in flat:
        box = boxes.get(name)
        if not box:
            continue

        display = name if not name.startswith("__element_") else f"[{etype}]"
        font_size = 10
        # Estimate text width (~6px per char at size 10)
        text_w = len(display) * 6 + 6
        text_h = font_size + 4

        cx = box.x + box.width / 2
        cy = box.y + box.height / 2

        # Background rectangle
        SubElement(
            g, "rect",
            attrib={
                "x": str(cx - text_w / 2),
                "y": str(cy - text_h / 2),
                "width": str(text_w),
                "height": str(text_h),
                "fill": "black", "opacity": "0.75",
                "rx": "2",
            },
        )

        # Text
        label = SubElement(
            g, "text",
            attrib={
                "x": str(cx), "y": str(cy + font_size / 2 - 1),
                "text-anchor": "middle",
                "font-size": str(font_size),
                "font-family": "monospace",
                "fill": "white",
            },
        )
        label.text = display
