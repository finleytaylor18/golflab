"""Validation of the impact model against published results.

These are the Phase 5 reproductions, kept as tests so they cannot silently
stop holding. Two are EXACT -- a published equation the model must reduce to
-- and the rest are comparisons against figures quoted in Penner (2003), with
tolerances that match how precisely Penner quotes them and docstrings that say
where each falls short. A tolerance chosen to make a test pass would defeat
the point of the phase, so each one states the published figure and the
model's figure side by side.

Page numbers are the journal's own (Rep. Prog. Phys. 66, 131-171), read from
the full text.
"""

import math

import numpy as np
import pytest

from ball_properties import BallProperties, conforming_three_piece_tour_ball
from head_mass_properties import HeadMassProperties, strike_from_toe_crown_mm
from impact_model import SwingConditions, solve_impact
from units import mph_to_mps

CENTRE = np.zeros(3)


def driver_head(mass_g: float, inertia_g_cm2=(3000.0, 5000.0, 4000.0)) -> HeadMassProperties:
    """Fixture head -- synthetic, per standing rule 4 -- with a chosen mass."""
    return HeadMassProperties.from_industry_units(
        mass_g, (0.0, 0.0, -35.0), np.diag(inertia_g_cm2))


@pytest.fixture
def ball():
    return conforming_three_piece_tour_ball()


# ---------------------------------------------------------------------------
# EXACT REPRODUCTIONS OF PUBLISHED EQUATIONS
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mass_g", [170.0, 191.0, 200.0, 215.0])
def test_reproduces_penner_equation_6_exactly(ball, mass_g):
    """Penner 2003, p.160, equation (6): Vb = (1 + e) Vc / (1 + Mb / Mc).

    Penner's one-dimensional launch-speed formula is the model's own
    sweet-spot result with the loft removed, so the full 3x3 solver must
    collapse to it to machine precision -- and does, across the range of
    clubhead masses Penner discusses on the same page.
    """
    head = driver_head(mass_g)
    speed = 45.0
    result = solve_impact(head, ball, SwingConditions(speed, 0.0), CENTRE)
    penner = (1.0 + ball.cor) * speed / (1.0 + ball.mass_kg / head.mass_kg)

    assert result.ball_speed_mps == pytest.approx(penner, rel=1e-12)


def test_reproduces_the_cor_protocol_formula_exactly(ball):
    """R&A/USGA COR protocol, p.4: e = [(Vout/Vin)(mC + mb) + mb] / mC.

    The protocol fires a ball at a FREE, STATIONARY clubhead and recovers the
    coefficient of restitution from the ball's speed ratio. Our solver has
    the head moving and the ball at rest; a Galilean shift of the result into
    the protocol's frame must give back exactly the COR that went in. This
    checks the momentum bookkeeping against the governing bodies' own
    algebra rather than against our own derivation.
    """
    head = driver_head(200.0)
    v_in = mph_to_mps(133.0 * 3600.0 / 5280.0)      # the protocol's 133 ft/s
    result = solve_impact(head, ball, SwingConditions(v_in, 0.0), CENTRE)

    # Shift into the frame where the head started at rest: everything along
    # the target line loses v_in. The ball then arrives at -v_in and leaves
    # at (ball velocity - v_in).
    v_out = result.ball_velocity_lab_mps[0] - v_in
    assert v_out > 0.0                                # arrived along -X, rebounds along +X
    speed_ratio = v_out / v_in
    m_c, m_b = head.mass_kg, ball.mass_kg
    protocol_e = (speed_ratio * (m_c + m_b) + m_b) / m_c

    assert protocol_e == pytest.approx(ball.cor, abs=1e-12)


# ---------------------------------------------------------------------------
# COMPARISONS AGAINST FIGURES QUOTED IN PENNER 2003
# ---------------------------------------------------------------------------

def test_cochran_cor_sensitivity_is_reproduced(ball):
    """Penner 2003, p.162, reporting Cochran (1999): raising COR "by as much
    as 12%" corresponds "to an increase of approximately 5% in ball launch
    speed for a typical drive".

    Model: 0.78 -> 0.8736 gives +5.25% at 45 m/s and 10.5 degrees. Penner
    says "approximately 5%", so the agreement is as close as the quote can
    support. This is also the size of the trampoline effect v1 cannot model
    -- see the report's validity section.
    """
    hot = BallProperties(ball.mass_kg, ball.radius_m, ball.cor * 1.12,
                         ball.friction_coefficient, description="fixture: +12% COR")
    conditions = SwingConditions(45.0, math.radians(10.5))
    head = driver_head(200.0)

    base = solve_impact(head, ball, conditions, CENTRE).ball_speed_mps
    lively = solve_impact(head, hot, conditions, CENTRE).ball_speed_mps
    gain_pct = 100.0 * (lively / base - 1.0)

    assert gain_pct == pytest.approx(5.25, abs=0.05)   # the model's own figure
    assert 4.5 <= gain_pct <= 5.5                       # Penner: "approximately 5%"


def test_reyes_mittendorf_mass_tradeoff_is_reproduced_with_a_known_gap(ball):
    """Penner 2003, p.160, reporting Reyes and Mittendorf (1999): reducing
    clubhead mass from 191 g to 170 g raised clubhead speed 8.5%, which via
    equation (6) "would correspond to approximately a 5.6% increase in the
    launch speed".

    Model: +5.96%. That is 0.36 percentage points above Penner's figure and
    the gap is NOT explained by ball mass -- a lighter ball moves it the wrong
    way. Penner does not state the COR he used; the ratio depends on it only
    weakly. The discrepancy is recorded rather than tuned away.
    """
    v_heavy = solve_impact(driver_head(191.0), ball, SwingConditions(45.0, 0.0), CENTRE).ball_speed_mps
    v_light = solve_impact(driver_head(170.0), ball, SwingConditions(45.0 * 1.085, 0.0), CENTRE).ball_speed_mps
    gain_pct = 100.0 * (v_light / v_heavy - 1.0)

    assert gain_pct == pytest.approx(5.96, abs=0.05)   # the model's own figure
    assert abs(gain_pct - 5.6) < 0.5                    # Penner: "approximately 5.6%"


def test_launch_angle_sits_below_loft_by_about_the_empirical_ratio(ball):
    """Model vs the rule of thumb hard-coded in this repo's ball_flight.py,
    launch ~ 0.85 x dynamic loft.

    The impact model derives the launch angle instead of assuming it: the
    ball leaves between the face normal and the path, so launch is below the
    loft. For a 10.5 degree driver at 45 m/s the model gives 8.63 degrees, a
    ratio of 0.822 -- the empirical shortcut is recovered as an OUTPUT of the
    physics, within 3% of the value the older module assumes.
    """
    result = solve_impact(driver_head(200.0), ball,
                          SwingConditions(45.0, math.radians(10.5)), CENTRE)
    ratio = result.launch_angle_rad / math.radians(10.5)

    assert ratio == pytest.approx(0.822, abs=0.005)
    assert abs(ratio - 0.85) < 0.05


def test_more_moi_means_less_gear_effect_as_iwatsubo_found_but_by_less(ball):
    """Penner 2003, p.166, reporting Iwatsubo et al (2000): for an impact
    10 mm toward the toe, a clubhead with about 19% more moment of inertia
    about the vertical axis imparted 2.3 rps of sidespin instead of 3.1 rps
    (a ratio of 0.74).

    Model: the same 19% raises the ratio only to 0.845, and the absolute
    sidespin is roughly three times theirs (9.8 rps vs 3.1 rps at 45 m/s).
    The DIRECTION reproduces; the magnitudes do not, and the report says
    why: their heads differed in more than one property (Penner notes this),
    their clubhead speed is not stated, they modelled a real curved face with
    an FEA ball, and v1's flat face is known to overstate gear effect.
    """
    strike = strike_from_toe_crown_mm(10.0, 0.0)
    conditions = SwingConditions(45.0, math.radians(10.5))
    base = solve_impact(driver_head(200.0), ball, conditions, strike).sidespin_rad_s
    stiff = solve_impact(driver_head(200.0, (3000.0, 5950.0, 4000.0)), ball,
                         conditions, strike).sidespin_rad_s

    ratio = stiff / base
    assert 0.0 < ratio < 1.0                           # more MOI, less gear spin
    assert ratio == pytest.approx(0.845, abs=0.01)     # the model's own figure
    assert ratio > 0.74                                # honestly short of Iwatsubo's


def test_knowles_four_iron_centre_strike_is_bracketed(ball):
    """Penner 2003, p.166, reporting Knowles et al (1998): a 4-iron at
    40 m/s gave a simulated centre-hit launch speed of 54 m/s and a measured
    one of 56.9 m/s.

    Model: 55.1 m/s, between the two. Head mass 250 g is an ASSUMPTION --
    the paper's clubhead is not specified in Penner's summary and this repo
    has no per-club head mass -- and 24 degrees is the floor of the repo's
    own 4-iron loft range. The result is therefore a bracket, not a match.
    """
    four_iron = HeadMassProperties.from_industry_units(
        250.0, (0.0, 0.0, -8.0), np.diag([3000.0, 5000.0, 4000.0]))
    result = solve_impact(four_iron, ball, SwingConditions(40.0, math.radians(24.0)), CENTRE)

    assert 54.0 < result.ball_speed_mps < 56.9
