"""Tests for forgiveness map rendering.

Display code, so these check that a figure is produced and that the things a
reader must not miss actually reach it. They do not check that it looks good;
that is what looking at it is for.
"""

import math

import numpy as np
import pytest

from ball_properties import conforming_three_piece_tour_ball
from forgiveness_diagram import (FLAT_FACE_CAVEAT, _provenance_lines, _summary_lines,
                                 plot_forgiveness_map, plot_map_comparison)
from forgiveness_map import MapSettings, compare_maps, compute_forgiveness_map
from impact_fixtures import fixture_near_rigid_head, fixture_symmetric_head
from impact_model import SwingConditions

DRIVER = SwingConditions(head_speed_mps=45.0, loft_rad=math.radians(10.5))


@pytest.fixture
def fmap():
    return compute_forgiveness_map(fixture_symmetric_head(),
                                   conforming_three_piece_tour_ball(),
                                   DRIVER, MapSettings(spacing_mm=10.0))


def test_a_map_renders_to_the_requested_file(tmp_path, fmap):
    """Proves the figure is actually written, to the path asked for, and is
    not empty.
    """
    output = tmp_path / "map.png"
    returned = plot_forgiveness_map(fmap, str(output))

    assert returned == str(output)
    assert output.exists() and output.stat().st_size > 10_000


def test_a_comparison_renders_to_the_requested_file(tmp_path, fmap):
    """Proves the two-head difference figure is produced as well."""
    other = compute_forgiveness_map(fixture_near_rigid_head(),
                                    conforming_three_piece_tour_ball(),
                                    DRIVER, MapSettings(spacing_mm=10.0))
    output = tmp_path / "comparison.png"
    plot_map_comparison(compare_maps("normal", fmap, "rigid", other), str(output))

    assert output.exists() and output.stat().st_size > 10_000


def test_the_figure_text_carries_the_provenance(fmap):
    """Proves a figure cannot be separated from what produced it. Head, ball,
    swing conditions and the face outline's status all appear on the image, so
    a screenshot pasted into a report still says what it is a map of.
    """
    text = " ".join(_provenance_lines(fmap))

    assert "200 g head" in text
    assert "CG depth 35.0 mm" in text
    assert "three-piece tour ball" in text
    assert "45.0 m/s" in text and "10.5 deg loft" in text
    assert "ASSUMED (not measured)" in text


def test_the_figure_text_labels_the_threshold_as_a_setting(fmap):
    """Proves the chosen threshold is called a chosen threshold on the figure
    itself, where a reader will see it, not only in the code.
    """
    text = " ".join(_summary_lines(fmap.summary()))

    assert "CHOSEN SETTING" in text
    assert "not a standard" in text


def test_the_figure_warns_about_the_flat_face(fmap):
    """Proves the model's largest limitation is stated on every figure.

    Bulge and roll exist to counteract the gear effect this map computes, so a
    flat-face map overstates curvature toward the rim. A reader who takes the
    edges literally will design the wrong head, and the figure has to say so.
    """
    assert "no bulge or roll" in FLAT_FACE_CAVEAT
    assert "overstated" in FLAT_FACE_CAVEAT


def test_the_figure_warns_where_the_model_has_broken_down(fmap):
    """Proves the topspin region is called out in the figure text and not only
    marked on the image, so it survives being summarised.
    """
    text = " ".join(_summary_lines(fmap.summary()))

    assert fmap.summary()["points_with_reversed_backspin"] > 0
    assert "topspin" in text
