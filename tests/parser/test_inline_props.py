"""Tests for inline property parsing."""

from stagscribe.parser.parser import parse


class TestInlineProperties:
    def test_inline_fill(self) -> None:
        source = 'rectangle "Box" 200 by 100 fill red\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.element_type == "rectangle"
        assert el.name == "Box"
        assert el.width is not None
        assert el.width.number == 200
        assert el.height is not None
        assert el.height.number == 100
        assert el.fill == "#FF0000"

    def test_inline_fill_and_position(self) -> None:
        source = 'rect "Box" 200 by 100 fill red at center\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.fill == "#FF0000"
        assert el.position is not None
        assert el.position.anchor == "center"

    def test_inline_with_keyword(self) -> None:
        source = 'rect "Box" 200 by 100 with fill red\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.fill == "#FF0000"

    def test_inline_multiple_props_with_and(self) -> None:
        source = 'rect "Box" fill red and stroke black 2 pixels\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.fill == "#FF0000"
        assert el.stroke is not None
        assert el.stroke.color == "#000000"
        assert el.stroke.width is not None
        assert el.stroke.width.number == 2

    def test_inline_plus_body(self) -> None:
        source = (
            'rect "Box" fill red at center\n'
            "  width 200\n"
            "  height 100\n"
            "  stroke black 2 pixels\n"
        )
        doc = parse(source)
        el = doc.elements[0]
        assert el.fill == "#FF0000"
        assert el.position is not None
        assert el.position.anchor == "center"
        assert el.width is not None
        assert el.width.number == 200
        assert el.stroke is not None

    def test_body_overrides_inline(self) -> None:
        source = (
            'rect "Box" fill red\n'
            "  fill blue\n"
        )
        doc = parse(source)
        el = doc.elements[0]
        # Body should override inline
        assert el.fill == "#0000FF"

    def test_inline_text_style(self) -> None:
        source = 'text "Hello" size 16 bold at center\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.text_style is not None
        assert el.text_style.size is not None
        assert el.text_style.size.number == 16
        assert el.text_style.weight == "bold"
        assert el.position is not None
        assert el.position.anchor == "center"

    def test_inline_opacity(self) -> None:
        source = 'rect "Box" 100 by 100 fill red opacity 0.5\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.fill == "#FF0000"
        assert el.opacity == 0.5

    def test_inline_rounded(self) -> None:
        source = 'rect "Box" 100 by 100 fill red rounded 8\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.rounded is not None
        assert el.rounded.number == 8

    def test_inline_dashed(self) -> None:
        source = 'rect "Box" 100 by 100 stroke black dashed\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.stroke is not None
        assert el.stroke.dash == "dashed"

    def test_inline_radius(self) -> None:
        source = 'circle "Dot" radius 25 fill red at center\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.radius is not None
        assert el.radius.number == 25
        assert el.fill == "#FF0000"


class TestPreFill:
    def test_pre_fill_color_name(self) -> None:
        source = 'red rectangle "Box" 100 by 100\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.element_type == "rectangle"
        assert el.fill == "#FF0000"

    def test_pre_fill_hex(self) -> None:
        source = '#FF0000 rect "Box" 100 by 100\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.fill is not None
        assert el.fill.lower() == "#ff0000"

    def test_pre_fill_friendly_color(self) -> None:
        source = 'light blue rect "Box" 100 by 100\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.fill == "#ADD8E6"

    def test_pre_fill_with_inline_props(self) -> None:
        source = 'red rect "Box" 100 by 100 at center\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.fill == "#FF0000"
        assert el.position is not None
        assert el.position.anchor == "center"


class TestNoiseWords:
    def test_radius_of(self) -> None:
        source = 'circle "Dot"\n  radius of 25\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.radius is not None
        assert el.radius.number == 25

    def test_size_of(self) -> None:
        source = 'text "Hello"\n  size of 16\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.text_style is not None
        assert el.text_style.size is not None
        assert el.text_style.size.number == 16

    def test_opacity_of(self) -> None:
        source = 'rect "Box"\n  opacity of 0.5\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.opacity == 0.5

    def test_rounded_of(self) -> None:
        source = 'rect "Box"\n  rounded of 8\n'
        doc = parse(source)
        el = doc.elements[0]
        assert el.rounded is not None
        assert el.rounded.number == 8
