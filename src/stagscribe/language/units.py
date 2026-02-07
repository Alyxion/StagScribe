"""Unit system and conversions for StagScribe."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Unit(StrEnum):
    PIXELS = "pixels"
    PX = "px"
    CM = "cm"
    MM = "mm"
    METERS = "meters"
    M = "m"
    INCHES = "in"
    PT = "pt"
    PERCENT = "%"


class NaturalSize(StrEnum):
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"
    FULL = "full"
    HALF = "half"
    THIRD = "third"
    QUARTER = "quarter"


# Pixels per unit at 96 DPI
_PX_PER_UNIT: dict[str, float] = {
    "pixels": 1.0,
    "px": 1.0,
    "cm": 37.7953,
    "mm": 3.77953,
    "meters": 3779.53,
    "m": 3779.53,
    "in": 96.0,
    "pt": 1.3333,
}

# Natural sizes as fraction of container
_NATURAL_FRACTIONS: dict[str, float] = {
    "tiny": 0.1,
    "small": 0.25,
    "medium": 0.5,
    "large": 0.75,
    "huge": 0.9,
    "full": 1.0,
    "half": 0.5,
    "third": 1.0 / 3.0,
    "quarter": 0.25,
}

UNIT_KEYWORDS: set[str] = {u.value for u in Unit} | {n.value for n in NaturalSize} | {"by"}


@dataclass(frozen=True)
class Value:
    """A numeric value with an optional unit."""

    number: float
    unit: str | None = None

    def to_pixels(self, container_size: float | None = None) -> float:
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


def is_unit_keyword(word: str) -> bool:
    return word in UNIT_KEYWORDS
