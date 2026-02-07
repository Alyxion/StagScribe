"""StagScribe CLI — Click commands for lint, convert, render, parse."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.group()
@click.version_option(package_name="stagscribe")
def cli() -> None:
    """StagScribe — a human-readable language for SVG design."""


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def lint(file: Path) -> None:
    """Validate a .stag file."""
    from stagscribe.linter.diagnostics import Severity
    from stagscribe.linter.linter import lint as run_lint
    from stagscribe.parser.parser import parse
    from stagscribe.resolver import resolve

    source = file.read_text()
    try:
        doc = parse(source)
        doc = resolve(doc)
    except Exception as e:
        click.echo(f"Parse error: {e}", err=True)
        sys.exit(1)

    diagnostics = run_lint(doc)
    if not diagnostics:
        click.echo(f"{file}: OK")
        return

    for d in diagnostics:
        click.echo(f"{file}{d}")

    if any(d.severity == Severity.ERROR for d in diagnostics):
        sys.exit(1)


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output SVG file path")
@click.option("--skip-lint", is_flag=True, help="Skip linting before conversion")
@click.option(
    "--debug", "debug_mode", default=None,
    help="Debug overlays: all, labels, colors, grid, boxes, markers (comma-separated)",
)
def convert(file: Path, output: Path | None, skip_lint: bool, debug_mode: str | None) -> None:
    """Convert a .stag file to SVG."""
    from stagscribe.converter.converter import convert as run_convert

    debug = _parse_debug_modes(debug_mode)
    source = file.read_text()
    try:
        svg, diagnostics = run_convert(source, skip_lint=skip_lint, debug=debug)
    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Print warnings
    for d in diagnostics:
        click.echo(f"{file}{d}", err=True)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(svg)
        click.echo(f"Written to {output}")
    else:
        click.echo(svg)


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output", type=click.Path(path_type=Path),
    required=True, help="Output PNG file path",
)
@click.option("--width", type=int, help="Output width in pixels")
@click.option("--skip-lint", is_flag=True, help="Skip linting before conversion")
@click.option(
    "--debug", "debug_mode", default=None,
    help="Debug overlays: all, labels, colors, grid, boxes, markers (comma-separated)",
)
def render(
    file: Path, output: Path, width: int | None, skip_lint: bool, debug_mode: str | None,
) -> None:
    """Render a .stag file to PNG."""
    from stagscribe.converter.converter import convert as run_convert
    from stagscribe.renderer.renderer import render_svg_to_png

    debug = _parse_debug_modes(debug_mode)
    source = file.read_text()
    try:
        svg, diagnostics = run_convert(source, skip_lint=skip_lint, debug=debug)
    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    for d in diagnostics:
        click.echo(f"{file}{d}", err=True)

    try:
        result_path = render_svg_to_png(svg, output, width=width)
        click.echo(f"Rendered to {result_path}")
    except RuntimeError as e:
        click.echo(f"Render error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def parse(file: Path) -> None:
    """Parse a .stag file and display the AST (debug)."""
    from stagscribe.parser.parser import parse as run_parse
    from stagscribe.resolver import resolve

    source = file.read_text()
    try:
        doc = run_parse(source)
        doc = resolve(doc)
    except Exception as e:
        click.echo(f"Parse error: {e}", err=True)
        sys.exit(1)

    _print_doc(doc)


def _print_doc(doc: object) -> None:
    """Pretty-print a Document AST."""
    from stagscribe.language.ast_nodes import Document

    if not isinstance(doc, Document):
        click.echo(repr(doc))
        return

    click.echo(f"Document ({len(doc.elements)} elements)")
    for el in doc.elements:
        _print_element(el, indent=2)


def _print_element(el: object, indent: int = 0) -> None:
    from stagscribe.language.ast_nodes import Element

    if not isinstance(el, Element):
        return

    prefix = " " * indent
    name_str = f' "{el.name}"' if el.name else ""
    click.echo(f"{prefix}{el.element_type}{name_str}")

    if el.width:
        click.echo(f"{prefix}  width: {el.width}")
    if el.height:
        click.echo(f"{prefix}  height: {el.height}")
    if el.fill:
        click.echo(f"{prefix}  fill: {el.fill}")
    if el.background:
        click.echo(f"{prefix}  background: {el.background}")
    if el.stroke:
        click.echo(f"{prefix}  stroke: {el.stroke}")
    if el.position:
        click.echo(f"{prefix}  position: {el.position}")
    if el.rounded:
        click.echo(f"{prefix}  rounded: {el.rounded}")
    if el.text_style:
        click.echo(f"{prefix}  text_style: {el.text_style}")
    if el.radius:
        click.echo(f"{prefix}  radius: {el.radius}")

    for child in el.children:
        _print_element(child, indent + 2)


def _parse_debug_modes(debug_mode: str | None) -> set[str] | None:
    """Parse the --debug option value into a set of mode names."""
    if debug_mode is None:
        return None
    return {m.strip() for m in debug_mode.split(",") if m.strip()}
