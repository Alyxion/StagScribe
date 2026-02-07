"""Tests for the SVG converter."""

from stagscribe.converter.converter import convert
from stagscribe.converter.layout import resolve_layout
from stagscribe.parser.parser import parse


class TestLayout:
    def test_canvas_box(self) -> None:
        doc = parse("canvas 800 by 600 pixels\n  background white\n")
        boxes = resolve_layout(doc)
        assert "__canvas" in boxes
        box = boxes["__canvas"]
        assert box.width == 800
        assert box.height == 600

    def test_centered_element(self) -> None:
        source = (
            "canvas 800 by 600 pixels\n"
            "  background white\n"
            "\n"
            'rectangle "Box"\n'
            "  width 200\n"
            "  height 100\n"
            "  at center\n"
        )
        doc = parse(source)
        boxes = resolve_layout(doc)
        box = boxes["Box"]
        assert box.x == 300.0  # (800 - 200) / 2
        assert box.y == 250.0  # (600 - 100) / 2
        assert box.width == 200.0
        assert box.height == 100.0

    def test_below_positioning(self) -> None:
        source = (
            "canvas 800 by 600 pixels\n"
            "  background white\n"
            "\n"
            'rectangle "A"\n'
            "  width 200\n"
            "  height 100\n"
            "  at center\n"
            "\n"
            'rectangle "B"\n'
            "  width 200\n"
            "  height 50\n"
            '  below "A" with gap 20\n'
        )
        doc = parse(source)
        boxes = resolve_layout(doc)
        box_a = boxes["A"]
        box_b = boxes["B"]
        assert box_b.y == box_a.y + box_a.height + 20

    def test_percentage_positioning(self) -> None:
        source = (
            "canvas 800 by 600 pixels\n"
            "  background white\n"
            "\n"
            'circle "Dot"\n'
            "  radius 10\n"
            "  at 50% 50%\n"
        )
        doc = parse(source)
        boxes = resolve_layout(doc)
        box = boxes["Dot"]
        # 50% of 800 = 400, minus half width (10) = 390
        assert box.x == 390.0
        assert box.y == 290.0  # 50% of 600 = 300, minus 10


class TestConvert:
    def test_basic_conversion(self) -> None:
        source = (
            "canvas 400 by 300 pixels\n"
            "  background white\n"
            "\n"
            'rectangle "Box"\n'
            "  width 200\n"
            "  height 100\n"
            "  at center\n"
            "  fill red\n"
        )
        svg, diags = convert(source)
        assert '<?xml' in svg
        assert 'xmlns' in svg
        assert '<rect' in svg
        assert 'fill="#FF0000"' in svg

    def test_svg_has_viewbox(self) -> None:
        source = "canvas 800 by 600 pixels\n  background white\n"
        svg, _ = convert(source)
        assert 'viewBox="0 0 800 600"' in svg

    def test_svg_has_background(self) -> None:
        source = "canvas 400 by 300 pixels\n  background #F5F5F5\n"
        svg, _ = convert(source)
        assert 'fill="#f5f5f5"' in svg or 'fill="#F5F5F5"' in svg

    def test_text_rendering(self) -> None:
        source = (
            "canvas 400 by 300 pixels\n"
            "  background white\n"
            "\n"
            'text "Hello"\n'
            "  at center\n"
            "  size 24\n"
            "  bold\n"
            "  color black\n"
        )
        svg, _ = convert(source)
        assert '<text' in svg
        assert 'Hello' in svg
        assert 'font-size="24' in svg  # may be "24" or "24.0"
        assert 'font-weight="bold"' in svg
