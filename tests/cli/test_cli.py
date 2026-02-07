"""Tests for the CLI commands."""

from pathlib import Path

from click.testing import CliRunner

from stagscribe.cli.main import cli


class TestCliLint:
    def test_lint_valid_file(self, tmp_path: Path) -> None:
        stag = tmp_path / "test.stag"
        stag.write_text(
            "canvas 800 by 600 pixels\n"
            "  background white\n"
            "\n"
            'rectangle "Box"\n'
            "  width 200\n"
            "  height 100\n"
            "  fill red\n"
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["lint", str(stag)])
        assert result.exit_code == 0
        assert "OK" in result.output

    def test_lint_empty_file(self, tmp_path: Path) -> None:
        stag = tmp_path / "empty.stag"
        stag.write_text("\n")
        runner = CliRunner()
        result = runner.invoke(cli, ["lint", str(stag)])
        assert result.exit_code == 1


class TestCliConvert:
    def test_convert_to_stdout(self, tmp_path: Path) -> None:
        stag = tmp_path / "test.stag"
        stag.write_text(
            "canvas 400 by 300 pixels\n"
            "  background white\n"
            "\n"
            'rectangle "Box"\n'
            "  width 200\n"
            "  height 100\n"
            "  at center\n"
            "  fill blue\n"
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["convert", str(stag)])
        assert result.exit_code == 0
        assert "<svg" in result.output

    def test_convert_to_file(self, tmp_path: Path) -> None:
        stag = tmp_path / "test.stag"
        stag.write_text(
            "canvas 400 by 300 pixels\n"
            "  background white\n"
        )
        out_svg = tmp_path / "out.svg"
        runner = CliRunner()
        result = runner.invoke(cli, ["convert", str(stag), "-o", str(out_svg)])
        assert result.exit_code == 0
        assert out_svg.exists()
        assert "<svg" in out_svg.read_text()


class TestCliParse:
    def test_parse_output(self, tmp_path: Path) -> None:
        stag = tmp_path / "test.stag"
        stag.write_text(
            "canvas 800 by 600 pixels\n"
            "  background white\n"
            "\n"
            'rectangle "Box"\n'
            "  width 200\n"
            "  height 100\n"
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["parse", str(stag)])
        assert result.exit_code == 0
        assert "Document" in result.output
        assert "canvas" in result.output
        assert "Box" in result.output


class TestCliRender:
    def test_render_to_png(self, tmp_path: Path) -> None:
        stag = tmp_path / "test.stag"
        stag.write_text(
            "canvas 200 by 200 pixels\n"
            "  background white\n"
            "\n"
            'circle "Dot"\n'
            "  radius 50\n"
            "  at center\n"
            "  fill red\n"
        )
        out_png = tmp_path / "out.png"
        runner = CliRunner()
        result = runner.invoke(cli, ["render", str(stag), "-o", str(out_png)])
        assert result.exit_code == 0
        assert out_png.exists()
        assert out_png.stat().st_size > 0
