"""Tests for the debug overlay system."""

from xml.etree.ElementTree import Element as XmlElement

from stagscribe.converter.converter import convert
from stagscribe.converter.debug_overlay import (
    _flatten_elements,
    apply_debug_overlays,
)
from stagscribe.converter.layout import ResolvedBox, resolve_layout
from stagscribe.parser.parser import parse
from stagscribe.resolver import resolve

BASIC_SOURCE = (
    "canvas 400 by 300 pixels\n"
    "  background white\n"
    "\n"
    'rectangle "Box"\n'
    "  width 200\n"
    "  height 100\n"
    "  at center\n"
    "  fill red\n"
)

TWO_ELEMENTS_SOURCE = (
    "canvas 400 by 300 pixels\n"
    "  background white\n"
    "\n"
    'rectangle "A"\n'
    "  width 100\n"
    "  height 50\n"
    "  at 25% 25%\n"
    "  fill blue\n"
    "\n"
    'rectangle "B"\n'
    "  width 100\n"
    "  height 50\n"
    "  at 75% 75%\n"
    "  fill green\n"
)

EMPTY_SOURCE = "canvas 400 by 300 pixels\n  background white\n"


def _make_svg_and_doc(
    source: str,
) -> tuple[XmlElement, object, dict[str, ResolvedBox], float, float]:
    """Parse source and build SVG + doc + boxes for overlay testing."""
    doc = parse(source)
    doc = resolve(doc)
    boxes = resolve_layout(doc)
    canvas = doc.canvas
    canvas_w = canvas.width.to_pixels() if canvas and canvas.width else 400.0
    canvas_h = canvas.height.to_pixels() if canvas and canvas.height else 300.0

    svg = XmlElement("svg")
    svg.set("xmlns", "http://www.w3.org/2000/svg")
    svg.set("width", str(int(canvas_w)))
    svg.set("height", str(int(canvas_h)))

    return svg, doc, boxes, canvas_w, canvas_h


class TestFlattenElements:
    def test_flatten_basic(self) -> None:
        doc = parse(BASIC_SOURCE)
        doc = resolve(doc)
        flat = _flatten_elements(doc)
        assert len(flat) == 1
        assert flat[0][0] == "Box"
        assert flat[0][1] == "rectangle"

    def test_flatten_two_elements(self) -> None:
        doc = parse(TWO_ELEMENTS_SOURCE)
        doc = resolve(doc)
        flat = _flatten_elements(doc)
        assert len(flat) == 2
        names = [name for name, _, _ in flat]
        assert "A" in names
        assert "B" in names

    def test_flatten_empty(self) -> None:
        doc = parse(EMPTY_SOURCE)
        doc = resolve(doc)
        flat = _flatten_elements(doc)
        assert flat == []


class TestGridOverlay:
    def test_grid_adds_lines(self) -> None:
        svg, doc, boxes, cw, ch = _make_svg_and_doc(BASIC_SOURCE)
        apply_debug_overlays(svg, doc, boxes, cw, ch, {"grid"})

        groups = list(svg)
        assert len(groups) == 1
        g = groups[0]
        assert g.get("class") == "debug-grid"

        lines = [el for el in g if el.tag == "line"]
        texts = [el for el in g if el.tag == "text"]
        assert len(lines) > 0
        assert len(texts) > 0

    def test_grid_covers_canvas(self) -> None:
        svg, doc, boxes, cw, ch = _make_svg_and_doc(BASIC_SOURCE)
        apply_debug_overlays(svg, doc, boxes, cw, ch, {"grid"})

        g = list(svg)[0]
        lines = [el for el in g if el.tag == "line"]
        # Should have vertical + horizontal lines every 50px
        # 400/50 + 1 = 9 vertical, 300/50 + 1 = 7 horizontal = 16
        assert len(lines) == 16


class TestColorsOverlay:
    def test_colors_adds_rects(self) -> None:
        svg, doc, boxes, cw, ch = _make_svg_and_doc(TWO_ELEMENTS_SOURCE)
        apply_debug_overlays(svg, doc, boxes, cw, ch, {"colors"})

        g = list(svg)[0]
        assert g.get("class") == "debug-colors"
        rects = [el for el in g if el.tag == "rect"]
        assert len(rects) == 2

    def test_colors_are_semitransparent(self) -> None:
        svg, doc, boxes, cw, ch = _make_svg_and_doc(BASIC_SOURCE)
        apply_debug_overlays(svg, doc, boxes, cw, ch, {"colors"})

        g = list(svg)[0]
        rect = list(g)[0]
        assert rect.get("opacity") == "0.25"


class TestBoxesOverlay:
    def test_boxes_adds_dashed_rects(self) -> None:
        svg, doc, boxes, cw, ch = _make_svg_and_doc(TWO_ELEMENTS_SOURCE)
        apply_debug_overlays(svg, doc, boxes, cw, ch, {"boxes"})

        g = list(svg)[0]
        assert g.get("class") == "debug-boxes"
        rects = [el for el in g if el.tag == "rect"]
        assert len(rects) == 2
        for r in rects:
            assert r.get("fill") == "none"
            assert r.get("stroke-dasharray") == "6,3"


class TestMarkersOverlay:
    def test_markers_adds_crosshairs(self) -> None:
        svg, doc, boxes, cw, ch = _make_svg_and_doc(BASIC_SOURCE)
        apply_debug_overlays(svg, doc, boxes, cw, ch, {"markers"})

        g = list(svg)[0]
        assert g.get("class") == "debug-markers"
        lines = [el for el in g if el.tag == "line"]
        # One element → one crosshair → two lines
        assert len(lines) == 2


class TestLabelsOverlay:
    def test_labels_adds_text(self) -> None:
        svg, doc, boxes, cw, ch = _make_svg_and_doc(BASIC_SOURCE)
        apply_debug_overlays(svg, doc, boxes, cw, ch, {"labels"})

        g = list(svg)[0]
        assert g.get("class") == "debug-labels"
        texts = [el for el in g if el.tag == "text"]
        assert len(texts) == 1
        assert texts[0].text == "Box"

    def test_labels_have_background_rects(self) -> None:
        svg, doc, boxes, cw, ch = _make_svg_and_doc(BASIC_SOURCE)
        apply_debug_overlays(svg, doc, boxes, cw, ch, {"labels"})

        g = list(svg)[0]
        rects = [el for el in g if el.tag == "rect"]
        assert len(rects) == 1
        assert rects[0].get("fill") == "black"


class TestAllMode:
    def test_all_enables_everything(self) -> None:
        svg, doc, boxes, cw, ch = _make_svg_and_doc(BASIC_SOURCE)
        apply_debug_overlays(svg, doc, boxes, cw, ch, {"all"})

        group_classes = {g.get("class") for g in svg}
        assert "debug-grid" in group_classes
        assert "debug-colors" in group_classes
        assert "debug-boxes" in group_classes
        assert "debug-markers" in group_classes
        assert "debug-labels" in group_classes


class TestOverlayIsAdditive:
    def test_original_elements_untouched(self) -> None:
        """Debug overlays should not modify existing SVG elements."""
        svg_no_debug, _ = convert(BASIC_SOURCE)
        svg_debug, _ = convert(BASIC_SOURCE, debug={"labels"})

        # Debug SVG should contain everything the original has, plus more
        assert '<?xml' in svg_debug
        assert '<rect' in svg_debug
        # Debug version should have extra debug content
        assert 'debug-labels' in svg_debug
        assert 'debug-labels' not in svg_no_debug


class TestEmptyDocument:
    def test_empty_doc_no_crash(self) -> None:
        svg, doc, boxes, cw, ch = _make_svg_and_doc(EMPTY_SOURCE)
        # Should not raise
        apply_debug_overlays(svg, doc, boxes, cw, ch, {"all"})

        # Grid should still be present
        group_classes = {g.get("class") for g in svg}
        assert "debug-grid" in group_classes


class TestConvertWithDebug:
    def test_convert_passes_debug(self) -> None:
        svg, _ = convert(BASIC_SOURCE, debug={"grid", "labels"})
        assert "debug-grid" in svg
        assert "debug-labels" in svg

    def test_convert_no_debug_by_default(self) -> None:
        svg, _ = convert(BASIC_SOURCE)
        assert "debug-" not in svg
