"""Tests for the unit system."""

import pytest

from stagscribe.language.ast_nodes import Value


class TestValue:
    def test_bare_number_is_pixels(self) -> None:
        v = Value(number=100)
        assert v.to_pixels() == 100.0

    def test_px_unit(self) -> None:
        v = Value(number=50, unit="px")
        assert v.to_pixels() == 50.0

    def test_pixels_unit(self) -> None:
        v = Value(number=50, unit="pixels")
        assert v.to_pixels() == 50.0

    def test_cm_conversion(self) -> None:
        v = Value(number=1, unit="cm")
        assert abs(v.to_pixels() - 37.7953) < 0.01

    def test_inches_conversion(self) -> None:
        v = Value(number=1, unit="in")
        assert v.to_pixels() == 96.0

    def test_meters_conversion(self) -> None:
        v = Value(number=1, unit="meters")
        assert abs(v.to_pixels() - 3779.53) < 0.01

    def test_percentage(self) -> None:
        v = Value(number=50, unit="%")
        assert v.to_pixels(container_size=800) == 400.0

    def test_percentage_requires_container(self) -> None:
        v = Value(number=50, unit="%")
        with pytest.raises(ValueError, match="percentage"):
            v.to_pixels()

    def test_natural_size_half(self) -> None:
        v = Value(number=1.0, unit="half")
        assert v.to_pixels(container_size=600) == 300.0

    def test_natural_size_third(self) -> None:
        v = Value(number=1.0, unit="third")
        assert abs(v.to_pixels(container_size=900) - 300.0) < 0.01

    def test_unknown_unit_raises(self) -> None:
        v = Value(number=10, unit="lightyears")
        with pytest.raises(ValueError, match="Unknown unit"):
            v.to_pixels()
