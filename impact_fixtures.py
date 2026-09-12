"""Synthetic clubheads for testing and worked examples.

NOT PRODUCTS. Every head here is invented. The numbers are chosen to be
plausible for a driver so the results are recognisable, and to make specific
tests sharp -- not to represent any manufacturer's club. None of these may be
quoted as a real clubhead (standing rule 4). Real head data has to come from
a Fusion model or a measurement, and until it does, Phase 4 has nothing real
to sweep.

Everything is in industry units and goes through the unit boundary, which
also makes these a working demonstration of that boundary.
"""

import numpy as np

from head_mass_properties import HeadMassProperties


def fixture_symmetric_head() -> HeadMassProperties:
    """A driver-sized head with its CG exactly behind the face centre.

    The symmetry is the point: the sweet spot sits at (0, 0), so a strike at
    +15 mm and one at -15 mm are mirror images and must give mirror-image
    results. Any asymmetry in the output is a bug, not physics.
    """
    return HeadMassProperties.from_industry_units(
        mass_g=200.0,
        cg_mm=(0.0, 0.0, -35.0),
        inertia_g_cm2=np.diag([3000.0, 5000.0, 4000.0]),
        face_half_width_mm=50.0,
        face_half_height_mm=30.0,
    )


def fixture_offset_cg_head() -> HeadMassProperties:
    """Same head with the CG moved 4 mm toward the heel and 2 mm up.

    Used to prove the model keys off the SWEET SPOT and not off the face
    centre. With an offset CG those two are different points, and a great deal
    of confusion in clubfitting comes from treating them as the same one.
    """
    return HeadMassProperties.from_industry_units(
        mass_g=200.0,
        cg_mm=(4.0, 2.0, -35.0),
        inertia_g_cm2=np.diag([3000.0, 5000.0, 4000.0]),
    )


def fixture_head_with_cg_depth(depth_mm: float) -> HeadMassProperties:
    """The symmetric head with a chosen CG depth, for the gear-effect sweep.

    Depth must stay positive: a CG in the face plane is the limit, not a
    reachable design, and a CG in front of the face is not a rigid body.
    """
    return HeadMassProperties.from_industry_units(
        mass_g=200.0,
        cg_mm=(0.0, 0.0, -depth_mm),
        inertia_g_cm2=np.diag([3000.0, 5000.0, 4000.0]),
    )


def fixture_near_rigid_head(stiffness: float = 1.0e6) -> HeadMassProperties:
    """The symmetric head with its inertia multiplied by a huge factor.

    This is the "infinitely resistant to twisting" limit. It is physically
    impossible -- it violates the triangle inequality's spirit only in scale,
    not in form, so it still validates -- and it exists to show what the
    forgiveness map looks like when off-centre twisting is switched off.
    """
    return HeadMassProperties.from_industry_units(
        mass_g=200.0,
        cg_mm=(0.0, 0.0, -35.0),
        inertia_g_cm2=np.diag([3000.0, 5000.0, 4000.0]) * stiffness,
    )
