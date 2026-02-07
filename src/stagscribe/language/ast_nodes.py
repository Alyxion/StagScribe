"""AST node dataclasses for the StagScribe language."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union  # noqa: UP007 — needed for forward-ref Statement type alias

# --- Expression AST nodes ---


@dataclass
class Expr:
    """Base class for expression nodes."""


@dataclass
class LiteralExpr(Expr):
    """A literal numeric value (resolved to a Value)."""

    value: Value


@dataclass
class VarRefExpr(Expr):
    """A reference to a variable by name."""

    name: str


@dataclass
class BinaryExpr(Expr):
    """Binary arithmetic expression: left op right."""

    op: str  # "+", "-", "*", "/"
    left: Expr
    right: Expr


@dataclass
class UnaryExpr(Expr):
    """Unary negation: -expr."""

    operand: Expr


# --- New statement types ---


@dataclass
class IsStatement:
    """Variable assignment: name is expr."""

    name: str
    expr: Expr
    line: int | None = None
    column: int | None = None


@dataclass
class ColorAssignment:
    """A single color variable: name = color_value."""

    name: str
    color: str
    is_var_ref: bool = False


@dataclass
class ColorsBlock:
    """colors: block with indented color assignments."""

    assignments: list[ColorAssignment] = field(default_factory=list)
    line: int | None = None
    column: int | None = None


@dataclass
class DefineBlock:
    """Template definition: define name: indented body."""

    name: str
    body_elements: list[Element] = field(default_factory=list)
    line: int | None = None
    column: int | None = None


@dataclass
class PlaceStatement:
    """Template instantiation: place template_name "instance" [props]."""

    template_name: str
    instance_name: str | None = None
    props: dict = field(default_factory=dict)  # type: ignore[type-arg]
    position: Position | None = None
    scale: Expr | None = None
    rotate_expr: Expr | None = None
    line: int | None = None
    column: int | None = None


# Type alias for all statement types
Statement = Union[
    "Element", IsStatement, ColorsBlock, DefineBlock, PlaceStatement
]


@dataclass
class GradientFill:
    """Linear gradient fill specification."""

    color1: str
    color2: str
    direction: str = "vertical"  # vertical = top to bottom


@dataclass
class Position:
    """Position specification for an element."""

    # Absolute coordinates
    x: Value | None = None
    y: Value | None = None
    # Anchor-based: "at center", "at top left"
    anchor: str | None = None
    # Relative: "below 'Title' with gap 20"
    relative: str | None = None  # above/below/left of/right of/inside
    reference: str | None = None  # name of referenced element
    ref_anchor: str | None = None  # anchor within referenced element
    gap: Value | None = None
    # Wall-based: "on the north wall"
    wall: str | None = None
    # Gear meshing: "mesh with 'Other Gear'"
    mesh_ref: str | None = None


@dataclass
class StrokeStyle:
    """Stroke properties."""

    color: str | None = None
    width: Value | None = None
    dash: str | None = None  # "dashed" or "dotted"


@dataclass
class TextStyle:
    """Text-specific style properties."""

    font: str | None = None
    size: Value | None = None
    color: str | None = None
    weight: str | None = None  # bold, light, normal
    style: str | None = None  # italic, normal
    align: str | None = None  # left, center, right


@dataclass
class Value:
    """A numeric value with optional unit."""

    number: float
    unit: str | None = None

    def to_pixels(self, container_size: float | None = None) -> float:
        from stagscribe.language.units import _NATURAL_FRACTIONS, _PX_PER_UNIT

        if self.unit is None or self.unit in ("pixels", "px"):
            return self.number
        if self.unit == "%":
            if container_size is None:
                raise ValueError("Cannot resolve percentage without container size")
            return self.number / 100.0 * container_size
        if self.unit in _NATURAL_FRACTIONS:
            if container_size is None:
                raise ValueError(f"Cannot resolve '{self.unit}' without container size")
            return _NATURAL_FRACTIONS[self.unit] * container_size
        if self.unit in _PX_PER_UNIT:
            return self.number * _PX_PER_UNIT[self.unit]
        raise ValueError(f"Unknown unit: {self.unit}")


@dataclass
class Element:
    """Base AST node for any StagScribe element."""

    element_type: str
    name: str | None = None
    position: Position | None = None
    children: list[Element] = field(default_factory=list)

    # Dimensions
    width: Value | None = None
    height: Value | None = None
    radius: Value | None = None  # circle radius

    # Appearance
    fill: str | None = None
    gradient: GradientFill | None = None
    stroke: StrokeStyle | None = None
    opacity: float | None = None
    rounded: Value | None = None
    rotate: float | None = None

    # Gear-specific
    teeth: int | None = None
    tooth_module: float | None = None

    # Text
    text_style: TextStyle | None = None
    text_content: str | None = None

    # Line endpoints
    line_from: tuple[Value, Value] | None = None
    line_to: tuple[Value, Value] | None = None

    # Polygon points
    points: list[tuple[Value, Value]] | None = None

    # Path
    path_data: str | None = None

    # Image
    src: str | None = None

    # Canvas-specific
    background: str | None = None

    # Source location for error reporting
    line: int | None = None
    column: int | None = None


@dataclass
class Document:
    """Root AST node representing an entire .stag file."""

    statements: list[Statement] = field(default_factory=list)

    @property
    def elements(self) -> list[Element]:
        """Backward-compatible: return only Element statements."""
        return [s for s in self.statements if isinstance(s, Element)]

    @property
    def canvas(self) -> Element | None:
        for el in self.elements:
            if el.element_type == "canvas":
                return el
        return None
