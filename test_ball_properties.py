"""Tests for the ball's properties and the provenance of its constants."""

import pytest

from ball_properties import (BALL_COR_AT_45_MPS, BALL_DIAMETER_MIN_MM,
                             BALL_FRICTION_THREE_PIECE, BALL_INERTIA_RATIO,
                             BALL_MASS_MAX_G, BallProperties,
                             conforming_three_piece_tour_ball)
from sourced_constant import SourcedConstant


def test_the_tour_ball_sits_at_the_rules_limits():
    """Proves the fixture ball is built from the Equipment Rules limits and
    nothing else -- 45.93 g and 42.67 mm diameter. It is a generic conforming
    ball, deliberately not a commercial product.
    """
    ball = conforming_three_piece_tour_ball()

    assert ball.mass_kg == pytest.approx(0.04593, rel=1e-15)
    assert ball.radius_m == pytest.approx(0.0213350, rel=1e-12)
    assert "not a commercial product" in ball.description


def test_the_inertia_follows_from_mass_radius_and_the_ratio():
    """Proves the ball's moment of inertia is computed, not stored, so it can
    never drift out of step with the mass and radius it depends on.
    """
    ball = conforming_three_piece_tour_ball()
    expected = BALL_INERTIA_RATIO * ball.mass_kg * ball.radius_m ** 2

    assert ball.inertia_kg_m2 == pytest.approx(expected, rel=1e-15)
    assert ball.inertia_kg_m2 == pytest.approx(8.36e-6, rel=1e-2)


def test_every_ball_constant_carries_a_unit_and_a_source():
    """Proves standing rule 3 holds for the whole set, not just the ones
    someone remembered. These are the numbers the model's outputs are most
    sensitive to, so each has to answer for itself.
    """
    for constant in (BALL_MASS_MAX_G, BALL_DIAMETER_MIN_MM, BALL_COR_AT_45_MPS,
                     BALL_FRICTION_THREE_PIECE, BALL_INERTIA_RATIO):
        assert isinstance(constant, SourcedConstant)
        assert constant.unit and constant.citation


def test_the_speed_dependent_constants_record_their_speed():
    """Proves COR and friction cannot be quoted without their measurement
    speed. Both vary strongly with speed -- COR runs 0.85 to 0.78 across the
    range a club sees -- so a bare number is not a fact about the ball, it is
    a fact about the ball at one speed.
    """
    assert "m/s" in BALL_COR_AT_45_MPS.note
    assert "m/s" in BALL_FRICTION_THREE_PIECE.note


def test_the_moment_of_inertia_is_flagged_as_the_one_estimate():
    """Proves the single unsourced number in the model announces itself, and
    that the measured ones do not. This is the honesty check: whoever reads
    a spin figure should be able to find out that it rests on a uniform-sphere
    assumption.
    """
    assert BALL_INERTIA_RATIO.is_estimate
    assert "ESTIMATE" in BALL_INERTIA_RATIO.provenance()

    for measured in (BALL_MASS_MAX_G, BALL_COR_AT_45_MPS, BALL_FRICTION_THREE_PIECE):
        assert not measured.is_estimate


def test_the_ball_can_list_its_own_provenance():
    """Proves a result can be traced back to its sources from the objects
    themselves, which is what makes the Phase 5 write-up auditable rather than
    a set of numbers someone has to take on trust.
    """
    lines = conforming_three_piece_tour_ball().provenance()

    assert any("Equipment Rules" in line for line in lines)
    assert any("Penner" in line for line in lines)
    assert any("ESTIMATE" in line for line in lines)


def test_a_cor_above_one_is_refused():
    """Proves the model cannot be asked to create energy from nothing. A COR
    above 1 would mean the ball leaves faster than it arrived, relative to the
    face, with nothing supplying the difference.
    """
    with pytest.raises(ValueError, match="cor"):
        BallProperties(0.04593, 0.021335, cor=1.2, friction_coefficient=0.38)


def test_an_impossible_inertia_ratio_is_refused():
    """Proves the sphere assumption is bounded by physics. 2/5 is a uniform
    sphere and 2/3 is a thin shell with every gram at the surface; nothing
    spherical can exceed that, so a higher value means an error upstream.
    """
    with pytest.raises(ValueError, match="inertia_ratio"):
        BallProperties(0.04593, 0.021335, cor=0.78, friction_coefficient=0.38,
                       inertia_ratio=0.9)


def test_impossible_masses_and_radii_are_refused():
    """Proves the boundary rejects the degenerate cases that would otherwise
    divide by zero inside the collision matrix.
    """
    with pytest.raises(ValueError, match="mass_kg"):
        BallProperties(0.0, 0.021335, cor=0.78, friction_coefficient=0.38)
    with pytest.raises(ValueError, match="radius_m"):
        BallProperties(0.04593, -0.02, cor=0.78, friction_coefficient=0.38)
    with pytest.raises(ValueError, match="friction_coefficient"):
        BallProperties(0.04593, 0.021335, cor=0.78, friction_coefficient=-0.1)
