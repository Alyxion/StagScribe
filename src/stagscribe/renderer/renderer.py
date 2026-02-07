"""SVG → PNG renderer using resvg-py (primary) and resvg CLI (fallback)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def render_svg_to_png(svg_string: str, output_path: str | Path, width: int | None = None) -> Path:
    """Render an SVG string to a PNG file.

    Tries resvg-py first, falls back to resvg CLI.
    Returns the path to the generated PNG.
    """
    output_path = Path(output_path)

    try:
        return _render_with_resvg_py(svg_string, output_path, width)
    except Exception:
        return _render_with_resvg_cli(svg_string, output_path, width)


def render_svg_file_to_png(
    svg_path: str | Path, output_path: str | Path, width: int | None = None,
) -> Path:
    """Render an SVG file to a PNG file."""
    svg_path = Path(svg_path)
    svg_string = svg_path.read_text()
    return render_svg_to_png(svg_string, output_path, width)


def _find_font_dir() -> str | None:
    """Find the bundled Roboto font directory."""
    # Walk up from this file to find the project root with fonts/
    candidate = Path(__file__).resolve().parent.parent.parent.parent / "fonts" / "roboto"
    if candidate.is_dir():
        return str(candidate)
    return None


def _render_with_resvg_py(svg_string: str, output_path: Path, width: int | None) -> Path:
    """Render using resvg-py Python bindings."""
    from resvg_py import svg_to_bytes  # type: ignore[import-untyped]

    kwargs: dict[str, object] = {"svg_string": svg_string}
    if width:
        kwargs["width"] = width

    font_dir = _find_font_dir()
    if font_dir:
        kwargs["font_dirs"] = [font_dir]
        kwargs["font_family"] = "Roboto"

    png_bytes: bytes = svg_to_bytes(**kwargs)  # type: ignore[arg-type]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(png_bytes)
    return output_path


def _render_with_resvg_cli(svg_string: str, output_path: Path, width: int | None) -> Path:
    """Render using resvg CLI as fallback."""
    resvg_bin = shutil.which("resvg")
    if not resvg_bin:
        raise RuntimeError(
            "Neither resvg-py nor resvg CLI is available. "
            "Install resvg-py (pip install resvg-py) or resvg CLI (brew install resvg)."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
        f.write(svg_string)
        svg_tmp = f.name

    try:
        cmd = [resvg_bin, svg_tmp, str(output_path)]
        if width:
            cmd.extend(["--width", str(width)])
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"resvg CLI failed: {result.stderr}")
    finally:
        Path(svg_tmp).unlink(missing_ok=True)

    return output_path
