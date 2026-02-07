"""Transform Lark parse tree into StagScribe AST nodes."""

from __future__ import annotations

from lark import Token, Transformer, Tree

from stagscribe.language.ast_nodes import (
    BinaryExpr,
    ColorAssignment,
    ColorsBlock,
    DefineBlock,
    Document,
    Element,
    Expr,
    IsStatement,
    LiteralExpr,
    PlaceStatement,
    Position,
    Statement,
    StrokeStyle,
    TextStyle,
    UnaryExpr,
    Value,
    VarRefExpr,
)
from stagscribe.language.colors import resolve_color


class StagTransformer(Transformer):  # type: ignore[type-arg]
    """Transforms a Lark parse tree into a StagScribe AST Document."""

    def start(self, items: list) -> Document:  # type: ignore[type-arg]
        statements: list[Statement] = [
            item
            for item in items
            if isinstance(
                item,
                (Element, IsStatement, ColorsBlock, DefineBlock, PlaceStatement),
            )
        ]
        return Document(statements=statements)

    def element_stmt(self, items: list) -> Element:  # type: ignore[type-arg]
        element_type = str(items[0])
        name = None
        props: dict = {}  # type: ignore[type-arg]
        children: list[Element] = []

        for item in items[1:]:
            if item is None:
                continue
            if isinstance(item, str) and not isinstance(item, Element):
                name = item
            elif isinstance(item, dict):
                props.update(item)
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, Element):
                        children.append(sub)
                    elif isinstance(sub, dict):
                        props.update(sub)
            elif isinstance(item, Element):
                children.append(item)

        el = Element(element_type=element_type, name=name, children=children)
        _apply_props(el, props)
        return el

    def element_type(self, items: list) -> str:  # type: ignore[type-arg]
        return str(items[0])

    def element_name(self, items: list) -> str:  # type: ignore[type-arg]
        return str(items[0]).strip('"')

    def body(self, items: list) -> list:  # type: ignore[type-arg]
        return list(items)

    def property_line(self, items: list) -> dict:  # type: ignore[type-arg]
        # Single property per line — just return the dict from the prop_pair
        for item in items:
            if isinstance(item, dict):
                return item
        return {}

    # --- Is statement ---
    def is_stmt(self, items: list) -> IsStatement:  # type: ignore[type-arg]
        name = str(items[0])
        expr = items[1]
        return IsStatement(name=name, expr=expr)

    # --- Colors block ---
    def colors_block(self, items: list) -> ColorsBlock:  # type: ignore[type-arg]
        assignments = [i for i in items if isinstance(i, ColorAssignment)]
        return ColorsBlock(assignments=assignments)

    def color_assignment(self, items: list) -> ColorAssignment:  # type: ignore[type-arg]
        name = str(items[0])
        color = items[1]
        is_var = isinstance(color, VarRefExpr)
        if is_var:
            return ColorAssignment(name=name, color=color.name, is_var_ref=True)
        return ColorAssignment(name=name, color=str(color))

    # --- Define block ---
    def define_block(self, items: list) -> DefineBlock:  # type: ignore[type-arg]
        name = str(items[0])
        body_items = items[1] if isinstance(items[1], list) else []
        elements = [i for i in body_items if isinstance(i, Element)]
        return DefineBlock(name=name, body_elements=elements)

    # --- Place statement ---
    def place_stmt(self, items: list) -> PlaceStatement:  # type: ignore[type-arg]
        template_name = str(items[0])
        instance_name = None
        props: dict = {}  # type: ignore[type-arg]

        for item in items[1:]:
            if item is None:
                continue
            if isinstance(item, str):
                instance_name = item
            elif isinstance(item, dict):
                props.update(item)
            elif isinstance(item, list):
                # body block returns a list of dicts/elements
                for sub in item:
                    if isinstance(sub, dict):
                        props.update(sub)

        position = props.pop("position", None)
        scale = props.pop("scale", None)
        rotate_expr = props.pop("rotate", None)

        return PlaceStatement(
            template_name=template_name,
            instance_name=instance_name,
            props=props,
            position=position,
            scale=scale,
            rotate_expr=rotate_expr,
        )

    # --- Size by (e.g. "800 by 600") ---
    def size_by_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        w = items[0]
        h = items[1]
        return {"width": w, "height": h}

    # --- Dimension properties ---
    def dimension_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        keyword = str(items[0])
        val = items[1]
        return {keyword: val}

    # --- Fill ---
    def fill_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"fill": _resolve_color_item(items[0])}

    # --- Stroke ---
    def stroke_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        color = _resolve_color_item(items[0])
        width = items[1] if len(items) > 1 else None
        return {"stroke": StrokeStyle(color=color, width=width)}

    # --- Background ---
    def background_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"background": _resolve_color_item(items[0])}

    # --- Opacity ---
    def opacity_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        val = items[0]
        if isinstance(val, Value):
            return {"opacity": val.number}
        return {"opacity": val}

    # --- Rounded ---
    def rounded_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"rounded": items[0]}

    # --- Rotate ---
    def rotate_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        val = items[0]
        if isinstance(val, Value):
            return {"rotate": val.number}
        return {"rotate": val}

    # --- Scale ---
    def scale_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"scale": items[0]}

    # --- Radius ---
    def radius_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"radius": items[0]}

    # --- Font ---
    def font_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"font": str(items[0]).strip('"')}

    # --- Dashed/dotted ---
    def dashed_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"dash": str(items[0])}

    # --- Path data ---
    def path_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"path_data": str(items[0]).strip('"')}

    # --- Image source ---
    def src_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"src": str(items[-1]).strip('"')}

    # --- Points ---
    def points_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"points": list(items)}

    def point(self, items: list) -> tuple[Value, Value]:  # type: ignore[type-arg]
        x = items[0]
        y = items[1]
        if isinstance(x, Value):
            xv = x
        else:
            xv = Value(number=float(x))
        if isinstance(y, Value):
            yv = y
        else:
            yv = Value(number=float(y))
        return (xv, yv)

    # --- Line endpoints ---
    def line_endpoint_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        keyword = str(items[0])
        x = items[1]
        y = items[2]
        if keyword == "from":
            return {"line_from": (x, y)}
        return {"line_to": (x, y)}

    # --- Position ---
    def at_position(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"position": items[0]}

    def anchor_position(self, items: list) -> Position:  # type: ignore[type-arg]
        anchor = str(items[0])
        ref_name = None
        for item in items[1:]:
            if isinstance(item, str):
                ref_name = item
        return Position(anchor=anchor, reference=ref_name)

    def of_ref(self, items: list) -> str:  # type: ignore[type-arg]
        return str(items[0]).strip('"')

    def coord_position(self, items: list) -> Position:
        return Position(x=items[0], y=items[1])

    def relative_position(self, items: list) -> dict:  # type: ignore[type-arg]
        rel_type = str(items[0])
        ref_name = str(items[1]).strip('"')
        anchor = None
        gap = None
        for item in items[2:]:
            if isinstance(item, str):
                anchor = item
            elif isinstance(item, (Value, Expr)):
                gap = item
        pos = Position(
            relative=rel_type, reference=ref_name, ref_anchor=anchor,
            gap=gap,  # type: ignore[arg-type]
        )
        return {"position": pos}

    def relative_anchor(self, items: list) -> str:  # type: ignore[type-arg]
        return str(items[0])

    def gap_clause(self, items: list) -> Value:  # type: ignore[type-arg]
        return items[0]  # type: ignore[no-any-return]

    # --- Text style ---
    def size_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"text_size": items[0]}

    def color_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"text_color": _resolve_color_item(items[0])}

    def weight_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"text_weight": str(items[0])}

    def italic_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"text_style": "italic"}

    def align_prop(self, items: list) -> dict:  # type: ignore[type-arg]
        return {"text_align": str(items[0])}

    # --- Expression nodes ---
    def expr_add(self, items: list) -> BinaryExpr:  # type: ignore[type-arg]
        return BinaryExpr(op="+", left=_to_expr(items[0]), right=_to_expr(items[1]))

    def expr_sub(self, items: list) -> BinaryExpr:  # type: ignore[type-arg]
        return BinaryExpr(op="-", left=_to_expr(items[0]), right=_to_expr(items[1]))

    def expr_mul(self, items: list) -> BinaryExpr:  # type: ignore[type-arg]
        return BinaryExpr(op="*", left=_to_expr(items[0]), right=_to_expr(items[1]))

    def expr_div(self, items: list) -> BinaryExpr:  # type: ignore[type-arg]
        return BinaryExpr(op="/", left=_to_expr(items[0]), right=_to_expr(items[1]))

    def expr_neg(self, items: list) -> UnaryExpr:  # type: ignore[type-arg]
        return UnaryExpr(operand=_to_expr(items[0]))

    def var_ref(self, items: list) -> VarRefExpr:  # type: ignore[type-arg]
        return VarRefExpr(name=str(items[0]))

    def color_var_ref(self, items: list) -> VarRefExpr:  # type: ignore[type-arg]
        return VarRefExpr(name=str(items[0]))

    def paren_expr(self, items: list) -> Expr:  # type: ignore[type-arg]
        return items[0]  # type: ignore[no-any-return]

    # --- Values (atom expressions) ---
    def unit_value(self, items: list) -> Value:  # type: ignore[type-arg]
        return Value(number=float(items[0]), unit=str(items[1]))

    def by_value(self, items: list) -> dict:  # type: ignore[type-arg]
        unit = str(items[2]) if len(items) > 2 else None
        return {
            "width": Value(number=float(items[0]), unit=unit),
            "height": Value(number=float(items[1]), unit=unit),
        }

    def percent_value(self, items: list) -> Value:  # type: ignore[type-arg]
        return Value(number=float(items[0]), unit="%")

    def bare_number(self, items: list) -> Value:  # type: ignore[type-arg]
        return Value(number=float(items[0]))

    def natural_value(self, items: list) -> Value:  # type: ignore[type-arg]
        return Value(number=float(items[0]), unit=str(items[1]))

    def natural_bare(self, items: list) -> Value:  # type: ignore[type-arg]
        return Value(number=1.0, unit=str(items[0]))

    # --- Colors ---
    def rgb_color(self, items: list) -> str:  # type: ignore[type-arg]
        return f"rgb({items[0]},{items[1]},{items[2]})"

    # --- Comment ---
    def comment(self, items: list) -> None:  # type: ignore[type-arg]
        return None


def _to_expr(item: object) -> Expr:
    """Convert a Value or Expr to an Expr node."""
    if isinstance(item, Expr):
        return item
    if isinstance(item, Value):
        return LiteralExpr(value=item)
    raise TypeError(f"Cannot convert {type(item)} to Expr")


def _resolve_color_item(item: object) -> str:
    """Resolve a color token or tree into a color string."""
    if isinstance(item, VarRefExpr):
        # Color variable reference — keep as special marker for resolver
        return f"$color:{item.name}"
    if isinstance(item, Token):
        text = str(item)
        resolved = resolve_color(text)
        return resolved if resolved else text
    if isinstance(item, Tree):
        # For rgb_color etc
        return str(item)
    return str(item)


def _apply_props(el: Element, props: dict) -> None:  # type: ignore[type-arg]
    """Apply parsed properties to an Element."""
    for key, val in props.items():
        if key == "width":
            el.width = val
        elif key == "height":
            el.height = val
        elif key == "fill":
            el.fill = val
        elif key == "stroke":
            el.stroke = val
        elif key == "background":
            el.background = val
        elif key == "opacity":
            el.opacity = val
        elif key == "rounded":
            el.rounded = val
        elif key == "rotate":
            el.rotate = val
        elif key == "radius":
            el.radius = val
        elif key == "position":
            el.position = val
        elif key == "text_size":
            if el.text_style is None:
                el.text_style = TextStyle()
            el.text_style.size = val
        elif key == "text_color":
            if el.text_style is None:
                el.text_style = TextStyle()
            el.text_style.color = val
        elif key == "text_weight":
            if el.text_style is None:
                el.text_style = TextStyle()
            el.text_style.weight = val
        elif key == "text_style":
            if el.text_style is None:
                el.text_style = TextStyle()
            el.text_style.style = val
        elif key == "text_align":
            if el.text_style is None:
                el.text_style = TextStyle()
            el.text_style.align = val
        elif key == "font":
            if el.text_style is None:
                el.text_style = TextStyle()
            el.text_style.font = val
        elif key == "dash":
            if el.stroke is None:
                el.stroke = StrokeStyle()
            el.stroke.dash = val
        elif key == "line_from":
            el.line_from = val
        elif key == "line_to":
            el.line_to = val
        elif key == "points":
            el.points = val
        elif key == "path_data":
            el.path_data = val
        elif key == "src":
            el.src = val
