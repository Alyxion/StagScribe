"""StagScribe converter orchestrator — .stag source → SVG string."""

from __future__ import annotations

from stagscribe.converter.svg_builder import build_svg
from stagscribe.language.ast_nodes import Document
from stagscribe.linter.diagnostics import Diagnostic
from stagscribe.linter.linter import has_errors, lint
from stagscribe.parser.parser import parse
from stagscribe.resolver import resolve


def convert(
    source: str,
    skip_lint: bool = False,
    debug: set[str] | None = None,
) -> tuple[str, list[Diagnostic]]:
    """Convert StagScribe source to SVG.

    Returns (svg_string, diagnostics).
    Raises ValueError if there are lint errors and skip_lint is False.
    """
    doc = parse(source)
    doc = resolve(doc)
    diagnostics = lint(doc)

    if has_errors(diagnostics) and not skip_lint:
        raise ValueError(
            "Lint errors found:\n" + "\n".join(str(d) for d in diagnostics)
        )

    svg = build_svg(doc, debug=debug)
    return svg, diagnostics


def convert_document(doc: Document, debug: set[str] | None = None) -> str:
    """Convert an already-parsed Document to SVG."""
    return build_svg(doc, debug=debug)
