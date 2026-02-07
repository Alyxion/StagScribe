"""Tests for the resolver: variables, color palettes, templates."""

import pytest

from stagscribe.parser.parser import parse
from stagscribe.resolver import resolve
from stagscribe.resolver.resolver import ResolveError


class TestVariableResolution:
    def test_simple_variable(self) -> None:
        source = "w is 200\ncanvas 800 by 600\nrect \"Box\" w by 100\n"
        doc = resolve(parse(source))
        box = doc.elements[1]
        assert box.name == "Box"
        assert box.width is not None
        assert box.width.number == 200.0

    def test_variable_in_expression(self) -> None:
        source = (
            "w is 500\nmargin is 10\n"
            "canvas 800 by 600\nrect \"Box\" w - margin * 2 by 100\n"
        )
        doc = resolve(parse(source))
        box = doc.elements[1]
        assert box.width is not None
        assert box.width.number == 480.0

    def test_variable_in_gap(self) -> None:
        source = (
            "gap_size is 25\n"
            "canvas 800 by 600\n"
            "rect \"A\" 100 by 50\n"
            "  at center\n"
            "rect \"B\" 100 by 50\n"
            "  below \"A\" with gap gap_size\n"
        )
        doc = resolve(parse(source))
        b = doc.elements[2]
        assert b.position is not None
        assert b.position.gap is not None
        assert b.position.gap.number == 25.0

    def test_undefined_variable_error(self) -> None:
        source = "canvas 800 by 600\nrect \"Box\" unknown_var by 100\n"
        with pytest.raises(ResolveError, match="Undefined variable"):
            resolve(parse(source))

    def test_forward_reference_error(self) -> None:
        source = "canvas w by 600\nw is 800\n"
        with pytest.raises(ResolveError, match="Undefined variable"):
            resolve(parse(source))


class TestColorPalette:
    def test_basic_color_palette(self) -> None:
        source = (
            "colors:\n"
            "  wall is beige\n"
            "  accent is #FF0000\n"
            "canvas 800 by 600\n"
            "rect \"Box\" 100 by 50\n"
            "  fill wall\n"
        )
        doc = resolve(parse(source))
        box = doc.elements[1]
        assert box.fill == "#F5F5DC"  # beige resolved to hex

    def test_hex_color_in_palette(self) -> None:
        source = (
            "colors:\n"
            "  desk is #EDE8D0\n"
            "canvas 800 by 600\n"
            "rect \"Box\" 100 by 50\n"
            "  fill desk\n"
        )
        doc = resolve(parse(source))
        box = doc.elements[1]
        assert box.fill is not None
        assert box.fill.lower() == "#ede8d0"

    def test_friendly_color_in_palette(self) -> None:
        source = (
            "colors:\n"
            "  bg is light gray\n"
            "canvas 800 by 600\n"
            "rect \"Box\" 100 by 50\n"
            "  fill bg\n"
        )
        doc = resolve(parse(source))
        box = doc.elements[1]
        assert box.fill == "#D3D3D3"  # light gray resolved

    def test_undefined_color_var_error(self) -> None:
        source = "canvas 800 by 600\nrect \"Box\" 100 by 50\n  fill not_a_color_var\n"
        with pytest.raises(ResolveError, match="Undefined color variable"):
            resolve(parse(source))


class TestTemplates:
    def test_basic_template(self) -> None:
        source = (
            "define desk:\n"
            "  rect 80 by 50\n"
            "    fill beige\n"
            "canvas 800 by 600\n"
            "place desk \"D1\"\n"
            "  at 100 100\n"
        )
        doc = resolve(parse(source))
        assert len(doc.elements) == 2  # canvas + placed desk
        desk = doc.elements[1]
        assert desk.element_type == "rect"
        assert desk.name == "D1"
        assert desk.width is not None
        assert desk.width.number == 80.0
        assert desk.position is not None
        assert desk.position.x is not None
        assert desk.position.x.number == 100.0

    def test_template_with_variables(self) -> None:
        source = (
            "desk_w is 80\n"
            "desk_h is 50\n"
            "define desk:\n"
            "  rect desk_w by desk_h\n"
            "    fill beige\n"
            "canvas 800 by 600\n"
            "place desk \"D1\"\n"
            "  at 100 100\n"
        )
        doc = resolve(parse(source))
        desk = doc.elements[1]
        assert desk.width is not None
        assert desk.width.number == 80.0
        assert desk.height is not None
        assert desk.height.number == 50.0

    def test_template_relative_position(self) -> None:
        source = (
            "define desk:\n"
            "  rect 80 by 50\n"
            "    fill beige\n"
            "canvas 800 by 600\n"
            "rect \"Ref\" 200 by 20\n"
            "  at center\n"
            "place desk \"D1\"\n"
            "  below \"Ref\" with gap 30\n"
        )
        doc = resolve(parse(source))
        desk = doc.elements[2]
        assert desk.name == "D1"
        assert desk.position is not None
        assert desk.position.relative == "below"
        assert desk.position.reference == "Ref"
        assert desk.position.gap is not None
        assert desk.position.gap.number == 30.0

    def test_template_override_fill(self) -> None:
        source = (
            "define box:\n"
            "  rect 80 by 50\n"
            "    fill beige\n"
            "canvas 800 by 600\n"
            "place box \"B1\"\n"
            "  at 100 100\n"
            "  fill red\n"
        )
        doc = resolve(parse(source))
        box = doc.elements[1]
        assert box.fill == "#FF0000"

    def test_template_with_scale(self) -> None:
        source = (
            "define box:\n"
            "  rect 80 by 50\n"
            "    fill beige\n"
            "canvas 800 by 600\n"
            "place box \"B1\"\n"
            "  at 100 100\n"
            "  scale 2\n"
        )
        doc = resolve(parse(source))
        box = doc.elements[1]
        assert box.width is not None
        assert box.width.number == 160.0
        assert box.height is not None
        assert box.height.number == 100.0

    def test_undefined_template_error(self) -> None:
        source = "canvas 800 by 600\nplace nonexistent \"X\"\n  at 100 100\n"
        with pytest.raises(ResolveError, match="Unknown template"):
            resolve(parse(source))

    def test_multiple_placements_independent(self) -> None:
        source = (
            "define desk:\n"
            "  rect 80 by 50\n"
            "    fill beige\n"
            "canvas 800 by 600\n"
            "place desk \"D1\"\n"
            "  at 100 100\n"
            "place desk \"D2\"\n"
            "  at 200 100\n"
        )
        doc = resolve(parse(source))
        d1 = doc.elements[1]
        d2 = doc.elements[2]
        assert d1.name == "D1"
        assert d2.name == "D2"
        assert d1.position is not None
        assert d1.position.x is not None
        assert d1.position.x.number == 100.0
        assert d2.position is not None
        assert d2.position.x is not None
        assert d2.position.x.number == 200.0


class TestExistingDocumentsUnchanged:
    def test_pure_element_document(self) -> None:
        """Resolve is a no-op for documents with no v2 features."""
        source = (
            "canvas 800 by 600\n"
            "  background white\n"
            "rect \"Box\" 200 by 100\n"
            "  fill red\n"
            "  at center\n"
        )
        doc = resolve(parse(source))
        assert len(doc.elements) == 2
        box = doc.elements[1]
        assert box.name == "Box"
        assert box.fill == "#FF0000"
        assert box.width is not None
        assert box.width.number == 200.0


class TestExpressionParsing:
    def test_arithmetic_parsed_correctly(self) -> None:
        source = "x is 10 + 5 * 2\ncanvas 800 by 600\nrect \"Box\" x by 50\n"
        doc = resolve(parse(source))
        box = doc.elements[1]
        assert box.width is not None
        assert box.width.number == 20.0  # 10 + (5*2) = 20

    def test_parenthesized_expression(self) -> None:
        source = "x is (10 + 5) * 2\ncanvas 800 by 600\nrect \"Box\" x by 50\n"
        doc = resolve(parse(source))
        box = doc.elements[1]
        assert box.width is not None
        assert box.width.number == 30.0

    def test_negation(self) -> None:
        source = (
            "offset is 10\nx is -offset\n"
            "canvas 800 by 600\nrect \"Box\" 100 by 50\n  at x 100\n"
        )
        doc = resolve(parse(source))
        box = doc.elements[1]
        assert box.position is not None
        assert box.position.x is not None
        assert box.position.x.number == -10.0

    def test_division(self) -> None:
        source = "w is 800 / 2\ncanvas 800 by 600\nrect \"Box\" w by 50\n"
        doc = resolve(parse(source))
        box = doc.elements[1]
        assert box.width is not None
        assert box.width.number == 400.0

    def test_complex_expression(self) -> None:
        """room_w - wall * 2"""
        source = (
            "room_w is 500\n"
            "wall is 10\n"
            "inner_w is room_w - wall * 2\n"
            "canvas 800 by 600\n"
            "rect \"Floor\" inner_w by 300\n"
        )
        doc = resolve(parse(source))
        floor = doc.elements[1]
        assert floor.width is not None
        assert floor.width.number == 480.0  # 500 - (10*2)
