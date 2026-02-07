"""Layout engine — resolve relative positions to absolute pixel coordinates."""

from __future__ import annotations

from dataclasses import dataclass

from stagscribe.language.ast_nodes import Document, Element, Position


@dataclass
class ResolvedBox:
    """Resolved absolute bounding box for an element."""

    x: float
    y: float
    width: float
    height: float


DEFAULT_CANVAS_W = 800.0
DEFAULT_CANVAS_H = 600.0

# Anchor positions as fractions of container
_ANCHOR_FRACTIONS: dict[str, tuple[float, float]] = {
    "center": (0.5, 0.5),
    "top": (0.5, 0.0),
    "bottom": (0.5, 1.0),
    "left": (0.0, 0.5),
    "right": (1.0, 0.5),
    "top left": (0.0, 0.0),
    "top right": (1.0, 0.0),
    "bottom left": (0.0, 1.0),
    "bottom right": (1.0, 1.0),
    "center left": (0.0, 0.5),
    "center right": (1.0, 0.5),
    "center top": (0.5, 0.0),
    "center bottom": (0.5, 1.0),
}


def resolve_layout(doc: Document) -> dict[str, ResolvedBox]:
    """Resolve all element positions to absolute pixel coordinates.

    Returns a dict mapping element name → ResolvedBox.
    Unnamed elements use a generated key like "__element_0".
    """
    canvas = doc.canvas
    canvas_w = canvas.width.to_pixels() if canvas and canvas.width else DEFAULT_CANVAS_W
    canvas_h = canvas.height.to_pixels() if canvas and canvas.height else DEFAULT_CANVAS_H

    boxes: dict[str, ResolvedBox] = {}
    counter = 0

    # Canvas itself
    if canvas:
        key = canvas.name or "__canvas"
        boxes[key] = ResolvedBox(0, 0, canvas_w, canvas_h)

    for el in doc.elements:
        if el.element_type == "canvas":
            continue
        counter = _resolve_element(el, boxes, canvas_w, canvas_h, 0, 0, counter)

    return boxes


def _resolve_element(
    el: Element,
    boxes: dict[str, ResolvedBox],
    container_w: float,
    container_h: float,
    container_x: float,
    container_y: float,
    counter: int,
) -> int:
    """Resolve a single element's position and recurse into children."""
    key = el.name or f"__element_{counter}"
    counter += 1

    # Resolve dimensions
    w = el.width.to_pixels(container_w) if el.width else 0.0
    h = el.height.to_pixels(container_h) if el.height else 0.0

    # For circles, use radius for both width and height
    if el.element_type == "circle" and el.radius:
        r = el.radius.to_pixels(min(container_w, container_h))
        w = r * 2
        h = r * 2

    # Resolve position
    x, y = _resolve_position(
        el.position, w, h, container_w, container_h, container_x, container_y, boxes,
    )

    box = ResolvedBox(x, y, w, h)
    boxes[key] = box

    # Recurse into children with this element as container
    for child in el.children:
        counter = _resolve_element(child, boxes, w, h, x, y, counter)

    return counter


def _resolve_position(
    pos: Position | None,
    el_w: float,
    el_h: float,
    container_w: float,
    container_h: float,
    container_x: float,
    container_y: float,
    boxes: dict[str, ResolvedBox],
) -> tuple[float, float]:
    """Resolve a Position to absolute (x, y) coordinates."""
    if pos is None:
        return container_x, container_y

    # Absolute coordinates
    if pos.x is not None and pos.y is not None:
        x = pos.x.to_pixels(container_w)
        y = pos.y.to_pixels(container_h)
        # Center the element on the given coordinate
        return x - el_w / 2, y - el_h / 2

    # Relative positioning (inside, below, above, etc.)
    if pos.relative and pos.reference:
        ref_box = boxes.get(pos.reference)
        if ref_box:
            return _resolve_relative(pos, el_w, el_h, ref_box)

    # Anchor positioning within container
    if pos.anchor:
        # If there's a reference, position within that element
        if pos.reference:
            ref_box = boxes.get(pos.reference)
            if ref_box:
                return _resolve_anchor_in(pos.anchor, el_w, el_h, ref_box)

        # Otherwise position within container
        fx, fy = _ANCHOR_FRACTIONS.get(pos.anchor, (0.5, 0.5))
        x = container_x + fx * (container_w - el_w)
        y = container_y + fy * (container_h - el_h)
        return x, y

    return container_x, container_y


def _resolve_anchor_in(
    anchor: str,
    el_w: float,
    el_h: float,
    ref_box: ResolvedBox,
) -> tuple[float, float]:
    """Position element inside a reference box at the given anchor."""
    fx, fy = _ANCHOR_FRACTIONS.get(anchor, (0.5, 0.5))
    x = ref_box.x + fx * (ref_box.width - el_w)
    y = ref_box.y + fy * (ref_box.height - el_h)
    return x, y


def _resolve_relative(
    pos: Position,
    el_w: float,
    el_h: float,
    ref_box: ResolvedBox,
) -> tuple[float, float]:
    """Resolve relative positioning (below, above, inside, etc.)."""
    gap = pos.gap.to_pixels() if pos.gap else 0.0

    if pos.relative == "below":
        x = ref_box.x + ref_box.width / 2 - el_w / 2
        y = ref_box.y + ref_box.height + gap
        return x, y

    if pos.relative == "above":
        x = ref_box.x + ref_box.width / 2 - el_w / 2
        y = ref_box.y - el_h - gap
        return x, y

    if pos.relative == "right of":
        x = ref_box.x + ref_box.width + gap
        y = ref_box.y + ref_box.height / 2 - el_h / 2
        return x, y

    if pos.relative == "left of":
        x = ref_box.x - el_w - gap
        y = ref_box.y + ref_box.height / 2 - el_h / 2
        return x, y

    if pos.relative == "inside":
        # Inside with optional anchor
        if pos.ref_anchor:
            return _resolve_anchor_in(pos.ref_anchor, el_w, el_h, ref_box)
        # Default: center inside
        x = ref_box.x + ref_box.width / 2 - el_w / 2
        y = ref_box.y + ref_box.height / 2 - el_h / 2
        return x, y

    return ref_box.x, ref_box.y
