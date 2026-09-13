"""Clubhead mass properties and face geometry, in the head-fixed frame.

Frame (see docs/impact_architecture.md section 1), right-handed, origin at the
GEOMETRIC CENTRE OF THE FACE:

    x  toe -> heel      (positive toward the HEEL -- see note below)
    y  sole -> crown
    z  outward face normal (away from the face, toward the ball)

The face plane is therefore z = 0, the CG sits at negative z, and CG depth is
just -cg_z. All conventions are for a right-handed head.

WHY x POINTS AT THE HEEL. docs/impact_architecture.md section 1.1 originally
had x pointing at the toe. That triad is LEFT-handed for a right-handed club:
with the crown up and the face normal down the target line, toe x crown =
-outward, not +outward. Cross products, inertia rotations and angular momentum
all assume a right-handed frame, so exactly one axis had to flip, and flipping
x is the only choice that leaves the face normal and the vertical axis -- the
two the physics is written around -- in their natural orientation. It also
happens to be the better choice for plotting: with +x drawn rightward and +y
upward, a forgiveness map is a true face-on view of the club, toe on the left,
which is how a driver face is always photographed and how a launch monitor
draws its impact pattern. So a toe strike is x < 0 and a heel strike x > 0.

The inertia tensor is taken ABOUT THE CG but expressed in head-frame AXES.
Those are two different things and mixing them up is a silent, plausible
looking error, which is why the field is named inertia_about_cg and never
just inertia.
"""

import math
from dataclasses import dataclass, field

import numpy as np

from units import g_cm2_to_kg_m2, grams_to_kg, kg_m2_to_g_cm2, m_to_mm, mm_to_m

# Equipment Rules, Part 2 Section 4b(i), p.54: the moment of inertia about the
# vertical axis through the clubhead's centre of gravity, with the club at a 60
# degree lie angle, must not exceed 5900 g cm^2, plus a 100 g cm^2 tolerance.
# Verified in the joint R&A/USGA Equipment Rules and the MOI test protocol p.3.
CONFORMANCE_MOI_LIMIT_G_CM2 = 5900.0
CONFORMANCE_MOI_TOLERANCE_G_CM2 = 100.0
CONFORMANCE_LIE_ANGLE_DEG = 60.0

# Relative tolerances for the tensor checks. Symmetry is tight because a real
# tensor is exactly symmetric and any asymmetry means a transcription slip. The
# triangle inequality gets a little slack so a legitimately flat body, where
# I1 + I2 == I3 exactly, is not rejected by floating point noise.
_SYMMETRY_RTOL = 1e-9
_TRIANGLE_RTOL = 1e-9


@dataclass
class FaceGeometry:
    """Flat face bounds, used to limit the forgiveness sweep.

    v1 assumes a flat face: no bulge, no roll. The impact solver never looks
    at this at all -- only the forgiveness sweep does, to decide which grid
    points lie on the face and how large that face is.

    The outline defaults to an ELLIPSE because a driver face is far closer to
    one than to a rectangle, and the difference is not cosmetic: a rectangle
    of the same half-extents has 4/pi, about 27%, more area. Since the sweep's
    summary metric is "how much face area keeps at least X% of ball speed",
    a rectangular outline would inflate that number by a quarter.

    `outline_source` says where the outline came from -- "assumed" (a
    guess), "design" (derived from a parametric design), or "measured" (from
    real geometry). Everything that draws a face must say which -- an assumed
    outline produces an assumed area.
    """

    half_width_m: float    # x half-extent, heel <-> toe
    half_height_m: float   # y half-extent, sole <-> crown
    outline_source: str = "assumed"
    shape: str = "ellipse"

    OUTLINE_SOURCES = ("assumed", "design", "measured")

    def __post_init__(self):
        for name, value in (("half_width_m", self.half_width_m),
                            ("half_height_m", self.half_height_m)):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive, finite length (got {value})")
        if self.shape not in {"ellipse", "rectangle"}:
            raise ValueError(f"shape must be 'ellipse' or 'rectangle' (got {self.shape!r})")
        if self.outline_source not in self.OUTLINE_SOURCES:
            raise ValueError(
                f"outline_source must be one of {self.OUTLINE_SOURCES} (got {self.outline_source!r})"
            )

    @property
    def outline_is_measured(self) -> bool:
        """Kept for callers that only care whether the outline is real."""
        return self.outline_source == "measured"

    def contains(self, x_m: float, y_m: float) -> bool:
        if self.shape == "rectangle":
            return abs(x_m) <= self.half_width_m and abs(y_m) <= self.half_height_m
        return ((x_m / self.half_width_m) ** 2
                + (y_m / self.half_height_m) ** 2) <= 1.0

    @property
    def area_m2(self) -> float:
        """Total face area, for expressing the sweep's summary metric."""
        box = self.half_width_m * self.half_height_m
        return math.pi * box if self.shape == "ellipse" else 4.0 * box

    def describe(self) -> str:
        """One line naming the outline and whether it can be trusted."""
        source = {"measured": "measured", "design": "from design",
                  "assumed": "ASSUMED (not measured)"}[self.outline_source]
        return (f"{self.shape} outline, {m_to_mm(2 * self.half_width_m):.0f} x "
                f"{m_to_mm(2 * self.half_height_m):.0f} mm, {source}")


@dataclass
class HeadMassProperties:
    """Mass, CG and full inertia tensor of a clubhead, in the head frame."""

    mass_kg: float
    cg_m: np.ndarray                 # (3,) CG position, origin = face centre
    inertia_about_cg: np.ndarray     # (3,3) kg*m^2, about the CG, head-frame axes
    face: FaceGeometry = field(default_factory=lambda: FaceGeometry(0.050, 0.030))

    def __post_init__(self):
        if not math.isfinite(self.mass_kg) or self.mass_kg <= 0:
            raise ValueError(f"mass_kg must be positive and finite (got {self.mass_kg})")

        self.cg_m = np.asarray(self.cg_m, dtype=float)
        if self.cg_m.shape != (3,):
            raise ValueError(f"cg_m must be a 3-vector (got shape {self.cg_m.shape})")
        if not np.all(np.isfinite(self.cg_m)):
            raise ValueError(f"cg_m must be finite (got {self.cg_m})")

        # The CG must lie behind the face plane. A non-negative z means the CG
        # was placed in front of the striking surface, which is impossible and
        # almost always means a sign convention was mixed up on import.
        if self.cg_m[2] >= 0.0:
            raise ValueError(
                f"cg_m z-component must be negative -- the CG lies behind the face plane, "
                f"and +z is the outward face normal (got cg_z={self.cg_m[2]})"
            )

        self.inertia_about_cg = np.asarray(self.inertia_about_cg, dtype=float)
        if self.inertia_about_cg.shape != (3, 3):
            raise ValueError(
                f"inertia_about_cg must be a 3x3 tensor (got shape {self.inertia_about_cg.shape})"
            )
        if not np.all(np.isfinite(self.inertia_about_cg)):
            raise ValueError("inertia_about_cg must be finite")

        if not np.allclose(self.inertia_about_cg, self.inertia_about_cg.T, rtol=_SYMMETRY_RTOL):
            raise ValueError(
                "inertia_about_cg must be symmetric; an asymmetric tensor usually means a "
                "transposed or mis-transcribed import"
            )

        principal = np.linalg.eigvalsh(self.inertia_about_cg)
        if principal[0] <= 0.0:
            raise ValueError(
                f"inertia_about_cg must be positive-definite (principal moments {principal})"
            )

        # Triangle inequality: for any real rigid body each principal moment is
        # an integral of mass times squared distance, so no one moment can
        # exceed the sum of the other two. A tensor can be symmetric AND
        # positive-definite and still be physically impossible -- which is
        # exactly what a mis-transcribed or wrongly-united export looks like.
        i1, i2, i3 = principal
        if i1 + i2 < i3 * (1.0 - _TRIANGLE_RTOL):
            raise ValueError(
                f"principal moments {principal} violate the triangle inequality "
                f"(I1 + I2 >= I3); no real rigid body has this inertia tensor"
            )

    @classmethod
    def from_industry_units(cls, mass_g: float, cg_mm, inertia_g_cm2,
                            face_half_width_mm: float = 50.0,
                            face_half_height_mm: float = 30.0) -> "HeadMassProperties":
        """Build from the units a CAD package and a spec sheet actually use.

        This is the unit boundary (standing rule 6): grams, millimetres and
        g*cm^2 go in, SI comes out, and nothing downstream ever sees a
        non-SI number. Going through here rather than converting by hand is
        the whole defence against the 10^7 inertia error.
        """
        return cls(
            mass_kg=grams_to_kg(mass_g),
            cg_m=np.array([mm_to_m(v) for v in cg_mm]),
            inertia_about_cg=g_cm2_to_kg_m2(np.asarray(inertia_g_cm2, dtype=float)),
            face=FaceGeometry(mm_to_m(face_half_width_mm), mm_to_m(face_half_height_mm)),
        )

    @property
    def cg_depth_m(self) -> float:
        """Perpendicular distance from the face plane back to the CG (positive).

        This is the quantity gear effect scales with: it vanishes as the CG
        approaches the face plane. See docs/impact_model.md section 4.2.
        """
        return -float(self.cg_m[2])

    @property
    def sweet_spot_m(self) -> np.ndarray:
        """The CG projected forward onto the face plane along the face normal.

        Equipment Rules COR protocol p.4 defines the test impact location as
        "the projection of the clubhead Centre of Mass through the club face",
        so this is the governing bodies' definition, not merely our convention.
        """
        return np.array([self.cg_m[0], self.cg_m[1], 0.0])

    def moment_arm_m(self, strike_m: np.ndarray) -> np.ndarray:
        """Offset of a strike point from the sweet spot, within the face plane.

        Zero exactly at the sweet spot, which is what makes the effective mass
        equal the full head mass there.
        """
        strike = np.asarray(strike_m, dtype=float)
        point = np.array([strike[0], strike[1], 0.0])
        return point - self.sweet_spot_m

    def rules_frame_moi_g_cm2(self) -> float:
        """MOI about the lab vertical with the head at 60 degrees of lie.

        This is NOT I_yy. The Equipment Rules measure about the vertical axis
        of the clubhead oriented at a 60 degree lie angle (MOI protocol p.3),
        and our y axis is head-fixed, so at 60 degrees of lie it sits 30
        degrees off the lab vertical. Comparing the two requires this rotation.

        Setting the lie angle rotates the head about the FACE NORMAL, not
        about the toe-heel axis: a more upright lie lifts the toe and drops
        the heel, which is a rotation in the plane of the face. So the lab
        vertical, written in head coordinates, leans toward the toe (-x) by
        the same 30 degrees. The sign of that lean only changes the answer
        when the tensor has a non-zero I_xy, but it is set correctly here so
        that a real Fusion export gives a real conformance number.
        """
        tilt = math.radians(90.0 - CONFORMANCE_LIE_ANGLE_DEG)
        vertical = np.array([-math.sin(tilt), math.cos(tilt), 0.0])
        moi_kg_m2 = float(vertical @ self.inertia_about_cg @ vertical)
        return kg_m2_to_g_cm2(moi_kg_m2)

    def conformance_report(self) -> dict:
        """Compare against the Equipment Rules MOI ceiling.

        Deliberately a report and not a validation error: GolfLab is a design
        and R&D tool, and modelling a non-conforming head is a legitimate thing
        to want to do. A value wildly outside the band is also the fastest way
        to notice a g*cm^2 / kg*m^2 unit slip on import.
        """
        moi = self.rules_frame_moi_g_cm2()
        ceiling = CONFORMANCE_MOI_LIMIT_G_CM2 + CONFORMANCE_MOI_TOLERANCE_G_CM2
        return {
            "rules_frame_moi_g_cm2": moi,
            "limit_g_cm2": CONFORMANCE_MOI_LIMIT_G_CM2,
            "limit_with_tolerance_g_cm2": ceiling,
            "conforms": moi <= ceiling,
            "citation": "Equipment Rules Part 2 Section 4b(i), p.54; MOI test protocol p.3",
        }


def strike_from_toe_crown_mm(toe_mm: float, crown_mm: float) -> np.ndarray:
    """Build a strike point from how a golfer describes one.

    `toe_mm` is millimetres toward the TOE (negative means toward the heel);
    `crown_mm` is millimetres toward the CROWN (negative means toward the
    sole). Since +x points at the heel, the toe offset carries a sign flip,
    and this function exists so that flip lives in exactly one place instead
    of in the head of whoever is writing the call.
    """
    return np.array([mm_to_m(-toe_mm), mm_to_m(crown_mm), 0.0])
