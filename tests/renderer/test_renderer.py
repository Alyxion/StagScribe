"""Tests for the renderer."""

from pathlib import Path

from stagscribe.renderer.renderer import render_svg_to_png


class TestRenderer:
    def test_render_simple_svg(self, tmp_path: Path) -> None:
        svg = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            '<rect width="100" height="100" fill="red"/>'
            '</svg>'
        )
        output = tmp_path / "test.png"
        result = render_svg_to_png(svg, output)
        assert result.exists()
        assert result.stat().st_size > 0

    def test_render_with_width(self, tmp_path: Path) -> None:
        svg = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">'
            '<circle cx="100" cy="100" r="50" fill="blue"/>'
            '</svg>'
        )
        output = tmp_path / "test_w.png"
        result = render_svg_to_png(svg, output, width=100)
        assert result.exists()
        assert result.stat().st_size > 0
