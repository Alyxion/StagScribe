"""Tests for the StagScribe linter."""

from stagscribe.language.ast_nodes import Document, Element, Position, TextStyle, Value
from stagscribe.linter.diagnostics import Severity
from stagscribe.linter.linter import has_errors, lint


class TestStructureRules:
    def test_empty_document(self) -> None:
        doc = Document(statements=[])
        diags = lint(doc)
        assert any(d.severity == Severity.ERROR and "no elements" in d.message for d in diags)

    def test_no_canvas_warning(self) -> None:
        doc = Document(statements=[
            Element(element_type="rectangle", name="Box", width=Value(100), height=Value(50)),
        ])
        diags = lint(doc)
        assert any(d.severity == Severity.WARNING and "No canvas" in d.message for d in diags)

    def test_multiple_canvases_error(self) -> None:
        doc = Document(statements=[
            Element(element_type="canvas", width=Value(800), height=Value(600)),
            Element(element_type="canvas", width=Value(400), height=Value(300)),
        ])
        diags = lint(doc)
        assert any(d.severity == Severity.ERROR and "Multiple canvas" in d.message for d in diags)

    def test_duplicate_names_error(self) -> None:
        doc = Document(statements=[
            Element(element_type="canvas", width=Value(800), height=Value(600)),
            Element(element_type="rectangle", name="Box"),
            Element(element_type="circle", name="Box"),
        ])
        diags = lint(doc)
        assert any(d.severity == Severity.ERROR and "Duplicate" in d.message for d in diags)

    def test_valid_document_no_errors(self) -> None:
        doc = Document(statements=[
            Element(
                element_type="canvas",
                width=Value(800),
                height=Value(600),
                background="#FFFFFF",
            ),
            Element(
                element_type="rectangle",
                name="Box",
                width=Value(200),
                height=Value(100),
                fill="#FF0000",
            ),
        ])
        diags = lint(doc)
        assert not has_errors(diags)


class TestReferenceRules:
    def test_valid_reference(self) -> None:
        doc = Document(statements=[
            Element(element_type="canvas", width=Value(800), height=Value(600)),
            Element(element_type="rectangle", name="Box", width=Value(200), height=Value(100)),
            Element(
                element_type="text",
                name="Label",
                position=Position(anchor="center", reference="Box"),
                text_style=TextStyle(size=Value(16)),
            ),
        ])
        diags = lint(doc)
        assert not any(d.rule == "references" for d in diags)

    def test_invalid_reference(self) -> None:
        doc = Document(statements=[
            Element(element_type="canvas", width=Value(800), height=Value(600)),
            Element(
                element_type="text",
                name="Label",
                position=Position(anchor="center", reference="NonExistent"),
                text_style=TextStyle(size=Value(16)),
            ),
        ])
        diags = lint(doc)
        assert any(
            d.severity == Severity.ERROR and "NonExistent" in d.message
            for d in diags
        )


class TestHasErrors:
    def test_no_errors(self) -> None:
        assert has_errors([]) is False

    def test_with_error(self) -> None:
        from stagscribe.linter.diagnostics import Diagnostic
        diags = [Diagnostic(Severity.ERROR, "test")]
        assert has_errors(diags) is True

    def test_warnings_only(self) -> None:
        from stagscribe.linter.diagnostics import Diagnostic
        diags = [Diagnostic(Severity.WARNING, "test")]
        assert has_errors(diags) is False
