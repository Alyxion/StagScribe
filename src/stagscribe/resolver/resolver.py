"""Resolve variables, expressions, color palettes, and templates in a Document."""

from __future__ import annotations

import copy
import re

from stagscribe.language.ast_nodes import (
    BinaryExpr,
    ColorsBlock,
    DefineBlock,
    Document,
    Element,
    Expr,
    ForStatement,
    IsStatement,
    LiteralExpr,
    PlaceStatement,
    Position,
    StrokeStyle,
    UnaryExpr,
    Value,
    VarRefExpr,
)
from stagscribe.language.colors import resolve_color

# Safety limits for for-loops
_MAX_LOOP_ITERATIONS = 10_000
_MAX_LOOP_DEPTH = 5


class ResolveError(Exception):
    """Error during resolution of variables/expressions/templates."""


class Resolver:
    """Processes a Document, resolving all v2 features into plain Elements."""

    def __init__(self) -> None:
        self.variables: dict[str, Value] = {}
        self.color_vars: dict[str, str] = {}
        self.templates: dict[str, DefineBlock] = {}
        self._loop_depth: int = 0

    def resolve(self, doc: Document) -> Document:
        """Resolve all v2 constructs and return a Document with only Elements."""
        resolved_elements: list[Element] = []
        self._resolve_statements(doc.statements, resolved_elements)
        return Document(statements=list(resolved_elements))  # type: ignore[arg-type]

    def _resolve_statements(
        self, statements: list, resolved_elements: list[Element]  # type: ignore[type-arg]
    ) -> None:
        for stmt in statements:
            if isinstance(stmt, IsStatement):
                self._handle_is(stmt)
            elif isinstance(stmt, ColorsBlock):
                self._handle_colors(stmt)
            elif isinstance(stmt, DefineBlock):
                self._handle_define(stmt)
            elif isinstance(stmt, PlaceStatement):
                elements = self._handle_place(stmt)
                resolved_elements.extend(elements)
            elif isinstance(stmt, ForStatement):
                elements = self._handle_for(stmt)
                resolved_elements.extend(elements)
            elif isinstance(stmt, Element):
                resolved_elements.append(self._resolve_element(stmt))

    def _handle_is(self, stmt: IsStatement) -> None:
        value = self._eval_expr(stmt.expr)
        self.variables[stmt.name] = value

    def _handle_colors(self, block: ColorsBlock) -> None:
        for assignment in block.assignments:
            color = assignment.color
            # Resolve CSS color names to hex
            resolved = resolve_color(color)
            if resolved:
                color = resolved
            self.color_vars[assignment.name] = color

    def _handle_define(self, block: DefineBlock) -> None:
        self.templates[block.name] = block

    def _handle_place(self, stmt: PlaceStatement) -> list[Element]:
        template = self.templates.get(stmt.template_name)
        if template is None:
            raise ResolveError(
                f"Unknown template '{stmt.template_name}'"
            )

        body = copy.deepcopy(template.body_elements)

        if len(body) == 1:
            el = body[0]
            if stmt.instance_name:
                el.name = stmt.instance_name
            if stmt.position:
                el.position = stmt.position
            self._apply_overrides(el, stmt.props)
            if stmt.scale is not None:
                self._apply_scale(el, self._eval_expr(stmt.scale))
            if stmt.rotate_expr is not None:
                val = self._eval_expr(stmt.rotate_expr)
                el.rotate = val.number
            return [self._resolve_element(el)]
        else:
            group = Element(
                element_type="group",
                name=stmt.instance_name,
                position=stmt.position,
                children=body,
            )
            self._apply_overrides(group, stmt.props)
            if stmt.scale is not None:
                scale_val = self._eval_expr(stmt.scale)
                for child in group.children:
                    self._apply_scale(child, scale_val)
            if stmt.rotate_expr is not None:
                val = self._eval_expr(stmt.rotate_expr)
                group.rotate = val.number
            return [self._resolve_element(group)]

    def _handle_for(self, stmt: ForStatement) -> list[Element]:
        """Unroll a for loop into resolved Elements."""
        if self._loop_depth >= _MAX_LOOP_DEPTH:
            raise ResolveError(
                f"Maximum loop nesting depth ({_MAX_LOOP_DEPTH}) exceeded"
            )

        start_val = self._eval_expr(stmt.start)
        end_val = self._eval_expr(stmt.end)

        # Validate: must be unitless integers
        if start_val.unit is not None:
            raise ResolveError("For loop 'from' value must be unitless")
        if end_val.unit is not None:
            raise ResolveError("For loop 'to' value must be unitless")

        start_n = start_val.number
        end_n = end_val.number

        if stmt.step is not None:
            step_val = self._eval_expr(stmt.step)
            if step_val.unit is not None:
                raise ResolveError("For loop 'step' value must be unitless")
            step_n = step_val.number
        else:
            step_n = 1.0 if end_n >= start_n else -1.0

        if step_n == 0:
            raise ResolveError("For loop step cannot be zero")
        if step_n > 0 and end_n < start_n:
            raise ResolveError(
                "For loop step direction does not match range "
                "(positive step, end < start)"
            )
        if step_n < 0 and end_n > start_n:
            raise ResolveError(
                "For loop step direction does not match range "
                "(negative step, end > start)"
            )

        # Count iterations for safety
        n_iters = int(abs(end_n - start_n) / abs(step_n)) + 1
        if n_iters > _MAX_LOOP_ITERATIONS:
            raise ResolveError(
                f"For loop would produce {n_iters} iterations "
                f"(max {_MAX_LOOP_ITERATIONS})"
            )

        # Save/restore variable if shadowed
        old_var = self.variables.get(stmt.var_name)
        resolved_elements: list[Element] = []

        self._loop_depth += 1
        try:
            i = start_n
            while (step_n > 0 and i <= end_n + 1e-9) or (step_n < 0 and i >= end_n - 1e-9):
                self.variables[stmt.var_name] = Value(number=float(i))
                body_copy = copy.deepcopy(stmt.body)
                # Interpolate names
                self._interpolate_names(body_copy)
                self._resolve_statements(body_copy, resolved_elements)
                i += step_n
        finally:
            self._loop_depth -= 1
            # Restore old variable
            if old_var is not None:
                self.variables[stmt.var_name] = old_var
            else:
                self.variables.pop(stmt.var_name, None)

        return resolved_elements

    def _interpolate_names(self, stmts: list) -> None:  # type: ignore[type-arg]
        """Replace {var} patterns in element names and references."""
        for stmt in stmts:
            if isinstance(stmt, Element):
                if stmt.name is not None:
                    stmt.name = self._interpolate_string(stmt.name)
                if stmt.position is not None:
                    self._interpolate_position(stmt.position)
                self._interpolate_names(stmt.children)
            elif isinstance(stmt, PlaceStatement):
                if stmt.instance_name is not None:
                    stmt.instance_name = self._interpolate_string(stmt.instance_name)
                if stmt.position is not None:
                    self._interpolate_position(stmt.position)
            elif isinstance(stmt, ForStatement):
                self._interpolate_names(stmt.body)

    def _interpolate_position(self, pos: Position) -> None:
        """Interpolate {var} in position reference strings."""
        if pos.reference is not None:
            pos.reference = self._interpolate_string(pos.reference)

    def _interpolate_string(self, s: str) -> str:
        """Replace {var_name} with the current integer value of the variable."""
        def _replace(m: re.Match[str]) -> str:
            var_name = m.group(1)
            val = self.variables.get(var_name)
            if val is None:
                return m.group(0)  # leave unreplaced
            n = val.number
            return str(int(n)) if n == int(n) else str(n)
        return re.sub(r"\{(\w+)\}", _replace, s)

    def _apply_scale(self, el: Element, scale_val: Value) -> None:
        factor = scale_val.number
        if el.width is not None and isinstance(el.width, Value):
            el.width = Value(number=el.width.number * factor, unit=el.width.unit)
        if el.height is not None and isinstance(el.height, Value):
            el.height = Value(number=el.height.number * factor, unit=el.height.unit)
        if el.radius is not None and isinstance(el.radius, Value):
            el.radius = Value(number=el.radius.number * factor, unit=el.radius.unit)

    def _apply_overrides(self, el: Element, props: dict) -> None:  # type: ignore[type-arg]
        for key, val in props.items():
            if key == "fill":
                el.fill = self._resolve_color_string(val) if isinstance(val, str) else val
            elif key == "stroke" and isinstance(val, StrokeStyle):
                el.stroke = val
            elif key == "width":
                el.width = val
            elif key == "height":
                el.height = val
            elif key == "background":
                el.background = self._resolve_color_string(val) if isinstance(val, str) else val

    def _resolve_element(self, el: Element) -> Element:
        """Resolve all expressions and color refs in an element."""
        # Resolve dimensions
        el.width = self._resolve_value_field(el.width)
        el.height = self._resolve_value_field(el.height)
        el.radius = self._resolve_value_field(el.radius)
        el.rounded = self._resolve_value_field(el.rounded)

        # Resolve opacity (can be Expr)
        if isinstance(el.opacity, Expr):
            val = self._eval_expr(el.opacity)
            el.opacity = val.number
        elif isinstance(el.opacity, Value):
            el.opacity = el.opacity.number

        # Resolve rotate (can be Expr)
        if isinstance(el.rotate, Expr):
            val = self._eval_expr(el.rotate)
            el.rotate = val.number

        # Resolve fill color var refs
        if isinstance(el.fill, str):
            el.fill = self._resolve_color_string(el.fill)

        # Resolve background color var refs
        if isinstance(el.background, str):
            el.background = self._resolve_color_string(el.background)

        # Resolve stroke
        if el.stroke is not None:
            if isinstance(el.stroke.color, str):
                el.stroke.color = self._resolve_color_string(el.stroke.color)
            el.stroke.width = self._resolve_value_field(el.stroke.width)

        # Resolve position
        if el.position is not None:
            el.position = self._resolve_position(el.position)

        # Resolve text style
        if el.text_style is not None:
            el.text_style.size = self._resolve_value_field(el.text_style.size)
            if isinstance(el.text_style.color, str):
                el.text_style.color = self._resolve_color_string(el.text_style.color)

        # Resolve line endpoints
        if el.line_from is not None:
            lf0 = self._resolve_value_field(el.line_from[0])
            lf1 = self._resolve_value_field(el.line_from[1])
            if lf0 is not None and lf1 is not None:
                el.line_from = (lf0, lf1)
        if el.line_to is not None:
            lt0 = self._resolve_value_field(el.line_to[0])
            lt1 = self._resolve_value_field(el.line_to[1])
            if lt0 is not None and lt1 is not None:
                el.line_to = (lt0, lt1)

        # Resolve polygon points
        if el.points is not None:
            resolved_points: list[tuple[Value, Value]] = []
            for p in el.points:
                px = self._resolve_value_field(p[0])
                py = self._resolve_value_field(p[1])
                if px is not None and py is not None:
                    resolved_points.append((px, py))
            el.points = resolved_points

        # Recurse into children
        el.children = [self._resolve_element(child) for child in el.children]

        return el

    def _resolve_position(self, pos: Position) -> Position:
        pos.x = self._resolve_value_field(pos.x)  # type: ignore[arg-type]
        pos.y = self._resolve_value_field(pos.y)  # type: ignore[arg-type]
        pos.gap = self._resolve_value_field(pos.gap)  # type: ignore[arg-type]
        return pos

    def _resolve_value_field(self, field: object) -> Value | None:
        """Resolve a field that may be Value, Expr, or None."""
        if field is None:
            return None
        if isinstance(field, Expr):
            return self._eval_expr(field)
        if isinstance(field, Value):
            return field
        return None

    def _eval_expr(self, expr: Expr | Value) -> Value:
        """Evaluate an expression to a concrete Value."""
        if isinstance(expr, Value):
            return expr
        if isinstance(expr, LiteralExpr):
            return expr.value
        if isinstance(expr, VarRefExpr):
            val = self.variables.get(expr.name)
            if val is None:
                raise ResolveError(f"Undefined variable '{expr.name}'")
            return val
        if isinstance(expr, UnaryExpr):
            operand = self._eval_expr(expr.operand)
            return Value(number=-operand.number, unit=operand.unit)
        if isinstance(expr, BinaryExpr):
            left = self._eval_expr(expr.left)
            right = self._eval_expr(expr.right)
            return self._eval_binary(expr.op, left, right)
        raise ResolveError(f"Unknown expression type: {type(expr)}")

    def _eval_binary(self, op: str, left: Value, right: Value) -> Value:
        if op == "+":
            unit = self._check_additive_units(left, right)
            return Value(number=left.number + right.number, unit=unit)
        elif op == "-":
            unit = self._check_additive_units(left, right)
            return Value(number=left.number - right.number, unit=unit)
        elif op == "*":
            unit = self._check_multiplicative_units(left, right)
            return Value(number=left.number * right.number, unit=unit)
        elif op == "/":
            if right.number == 0:
                raise ResolveError("Division by zero")
            unit = self._check_multiplicative_units(left, right)
            return Value(number=left.number / right.number, unit=unit)
        raise ResolveError(f"Unknown operator: {op}")

    def _check_additive_units(self, left: Value, right: Value) -> str | None:
        """For +/-, both must have same unit or one must be unitless."""
        if left.unit is None and right.unit is None:
            return None
        if left.unit is None:
            return right.unit
        if right.unit is None:
            return left.unit
        if left.unit == right.unit:
            return left.unit
        raise ResolveError(
            f"Cannot add/subtract values with different units: "
            f"'{left.unit}' and '{right.unit}'"
        )

    def _check_multiplicative_units(self, left: Value, right: Value) -> str | None:
        """For *///, one side must be unitless (scalar)."""
        if left.unit is None and right.unit is None:
            return None
        if left.unit is None:
            return right.unit
        if right.unit is None:
            return left.unit
        raise ResolveError(
            f"Cannot multiply/divide values with units on both sides: "
            f"'{left.unit}' and '{right.unit}'"
        )

    def _resolve_color_string(self, color: str) -> str:
        """Resolve a color string, handling $color:name references."""
        if color.startswith("$color:"):
            var_name = color[7:]
            resolved = self.color_vars.get(var_name)
            if resolved is not None:
                return resolved
            # Fall back to regular color resolution
            css = resolve_color(var_name)
            if css:
                return css
            raise ResolveError(f"Undefined color variable '{var_name}'")
        return color


def resolve(doc: Document) -> Document:
    """Resolve all v2 constructs in a Document."""
    resolver = Resolver()
    return resolver.resolve(doc)
