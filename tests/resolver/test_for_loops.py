"""Tests for for-loop resolution (unrolling)."""

import pytest

from stagscribe.parser.parser import parse
from stagscribe.resolver import resolve
from stagscribe.resolver.resolver import ResolveError


class TestForLoopUnrolling:
    def test_basic_unroll(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 3\n"
            "  rect \"Box_{i}\" 50 by 50\n"
        )
        doc = resolve(parse(source))
        # canvas + 4 rects (i=0,1,2,3 inclusive)
        assert len(doc.elements) == 5
        names = [el.name for el in doc.elements[1:]]
        assert names == ["Box_0", "Box_1", "Box_2", "Box_3"]

    def test_for_loop_with_step(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 6 step 2\n"
            "  rect \"Box_{i}\" 50 by 50\n"
        )
        doc = resolve(parse(source))
        names = [el.name for el in doc.elements[1:]]
        assert names == ["Box_0", "Box_2", "Box_4", "Box_6"]

    def test_for_loop_descending(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 3 to 0 step -1\n"
            "  rect \"Box_{i}\" 50 by 50\n"
        )
        doc = resolve(parse(source))
        names = [el.name for el in doc.elements[1:]]
        assert names == ["Box_3", "Box_2", "Box_1", "Box_0"]

    def test_for_loop_auto_step_descending(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 3 to 0\n"
            "  rect \"Box_{i}\" 50 by 50\n"
        )
        doc = resolve(parse(source))
        names = [el.name for el in doc.elements[1:]]
        assert names == ["Box_3", "Box_2", "Box_1", "Box_0"]

    def test_variable_in_expressions(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 2\n"
            "  rect \"Box_{i}\" 50 by 50\n"
            "    at i * 100 + 50 i * 100 + 50\n"
        )
        doc = resolve(parse(source))
        positions = [
            (el.position.x.number, el.position.y.number)
            for el in doc.elements[1:]
            if el.position and el.position.x and el.position.y
        ]
        assert positions == [(50.0, 50.0), (150.0, 150.0), (250.0, 250.0)]

    def test_nested_for_loops(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for row from 0 to 1\n"
            "  for col from 0 to 1\n"
            "    rect \"Tile_{row}_{col}\" 50 by 50\n"
        )
        doc = resolve(parse(source))
        names = [el.name for el in doc.elements[1:]]
        assert names == ["Tile_0_0", "Tile_0_1", "Tile_1_0", "Tile_1_1"]

    def test_for_loop_with_variable_bounds(self) -> None:
        source = (
            "n is 3\n"
            "canvas 400 by 400\n"
            "for i from 0 to n\n"
            "  rect \"Box_{i}\" 50 by 50\n"
        )
        doc = resolve(parse(source))
        names = [el.name for el in doc.elements[1:]]
        assert names == ["Box_0", "Box_1", "Box_2", "Box_3"]

    def test_for_loop_variable_shadowing(self) -> None:
        """Loop variable should not clobber an outer variable."""
        source = (
            "i is 99\n"
            "canvas 400 by 400\n"
            "for i from 0 to 1\n"
            "  rect \"Box_{i}\" 50 by 50\n"
            "rect \"After\" i by 50\n"
        )
        doc = resolve(parse(source))
        after = [el for el in doc.elements if el.name == "After"][0]
        assert after.width is not None
        assert after.width.number == 99.0

    def test_is_stmt_in_for_body(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 2\n"
            "  x is i * 100 + 25\n"
            "  rect \"Box_{i}\" 50 by 50\n"
            "    at x 50\n"
        )
        doc = resolve(parse(source))
        xs = [
            el.position.x.number
            for el in doc.elements[1:]
            if el.position and el.position.x
        ]
        assert xs == [25.0, 125.0, 225.0]


class TestForLoopSafety:
    def test_zero_step_error(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 5 step 0\n"
            "  rect \"Box\" 50 by 50\n"
        )
        with pytest.raises(ResolveError, match="step cannot be zero"):
            resolve(parse(source))

    def test_wrong_step_direction_positive(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 5 to 0 step 1\n"
            "  rect \"Box\" 50 by 50\n"
        )
        with pytest.raises(ResolveError, match="step direction"):
            resolve(parse(source))

    def test_wrong_step_direction_negative(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 5 step -1\n"
            "  rect \"Box\" 50 by 50\n"
        )
        with pytest.raises(ResolveError, match="step direction"):
            resolve(parse(source))

    def test_max_iterations_exceeded(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 100000\n"
            "  rect \"Box\" 50 by 50\n"
        )
        with pytest.raises(ResolveError, match="iterations"):
            resolve(parse(source))

    def test_max_nesting_depth(self) -> None:
        # Build 6 levels of nested for loops (exceeds max of 5)
        source = "canvas 400 by 400\n"
        indent = ""
        for level in range(6):
            source += f"{indent}for v{level} from 0 to 1\n"
            indent += "  "
        source += f"{indent}rect \"Box\" 50 by 50\n"
        with pytest.raises(ResolveError, match="nesting depth"):
            resolve(parse(source))

    def test_unitless_bounds_required(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 pixels to 3\n"
            "  rect \"Box\" 50 by 50\n"
        )
        with pytest.raises(ResolveError, match="unitless"):
            resolve(parse(source))


class TestForLoopInterpolation:
    def test_interpolation_with_float_value(self) -> None:
        """Integer-valued floats should render without decimal."""
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 2\n"
            "  rect \"Item_{i}\" 50 by 50\n"
        )
        doc = resolve(parse(source))
        names = [el.name for el in doc.elements[1:]]
        assert all("." not in n for n in names)

    def test_no_interpolation_without_braces(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 1\n"
            "  rect \"NoVar\" 50 by 50\n"
        )
        doc = resolve(parse(source))
        names = [el.name for el in doc.elements[1:]]
        assert names == ["NoVar", "NoVar"]

    def test_unknown_var_in_braces_unchanged(self) -> None:
        source = (
            "canvas 400 by 400\n"
            "for i from 0 to 0\n"
            "  rect \"Item_{unknown}\" 50 by 50\n"
        )
        doc = resolve(parse(source))
        assert doc.elements[1].name == "Item_{unknown}"

    def test_reference_interpolation(self) -> None:
        """Position references like 'below "Row_{i}"' should be interpolated."""
        source = (
            "canvas 400 by 400\n"
            "rect \"Row_0\" 100 by 50\n"
            "  at 50% 10%\n"
            "rect \"Row_1\" 100 by 50\n"
            "  at 50% 30%\n"
            "for i from 0 to 1\n"
            "  rect \"Child_{i}\" 50 by 20\n"
            "    below \"Row_{i}\" with gap 5\n"
        )
        doc = resolve(parse(source))
        child0 = [el for el in doc.elements if el.name == "Child_0"][0]
        child1 = [el for el in doc.elements if el.name == "Child_1"][0]
        assert child0.position is not None
        assert child0.position.reference == "Row_0"
        assert child1.position is not None
        assert child1.position.reference == "Row_1"
