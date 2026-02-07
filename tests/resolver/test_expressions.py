"""Tests for expression evaluation in the resolver."""

import pytest

from stagscribe.language.ast_nodes import (
    BinaryExpr,
    LiteralExpr,
    UnaryExpr,
    Value,
    VarRefExpr,
)
from stagscribe.resolver.resolver import ResolveError, Resolver


class TestBasicArithmetic:
    def setup_method(self) -> None:
        self.resolver = Resolver()

    def test_literal(self) -> None:
        expr = LiteralExpr(value=Value(number=42.0))
        result = self.resolver._eval_expr(expr)
        assert result.number == 42.0
        assert result.unit is None

    def test_addition(self) -> None:
        expr = BinaryExpr(
            op="+",
            left=LiteralExpr(value=Value(number=10.0)),
            right=LiteralExpr(value=Value(number=5.0)),
        )
        result = self.resolver._eval_expr(expr)
        assert result.number == 15.0

    def test_subtraction(self) -> None:
        expr = BinaryExpr(
            op="-",
            left=LiteralExpr(value=Value(number=10.0)),
            right=LiteralExpr(value=Value(number=3.0)),
        )
        result = self.resolver._eval_expr(expr)
        assert result.number == 7.0

    def test_multiplication(self) -> None:
        expr = BinaryExpr(
            op="*",
            left=LiteralExpr(value=Value(number=6.0)),
            right=LiteralExpr(value=Value(number=7.0)),
        )
        result = self.resolver._eval_expr(expr)
        assert result.number == 42.0

    def test_division(self) -> None:
        expr = BinaryExpr(
            op="/",
            left=LiteralExpr(value=Value(number=20.0)),
            right=LiteralExpr(value=Value(number=4.0)),
        )
        result = self.resolver._eval_expr(expr)
        assert result.number == 5.0

    def test_negation(self) -> None:
        expr = UnaryExpr(operand=LiteralExpr(value=Value(number=10.0)))
        result = self.resolver._eval_expr(expr)
        assert result.number == -10.0

    def test_division_by_zero(self) -> None:
        expr = BinaryExpr(
            op="/",
            left=LiteralExpr(value=Value(number=10.0)),
            right=LiteralExpr(value=Value(number=0.0)),
        )
        with pytest.raises(ResolveError, match="Division by zero"):
            self.resolver._eval_expr(expr)


class TestPrecedence:
    def setup_method(self) -> None:
        self.resolver = Resolver()

    def test_mul_before_add(self) -> None:
        # 10 + 5 * 2 = 20
        expr = BinaryExpr(
            op="+",
            left=LiteralExpr(value=Value(number=10.0)),
            right=BinaryExpr(
                op="*",
                left=LiteralExpr(value=Value(number=5.0)),
                right=LiteralExpr(value=Value(number=2.0)),
            ),
        )
        result = self.resolver._eval_expr(expr)
        assert result.number == 20.0

    def test_sub_with_mul(self) -> None:
        # 100 - 10 * 2 = 80
        expr = BinaryExpr(
            op="-",
            left=LiteralExpr(value=Value(number=100.0)),
            right=BinaryExpr(
                op="*",
                left=LiteralExpr(value=Value(number=10.0)),
                right=LiteralExpr(value=Value(number=2.0)),
            ),
        )
        result = self.resolver._eval_expr(expr)
        assert result.number == 80.0


class TestUnitArithmetic:
    def setup_method(self) -> None:
        self.resolver = Resolver()

    def test_add_same_units(self) -> None:
        expr = BinaryExpr(
            op="+",
            left=LiteralExpr(value=Value(number=10.0, unit="px")),
            right=LiteralExpr(value=Value(number=5.0, unit="px")),
        )
        result = self.resolver._eval_expr(expr)
        assert result.number == 15.0
        assert result.unit == "px"

    def test_add_unitless_and_unit(self) -> None:
        expr = BinaryExpr(
            op="+",
            left=LiteralExpr(value=Value(number=10.0)),
            right=LiteralExpr(value=Value(number=5.0, unit="px")),
        )
        result = self.resolver._eval_expr(expr)
        assert result.number == 15.0
        assert result.unit == "px"

    def test_add_different_units_error(self) -> None:
        expr = BinaryExpr(
            op="+",
            left=LiteralExpr(value=Value(number=10.0, unit="px")),
            right=LiteralExpr(value=Value(number=5.0, unit="cm")),
        )
        with pytest.raises(ResolveError, match="different units"):
            self.resolver._eval_expr(expr)

    def test_multiply_scalar_by_unit(self) -> None:
        expr = BinaryExpr(
            op="*",
            left=LiteralExpr(value=Value(number=2.0)),
            right=LiteralExpr(value=Value(number=50.0, unit="px")),
        )
        result = self.resolver._eval_expr(expr)
        assert result.number == 100.0
        assert result.unit == "px"

    def test_multiply_two_units_error(self) -> None:
        expr = BinaryExpr(
            op="*",
            left=LiteralExpr(value=Value(number=10.0, unit="px")),
            right=LiteralExpr(value=Value(number=5.0, unit="px")),
        )
        with pytest.raises(ResolveError, match="units on both sides"):
            self.resolver._eval_expr(expr)

    def test_negate_with_unit(self) -> None:
        expr = UnaryExpr(operand=LiteralExpr(value=Value(number=10.0, unit="px")))
        result = self.resolver._eval_expr(expr)
        assert result.number == -10.0
        assert result.unit == "px"


class TestVariableReferences:
    def setup_method(self) -> None:
        self.resolver = Resolver()

    def test_var_ref(self) -> None:
        self.resolver.variables["x"] = Value(number=42.0)
        expr = VarRefExpr(name="x")
        result = self.resolver._eval_expr(expr)
        assert result.number == 42.0

    def test_undefined_var(self) -> None:
        expr = VarRefExpr(name="unknown")
        with pytest.raises(ResolveError, match="Undefined variable"):
            self.resolver._eval_expr(expr)

    def test_var_in_expression(self) -> None:
        self.resolver.variables["w"] = Value(number=500.0)
        self.resolver.variables["margin"] = Value(number=10.0)
        # w - margin * 2
        expr = BinaryExpr(
            op="-",
            left=VarRefExpr(name="w"),
            right=BinaryExpr(
                op="*",
                left=VarRefExpr(name="margin"),
                right=LiteralExpr(value=Value(number=2.0)),
            ),
        )
        result = self.resolver._eval_expr(expr)
        assert result.number == 480.0
