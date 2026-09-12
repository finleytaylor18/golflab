"""Physics tests for the impact model.

Each test states, in its docstring, WHAT PHYSICAL CLAIM IT PROVES. That is
the point of the suite: these are not regression tests guarding today's
numbers, they are independent checks that the model obeys mechanics. A test
that only asserts "the number is still 63.06" proves nothing, so wherever a
result can be derived by hand or forced by a conservation law, it is.
"""

import math

import numpy as np
import pytest

from ball_properties import (BALL_FRICTION_TWO_PIECE, BallProperties,
                             conforming_three_piece_tour_ball)
from head_mass_properties import (HeadMassProperties, strike_from_toe_crown_mm)
from impact_fixtures import (fixture_head_with_cg_depth, fixture_near_rigid_head,
                             fixture_offset_cg_head, fixture_symmetric_head)
from impact_model import (SwingConditions, collision_matrix, effective_mass,
                          head_to_lab_rotation, skew, solve_impact)

DRIVER = SwingConditions(head_speed_mps=45.0, loft_rad=math.radians(10.5))
SQUARE = SwingConditions(head_speed_mps=45.0, loft_rad=0.0)
CENTRE = np.array([0.0, 0.0, 0.0])


@pytest.fixture
def ball():
    return conforming_three_piece_tour_ball()


# ---------------------------------------------------------------------------
# 1. HAND-DERIVED SWEET-SPOT CHECK
# ---------------------------------------------------------------------------

def test_sweet_spot_ball_speed_matches_the_hand_derivation(ball):
    """Proves: on a square, centred strike the model reduces to the textbook
    one-dimensional collision, ball speed = u * M(1+e)/(M+m).

    This is the single most important test in the suite. With no loft and no
    offset there is nothing for the inertia tensor, friction or gear effect to
    do, so the whole 3x3 machinery must collapse to a result that can be
    derived on paper in one line. If it does not, the machinery is wrong and
    every other number it produces is meaningless.
    """
    head = fixture_symmetric_head()
    result = solve_impact(head, ball, SQUARE, CENTRE)

    m, M, e, u = ball.mass_kg, head.mass_kg, ball.cor, SQUARE.head_speed_mps
    expected = u * M * (1.0 + e) / (M + m)

    assert result.ball_speed_mps == pytest.approx(expected, rel=1e-12)
    # ... and it goes straight down the target line with no spin at all.
    assert result.ball_velocity_lab_mps[1] == pytest.approx(0.0, abs=1e-12)
    assert result.ball_velocity_lab_mps[2] == pytest.approx(0.0, abs=1e-12)
    assert np.allclose(result.ball_spin_lab_rad_s, 0.0, atol=1e-9)


def test_sweet_spot_smash_factor_is_the_classic_expression(ball):
    """Proves: smash factor at the sweet spot depends ONLY on head mass, ball
    mass and COR -- not on inertia, loft or where the CG sits in depth.

    This is why smash factor is a useful number to quote at all, and also why
    it is capped: with a 200 g head and a legal ball, no COR below 1 can push
    it past about 1.5.
    """
    head = fixture_symmetric_head()
    result = solve_impact(head, ball, SQUARE, CENTRE)
    m, M, e = ball.mass_kg, head.mass_kg, ball.cor

    assert (result.ball_speed_mps / SQUARE.head_speed_mps
            == pytest.approx(M * (1.0 + e) / (M + m), rel=1e-12))


def test_sweet_spot_head_rebound_matches_momentum_by_hand(ball):
    """Proves: the head's own post-impact speed is what momentum says it must
    be. The ball is not accelerated for free -- the head pays for it.
    """
    head = fixture_symmetric_head()
    result = solve_impact(head, ball, SQUARE, CENTRE)
    m, M, e, u = ball.mass_kg, head.mass_kg, ball.cor, SQUARE.head_speed_mps

    expected = u * (1.0 - (1.0 + e) * m / (M + m))
    assert result.head_velocity_after_lab_mps[0] == pytest.approx(expected, rel=1e-12)


def test_effective_mass_at_the_sweet_spot_is_the_whole_head_mass():
    """Proves: the sweet spot is exactly the point where the ball feels the
    entire head, because the moment arm about the CG is zero and there is no
    torque to twist the head. Everywhere else the ball feels less.

    Note it holds for an OFFSET CG too -- the sweet spot follows the CG, it is
    not a fixed feature of the face.
    """
    for head in (fixture_symmetric_head(), fixture_offset_cg_head()):
        assert effective_mass(head, head.sweet_spot_m) == pytest.approx(head.mass_kg, rel=1e-12)


def test_rolling_contact_reproduces_the_two_sevenths_result(ball):
    """Proves: when the head is effectively immovable and the face grips, the
    model reproduces the classic rigid-sphere rolling result -- tangential
    impulse (2/7) m u_t, and surface speed omega*R = (5/7) u_t.

    The 2/7 and 5/7 come from the uniform sphere's inertia ratio alpha = 2/5
    via alpha/(1+alpha) and 1/(1+alpha). Recovering them is a direct check
    that the ball's rotational compliance enters K correctly, which is what
    sets every spin number the model produces.
    """
    huge = HeadMassProperties.from_industry_units(
        mass_g=200.0e9, cg_mm=(0.0, 0.0, -35.0),
        inertia_g_cm2=np.diag([3000.0, 5000.0, 4000.0]) * 1.0e12)
    result = solve_impact(huge, ball, DRIVER, CENTRE)
    assert result.is_rolling

    u_t = DRIVER.head_speed_mps * math.sin(DRIVER.loft_rad)
    alpha = ball.inertia_ratio

    tangential_impulse = math.hypot(*result.impulse_head_frame_ns[:2])
    assert tangential_impulse == pytest.approx(
        alpha / (1.0 + alpha) * ball.mass_kg * u_t, rel=1e-6)

    surface_speed = np.linalg.norm(result.ball_spin_lab_rad_s) * ball.radius_m
    assert surface_speed == pytest.approx(u_t / (1.0 + alpha), rel=1e-6)


def test_a_gripping_face_leaves_the_ball_truly_rolling(ball):
    """Proves: 'rolling' is not a label the code attaches, it is a physical
    state. At separation the ball's contact point and the face are moving at
    the same speed -- zero relative sliding -- which is the definition.
    """
    head = fixture_symmetric_head()
    strike = strike_from_toe_crown_mm(12.0, 8.0)
    result = solve_impact(head, ball, DRIVER, strike)
    assert result.is_rolling

    contact = np.array([strike[0], strike[1], 0.0])
    r_ball = np.array([0.0, 0.0, -ball.radius_m])
    r_head = contact - head.cg_m
    rot = head_to_lab_rotation(DRIVER.loft_rad)

    ball_point = (rot.T @ result.ball_velocity_lab_mps
                  + np.cross(rot.T @ result.ball_spin_lab_rad_s, r_ball))
    head_point = (rot.T @ result.head_velocity_after_lab_mps
                  + np.cross(rot.T @ result.head_spin_after_lab_rad_s, r_head))

    assert ball_point[:2] == pytest.approx(head_point[:2], abs=1e-9)


# ---------------------------------------------------------------------------
# 2. SYMMETRY
# ---------------------------------------------------------------------------

def test_heel_and_toe_strikes_are_exact_mirror_images(ball):
    """Proves: the model contains no hidden left/right bias. On a head whose
    CG is dead centre, nothing physical distinguishes 15 mm toward the toe
    from 15 mm toward the heel except direction, so ball speed and backspin
    must be identical and the sideways quantities equal and opposite.

    A failure here means a sign error or an asymmetric term -- the kind of bug
    that would otherwise hide inside a plausible-looking forgiveness map.
    """
    head = fixture_symmetric_head()
    toe = solve_impact(head, ball, DRIVER, strike_from_toe_crown_mm(15.0, 0.0))
    heel = solve_impact(head, ball, DRIVER, strike_from_toe_crown_mm(-15.0, 0.0))

    assert toe.ball_speed_mps == pytest.approx(heel.ball_speed_mps, rel=1e-12)
    assert toe.backspin_rad_s == pytest.approx(heel.backspin_rad_s, rel=1e-12)
    assert toe.effective_mass_kg == pytest.approx(heel.effective_mass_kg, rel=1e-12)
    assert toe.sidespin_rad_s == pytest.approx(-heel.sidespin_rad_s, rel=1e-12)
    assert toe.horizontal_launch_rad == pytest.approx(-heel.horizontal_launch_rad, rel=1e-12)


def test_the_mirror_line_follows_the_cg_not_the_face_centre(ball):
    """Proves: symmetry is about the SWEET SPOT. Move the CG 4 mm toward the
    heel and the mirror line moves with it, so strikes 15 mm either side of
    the sweet spot still match -- while strikes either side of the face centre
    no longer do.

    This is the practical content of 'the sweet spot is where the CG points',
    and it is why a head with an off-centre CG has an off-centre best strike.
    """
    head = fixture_offset_cg_head()
    sweet = head.sweet_spot_m
    left = solve_impact(head, ball, DRIVER, sweet + np.array([0.015, 0.0, 0.0]))
    right = solve_impact(head, ball, DRIVER, sweet - np.array([0.015, 0.0, 0.0]))

    assert left.ball_speed_mps == pytest.approx(right.ball_speed_mps, rel=1e-12)
    assert left.sidespin_rad_s == pytest.approx(-right.sidespin_rad_s, rel=1e-12)

    off_centre = solve_impact(head, ball, DRIVER, np.array([0.015, 0.0, 0.0]))
    mirrored = solve_impact(head, ball, DRIVER, np.array([-0.015, 0.0, 0.0]))
    assert off_centre.ball_speed_mps != pytest.approx(mirrored.ball_speed_mps, rel=1e-9)


# ---------------------------------------------------------------------------
# 3. RIGID LIMIT
# ---------------------------------------------------------------------------

def test_an_infinitely_stiff_head_loses_no_ball_speed_off_centre(ball):
    """Proves: ALL off-centre ball-speed loss comes from the head twisting.
    Make the inertia enormous and the head cannot rotate, so the ball feels
    the full mass everywhere and effective mass is flat across the face.

    This is the clearest statement of what a forgiveness map measures: not
    some property of the face, but how much the head turns when you miss.
    """
    head = fixture_near_rigid_head()
    centre = solve_impact(head, ball, DRIVER, CENTRE)
    miss = solve_impact(head, ball, DRIVER, strike_from_toe_crown_mm(25.0, 15.0))

    assert miss.effective_mass_kg == pytest.approx(head.mass_kg, rel=1e-5)
    assert miss.ball_speed_mps == pytest.approx(centre.ball_speed_mps, rel=1e-5)


def test_an_infinitely_stiff_head_produces_no_gear_effect(ball):
    """Proves: gear-effect sidespin is generated by head rotation and by
    nothing else. No twist, no gear spin -- even with the CG 35 mm deep.
    """
    head = fixture_near_rigid_head()
    miss = solve_impact(head, ball, DRIVER, strike_from_toe_crown_mm(25.0, 0.0))
    assert miss.sidespin_rad_s == pytest.approx(0.0, abs=1e-3)


def test_raising_moi_always_reduces_the_off_centre_penalty(ball):
    """Proves: higher MOI means more forgiveness, monotonically -- the single
    design claim the whole 5900 g*cm^2 rule exists to constrain.
    """
    strike = strike_from_toe_crown_mm(20.0, 0.0)
    losses = []
    for scale in (1.0, 2.0, 4.0, 8.0):
        head = HeadMassProperties.from_industry_units(
            mass_g=200.0, cg_mm=(0.0, 0.0, -35.0),
            inertia_g_cm2=np.diag([3000.0, 5000.0, 4000.0]) * scale)
        centre = solve_impact(head, ball, DRIVER, CENTRE).ball_speed_mps
        losses.append(centre - solve_impact(head, ball, DRIVER, strike).ball_speed_mps)

    assert all(a > b > 0 for a, b in zip(losses, losses[1:]))


# ---------------------------------------------------------------------------
# 4. MONOTONIC LOSS
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("direction", [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0),
                                       (0.0, -1.0), (0.7, 0.7), (-0.7, 0.7)])
def test_ball_speed_falls_away_from_the_sweet_spot_in_every_direction(ball, direction):
    """Proves: the sweet spot is a strict maximum of ball speed, and the
    forgiveness map has no local bumps or ridges in any direction.

    Physically this follows from K being positive-definite: the moment arm
    enters squared, so moving away from the sweet spot can only ever add
    rotational compliance, never remove it. The test checks that the code
    actually inherits that property.
    """
    head = fixture_symmetric_head()
    unit = np.array([direction[0], direction[1], 0.0])
    speeds = [solve_impact(head, ball, DRIVER, head.sweet_spot_m + unit * offset).ball_speed_mps
              for offset in (0.0, 0.005, 0.010, 0.015, 0.020, 0.025)]

    assert all(a > b for a, b in zip(speeds, speeds[1:])), speeds


def test_effective_mass_falls_away_from_the_sweet_spot(ball):
    """Proves: the ball-speed fall-off is driven by effective mass, so the two
    maps are the same shape. Effective mass is the physical quantity; ball
    speed is what a launch monitor happens to report.
    """
    head = fixture_symmetric_head()
    masses = [effective_mass(head, np.array([offset, 0.0, 0.0]))
              for offset in (0.0, 0.005, 0.010, 0.015, 0.020)]
    assert all(a > b for a, b in zip(masses, masses[1:])), masses
    assert masses[0] == pytest.approx(head.mass_kg, rel=1e-12)


# ---------------------------------------------------------------------------
# 5. SIGN CONVENTIONS
# ---------------------------------------------------------------------------

def test_a_toe_strike_starts_right_and_curves_left(ball):
    """Proves the gear effect's direction for a toe miss: the head opens, so
    the ball STARTS RIGHT of target, and the face gears draw spin onto it, so
    it CURVES LEFT. The familiar toe-hook.

    Getting this backwards would invert the entire design conclusion of a
    forgiveness map, so it is checked as a signed fact, not a magnitude.
    """
    head = fixture_symmetric_head()
    toe = solve_impact(head, ball, DRIVER, strike_from_toe_crown_mm(15.0, 0.0))

    assert toe.horizontal_launch_rad > 0.0      # starts right of target
    assert toe.sidespin_rad_s < 0.0             # curves left: a draw


def test_a_heel_strike_starts_left_and_curves_right(ball):
    """Proves the mirror case: the head closes, the ball starts LEFT, and gear
    effect puts fade spin on it so it CURVES RIGHT. The familiar heel-slice.
    """
    head = fixture_symmetric_head()
    heel = solve_impact(head, ball, DRIVER, strike_from_toe_crown_mm(-15.0, 0.0))

    assert heel.horizontal_launch_rad < 0.0
    assert heel.sidespin_rad_s > 0.0


def test_a_high_strike_launches_higher_with_less_backspin(ball):
    """Proves the vertical gear effect: strike above the sweet spot and the
    head's crown rotates back, gearing topspin onto the ball, which SUBTRACTS
    from backspin and raises the launch angle.

    This is why 'high on the face' is the good miss with a driver -- high
    launch and low spin is exactly the combination that carries.
    """
    head = fixture_symmetric_head()
    centre = solve_impact(head, ball, DRIVER, CENTRE)
    high = solve_impact(head, ball, DRIVER, strike_from_toe_crown_mm(0.0, 10.0))

    assert high.launch_angle_rad > centre.launch_angle_rad
    assert high.backspin_rad_s < centre.backspin_rad_s
    assert high.backspin_rad_s > 0.0            # still genuine backspin


def test_a_low_strike_launches_lower_with_more_backspin(ball):
    """Proves the opposite sign of the same mechanism -- and, taken with the
    test above, that the effect is driven by the OFFSET and not by some
    constant bias, because reversing the offset reverses the result.
    """
    head = fixture_symmetric_head()
    centre = solve_impact(head, ball, DRIVER, CENTRE)
    low = solve_impact(head, ball, DRIVER, strike_from_toe_crown_mm(0.0, -10.0))

    assert low.launch_angle_rad < centre.launch_angle_rad
    assert low.backspin_rad_s > centre.backspin_rad_s


def test_loft_alone_creates_backspin_and_launch(ball):
    """Proves the baseline every golfer relies on: a perfectly centred strike
    with a lofted face still launches up and still spins backwards, purely
    because the face is tilted relative to the direction of travel.

    Launch angle sits BELOW the loft, which is the standard result -- the ball
    leaves between the face normal and the path, not along the normal.
    """
    head = fixture_symmetric_head()
    result = solve_impact(head, ball, DRIVER, CENTRE)

    assert result.backspin_rad_s > 0.0
    assert 0.0 < result.launch_angle_rad < DRIVER.loft_rad
    assert result.sidespin_rad_s == pytest.approx(0.0, abs=1e-9)


def test_a_square_face_produces_no_spin_at_all(ball):
    """Proves there is no spurious spin source: remove the loft and remove the
    offset, and every component of spin must be exactly zero.
    """
    head = fixture_symmetric_head()
    result = solve_impact(head, ball, SQUARE, CENTRE)
    assert np.allclose(result.ball_spin_lab_rad_s, 0.0, atol=1e-9)


# ---------------------------------------------------------------------------
# 6. CG DEPTH AND GEAR EFFECT
# ---------------------------------------------------------------------------

def test_gear_effect_vanishes_as_the_cg_approaches_the_face(ball):
    """Proves the structural claim behind the whole gear effect: sidespin on
    an off-centre strike is generated by the CG being BEHIND the face. Bring
    the CG toward the face plane and the gear spin goes to zero.

    This is why a driver (deep CG) gears strongly and a blade iron (shallow
    CG) barely gears at all -- the same physics, a different lever arm.
    """
    strike = strike_from_toe_crown_mm(15.0, 0.0)
    spins = [abs(solve_impact(fixture_head_with_cg_depth(d), ball, DRIVER, strike).sidespin_rad_s)
             for d in (35.0, 10.0, 1.0, 0.1, 0.01)]

    assert all(a > b for a, b in zip(spins, spins[1:])), spins
    assert spins[-1] < 1.0e-2 * spins[0]


def test_gear_spin_is_proportional_to_cg_depth_for_small_depths(ball):
    """Proves the relationship is LINEAR in depth, not merely decreasing.

    Halving the depth halves the gear spin. That gives a designer a directly
    usable rule: CG depth is the gear-effect knob, and it is a proportional
    one, which is not obvious from the fact that it merely 'vanishes'.
    """
    strike = strike_from_toe_crown_mm(15.0, 0.0)
    fine = abs(solve_impact(fixture_head_with_cg_depth(0.5), ball, DRIVER, strike).sidespin_rad_s)
    half = abs(solve_impact(fixture_head_with_cg_depth(0.25), ball, DRIVER, strike).sidespin_rad_s)

    assert half == pytest.approx(fine / 2.0, rel=1e-3)


def test_cg_depth_leaves_the_normal_impulse_alone_but_lowers_backspin(ball):
    """Proves a result worth knowing as a designer: CG depth does not touch the
    ball speed the face delivers ALONG ITS NORMAL, but it does reduce backspin
    even on a perfectly centred strike.

    The reason is that friction acts in the face plane while the CG sits a
    distance d behind it, so the friction impulse torques the head about that
    arm. A deeper CG lets the head give way rotationally, so less tangential
    impulse is needed to grip, and less tangential impulse means less spin.

    It is the vertical gear effect appearing WITHOUT any off-centre strike --
    which is why "move the CG back to lower spin" works, and why a centred
    strike is not immune to the CG's position.
    """
    rot = head_to_lab_rotation(DRIVER.loft_rad)
    normals, spins = [], []
    for depth_mm in (5.0, 20.0, 45.0):
        result = solve_impact(fixture_head_with_cg_depth(depth_mm), ball, DRIVER, CENTRE)
        normals.append((rot.T @ result.ball_velocity_lab_mps)[2])
        spins.append(result.backspin_rad_s)

    for value in normals[1:]:
        assert value == pytest.approx(normals[0], rel=1e-12)
    assert all(a > b for a, b in zip(spins, spins[1:])), spins


# ---------------------------------------------------------------------------
# 7. CONSERVATION
# ---------------------------------------------------------------------------

def _momenta(head, ball_props, conditions, strike, result):
    """Total linear and angular momentum before and after, in the head frame.

    Angular momentum is taken about the head-frame ORIGIN, a point fixed in
    space during the impulsive contact. Because the contact impulse acts at a
    single point with equal and opposite signs, its moment cancels exactly,
    so angular momentum about ANY fixed point must be conserved.
    """
    rot = head_to_lab_rotation(conditions.loft_rad)
    contact = np.array([strike[0], strike[1], 0.0])
    m, M = ball_props.mass_kg, head.mass_kg

    v_head = conditions.head_speed_mps * np.array(
        [0.0, -math.sin(conditions.loft_rad), math.cos(conditions.loft_rad)])
    ball_centre = contact + np.array([0.0, 0.0, ball_props.radius_m])

    v_ball_a = rot.T @ result.ball_velocity_lab_mps
    w_ball_a = rot.T @ result.ball_spin_lab_rad_s
    v_head_a = rot.T @ result.head_velocity_after_lab_mps
    w_head_a = rot.T @ result.head_spin_after_lab_rad_s

    p_before = M * v_head
    p_after = m * v_ball_a + M * v_head_a

    l_before = np.cross(head.cg_m, M * v_head)
    l_after = (np.cross(ball_centre, m * v_ball_a) + ball_props.inertia_kg_m2 * w_ball_a
               + np.cross(head.cg_m, M * v_head_a) + head.inertia_about_cg @ w_head_a)
    return p_before, p_after, l_before, l_after


@pytest.mark.parametrize("toe_mm,crown_mm", [(0.0, 0.0), (15.0, 0.0), (0.0, -12.0), (20.0, 10.0)])
def test_linear_momentum_is_conserved(ball, toe_mm, crown_mm):
    """Proves Newton's third law is actually obeyed: whatever momentum the
    ball gains, the head loses, in every direction.

    Nothing in the solver imposes this -- it applies +J to the ball and -J to
    the head and then computes each body independently. Conservation emerging
    from that is real evidence the bookkeeping is right.
    """
    head = fixture_symmetric_head()
    strike = strike_from_toe_crown_mm(toe_mm, crown_mm)
    result = solve_impact(head, ball, DRIVER, strike)
    p_before, p_after, _, _ = _momenta(head, ball, DRIVER, strike, result)

    assert p_after == pytest.approx(p_before, abs=1e-9)


@pytest.mark.parametrize("toe_mm,crown_mm", [(0.0, 0.0), (15.0, 0.0), (0.0, -12.0), (20.0, 10.0)])
def test_angular_momentum_is_conserved(ball, toe_mm, crown_mm):
    """Proves the moment arms are right. This is the test that catches a
    wrong r_head or r_ball, because those enter the spin and the head's
    rotation with opposite signs and only cancel if both are correct.

    It is a much stronger check than linear momentum: an impulse applied at
    the wrong POINT still conserves linear momentum perfectly.
    """
    head = fixture_symmetric_head()
    strike = strike_from_toe_crown_mm(toe_mm, crown_mm)
    result = solve_impact(head, ball, DRIVER, strike)
    _, _, l_before, l_after = _momenta(head, ball, DRIVER, strike, result)

    assert l_after == pytest.approx(l_before, abs=1e-9)


@pytest.mark.parametrize("toe_mm,crown_mm", [(0.0, 0.0), (15.0, 0.0), (25.0, -18.0)])
def test_kinetic_energy_never_increases(ball, toe_mm, crown_mm):
    """Proves the model cannot manufacture energy. With COR below 1 the
    collision is inelastic, so energy must strictly fall -- most of it into
    deforming the ball.
    """
    head = fixture_symmetric_head()
    result = solve_impact(head, ball, DRIVER, strike_from_toe_crown_mm(toe_mm, crown_mm))

    assert result.energy_after_j < result.energy_before_j
    assert result.energy_lost_j > 0.0


def _elastic(ball):
    return BallProperties(mass_kg=ball.mass_kg, radius_m=ball.radius_m,
                          cor=1.0, friction_coefficient=10.0,
                          description="fixture: perfectly elastic test ball")


def test_a_perfectly_elastic_square_impact_conserves_energy_exactly(ball):
    """Proves there is no numerical leak in the solver: remove every
    dissipative mechanism and energy is conserved to machine precision.

    Removing every mechanism takes BOTH a COR of 1 and a square face, because
    with no loft there is no tangential relative velocity for friction to act
    on. The strike is still well off-centre, so the head is genuinely
    twisting -- rotation is not a loss mechanism, and this shows it.
    """
    head = fixture_symmetric_head()
    result = solve_impact(head, _elastic(ball), SQUARE, strike_from_toe_crown_mm(15.0, 8.0))

    assert result.is_rolling
    assert result.energy_after_j == pytest.approx(result.energy_before_j, rel=1e-12)


def test_gripping_a_lofted_face_dissipates_energy_even_at_cor_one(ball):
    """Proves that a gripping contact is ITSELF dissipative, independently of
    COR. This is easy to get wrong: COR = 1 is often read as "lossless".

    In the tangential direction, sticking is a perfectly INELASTIC collision --
    the ball's surface and the face end up moving together, and the relative
    tangential kinetic energy they started with has to go somewhere. So a
    lofted strike with a perfect COR still loses energy, all of it to the
    grip. It is the energy that became spin.
    """
    head = fixture_symmetric_head()
    square = solve_impact(head, _elastic(ball), SQUARE, CENTRE)
    lofted = solve_impact(head, _elastic(ball), DRIVER, CENTRE)

    assert lofted.is_rolling
    assert square.energy_lost_j == pytest.approx(0.0, abs=1e-9)
    assert lofted.energy_lost_j > 0.0


def test_ball_speed_never_exceeds_the_perfectly_elastic_limit(ball):
    """Proves the COR ceiling is respected: no strike anywhere on the face can
    beat a perfectly elastic centred one. A forgiveness map that showed a spot
    faster than this would be reporting an impossibility.
    """
    head = fixture_symmetric_head()
    m, M, u = ball.mass_kg, head.mass_kg, DRIVER.head_speed_mps
    ceiling = u * M * 2.0 / (M + m)

    for toe in (-25.0, -10.0, 0.0, 10.0, 25.0):
        for crown in (-15.0, 0.0, 15.0):
            result = solve_impact(head, ball, DRIVER, strike_from_toe_crown_mm(toe, crown))
            assert result.ball_speed_mps < ceiling


# ---------------------------------------------------------------------------
# 8. REDUCTION: 3D MATCHES THE PLANAR DERIVATION
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("offset_mm", [5.0, 12.0, 20.0, 30.0])
def test_heel_toe_effective_mass_matches_the_planar_formula(offset_mm):
    """Proves the 3x3 formulation reduces exactly to the planar result
    1/M_eff = 1/M + b^2/I that docs/impact_model.md derives by hand.

    For a heel-toe miss the head twists about the CROWN-SOLE axis, so the
    relevant inertia is I_yy. Matching to machine precision means the tensor
    algebra adds nothing spurious -- the extra dimensions are carrying real
    physics, not noise.
    """
    head = fixture_symmetric_head()
    b = offset_mm / 1000.0
    planar = 1.0 / (1.0 / head.mass_kg + b ** 2 / head.inertia_about_cg[1, 1])

    assert effective_mass(head, np.array([b, 0.0, 0.0])) == pytest.approx(planar, rel=1e-12)


@pytest.mark.parametrize("offset_mm", [5.0, 12.0, 20.0])
def test_high_low_effective_mass_matches_the_planar_formula(offset_mm):
    """Proves the same reduction in the other plane, where the head twists
    about the TOE-HEEL axis and the relevant inertia is I_xx.

    Two independent planar checks against two different tensor components is
    what makes this evidence that the axes are wired up correctly, rather than
    a coincidence that would survive a transposed tensor.
    """
    head = fixture_symmetric_head()
    b = offset_mm / 1000.0
    planar = 1.0 / (1.0 / head.mass_kg + b ** 2 / head.inertia_about_cg[0, 0])

    assert effective_mass(head, np.array([0.0, b, 0.0])) == pytest.approx(planar, rel=1e-12)


def test_effective_mass_ignores_cg_depth():
    """Proves the analytic result that CG depth drops out of the NORMAL
    effective mass entirely: the moment arm that matters is the in-face
    offset, and depth is perpendicular to it.

    Together with the gear-effect tests this separates the two roles of the
    CG cleanly -- its in-face position sets ball speed, its depth sets spin.
    """
    strike = np.array([0.018, 0.010, 0.0])
    values = [effective_mass(fixture_head_with_cg_depth(d), strike) for d in (1.0, 20.0, 60.0)]
    assert values[0] == pytest.approx(values[1], rel=1e-12)
    assert values[1] == pytest.approx(values[2], rel=1e-12)


def test_the_collision_matrix_is_symmetric_and_positive_definite(ball):
    """Proves K is a valid compliance matrix. Symmetry is a consequence of
    Newton's third law; positive-definiteness means any impulse you apply
    changes the relative velocity in the direction you pushed.

    If either failed, the stick solution could not be trusted to exist, and
    the monotonic fall-off of the forgiveness map would not be guaranteed.
    """
    head = fixture_symmetric_head()
    k = collision_matrix(head, ball, strike_from_toe_crown_mm(15.0, 10.0))

    assert np.allclose(k, k.T, rtol=1e-12)
    assert np.all(np.linalg.eigvalsh(k) > 0.0)


def test_skew_matrix_reproduces_the_cross_product():
    """Proves the one piece of index gymnastics in the module. Every moment
    arm in the model passes through skew(), so a transposed sign here would
    corrupt all of the spin results at once while leaving speeds untouched.
    """
    a = np.array([0.3, -1.2, 4.5])
    b = np.array([-2.0, 0.7, 1.1])
    assert np.allclose(skew(a) @ b, np.cross(a, b))
    assert np.allclose(skew(a), -skew(a).T)


def test_head_to_lab_rotation_is_a_proper_rotation():
    """Proves the frame transform preserves lengths, angles and handedness
    (determinant +1, not -1). A determinant of -1 would be a reflection, which
    would silently mirror every draw into a fade.
    """
    for loft_deg in (0.0, 9.0, 10.5, 24.0, 45.0):
        rot = head_to_lab_rotation(math.radians(loft_deg))
        assert np.allclose(rot @ rot.T, np.eye(3), atol=1e-12)
        assert np.linalg.det(rot) == pytest.approx(1.0, rel=1e-12)


def test_a_square_head_travels_straight_down_the_target_line():
    """Proves the rotation is the right one and not merely a valid one.

    The physical fact it encodes: whatever the loft, the head is delivered
    moving horizontally at the target. Expressed in the tilted head frame that
    velocity has components on two axes, and only the correct rotation puts it
    back on the target line with nothing sideways or vertical.
    """
    for loft_deg in (0.0, 10.5, 30.0):
        loft = math.radians(loft_deg)
        rot = head_to_lab_rotation(loft)
        head_frame = 45.0 * np.array([0.0, -math.sin(loft), math.cos(loft)])
        assert rot @ head_frame == pytest.approx(np.array([45.0, 0.0, 0.0]), abs=1e-12)


# ---------------------------------------------------------------------------
# 9. FRICTION REGIME
# ---------------------------------------------------------------------------

def test_a_frictionless_face_puts_no_spin_on_the_ball(ball):
    """Proves spin comes from friction and from nothing else. Set mu to zero
    and the impulse can only act along the face normal, so the ball squirts
    off with no backspin at all -- which is also, physically, what a genuinely
    wet or oily face does to a wedge shot.
    """
    slick = BallProperties(mass_kg=ball.mass_kg, radius_m=ball.radius_m,
                           cor=ball.cor, friction_coefficient=0.0,
                           description="fixture: frictionless test ball")
    head = fixture_symmetric_head()
    result = solve_impact(head, slick, DRIVER, CENTRE)

    assert not result.is_rolling
    assert np.allclose(result.ball_spin_lab_rad_s, 0.0, atol=1e-9)
    assert result.launch_angle_rad == pytest.approx(DRIVER.loft_rad, rel=1e-9)


def test_a_driver_strike_grips_but_a_steep_loft_slides(ball):
    """Proves the model chooses its contact regime from the physics rather
    than assuming one. A driver needs only a few percent of the available
    friction and grips; increase the loft far enough and the tangential
    demand outruns what the cover can supply, and the face slides.

    This matters because the two regimes have different sensitivities: a
    gripping impact's spin is set by geometry, a sliding one's is set by mu --
    and mu is the constant we know least precisely.
    """
    head = fixture_symmetric_head()
    driver = solve_impact(head, ball, DRIVER, CENTRE)
    assert driver.is_rolling
    assert driver.required_friction < ball.friction_coefficient

    # A hard two-piece cover grips about 2.4x less well than a soft tour
    # cover (Penner p.149). Put that ball on a 50 degree wedge and the
    # tangential demand outruns what the cover can supply.
    two_piece = BallProperties(mass_kg=ball.mass_kg, radius_m=ball.radius_m,
                               cor=ball.cor,
                               friction_coefficient=BALL_FRICTION_TWO_PIECE,
                               description="fixture: hard two-piece test ball")
    wedge = SwingConditions(head_speed_mps=30.0, loft_rad=math.radians(50.0))
    slid = solve_impact(head, two_piece, wedge, CENTRE)
    assert not slid.is_rolling
    assert slid.required_friction > two_piece.friction_coefficient

    # The same wedge with the soft tour cover still grips -- which is the
    # whole reason tour players pay for a urethane cover.
    assert solve_impact(head, ball, wedge, CENTRE).is_rolling


def test_required_friction_is_independent_of_swing_speed(ball):
    """Proves the standing-rule-3 point from docs/impact_model.md section 5.4:
    whether the face grips is set by loft, COR and the mass ratio -- NOT by
    how hard you swing. Both impulses scale linearly with speed, so their
    ratio does not.

    The practical reading: swinging harder does not make a club start sliding.
    Changing ball or loft does.
    """
    head = fixture_symmetric_head()
    ratios = [solve_impact(head, ball, SwingConditions(speed, DRIVER.loft_rad),
                           CENTRE).required_friction
              for speed in (20.0, 35.0, 50.0, 65.0)]

    for ratio in ratios[1:]:
        assert ratio == pytest.approx(ratios[0], rel=1e-12)


# ---------------------------------------------------------------------------
# INPUT VALIDATION AT THE DOMAIN BOUNDARY
# ---------------------------------------------------------------------------

def test_swing_conditions_reject_impossible_inputs():
    """Proves bad inputs fail loudly at the boundary rather than producing a
    plausible-looking number deep inside the physics.
    """
    with pytest.raises(ValueError, match="head_speed_mps"):
        SwingConditions(head_speed_mps=0.0, loft_rad=0.2)
    with pytest.raises(ValueError, match="loft_rad"):
        SwingConditions(head_speed_mps=45.0, loft_rad=math.pi / 2)
    with pytest.raises(ValueError, match="loft_rad"):
        SwingConditions(head_speed_mps=45.0, loft_rad=-0.1)


def test_a_strike_off_the_face_outline_is_reported(ball):
    """Proves the face outline knows its own bounds. v1 does not refuse to
    solve an off-face strike -- the mechanics is still valid -- but Phase 4
    needs this to decide which grid points belong on the map.
    """
    head = fixture_symmetric_head()
    assert head.face.contains(0.02, 0.01)
    assert not head.face.contains(0.20, 0.01)
