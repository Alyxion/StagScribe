"""Tests for for-loop parsing."""

from stagscribe.language.ast_nodes import (
    ForStatement,
    LiteralExpr,
    VarRefExpr,
)
from stagscribe.parser.parser import parse


class TestForLoopParsing:
    def test_basic_for_loop(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 3\n"
            "  rect \"Box_{i}\" 50 by 50\n"
        )
        doc = parse(source)
        stmts = doc.statements
        assert any(isinstance(s, ForStatement) for s in stmts)
        fs = [s for s in stmts if isinstance(s, ForStatement)][0]
        assert fs.var_name == "i"
        assert isinstance(fs.start, LiteralExpr)
        assert fs.start.value.number == 0
        assert isinstance(fs.end, LiteralExpr)
        assert fs.end.value.number == 3
        assert fs.step is None
        assert len(fs.body) == 1

    def test_for_loop_with_step(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 10 step 2\n"
            "  rect \"Box_{i}\" 50 by 50\n"
        )
        doc = parse(source)
        fs = [s for s in doc.statements if isinstance(s, ForStatement)][0]
        assert fs.step is not None

    def test_for_loop_with_expression_bounds(self) -> None:
        source = (
            "n is 5\n"
            "canvas 400 by 400\n"
            "for i from 0 to n\n"
            "  rect \"Box_{i}\" 50 by 50\n"
        )
        doc = parse(source)
        fs = [s for s in doc.statements if isinstance(s, ForStatement)][0]
        assert isinstance(fs.end, VarRefExpr)
        assert fs.end.name == "n"

    def test_nested_for_loops(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for row from 0 to 2\n"
            "  for col from 0 to 2\n"
            "    rect \"Tile_{row}_{col}\" 50 by 50\n"
        )
        doc = parse(source)
        outer = [s for s in doc.statements if isinstance(s, ForStatement)][0]
        assert outer.var_name == "row"
        assert len(outer.body) == 1
        inner = outer.body[0]
        assert isinstance(inner, ForStatement)
        assert inner.var_name == "col"
        assert len(inner.body) == 1

    def test_for_loop_with_multiple_body_stmts(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 2\n"
            "  rect \"Box_{i}\" 50 by 50\n"
            "  circle \"Dot_{i}\"\n"
            "    radius 10\n"
        )
        doc = parse(source)
        fs = [s for s in doc.statements if isinstance(s, ForStatement)][0]
        assert len(fs.body) == 2

    def test_for_loop_with_expr_arithmetic(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 1 to 3\n"
            "  rect \"Box_{i}\" 50 by 50\n"
            "    at i * 100 i * 50\n"
        )
        doc = parse(source)
        fs = [s for s in doc.statements if isinstance(s, ForStatement)][0]
        assert len(fs.body) == 1
        el = fs.body[0]
        assert el.name == "Box_{i}"  # Not yet interpolated (that's resolver)
