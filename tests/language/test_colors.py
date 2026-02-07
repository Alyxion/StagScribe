"""Tests for color resolution."""

from stagscribe.language.colors import is_color_keyword, resolve_color


class TestResolveColor:
    def test_css_named_color(self) -> None:
        assert resolve_color("red") == "#FF0000"
        assert resolve_color("blue") == "#0000FF"
        assert resolve_color("white") == "#FFFFFF"

    def test_css_color_case_insensitive(self) -> None:
        assert resolve_color("Red") == "#FF0000"
        assert resolve_color("WHITE") == "#FFFFFF"

    def test_friendly_alias(self) -> None:
        assert resolve_color("light gray") == "#D3D3D3"
        assert resolve_color("dark gray") == "#A9A9A9"
        assert resolve_color("sky blue") == "#87CEEB"

    def test_hex_color_6_digit(self) -> None:
        assert resolve_color("#FF0000") == "#ff0000"
        assert resolve_color("#007AFF") == "#007aff"

    def test_hex_color_3_digit(self) -> None:
        assert resolve_color("#F00") == "#f00"

    def test_invalid_hex(self) -> None:
        assert resolve_color("#ZZZZZZ") is None

    def test_unknown_color(self) -> None:
        assert resolve_color("unicorn") is None

    def test_none_and_transparent(self) -> None:
        assert resolve_color("none") == "none"
        assert resolve_color("transparent") == "none"

    def test_rgb_passthrough(self) -> None:
        assert resolve_color("rgb(255,0,0)") == "rgb(255,0,0)"


class TestIsColorKeyword:
    def test_known_colors(self) -> None:
        assert is_color_keyword("red") is True
        assert is_color_keyword("skyblue") is True

    def test_friendly_alias(self) -> None:
        assert is_color_keyword("light gray") is True

    def test_unknown(self) -> None:
        assert is_color_keyword("unicorn") is False
