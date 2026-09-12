"""Tests for clubhead mass properties and their validation.

The validation here is the project's defence against a mis-transcribed or
wrongly-united Fusion export. Every rule rejects a tensor that is arithmetically
fine but physically impossible, because that is what an import error looks like:
never a crash, always a plausible number.
"""

import math

import numpy as np
import pytest

from head_mass_properties import (CONFORMANCE_MOI_LIMIT_G_CM2, FaceGeometry,
                                  HeadMassProperties, strike_from_toe_crown_mm)
from impact_fixtures import fixture_offset_cg_head, fixture_symmetric_head

GOOD_TENSOR = np.diag([3.0e-4, 5.0e-4, 4.0e-4])


def test_the_unit_boundary_converts_a_whole_head_correctly():
    """Proves standing rule 6 end to end: grams, millimetres and g*cm^2 go in,
    and the object holds kilograms, metres and kg*m^2 -- so nothing downstream
    ever has to ask which units it is looking at.
    """
    head = HeadMassProperties.from_industry_units(
        mass_g=200.0, cg_mm=(0.0, 0.0, -35.0),
        inertia_g_cm2=np.diag([3000.0, 5000.0, 4000.0]))

    assert head.mass_kg == pytest.approx(0.200, rel=1e-15)
    assert head.cg_m[2] == pytest.approx(-0.035, rel=1e-15)
    assert head.inertia_about_cg[1, 1] == pytest.approx(5.0e-4, rel=1e-12)
    assert head.cg_depth_m == pytest.approx(0.035, rel=1e-15)


def test_the_sweet_spot_is_the_cg_projected_onto_the_face():
    """Proves our sweet spot is the governing bodies' definition, not a
    convention of our own: the COR protocol (p.4) specifies the test impact
    at "the projection of the clubhead Centre of Mass through the club face".
    """
    head = fixture_offset_cg_head()
    spot = head.sweet_spot_m

    assert spot[0] == pytest.approx(head.cg_m[0])
    assert spot[1] == pytest.approx(head.cg_m[1])
    assert spot[2] == 0.0                       # on the face plane by construction
    assert np.allclose(head.moment_arm_m(spot), 0.0)


def test_the_moment_arm_is_measured_from_the_sweet_spot_not_the_face_centre():
    """Proves the quantity that drives ball-speed loss is offset from the CG
    projection. On a head with an off-centre CG, a strike dead-centre on the
    face already carries a moment arm -- and therefore already loses speed.
    """
    head = fixture_offset_cg_head()
    arm = head.moment_arm_m(np.array([0.0, 0.0, 0.0]))

    assert arm[0] == pytest.approx(-head.cg_m[0])
    assert arm[1] == pytest.approx(-head.cg_m[1])
    assert np.linalg.norm(arm) > 0.0


def test_the_toe_crown_helper_puts_the_sign_in_one_place():
    """Proves the sign convention is encapsulated. x points at the HEEL, so a
    toe offset is negative -- and this helper is the only place that has to
    know, which is the point of having it.
    """
    toe = strike_from_toe_crown_mm(15.0, 0.0)
    heel = strike_from_toe_crown_mm(-15.0, 0.0)
    high = strike_from_toe_crown_mm(0.0, 10.0)

    assert toe[0] == pytest.approx(-0.015)
    assert heel[0] == pytest.approx(0.015)
    assert high[1] == pytest.approx(0.010)
    assert toe[2] == 0.0


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def test_a_cg_in_front_of_the_face_is_refused():
    """Proves the most likely sign error on import is caught. A positive cg_z
    puts the centre of mass out in front of the striking surface, which no
    clubhead can do -- it means someone measured depth as positive.
    """
    with pytest.raises(ValueError, match="behind the face plane"):
        HeadMassProperties(0.200, np.array([0.0, 0.0, 0.035]), GOOD_TENSOR)
    with pytest.raises(ValueError, match="behind the face plane"):
        HeadMassProperties(0.200, np.array([0.0, 0.0, 0.0]), GOOD_TENSOR)


def test_an_asymmetric_inertia_tensor_is_refused():
    """Proves a transposed or partially-copied tensor is caught. A real
    inertia tensor is exactly symmetric by construction, so any asymmetry at
    all means the numbers were mis-transcribed, not that the head is odd.
    """
    bad = GOOD_TENSOR.copy()
    bad[0, 1] = 1.0e-5                          # only one half of the pair set
    with pytest.raises(ValueError, match="symmetric"):
        HeadMassProperties(0.200, np.array([0.0, 0.0, -0.035]), bad)


def test_a_non_positive_definite_tensor_is_refused():
    """Proves a tensor that would let the head have negative rotational
    inertia about some axis is rejected. Physically it would mean the head
    spins up for free when you torque it.
    """
    bad = np.diag([3.0e-4, -5.0e-4, 4.0e-4])
    with pytest.raises(ValueError, match="positive-definite"):
        HeadMassProperties(0.200, np.array([0.0, 0.0, -0.035]), bad)


def test_a_tensor_violating_the_triangle_inequality_is_refused():
    """Proves the subtlest check of the three. This tensor is symmetric AND
    positive-definite -- it passes every obvious test -- and still describes
    no object that can exist, because each principal moment is an integral of
    mass times distance squared and so cannot exceed the sum of the other two.

    This is exactly what a tensor assembled from the wrong axes, or from
    mixed units per row, tends to look like.
    """
    bad = np.diag([1.0e-4, 1.0e-4, 9.0e-4])     # 1 + 1 < 9
    with pytest.raises(ValueError, match="triangle inequality"):
        HeadMassProperties(0.200, np.array([0.0, 0.0, -0.035]), bad)


def test_a_flat_plate_sits_exactly_on_the_triangle_limit():
    """Proves the triangle check does not reject legitimate bodies at the
    boundary. A flat plate has I1 + I2 = I3 exactly, and a thin face insert is
    a real thing to want to model.
    """
    plate = np.diag([1.0e-4, 3.0e-4, 4.0e-4])   # 1 + 3 == 4
    head = HeadMassProperties(0.200, np.array([0.0, 0.0, -0.035]), plate)
    assert head.mass_kg == 0.200


def test_impossible_masses_and_shapes_are_refused():
    """Proves the cheap checks are present too, so a zero or missing field
    fails at the boundary rather than dividing by zero inside the solver.
    """
    with pytest.raises(ValueError, match="mass_kg"):
        HeadMassProperties(0.0, np.array([0.0, 0.0, -0.035]), GOOD_TENSOR)
    with pytest.raises(ValueError, match="3-vector"):
        HeadMassProperties(0.200, np.array([0.0, -0.035]), GOOD_TENSOR)
    with pytest.raises(ValueError, match="3x3"):
        HeadMassProperties(0.200, np.array([0.0, 0.0, -0.035]), np.eye(2))
    with pytest.raises(ValueError, match="positive"):
        FaceGeometry(0.0, 0.030)


# ---------------------------------------------------------------------------
# CONFORMANCE
# ---------------------------------------------------------------------------

def test_the_conformance_moi_is_not_simply_i_yy():
    """Proves the Rules' 5900 g*cm^2 figure is measured about a DIFFERENT axis
    from our head-fixed y. The Rules measure about the lab vertical with the
    club at a 60 degree lie (MOI protocol p.3), which is 30 degrees away.

    Comparing I_yy directly to 5900 would quietly overstate the margin, and
    this is the check that keeps those two numbers from being conflated.
    """
    head = fixture_symmetric_head()
    i_yy_in_g_cm2 = head.inertia_about_cg[1, 1] * 1.0e7

    assert i_yy_in_g_cm2 == pytest.approx(5000.0, rel=1e-9)
    assert head.rules_frame_moi_g_cm2() == pytest.approx(4500.0, rel=1e-9)


def test_the_conformance_rotation_is_a_weighted_blend_of_two_axes():
    """Proves the rotation is doing what the geometry says: at a 60 degree lie
    the lab vertical leans 30 degrees off the head's crown axis toward the toe,
    so the measured MOI is cos^2(30) of I_yy plus sin^2(30) of I_xx.

    Checking against the closed form rather than against a stored number means
    the test would survive a change of fixture but not a change of axis.
    """
    head = fixture_symmetric_head()
    tilt = math.radians(30.0)
    expected = (math.cos(tilt) ** 2 * head.inertia_about_cg[1, 1]
                + math.sin(tilt) ** 2 * head.inertia_about_cg[0, 0]) * 1.0e7

    assert head.rules_frame_moi_g_cm2() == pytest.approx(expected, rel=1e-12)


def test_conformance_is_reported_and_not_enforced():
    """Proves a non-conforming head can still be modelled. GolfLab is a design
    tool, and asking "how much would this gain if it were legal?" is a
    legitimate question -- so this is a report, never a rejection.
    """
    illegal = HeadMassProperties.from_industry_units(
        mass_g=200.0, cg_mm=(0.0, 0.0, -35.0),
        inertia_g_cm2=np.diag([7000.0, 9000.0, 8000.0]))
    report = illegal.conformance_report()

    assert report["conforms"] is False
    assert report["rules_frame_moi_g_cm2"] > CONFORMANCE_MOI_LIMIT_G_CM2
    assert "p.54" in report["citation"]
    assert fixture_symmetric_head().conformance_report()["conforms"] is True


def test_a_ten_million_fold_unit_error_shows_up_in_the_conformance_report():
    """Proves the backstop works for the error the whole units module exists to
    prevent. Pass g*cm^2 where kg*m^2 belongs and nothing else complains --
    the tensor is still symmetric, positive-definite and physically shaped --
    but the conformance number lands absurdly far outside the legal band.
    """
    mistaken = HeadMassProperties(0.200, np.array([0.0, 0.0, -0.035]),
                                  np.diag([3000.0, 5000.0, 4000.0]))
    report = mistaken.conformance_report()

    assert report["conforms"] is False
    assert report["rules_frame_moi_g_cm2"] > 1.0e6 * CONFORMANCE_MOI_LIMIT_G_CM2
