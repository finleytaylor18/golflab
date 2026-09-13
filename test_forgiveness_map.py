"""Tests for the forgiveness sweep.

The physics is already tested in test_impact_model.py. These tests check the
things a SWEEP can get wrong that a single impact cannot: grid alignment,
masking, the baseline it normalises against, the area metric, and the flags
that tell a reader where the model has stopped being trustworthy.
"""

import math

import numpy as np
import pytest

from ball_properties import BALL_FRICTION_TWO_PIECE, BallProperties, conforming_three_piece_tour_ball
from head_mass_properties import FaceGeometry, HeadMassProperties
from impact_fixtures import fixture_near_rigid_head, fixture_offset_cg_head, fixture_symmetric_head
from impact_model import SwingConditions
from forgiveness_map import (DEFAULT_RETENTION_THRESHOLD_PCT, MapSettings,
                             compare_maps, compute_forgiveness_map)

DRIVER = SwingConditions(head_speed_mps=45.0, loft_rad=math.radians(10.5))


@pytest.fixture
def ball():
    return conforming_three_piece_tour_ball()


@pytest.fixture
def coarse():
    return MapSettings(spacing_mm=5.0)


# ---------------------------------------------------------------------------
# GRID AND MASKING
# ---------------------------------------------------------------------------

def test_the_face_centre_is_always_a_grid_point(ball, coarse):
    """Proves the two reference points a map is read against are exact, not
    interpolated. Zero must fall on the grid in both axes, whatever spacing
    is chosen, or the face centre would be a blur between four cells.
    """
    for spacing in (1.0, 2.0, 2.5, 7.0):
        fmap = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER,
                                       MapSettings(spacing_mm=spacing))
        assert 0.0 in fmap.x_mm
        assert 0.0 in fmap.y_mm


def test_points_outside_the_outline_are_masked_not_solved(ball, coarse):
    """Proves the map covers the FACE, not its bounding box. The corners of an
    elliptical face are not struck by anything and must be blank, otherwise
    the area metric would count face that does not exist.
    """
    fmap = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, coarse)
    corner_row, corner_column = 0, 0

    assert not fmap.on_face[corner_row, corner_column]
    assert math.isnan(fmap.speed_retention_pct[corner_row, corner_column])
    assert np.all(np.isnan(fmap.backspin_rpm[~fmap.on_face]))


def test_an_elliptical_face_has_less_area_than_a_rectangular_one(ball, coarse):
    """Proves the outline shape genuinely changes the answer, by the factor
    4/pi that it should. This is why the ellipse is the default: a rectangle
    would inflate every reported area by about 27%.
    """
    half_width, half_height = 0.050, 0.030
    tensor = np.diag([3.0e-4, 5.0e-4, 4.0e-4])
    ellipse = HeadMassProperties(0.200, np.array([0.0, 0.0, -0.035]), tensor,
                                 FaceGeometry(half_width, half_height, shape="ellipse"))
    rectangle = HeadMassProperties(0.200, np.array([0.0, 0.0, -0.035]), tensor,
                                   FaceGeometry(half_width, half_height, shape="rectangle"))

    assert ellipse.face.area_m2 / rectangle.face.area_m2 == pytest.approx(math.pi / 4.0, rel=1e-12)

    swept_ellipse = compute_forgiveness_map(ellipse, ball, DRIVER, coarse).face_area_mm2()
    swept_rectangle = compute_forgiveness_map(rectangle, ball, DRIVER, coarse).face_area_mm2()
    assert swept_ellipse < swept_rectangle


def test_a_finer_grid_does_not_move_the_physics(ball):
    """Proves grid spacing changes only the RESOLUTION, not the results. The
    retention at a given strike must be the same number however finely the
    face was swept -- otherwise the map would be an artefact of the sweep.
    """
    fine = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER,
                                   MapSettings(spacing_mm=2.0))
    coarse = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER,
                                     MapSettings(spacing_mm=10.0))

    for x, y in ((0.0, 0.0), (20.0, 10.0), (-30.0, -20.0)):
        fine_value = fine.speed_retention_pct[np.where(fine.y_mm == y)[0][0],
                                              np.where(fine.x_mm == x)[0][0]]
        coarse_value = coarse.speed_retention_pct[np.where(coarse.y_mm == y)[0][0],
                                                  np.where(coarse.x_mm == x)[0][0]]
        assert fine_value == pytest.approx(coarse_value, rel=1e-12)


# ---------------------------------------------------------------------------
# THE BASELINE
# ---------------------------------------------------------------------------

def test_retention_peaks_at_one_hundred_percent_at_the_sweet_spot(ball, coarse):
    """Proves the map is normalised against the right point. The sweet spot is
    the fastest strike available, so nothing on the face may exceed 100%.
    """
    fmap = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, coarse)
    on_face = fmap.speed_retention_pct[fmap.on_face]

    assert np.nanmax(on_face) == pytest.approx(100.0, rel=1e-9)
    assert np.all(on_face <= 100.0 + 1e-9)


def test_the_baseline_follows_an_off_centre_cg(ball, coarse):
    """Proves the baseline is solved at the sweet spot, not read off the grid.

    On a head whose CG is offset, the sweet spot need not land on a grid
    point at all -- so taking the grid maximum as the baseline would quietly
    understate the loss everywhere. Here the 100% point sits where the CG
    projects, not at the face centre.
    """
    head = fixture_offset_cg_head()
    fmap = compute_forgiveness_map(head, ball, DRIVER, MapSettings(spacing_mm=1.0))

    assert fmap.sweet_spot_mm[0] == pytest.approx(4.0, abs=1e-9)
    assert fmap.sweet_spot_mm[1] == pytest.approx(2.0, abs=1e-9)

    best_row, best_column = np.unravel_index(
        np.nanargmax(np.where(fmap.on_face, fmap.speed_retention_pct, -np.inf)),
        fmap.speed_retention_pct.shape)
    assert fmap.x_mm[best_column] == pytest.approx(4.0, abs=1.0)
    assert fmap.y_mm[best_row] == pytest.approx(2.0, abs=1.0)

    centre_value = fmap.speed_retention_pct[np.where(fmap.y_mm == 0.0)[0][0],
                                            np.where(fmap.x_mm == 0.0)[0][0]]
    assert centre_value < 100.0


# ---------------------------------------------------------------------------
# THE SUMMARY METRIC
# ---------------------------------------------------------------------------

def test_a_stiffer_head_has_a_larger_forgiving_area(ball, coarse):
    """Proves the summary number measures what it claims to. A head that
    resists twisting keeps its ball speed across more of the face, so the
    forgiving area must grow -- and for a near-rigid head it covers all of it.
    """
    normal = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, coarse)
    rigid = compute_forgiveness_map(fixture_near_rigid_head(), ball, DRIVER, coarse)

    assert rigid.forgiving_area_mm2() > normal.forgiving_area_mm2()
    assert rigid.forgiving_area_fraction() == pytest.approx(1.0, rel=1e-9)


def test_a_lower_threshold_never_shrinks_the_forgiving_area(ball, coarse):
    """Proves the metric is monotonic in its own setting, so two maps quoted
    at different thresholds can never be compared by accident and come out
    backwards.
    """
    fmap = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, coarse)
    areas = [fmap.forgiving_area_mm2(t) for t in (100.0, 99.0, 97.0, 95.0, 90.0, 50.0)]

    assert all(a <= b for a, b in zip(areas, areas[1:]))
    assert areas[-1] == pytest.approx(fmap.face_area_mm2(), rel=1e-12)


def test_the_threshold_is_reported_as_a_setting_not_a_standard(ball, coarse):
    """Proves the one invented number in the sweep announces itself.

    No source read for this project defines a "forgiveness area", so the
    threshold is a choice. Standing rule 3 means it has to travel with the
    result that depends on it rather than sit in a default somewhere.
    """
    fmap = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, coarse)
    summary = fmap.summary()

    assert summary["threshold_is_a_chosen_setting"] is True
    assert summary["threshold_pct"] == DEFAULT_RETENTION_THRESHOLD_PCT

    custom = MapSettings(spacing_mm=5.0, retention_threshold_pct=90.0)
    other = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, custom)
    assert other.summary()["threshold_pct"] == 90.0
    assert other.forgiving_area_mm2() > fmap.forgiving_area_mm2()


def test_impossible_settings_are_refused():
    """Proves the sweep's own inputs are validated at the boundary too."""
    with pytest.raises(ValueError, match="spacing_mm"):
        MapSettings(spacing_mm=0.0)
    with pytest.raises(ValueError, match="retention_threshold_pct"):
        MapSettings(retention_threshold_pct=120.0)


# ---------------------------------------------------------------------------
# FLAGS: WHERE THE MODEL STOPS BEING TRUSTWORTHY
# ---------------------------------------------------------------------------

def test_grid_points_needing_more_friction_than_sourced_are_flagged(ball, coarse):
    """Proves the map says where it is extrapolating.

    With a soft tour cover on a driver nothing slides. Put a hard two-piece
    cover on a 50 degree wedge and the no-slip solution demands more friction
    than the sourced coefficient provides -- and every such point is flagged
    rather than quietly plotted as if it were solved.
    """
    driver_map = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, coarse)
    assert not np.any(driver_map.exceeds_friction)
    assert driver_map.summary()["points_needing_more_friction"] == 0

    two_piece = BallProperties(ball.mass_kg, ball.radius_m, ball.cor,
                               BALL_FRICTION_TWO_PIECE, description="fixture: two-piece")
    wedge = SwingConditions(head_speed_mps=30.0, loft_rad=math.radians(50.0))
    wedge_map = compute_forgiveness_map(fixture_symmetric_head(), two_piece, wedge, coarse)

    assert np.any(wedge_map.exceeds_friction)
    assert wedge_map.summary()["points_needing_more_friction"] > 0
    assert np.all(wedge_map.required_friction[wedge_map.exceeds_friction]
                  > two_piece.friction_coefficient)


def test_topspin_points_are_flagged_and_their_spin_axis_left_undefined(ball, coarse):
    """Proves the map refuses to report a meaningless angle.

    High on a flat face the vertical gear effect can overcome the loft
    entirely and leave the ball with topspin. "Spin axis tilt" then wraps past
    90 degrees and stops meaning what a reader thinks it means, so those
    points carry NaN and a flag instead. A real driver's roll would probably
    prevent this happening at all -- which is the point of the flag.
    """
    fmap = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, coarse)

    assert np.any(fmap.backspin_reversed)
    assert np.all(fmap.backspin_rpm[fmap.backspin_reversed] <= 0.0)
    assert np.all(np.isnan(fmap.spin_axis_deg[fmap.backspin_reversed]))
    assert np.all(np.isfinite(
        fmap.spin_axis_deg[fmap.on_face & ~fmap.backspin_reversed]))


def test_the_face_outline_is_labelled_as_assumed_until_it_is_measured(ball, coarse):
    """Proves an assumed outline cannot be mistaken for a measured one. The
    area metric is only as good as the outline it was computed on, so the
    provenance has to travel with it onto the figure.
    """
    fmap = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, coarse)
    assert "ASSUMED" in fmap.face_description

    measured = fixture_symmetric_head()
    measured.face = FaceGeometry(0.050, 0.030, outline_source="measured")
    described = compute_forgiveness_map(measured, ball, DRIVER, coarse).face_description
    assert "measured" in described and "ASSUMED" not in described


# ---------------------------------------------------------------------------
# SYMMETRY AND COMPARISON
# ---------------------------------------------------------------------------

def test_the_map_of_a_symmetric_head_is_left_right_symmetric(ball, coarse):
    """Proves the sweep introduces no bias of its own. The single-impact
    symmetry test already proved the physics; this proves the grid, the
    masking and the array indexing preserve it.
    """
    fmap = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, coarse)
    mirrored = fmap.speed_retention_pct[:, ::-1]

    assert np.allclose(fmap.speed_retention_pct, mirrored, equal_nan=True)
    assert np.allclose(fmap.sidespin_rpm, -fmap.sidespin_rpm[:, ::-1], equal_nan=True)
    assert np.allclose(fmap.backspin_rpm, fmap.backspin_rpm[:, ::-1], equal_nan=True)


def test_a_comparison_subtracts_b_minus_a_in_the_projects_direction(ball, coarse):
    """Proves the delta sign matches `club_comparison.py`, where
    `moi_delta = moi_b - moi_a`. A difference map with the sign reversed would
    recommend exactly the wrong head, and nothing on the figure would look
    wrong.
    """
    normal = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, coarse)
    rigid = compute_forgiveness_map(fixture_near_rigid_head(), ball, DRIVER, coarse)
    comparison = compare_maps("normal", normal, "rigid", rigid)

    on_face = comparison.on_face
    assert np.all(comparison.delta_speed_retention_pct[on_face] >= -1e-9)
    assert np.nanmax(comparison.delta_speed_retention_pct[on_face]) > 1.0

    reversed_comparison = compare_maps("rigid", rigid, "normal", normal)
    assert np.allclose(reversed_comparison.delta_speed_retention_pct[on_face],
                       -comparison.delta_speed_retention_pct[on_face])


def test_a_head_compared_with_itself_is_flat_zero(ball, coarse):
    """Proves the subtraction has no drift in it: identical inputs must give
    an exactly blank difference map, not a faint pattern of rounding.
    """
    fmap = compute_forgiveness_map(fixture_symmetric_head(), ball, DRIVER, coarse)
    comparison = compare_maps("same", fmap, "same", fmap)

    assert np.all(comparison.delta_speed_retention_pct[comparison.on_face] == 0.0)
    assert np.all(comparison.delta_backspin_rpm[comparison.on_face] == 0.0)


def test_maps_on_different_grids_refuse_to_be_compared(ball):
    """Proves the comparison will not silently interpolate. Two heads with
    different face sizes are not comparable point by point, and a map that
    pretended otherwise would be worse than no map -- so this fails loudly.
    """
    small = fixture_symmetric_head()
    large = HeadMassProperties.from_industry_units(
        200.0, (0.0, 0.0, -35.0), np.diag([3000.0, 5000.0, 4000.0]),
        face_half_width_mm=60.0, face_half_height_mm=30.0)

    map_a = compute_forgiveness_map(small, ball, DRIVER, MapSettings(spacing_mm=5.0))
    map_b = compute_forgiveness_map(large, ball, DRIVER, MapSettings(spacing_mm=5.0))

    with pytest.raises(ValueError, match="different grids"):
        compare_maps("small", map_a, "large", map_b)


def test_a_comparison_only_covers_points_on_both_faces(ball):
    """Proves the shared mask is an intersection. A point that exists on one
    face and not the other has no meaningful difference, so it stays blank.
    """
    settings = MapSettings(spacing_mm=5.0)
    round_face = fixture_symmetric_head()
    tall_face = HeadMassProperties.from_industry_units(
        200.0, (0.0, 0.0, -35.0), np.diag([3000.0, 5000.0, 4000.0]),
        face_half_width_mm=50.0, face_half_height_mm=30.0)
    tall_face.face.shape = "rectangle"

    map_a = compute_forgiveness_map(round_face, ball, DRIVER, settings)
    map_b = compute_forgiveness_map(tall_face, ball, DRIVER, settings)
    comparison = compare_maps("ellipse", map_a, "rectangle", map_b)

    assert np.array_equal(comparison.on_face, map_a.on_face & map_b.on_face)
    assert np.count_nonzero(comparison.on_face) < np.count_nonzero(map_b.on_face)
    assert np.all(np.isnan(comparison.delta_backspin_rpm[~comparison.on_face]))
