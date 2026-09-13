"""Validation of the parametric head: what can and cannot be checked.

No source read for this project states a real driver's absolute moment of
inertia -- Penner (2003) is qualitative, the Equipment Rules give only the
ceiling, the MOI protocol gives no example values -- so no published
absolute figure is cited or asserted here. What CAN be checked, honestly:

  * the Rules band: the design lands inside every cited limit, in the right
    order of magnitude, with no tuning;
  * the idealisation bracket: the same shell mass in the same outer box as a
    rectangular box shell (closed form) bounds the ellipsoid from above --
    a real driver lies between the two;
  * a published RELATIVE result, re-run through Step 1's validated engine on
    designed heads (Iwatsubo et al 2000, via Penner p.166);
  * which design inputs matter, and in which direction.

Each test states the published or derived figure and the model's side by
side, and the write-up records the ones that do not agree.
"""

import math
from dataclasses import replace

import numpy as np
import pytest

from ball_properties import conforming_three_piece_tour_ball
from head_geometry import (MeshResolution, PointMass, default_design,
                           design_mass_properties)
from head_mass_properties import strike_from_toe_crown_mm
from impact_model import SwingConditions, solve_impact
from units import kg_m2_to_g_cm2

COARSE = MeshResolution(60, 120)


def design(**overrides):
    return replace(default_design(), mesh=COARSE, **overrides)


def thin_box_shell_g_cm2(length_mm, height_mm, depth_mm, mass_g) -> np.ndarray:
    """Closed form for a thin-walled rectangular box of uniform surface
    density: six plates, each m/12 (q^2, p^2, p^2 + q^2) about its own centre,
    shifted to the box centre by the parallel-axis theorem.
    """
    sigma = mass_g / (2 * (length_mm * height_mm + height_mm * depth_mm + length_mm * depth_mm))
    total = np.zeros((3, 3))

    def plate(p, q, normal, offset):
        m = sigma * p * q
        axes = [i for i in range(3) if i != normal]
        own = np.zeros(3)
        own[axes[0]], own[axes[1]], own[normal] = m * q * q / 12, m * p * p / 12, m * (p * p + q * q) / 12
        r = np.zeros(3)
        r[normal] = offset
        return np.diag(own) + m * (float(r @ r) * np.eye(3) - np.outer(r, r))

    for sign in (+1, -1):
        total += plate(length_mm, height_mm, 2, sign * depth_mm / 2)
        total += plate(height_mm, depth_mm, 0, sign * length_mm / 2)
        total += plate(length_mm, depth_mm, 1, sign * height_mm / 2)
    return np.diag(total) / 100.0            # g mm^2 -> g cm^2


# ---------------------------------------------------------------------------
# THE RULES BAND
# ---------------------------------------------------------------------------

def test_the_placeholder_design_lands_inside_every_cited_limit_without_tuning():
    """Equipment Rules Part 2 section 4b(i): heel-toe <= 127 mm, sole-crown
    <= 71.12 mm, heel-toe > face-back (p.51), volume <= 460 + 10 cc (p.52),
    MOI <= 5900 + 100 g.cm^2 (p.54). The default design was chosen for
    plausibility, not fitted -- and it conforms on all five with a Rules-frame
    MOI in the low thousands, where a mid-forgiveness driver sits.
    """
    report = design_mass_properties(design()).conformance
    assert report["conforms"] is True
    assert 3000.0 < report["rules_frame_moi_g_cm2"] < 4500.0
    assert 350.0 < report["volume_cc"] < 460.0


def test_the_rules_ceiling_is_reachable_only_by_a_bigger_or_heavier_head():
    """The Rules limits exist because they bind -- and the VOLUME limit binds
    first. A design at the placeholder's mass cannot reach 5900 g.cm^2 by
    moving its 28 g of weights alone; growing the shell to the dimensional
    limits (126 x 70 mm) lifts the MOI to ~4770 g.cm^2 but takes the volume
    to ~499 cc, over the 460 + 10 cc limit. So at this mass, high MOI inside
    the Rules has to come from perimeter mass, not size -- which is exactly
    why the Rules carry both limits, and the model reproduces the squeeze.
    """
    at_limits = design(half_width_mm=63.0, half_height_mm=35.0, half_depth_mm=60.0,
                       face_width_mm=100.0,
                       weights=[PointMass("toe", 14.0, 55.0, -12.0, 90.0),
                                PointMass("heel", 14.0, -55.0, -12.0, 90.0)])
    report = design_mass_properties(at_limits).conformance
    assert report["heel_toe_mm"] == pytest.approx(126.0)
    assert report["rules_frame_moi_g_cm2"] > design_mass_properties(design()).conformance["rules_frame_moi_g_cm2"] * 1.15
    assert report["rules_frame_moi_g_cm2"] < 6000.0          # still under the MOI ceiling...
    assert report["volume_conforms"] is False                # ...but over the volume limit first
    assert report["conforms"] is False


# ---------------------------------------------------------------------------
# THE IDEALISATION BRACKET
# ---------------------------------------------------------------------------

def test_a_box_shell_bounds_the_ellipsoidal_shell_from_above():
    """Same shell mass, same outer box: the thin rectangular box (closed form)
    puts all its mass at the extremities, the ellipsoid rounds it inward. A
    real driver is fuller than an ellipsoid and hollower than a box, so the
    two bracket where its shell tensor lies. For the placeholder's box the
    ratio is about 1.5-1.65 on every axis -- that is the size of the shape
    assumption, stated rather than hidden.
    """
    d = design()
    shell_only = replace(d, face_mass_g=0.0, hosel=PointMass("hosel", 0, 0, 0, 0), weights=[])
    ellipsoid = np.diag(kg_m2_to_g_cm2(design_mass_properties(shell_only).head.inertia_about_cg))
    box = thin_box_shell_g_cm2(2 * d.half_width_mm, 2 * d.half_height_mm, d.face_to_back_mm,
                               d.crown_mass_g + d.sole_mass_g)

    ratio = box / ellipsoid
    assert np.all(ratio > 1.0)
    assert np.all((ratio > 1.4) & (ratio < 1.7)), ratio


def test_the_bracket_narrows_for_the_assembled_head():
    """The shell is only part of the head. Face plate, hosel and weights are
    the same in either idealisation, so the ASSEMBLED head's bracket is
    narrower than the shell's: replacing the ellipsoidal shell by the box
    shell (parallel-axis about the same CG) moves Iyy by roughly a third,
    not a half.
    """
    d = design()
    result = design_mass_properties(d)
    ellipsoid_total = np.diag(kg_m2_to_g_cm2(result.head.inertia_about_cg))
    shell_terms = sum(p.inertia_g_cm2 for p in result.breakdown if "shell" in p.name)
    box = thin_box_shell_g_cm2(2 * d.half_width_mm, 2 * d.half_height_mm, d.face_to_back_mm,
                               d.crown_mass_g + d.sole_mass_g)
    # Swap the shell's own-centre tensor for the box's, keep its parallel-axis term.
    shell_own = np.diag(kg_m2_to_g_cm2(design_mass_properties(
        replace(d, face_mass_g=0.0, hosel=PointMass("hosel", 0, 0, 0, 0), weights=[])).head.inertia_about_cg))
    box_total = ellipsoid_total - shell_own + box

    ratio_yy = box_total[1] / ellipsoid_total[1]
    assert 1.2 < ratio_yy < 1.45, ratio_yy
    assert np.diag(shell_terms)[1] / ellipsoid_total[1] > 0.5     # the shell still dominates Iyy


# ---------------------------------------------------------------------------
# A PUBLISHED RELATIVE RESULT, THROUGH STEP 1'S ENGINE
# ---------------------------------------------------------------------------

def test_iwatsubos_moi_effect_on_designed_heads():
    """Iwatsubo et al (2000), via Penner 2003 p.166: a head with about 19%
    more MOI about the vertical axis imparted 2.3 rps instead of 3.1 rps of
    sidespin on a 10 mm toe strike -- a ratio of 0.74.

    Step 1 ran this on a fixture, scaling the tensor alone, and got 0.845.
    Here both heads are DESIGNED and the +19% comes from a larger shell at
    the same mass, which is how Penner says manufacturers raise MOI. The
    direction reproduces; the ratio is 0.915 -- FURTHER from 0.74 than the
    fixture was, and honestly so: growing the shell also moves the CG deeper
    (the gear-effect lever arm), which hands back part of what the extra MOI
    took away. MOI alone does not set gear effect. The larger head is also
    non-conforming (137 mm heel-toe, ~500 cc), so it is a physics comparison,
    not a design. The remaining gap to Iwatsubo is the flat face, as recorded
    in docs/impact_model.md.
    """
    base = design_mass_properties(design())
    target = 1.19 * kg_m2_to_g_cm2(base.head.inertia_about_cg)[1, 1]

    bigger = None
    for scale in np.linspace(1.02, 1.20, 19):
        candidate = design(half_width_mm=60.0 * scale, half_depth_mm=55.0 * scale,
                           face_width_mm=100.0 * scale)
        iyy = kg_m2_to_g_cm2(design_mass_properties(candidate).head.inertia_about_cg)[1, 1]
        if iyy >= target:
            bigger = design_mass_properties(candidate)
            break
    assert bigger is not None
    achieved = kg_m2_to_g_cm2(bigger.head.inertia_about_cg)[1, 1] / kg_m2_to_g_cm2(base.head.inertia_about_cg)[1, 1]
    assert 1.17 < achieved < 1.25

    ball = conforming_three_piece_tour_ball()
    conditions = SwingConditions(45.0, math.radians(10.5))
    strike = strike_from_toe_crown_mm(10.0, 0.0)
    s0 = solve_impact(base.head, ball, conditions, strike).sidespin_rad_s
    s1 = solve_impact(bigger.head, ball, conditions, strike).sidespin_rad_s

    ratio = s1 / s0
    assert 0.0 < ratio < 1.0                    # more MOI, less gear spin
    assert ratio == pytest.approx(0.915, abs=0.01)   # the model's own figure
    assert ratio > 0.845 > 0.74                 # weaker than the fixture, further from Iwatsubo
    assert bigger.head.cg_depth_m > base.head.cg_depth_m     # the reason why
    assert bigger.conformance["conforms"] is False


def test_step_ones_engine_conserves_momentum_on_a_designed_head():
    """Ties the two steps together: the impact model's momentum bookkeeping
    was proven on fixtures; a designed head with a hosel, an offset CG and
    non-zero products of inertia must obey it just the same.
    """
    head = design_mass_properties(design()).head
    ball = conforming_three_piece_tour_ball()
    conditions = SwingConditions(45.0, math.radians(10.5))
    result = solve_impact(head, ball, conditions, strike_from_toe_crown_mm(18.0, 7.0))

    p_before = head.mass_kg * np.array([conditions.head_speed_mps, 0.0, 0.0])
    p_after = (ball.mass_kg * result.ball_velocity_lab_mps
               + head.mass_kg * result.head_velocity_after_lab_mps)
    assert p_after == pytest.approx(p_before, abs=1e-9)
    assert result.energy_after_j < result.energy_before_j


# ---------------------------------------------------------------------------
# WHICH INPUTS MATTER
# ---------------------------------------------------------------------------

def test_half_width_is_the_strongest_lever_on_iyy_and_face_width_pulls_the_other_way():
    """Sensitivity, +10% on each dimension: half-width raises Iyy by about
    its own 10% (mass moves outward on the axis that matters for heel-toe
    forgiveness); a wider face LOWERS Iyy and Ixx and brings the CG forward,
    because the plane cuts more shell off the front. A designer who wants
    forgiveness widens the head, not the face.
    """
    base = design_mass_properties(design())
    I0 = kg_m2_to_g_cm2(base.head.inertia_about_cg)

    def change(**kw):
        I = kg_m2_to_g_cm2(design_mass_properties(design(**kw)).head.inertia_about_cg)
        return I[1, 1] / I0[1, 1] - 1.0, I[0, 0] / I0[0, 0] - 1.0

    d_yy_width, _ = change(half_width_mm=66.0)
    d_yy_height, _ = change(half_height_mm=35.2)
    d_yy_face, d_xx_face = change(face_width_mm=110.0)

    assert 0.08 < d_yy_width < 0.13
    assert d_yy_width > 5 * d_yy_height          # height barely touches Iyy
    assert d_yy_face < 0.0 and d_xx_face < 0.0

    wider_face = design_mass_properties(design(face_width_mm=110.0)).head
    assert wider_face.cg_depth_m < base.head.cg_depth_m
