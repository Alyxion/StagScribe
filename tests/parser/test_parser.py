"""Tests for the StagScribe parser."""


from stagscribe.language.ast_nodes import Document
from stagscribe.parser.parser import parse


class TestParseBasic:
    def test_empty_canvas(self) -> None:
        doc = parse("canvas 800 by 600 pixels\n")
        assert isinstance(doc, Document)
        assert len(doc.elements) == 1
        assert doc.canvas is not None
        assert doc.canvas.width is not None
        assert doc.canvas.width.number == 800

    def test_canvas_with_background(self) -> None:
        source = "canvas 400 by 300 pixels\n  background white\n"
        doc = parse(source)
        assert doc.canvas is not None
        assert doc.canvas.background == "#FFFFFF"

    def test_rectangle_with_dimensions(self) -> None:
        source = 'rectangle "Box"\n  width 200\n  height 100\n'
        doc = parse(source)
        assert len(doc.elements) == 1
        el = doc.elements[0]
        assert el.element_type == "rectangle"
        assert el.name == "Box"
        assert el.width is not None
        assert el.width.number == 200
        assert el.height is not None
        assert el.height.number == 100

    def test_fill_color(self) -> None:
        source = 'rectangle "Box"\n  fill red\n'
        doc = parse(source)
        assert doc.elements[0].fill == "#FF0000"

    def test_fill_hex_color(self) -> None:
        source = 'rectangle "Box"\n  fill #007AFF\n'
        doc = parse(source)
        assert doc.elements[0].fill is not None
        assert doc.elements[0].fill.lower() == "#007aff"

    def test_fill_friendly_color(self) -> None:
        source = 'rectangle "Box"\n  fill light blue\n'
        doc = parse(source)
        assert doc.elements[0].fill == "#ADD8E6"

    def test_stroke_with_width(self) -> None:
        source = 'rectangle "Box"\n  stroke dark gray 2 pixels\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.stroke is not None
        assert el.stroke.color == "#A9A9A9"
        assert el.stroke.width is not None
        assert el.stroke.width.number == 2

    def test_text_style(self) -> None:
        source = 'text "Title"\n  size 24\n  bold\n  color #333333\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.text_style is not None
        assert el.text_style.size is not None
        assert el.text_style.size.number == 24
        assert el.text_style.weight == "bold"
        assert el.text_style.color == "#333333"


class TestParsePositioning:
    def test_at_center(self) -> None:
        source = 'rectangle "Box"\n  at center\n'
        doc = parse(source)
        pos = doc.elements[0].position
        assert pos is not None
        assert pos.anchor == "center"

    def test_at_top_left(self) -> None:
        source = 'rectangle "Box"\n  at top left\n'
        doc = parse(source)
        pos = doc.elements[0].position
        assert pos is not None
        assert pos.anchor == "top left"

    def test_at_coordinates(self) -> None:
        source = 'rectangle "Box"\n  at 50% 20%\n'
        doc = parse(source)
        pos = doc.elements[0].position
        assert pos is not None
        assert pos.x is not None
        assert pos.x.number == 50
        assert pos.x.unit == "%"

    def test_at_center_of(self) -> None:
        source = 'text "Label"\n  at center of "Box"\n'
        doc = parse(source)
        pos = doc.elements[0].position
        assert pos is not None
        assert pos.anchor == "center"
        assert pos.reference == "Box"

    def test_below_with_gap(self) -> None:
        source = 'rectangle "B"\n  below "A" with gap 20\n'
        doc = parse(source)
        pos = doc.elements[0].position
        assert pos is not None
        assert pos.relative == "below"
        assert pos.reference == "A"
        assert pos.gap is not None
        assert pos.gap.number == 20

    def test_inside_at_anchor(self) -> None:
        source = 'text "Label"\n  inside "Box" at top right\n'
        doc = parse(source)
        pos = doc.elements[0].position
        assert pos is not None
        assert pos.relative == "inside"
        assert pos.reference == "Box"
        assert pos.ref_anchor == "top right"


class TestParseNesting:
    def test_group_with_children(self) -> None:
        source = (
            'group "Panel"\n'
            '  rectangle "Background"\n'
            '    width 200\n'
            '    height 100\n'
            '  text "Title"\n'
            '    size 16\n'
        )
        doc = parse(source)
        assert len(doc.elements) == 1
        group = doc.elements[0]
        assert group.element_type == "group"
        assert len(group.children) == 2
        assert group.children[0].element_type == "rectangle"
        assert group.children[1].element_type == "text"

    def test_comments_ignored(self) -> None:
        source = "-- This is a comment\ncanvas 800 by 600\n-- Another comment\n"
        doc = parse(source)
        assert len(doc.elements) == 1


class TestParseUnits:
    def test_meters(self) -> None:
        source = 'rectangle "Room"\n  width 6 meters\n  height 4 meters\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.width is not None
        assert el.width.unit == "meters"

    def test_size_by(self) -> None:
        source = "canvas 800 by 600 pixels\n"
        doc = parse(source)
        assert doc.canvas is not None
        assert doc.canvas.width is not None
        assert doc.canvas.width.number == 800
        assert doc.canvas.width.unit is None  # "800" has no explicit unit
        assert doc.canvas.height is not None
        assert doc.canvas.height.number == 600
        assert doc.canvas.height.unit == "pixels"

    def test_size_by_no_unit(self) -> None:
        source = "canvas 800 by 600\n"
        doc = parse(source)
        assert doc.canvas is not None
        assert doc.canvas.width is not None
        assert doc.canvas.width.number == 800
        assert doc.canvas.width.unit is None


class TestParseFullExamples:
    def test_floor_plan(self) -> None:
        source = """-- Simple Studio Apartment
canvas 800 by 600 pixels
  background white

rectangle "Main Room"
  width 6 meters
  height 4 meters
  at center
  fill white
  stroke dark gray 2 pixels

rectangle "Bathroom"
  width 2 meters
  height 2 meters
  inside "Main Room" at top right
  fill light blue
  stroke dark gray

text "Living Area"
  at center of "Main Room"
  size 16
  color dark gray
  bold
"""
        doc = parse(source)
        assert len(doc.elements) == 4
        assert doc.canvas is not None
        assert doc.elements[1].name == "Main Room"
        assert doc.elements[2].name == "Bathroom"
        assert doc.elements[3].name == "Living Area"
