"""Tests for gear element and gradient fill features."""

from __future__ import annotations

import math

import pytest

from stagscribe.converter.converter import convert
from stagscribe.converter.layout import resolve_layout
from stagscribe.converter.shapes import _gear_path_data
from stagscribe.language.ast_nodes import GradientFill
from stagscribe.parser.parser import parse
from stagscribe.resolver import resolve


# --- Gradient fill tests ---


def test_gradient_fill_parsed():
    """Gradient fill syntax produces GradientFill on the element."""
    doc = parse(
        'canvas 400 by 300 pixels\n'
        '  background white\n'
        'rect "Box" 100 by 50\n'
        '  fill gradient silver to gray\n'
        '  at center\n'
    )
    doc = resolve(doc)
    el = doc.elements[1]
    assert el.gradient is not None
    assert el.gradient.color1 == "#C0C0C0"  # silver resolved
    assert el.gradient.color2 == "#808080"  # gray resolved
    assert el.fill is None  # solid fill should be None


def test_gradient_in_svg_output():
    """Gradient fill creates linearGradient defs and url() fill."""
    svg, _ = convert(
        'canvas 400 by 300 pixels\n'
        '  background white\n'
        'rect "Box" 100 by 50\n'
        '  fill gradient silver to gray\n'
        '  at center\n'
    )
    assert "<linearGradient" in svg
    assert 'stop-color' in svg
    assert 'url(#grad_0)' in svg


def test_solid_fill_unchanged():
    """Solid fill still works normally alongside gradient support."""
    svg, _ = convert(
        'canvas 400 by 300 pixels\n'
        '  background white\n'
        'rect "Box" 100 by 50\n'
        '  fill red\n'
        '  at center\n'
    )
    assert "<linearGradient" not in svg
    assert 'fill="#FF0000"' in svg  # red resolved to hex


# --- Gear element tests ---


def test_gear_parsed():
    """Gear element with teeth and module is parsed correctly."""
    doc = parse(
        'canvas 400 by 300 pixels\n'
        '  background white\n'
        'gear "G1"\n'
        '  teeth 12\n'
        '  module 10\n'
        '  fill gray\n'
        '  at center\n'
    )
    doc = resolve(doc)
    el = doc.elements[1]
    assert el.element_type == "gear"
    assert el.teeth == 12
    assert el.tooth_module == 10.0


def test_gear_sizing():
    """Gear dimensions computed from teeth and module."""
    doc = parse(
        'canvas 600 by 400 pixels\n'
        '  background white\n'
        'gear "G1"\n'
        '  teeth 12\n'
        '  module 10\n'
        '  fill gray\n'
        '  at center\n'
    )
    doc = resolve(doc)
    boxes = resolve_layout(doc)
    box = boxes["G1"]
    # outer_r = module * teeth / 2 + module = 10*12/2 + 10 = 70
    assert box.width == pytest.approx(140.0)
    assert box.height == pytest.approx(140.0)


def test_gear_in_svg():
    """Gear renders as an SVG path element."""
    svg, _ = convert(
        'canvas 400 by 300 pixels\n'
        '  background white\n'
        'gear "G1"\n'
        '  teeth 8\n'
        '  module 10\n'
        '  fill gray\n'
        '  at center\n'
    )
    assert "<path" in svg
    assert 'fill="#808080"' in svg


# --- Mesh positioning tests ---


def test_mesh_positioning():
    """Driven gear is positioned at correct center distance from drive gear."""
    doc = parse(
        'canvas 800 by 400 pixels\n'
        '  background white\n'
        'gear "G1"\n'
        '  teeth 12\n'
        '  module 10\n'
        '  fill gray\n'
        '  at 200 200\n'
        'gear "G2"\n'
        '  teeth 18\n'
        '  module 10\n'
        '  fill gray\n'
        '  mesh with "G1"\n'
    )
    doc = resolve(doc)
    boxes = resolve_layout(doc)

    g1 = boxes["G1"]
    g2 = boxes["G2"]

    # G1 center
    g1_cx = g1.x + g1.width / 2
    g1_cy = g1.y + g1.height / 2
    # G2 center
    g2_cx = g2.x + g2.width / 2
    g2_cy = g2.y + g2.height / 2

    # Center distance should be pitch_r1 + pitch_r2
    pitch_r1 = 10 * 12 / 2  # 60
    pitch_r2 = 10 * 18 / 2  # 90
    expected_dist = pitch_r1 + pitch_r2  # 150

    actual_dist = math.sqrt((g2_cx - g1_cx) ** 2 + (g2_cy - g1_cy) ** 2)
    assert actual_dist == pytest.approx(expected_dist, abs=0.1)


def test_mesh_rotation():
    """Driven gear has correct rotation offset for tooth interleaving."""
    doc = parse(
        'canvas 800 by 400 pixels\n'
        '  background white\n'
        'gear "G1"\n'
        '  teeth 12\n'
        '  module 10\n'
        '  fill gray\n'
        '  at center\n'
        'gear "G2"\n'
        '  teeth 18\n'
        '  module 10\n'
        '  fill gray\n'
        '  mesh with "G1"\n'
    )
    doc = resolve(doc)
    boxes = resolve_layout(doc)

    # Drive gear has 0 rotation
    assert boxes["G1"].rotation == pytest.approx(0.0)
    # Driven gear rotation: 180 * (18-1)/18 = 170 degrees
    assert boxes["G2"].rotation == pytest.approx(170.0)


# --- Gear path generation tests ---


def test_gear_path_data_returns_closed_path():
    """Gear path data starts with M and ends with Z."""
    d = _gear_path_data(100, 100, 8, 10)
    assert d.startswith("M ")
    assert d.endswith("Z")


def test_gear_path_data_has_correct_elements():
    """Gear path contains arcs and lines for each tooth."""
    d = _gear_path_data(100, 100, 6, 10)
    # 6 teeth × 3 arcs each (root-to-base, tip, base-to-root) = 18
    assert d.count(" A ") == 18
    # 6 teeth × 4 flank lines (root→pitch, pitch→tip, tip→pitch, pitch→root)
    assert d.count(" L ") >= 24


# --- Gradient + gear combo test ---


def test_gear_with_gradient():
    """Gear with gradient fill renders correctly."""
    svg, _ = convert(
        'canvas 400 by 300 pixels\n'
        '  background white\n'
        'gear "G1"\n'
        '  teeth 10\n'
        '  module 8\n'
        '  fill gradient silver to dark gray\n'
        '  at center\n'
    )
    assert "<linearGradient" in svg
    assert "<path" in svg
    assert 'url(#grad_0)' in svg
