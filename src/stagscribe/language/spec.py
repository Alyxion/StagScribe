"""StagScribe language specification — keywords, element types, enums."""

from enum import StrEnum


class ElementType(StrEnum):
    CANVAS = "canvas"
    RECTANGLE = "rectangle"
    RECT = "rect"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    LINE = "line"
    PATH = "path"
    POLYGON = "polygon"
    TEXT = "text"
    GROUP = "group"
    IMAGE = "image"
    ARC = "arc"


class Anchor(StrEnum):
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    TOP_LEFT = "top left"
    TOP_RIGHT = "top right"
    BOTTOM_LEFT = "bottom left"
    BOTTOM_RIGHT = "bottom right"


class RelativePosition(StrEnum):
    ABOVE = "above"
    BELOW = "below"
    LEFT_OF = "left of"
    RIGHT_OF = "right of"
    INSIDE = "inside"


class WallPosition(StrEnum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


class FontWeight(StrEnum):
    NORMAL = "normal"
    BOLD = "bold"
    LIGHT = "light"


class FontStyle(StrEnum):
    NORMAL = "normal"
    ITALIC = "italic"


ELEMENT_KEYWORDS: set[str] = {e.value for e in ElementType}

ELEMENT_ALIASES: dict[str, ElementType] = {
    "rect": ElementType.RECTANGLE,
}

PROPERTY_KEYWORDS: set[str] = {
    "width",
    "height",
    "fill",
    "stroke",
    "background",
    "size",
    "color",
    "opacity",
    "rounded",
    "rotate",
    "at",
    "above",
    "below",
    "inside",
    "bold",
    "italic",
    "light",
    "font",
    "dashed",
    "dotted",
    "points",
    "radius",
    "from",
    "to",
    "d",
    "src",
    "href",
    "is",
    "by",
}
