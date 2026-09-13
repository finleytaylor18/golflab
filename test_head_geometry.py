"""Tests for the parametric head.

The integrator is tested against oracles in test_mesh_mass_properties.py.
These tests check what the ASSEMBLY can get wrong that a single part cannot:
the parallel-axis bookkeeping, the frame, the breakdown being a true
partition, the design levers moving the right way, and the boundary
validation -- plus that the result is something the impact model accepts.
"""

import math
from dataclasses import replace

import numpy as np
import pytest

from head_geometry import (HeadDesign, MeshResolution, Part, PointMass, assemble,
                           conformance_trio, default_design, design_mass_properties,
                           position_from_toe_crown_back_mm)
from units import kg_m2_to_g_cm2


@pytest.fixture
def coarse():
    """A coarse mesh keeps the suite fast; the tensor is still within ~1e-3."""
    return MeshResolution(n_theta=60, n_phi=120)


def design(**overrides) -> HeadDesign:
    base = default_design()
    return replace(base, **overrides)


def test_the_position_helper_owns_both_sign_flips():
    """Proves the designer never types a sign: toe is -x, back is -z."""
    p = position_from_toe_crown_back_mm(14.0, 6.0, 42.0)
    assert p == pytest.approx([-0.014, 0.006, -0.042])


# ---------------------------------------------------------------------------
# ASSEMBLY
# ---------------------------------------------------------------------------

def test_assembling_about_a_shifted_reference_gives_the_same_tensor():
    """Proves the parallel-axis bookkeeping. Translate every part by the same
    offset and the assembled tensor must not change at all, while the CG
    moves by exactly that offset.
    """
    parts = [Part("a", 0.10, np.array([0.01, 0.0, -0.03]), 1e-5 * np.eye(3)),
             Part("b", 0.05, np.array([-0.02, 0.01, -0.05]), np.zeros((3, 3))),
             Part("c", 0.02, np.array([0.03, -0.01, -0.04]), 2e-6 * np.eye(3))]
    offset = np.array([0.123, -0.045, 0.067])
    shifted = [replace(p, cg_m=p.cg_m + offset) for p in parts]

    mass, cg, inertia, _ = assemble(parts)
    mass2, cg2, inertia2, _ = assemble(shifted)

    assert mass2 == pytest.approx(mass)
    assert cg2 == pytest.approx(cg + offset)
    assert np.allclose(inertia2, inertia, rtol=1e-12, atol=1e-18)


def test_the_breakdown_is_a_true_partition(coarse):
    """Proves the shares mean what they say: part contributions sum to the
    assembled tensor, mass shares sum to one, and the CG pulls sum to zero.
    A breakdown that did not partition would be a story, not a decomposition.
    """
    result = design_mass_properties(design(mesh=coarse))
    total = kg_m2_to_g_cm2(result.head.inertia_about_cg)

    assert sum(c.mass_share for c in result.breakdown) == pytest.approx(1.0, abs=1e-12)
    assert sum(c.ixx_share for c in result.breakdown) == pytest.approx(1.0, abs=1e-12)
    assert sum(c.iyy_share for c in result.breakdown) == pytest.approx(1.0, abs=1e-12)
    assert np.allclose(sum(c.inertia_g_cm2 for c in result.breakdown), total, rtol=1e-12)
    assert np.allclose(sum(c.cg_pull_mm for c in result.breakdown), 0.0, atol=1e-9)


# ---------------------------------------------------------------------------
# THE FRAME AND SYMMETRY
# ---------------------------------------------------------------------------

def test_heel_toe_symmetry_kills_the_products_involving_x(coarse):
    """Proves the frame is wired correctly, and which symmetry does what.

    With the hosel removed and the weights mirrored, nothing distinguishes
    heel from toe: the CG sits on the centreline, the sweet spot is at the
    face centre, and the products of inertia involving x (I_xy, I_xz) vanish.
    I_yz does NOT vanish -- the sole is heavier than the crown and the weights
    sit below centre, so the head is not mirror-symmetric top to bottom, and
    a y-z product is the correct consequence. A test that demanded all three
    products vanish here would be asserting a symmetry the design does not
    have.
    """
    symmetric = design(mesh=coarse, hosel=PointMass("hosel", 0.0, 0.0, 0.0, 0.0),
                       weights=[PointMass("l", 14.0, 40.0, -10.0, 65.0),
                                PointMass("r", 14.0, -40.0, -10.0, 65.0)])
    inertia = design_mass_properties(symmetric).head.inertia_about_cg
    head = design_mass_properties(symmetric).head

    assert head.cg_m[0] == pytest.approx(0.0, abs=1e-12)
    assert head.sweet_spot_m[0] == pytest.approx(0.0, abs=1e-12)
    assert abs(inertia[0, 1]) < 1e-15 and abs(inertia[0, 2]) < 1e-15
    assert abs(inertia[1, 2]) > 1e-7                  # ~70 g.cm^2: real, and expected


def test_full_mirror_symmetry_kills_every_product_of_inertia(coarse):
    """Proves the complement: equal crown and sole masses and weights on the
    centreline make the head symmetric top to bottom as well, and then all
    three products vanish and the principal axes are the head axes.
    """
    fully = design(mesh=coarse, crown_mass_g=65.0, sole_mass_g=65.0,
                   hosel=PointMass("hosel", 0.0, 0.0, 0.0, 0.0),
                   weights=[PointMass("l", 14.0, 40.0, 0.0, 65.0),
                            PointMass("r", 14.0, -40.0, 0.0, 65.0)])
    inertia = design_mass_properties(fully).head.inertia_about_cg
    off_diagonal = inertia - np.diag(np.diag(inertia))
    assert np.allclose(off_diagonal, 0.0, atol=1e-14)


def test_the_cg_lies_behind_the_face_and_below_centre_for_a_heavy_sole(coarse):
    """Proves two physical facts of the default design: everything but the
    face plate sits behind the face plane, so the CG has negative z; and an
    80 g sole against a 50 g crown pulls it below the centreline.
    """
    head = design_mass_properties(design(mesh=coarse)).head
    assert head.cg_m[2] < -0.020
    assert head.cg_m[1] < 0.0
    assert head.cg_depth_m == pytest.approx(-head.cg_m[2])


def test_the_hosel_pulls_the_cg_toward_the_heel(coarse):
    """Proves the one asymmetric part does what it should: the hosel is on
    the heel side (+x), so the CG and the sweet spot move that way.
    """
    head = design_mass_properties(design(mesh=coarse)).head
    assert head.cg_m[0] > 0.0
    assert head.sweet_spot_m[0] > 0.0


# ---------------------------------------------------------------------------
# THE DESIGN LEVERS
# ---------------------------------------------------------------------------

def test_moving_mass_to_the_rear_deepens_the_cg_and_raises_the_moi(coarse):
    """Proves the rear-weight lever: mass far behind the CG adds to both
    Ixx and Iyy through the parallel-axis term, and pulls the CG back.
    """
    base = design(mesh=coarse, weights=[])
    rear = design(mesh=coarse, weights=[PointMass("rear", 28.0, 0.0, -10.0, 80.0)])
    h0, h1 = design_mass_properties(base).head, design_mass_properties(rear).head

    assert h1.cg_depth_m > h0.cg_depth_m
    assert h1.inertia_about_cg[0, 0] > h0.inertia_about_cg[0, 0]
    assert h1.inertia_about_cg[1, 1] > h0.inertia_about_cg[1, 1]


def test_a_heel_toe_pair_raises_iyy_more_than_ixx(coarse):
    """Proves the perimeter-weighting lever: weights out at the heel and toe
    are far from the crown-sole axis (Iyy) but not from the toe-heel axis
    (Ixx), so Iyy gains more. This is what a "high-MOI" driver does.
    """
    base = design(mesh=coarse, weights=[])
    pair = design(mesh=coarse, weights=[PointMass("t", 14.0, 45.0, 0.0, 40.0),
                                        PointMass("h", 14.0, -45.0, 0.0, 40.0)])
    h0, h1 = design_mass_properties(base).head, design_mass_properties(pair).head

    gain_xx = h1.inertia_about_cg[0, 0] / h0.inertia_about_cg[0, 0] - 1.0
    gain_yy = h1.inertia_about_cg[1, 1] / h0.inertia_about_cg[1, 1] - 1.0
    assert gain_yy > 2.0 * gain_xx > 0.0


def test_a_lighter_crown_lowers_the_cg(coarse):
    """Proves the crown-lightening lever: moving 30 g from the crown to the
    sole, at fixed total mass, lowers the CG. This is the modern carbon-crown
    design move, and the vertical gear effect depends on it.
    """
    heavy_crown = design(mesh=coarse, crown_mass_g=80.0, sole_mass_g=50.0)
    light_crown = design(mesh=coarse, crown_mass_g=50.0, sole_mass_g=80.0)
    y_heavy = design_mass_properties(heavy_crown).head.cg_m[1]
    y_light = design_mass_properties(light_crown).head.cg_m[1]

    assert y_light < y_heavy


# ---------------------------------------------------------------------------
# OUTPUTS THE IMPACT MODEL AND THE RULES CARE ABOUT
# ---------------------------------------------------------------------------

def test_the_result_is_a_validated_head_with_a_designed_outline(coarse):
    """Proves the output is something the impact model accepts as-is, with
    the face outline derived from the design and labelled as such.
    """
    result = design_mass_properties(design(mesh=coarse))
    head, d = result.head, result.design

    assert head.mass_kg == pytest.approx(0.200, rel=1e-12)
    assert head.face.shape == "ellipse"
    assert head.face.outline_source == "design"
    assert "from design" in head.face.describe()
    assert head.face.half_width_m == pytest.approx(0.050, rel=1e-12)
    assert head.face.half_height_m == pytest.approx(d.face_half_height_mm / 1000.0, rel=1e-12)
    assert head.face.half_height_m < 0.032          # the plane cuts inside the semi-axis


def test_the_default_design_is_plausible_and_conforming(coarse):
    """Proves the placeholder opens on something sensible: 200 g, no
    warnings, inside every Rules limit, and a Rules-frame MOI in the low
    thousands of g.cm^2 -- the band a real driver occupies.
    """
    result = design_mass_properties(design(mesh=coarse))

    assert result.warnings == []
    assert result.conformance["conforms"] is True
    assert 2500.0 < result.conformance["rules_frame_moi_g_cm2"] < 5900.0
    assert result.conformance["volume_cc"] == pytest.approx(385.9, abs=0.5)


def test_the_conformance_trio_uses_the_cited_limits(coarse):
    """Proves the design box is the Rules' box, and that face-to-back is
    measured from the face plane to the back pole, not as 2c.
    """
    d = design(mesh=coarse)
    report = conformance_trio(d, design_mass_properties(d).head)

    assert report["heel_toe_mm"] == pytest.approx(120.0)
    assert report["sole_crown_mm"] == pytest.approx(64.0)
    assert report["face_to_back_mm"] == pytest.approx(d.face_offset_mm + 55.0)
    assert report["face_to_back_mm"] < 110.0
    assert report["proportion_conforms"] is True
    assert "p.51" in report["citation"] and "p.54" in report["citation"]

    wide = design(mesh=coarse, half_width_mm=65.0, face_width_mm=100.0)      # 130 mm > 127
    assert conformance_trio(wide, design_mass_properties(wide).head)["heel_toe_conforms"] is False


def test_the_truncated_volume_matches_the_closed_form():
    """Proves the cap formula in code agrees with the value verified during
    the architecture phase: 442.3 cc whole, 56.5 cc cap, 385.9 cc kept.
    """
    d = design()
    assert d.cap_volume_mm3() / 1000.0 == pytest.approx(56.46, abs=0.05)
    assert d.volume_cc() == pytest.approx(385.9, abs=0.1)


def test_the_uniform_shell_lands_near_the_briefs_pre_check(coarse):
    """Proves the documented order of magnitude. The brief's closed-form
    pre-check for a 200 g untruncated shell gave a Rules-frame MOI of about
    3630 g.cm^2. The truncated, uniform-surface shell with a face plate is
    a different (better) model, so agreement is to within a band, not a
    number -- but a factor-of-two disagreement would mean one of them is
    wrong.
    """
    shell_only = design(mesh=coarse, crown_mass_g=100.0, sole_mass_g=100.0, face_mass_g=0.0,
                        hosel=PointMass("hosel", 0.0, 0.0, 0.0, 0.0), weights=[])
    moi = design_mass_properties(shell_only).conformance["rules_frame_moi_g_cm2"]
    assert 0.7 * 3630.0 < moi < 1.3 * 3630.0


def test_a_finer_mesh_barely_moves_the_answer():
    """Proves the default resolution is converged for design purposes."""
    coarse_head = design_mass_properties(design(mesh=MeshResolution(60, 120))).head
    fine_head = design_mass_properties(design(mesh=MeshResolution(180, 360))).head
    assert np.allclose(coarse_head.inertia_about_cg, fine_head.inertia_about_cg, rtol=2e-3)


# ---------------------------------------------------------------------------
# WARNINGS AND VALIDATION
# ---------------------------------------------------------------------------

def test_a_protruding_hosel_is_a_warning_not_an_error(coarse):
    """Proves the boundary distinguishes a typo from a real thing: a hosel
    outside the shell surface but inside the box is allowed and reported.
    """
    protruding = design(mesh=coarse, hosel=PointMass("hosel", 12.0, -55.0, 28.0, 5.0))
    result = design_mass_properties(protruding)
    assert any("hosel" in w and "outside the shell" in w for w in result.warnings)


def test_an_implausible_total_mass_is_a_warning(coarse):
    heavy = design(mesh=coarse, sole_mass_g=200.0)
    assert any("total mass" in w for w in design_mass_properties(heavy).warnings)


def test_impossible_designs_are_rejected_at_the_boundary():
    """Proves each rule in the architecture's validation table."""
    with pytest.raises(ValueError, match="face_width_mm"):
        design(face_width_mm=120.0)                      # equals 2a: a tangent, not a face
    with pytest.raises(ValueError, match="half_depth_mm"):
        design(half_depth_mm=0.0)
    with pytest.raises(ValueError, match="crown_mass_g"):
        design(crown_mass_g=-1.0)
    with pytest.raises(ValueError, match="outside the head's bounding box"):
        design(weights=[PointMass("far", 5.0, 0.0, 0.0, 200.0)])
    with pytest.raises(ValueError, match="needs a name"):
        design(name="")
    with pytest.raises(ValueError, match="no mass"):
        design(crown_mass_g=0.0, sole_mass_g=0.0, face_mass_g=0.0,
               hosel=PointMass("hosel", 0.0, 0.0, 0.0, 0.0), weights=[])
    with pytest.raises(ValueError, match="even n_phi"):
        MeshResolution(60, 121)
