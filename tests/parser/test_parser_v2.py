"""Tests for parsing v2/v3 syntax: is, colors, define, place, expressions."""

from stagscribe.language.ast_nodes import (
    BinaryExpr,
    ColorsBlock,
    DefineBlock,
    IsStatement,
    PlaceStatement,
    Value,
    VarRefExpr,
)
from stagscribe.parser.parser import parse


class TestIsStatement:
    def test_simple_is(self) -> None:
        doc = parse("w is 200\ncanvas 800 by 600\n")
        assert len(doc.statements) == 2
        stmt = doc.statements[0]
        assert isinstance(stmt, IsStatement)
        assert stmt.name == "w"
        assert isinstance(stmt.expr, Value)
        assert stmt.expr.number == 200.0

    def test_is_with_expression(self) -> None:
        doc = parse("x is 10 + 5\ncanvas 800 by 600\n")
        stmt = doc.statements[0]
        assert isinstance(stmt, IsStatement)
        assert isinstance(stmt.expr, BinaryExpr)
        assert stmt.expr.op == "+"

    def test_is_with_var_ref(self) -> None:
        doc = parse("a is 10\nb is a\ncanvas 800 by 600\n")
        stmt = doc.statements[1]
        assert isinstance(stmt, IsStatement)
        assert isinstance(stmt.expr, VarRefExpr)
        assert stmt.expr.name == "a"


class TestColorsBlock:
    def test_basic_colors(self) -> None:
        source = "colors:\n  wall is beige\n  floor is #EDE8D0\ncanvas 800 by 600\n"
        doc = parse(source)
        assert isinstance(doc.statements[0], ColorsBlock)
        block = doc.statements[0]
        assert len(block.assignments) == 2
        assert block.assignments[0].name == "wall"
        assert block.assignments[1].name == "floor"
        assert block.assignments[1].color == "#EDE8D0"

    def test_friendly_color_in_palette(self) -> None:
        source = "colors:\n  bg is light gray\ncanvas 800 by 600\n"
        doc = parse(source)
        block = doc.statements[0]
        assert isinstance(block, ColorsBlock)
        assert len(block.assignments) == 1


class TestDefineBlock:
    def test_simple_define(self) -> None:
        source = "define desk:\n  rect 80 by 50\n    fill beige\ncanvas 800 by 600\n"
        doc = parse(source)
        define = doc.statements[0]
        assert isinstance(define, DefineBlock)
        assert define.name == "desk"
        assert len(define.body_elements) == 1
        assert define.body_elements[0].element_type == "rect"

    def test_multi_element_define(self) -> None:
        source = (
            "define widget:\n"
            "  rect 100 by 50\n"
            "    fill white\n"
            "  text \"Label\"\n"
            "canvas 800 by 600\n"
        )
        doc = parse(source)
        define = doc.statements[0]
        assert isinstance(define, DefineBlock)
        assert len(define.body_elements) == 2


class TestPlaceStatement:
    def test_simple_place(self) -> None:
        source = (
            "define desk:\n"
            "  rect 80 by 50\n"
            "canvas 800 by 600\n"
            "place desk \"D1\"\n"
            "  at 100 200\n"
        )
        doc = parse(source)
        place = doc.statements[2]
        assert isinstance(place, PlaceStatement)
        assert place.template_name == "desk"
        assert place.instance_name == "D1"
        assert place.position is not None
        assert place.position.x is not None

    def test_place_with_relative_pos(self) -> None:
        source = (
            "define desk:\n"
            "  rect 80 by 50\n"
            "canvas 800 by 600\n"
            "place desk \"D1\"\n"
            "  below \"Other\" with gap 20\n"
        )
        doc = parse(source)
        place = doc.statements[2]
        assert isinstance(place, PlaceStatement)
        assert place.position is not None
        assert place.position.relative == "below"
        assert place.position.reference == "Other"

    def test_place_with_scale(self) -> None:
        source = (
            "define desk:\n"
            "  rect 80 by 50\n"
            "canvas 800 by 600\n"
            "place desk \"D1\"\n"
            "  at 100 100\n"
            "  scale 2\n"
        )
        doc = parse(source)
        place = doc.statements[2]
        assert isinstance(place, PlaceStatement)
        assert place.scale is not None

    def test_place_with_fill_override(self) -> None:
        source = (
            "define box:\n"
            "  rect 80 by 50\n"
            "    fill blue\n"
            "canvas 800 by 600\n"
            "place box \"B1\"\n"
            "  at 100 100\n"
            "  fill red\n"
        )
        doc = parse(source)
        place = doc.statements[2]
        assert isinstance(place, PlaceStatement)
        assert "fill" in place.props


class TestExpressionParsing:
    def test_var_ref_in_dimension(self) -> None:
        source = "w is 200\ncanvas 800 by 600\nrect \"Box\" w by 100\n"
        doc = parse(source)
        box = doc.elements[1]
        assert isinstance(box.width, VarRefExpr)
        assert box.width.name == "w"

    def test_binary_expression_in_dimension(self) -> None:
        source = "w is 200\ncanvas 800 by 600\nrect \"Box\" w - 20 by 100\n"
        doc = parse(source)
        box = doc.elements[1]
        assert isinstance(box.width, BinaryExpr)
        assert box.width.op == "-"

    def test_expression_with_unit(self) -> None:
        source = "canvas 800 by 600\nrect \"Box\" 200 pixels by 100\n"
        doc = parse(source)
        box = doc.elements[1]
        assert isinstance(box.width, Value)
        assert box.width.number == 200.0
        assert box.width.unit == "pixels"

    def test_percent_value(self) -> None:
        source = "canvas 800 by 600\nrect \"Box\" 50% by 50%\n"
        doc = parse(source)
        box = doc.elements[1]
        assert isinstance(box.width, Value)
        assert box.width.number == 50.0
        assert box.width.unit == "%"
