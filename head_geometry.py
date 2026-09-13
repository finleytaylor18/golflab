"""A parametric clubhead: a few design numbers in, mass properties out.

WHAT THIS IS FOR
----------------
The impact model needs a head's mass, centre of gravity and full inertia
tensor, and a tensor is an integral over an actual shape. There is no CAD
model yet. This module makes the shape a DESIGN INPUT: the designer states an
idealised head -- a thin ellipsoidal body shell truncated at the face plane,
a flat face plate filling the opening, a hosel and some weights, each with a
mass -- and the tensor is derived from that by superposition.

A head defined this way is a design, named `design_*`, and never a product.
Its mass properties are DERIVED from the stated inputs; the idealised shape
is an ESTIMATE of a real driver's, and the outputs say so.

THE ONE IDEA
------------
An assembly's mass properties are the sum of its parts', once every part's
tensor is shifted to the same point (the parallel-axis theorem). So: work
out each part about its own centre, then assemble. The body shell is the
only part without a closed form, and mesh_mass_properties integrates it.

FRAME
-----
Everything the designer types and everything returned is in the HEAD FRAME
of docs/impact_architecture.md section 1: origin at the geometric face
centre, +x toward the heel, +y toward the crown, +z along the outward face
normal. The ellipsoid's centre is a derived point (0, 0, -z_f) behind the
face; the designer never sees it.
"""

import math
from dataclasses import dataclass, field

import numpy as np

from head_mass_properties import FaceGeometry, HeadMassProperties
from mesh_mass_properties import (CROWN, SOLE, ellipsoid_surface_mesh,
                                  surface_mass_properties, triangle_areas)
from units import grams_to_kg, kg_m2_to_g_cm2, kg_to_grams, m_to_mm, mm_to_m

# Equipment Rules Part 2 section 4b(i) -- woodheads, measured at a 60 degree
# lie angle. Page numbers are the PDF's. Reported against, never enforced.
RULES_MAX_HEEL_TOE_MM = 127.0            # p.51
RULES_MAX_SOLE_CROWN_MM = 71.12          # p.51
RULES_MAX_VOLUME_CC = 460.0              # p.52
RULES_VOLUME_TOLERANCE_CC = 10.0         # p.52
RULES_CITATION = "Equipment Rules Part 2 section 4b(i), pp.51-52; MOI limit p.54"

# A driver head is about 200 g. Outside this band the design is more likely
# a slip than an intention, so it is worth a warning -- but only a warning.
PLAUSIBLE_HEAD_MASS_G = (150.0, 250.0)


def position_from_toe_crown_back_mm(toe_mm: float, crown_mm: float, back_mm: float) -> np.ndarray:
    """Head-frame position, in metres, from how a designer describes one.

    +x is the heel, so a toe offset carries a sign flip; +z is outward, so
    "back" does too. This is the only place those two flips live.
    """
    return np.array([mm_to_m(-toe_mm), mm_to_m(crown_mm), mm_to_m(-back_mm)])


@dataclass(frozen=True)
class MeshResolution:
    """How finely the shell is tessellated. A numerical setting, not a design one."""

    n_theta: int = 180      # polar divisions, face plane to back pole
    n_phi: int = 360        # around the axis; even, so y = 0 is a grid line

    def __post_init__(self):
        if self.n_theta < 2 or self.n_phi < 4 or self.n_phi % 2:
            raise ValueError("need n_theta >= 2 and an even n_phi >= 4")


@dataclass
class PointMass:
    """A hosel or a weight: a mass at a place, in the designer's words."""

    name: str
    mass_g: float
    toe_mm: float           # + toward the toe
    crown_mm: float         # + toward the crown
    back_mm: float          # + deeper into the head, from the face plane

    def __post_init__(self):
        if not self.name:
            raise ValueError("a point mass needs a name")
        if not math.isfinite(self.mass_g) or self.mass_g < 0.0:
            raise ValueError(f"{self.name}: mass_g must be non-negative and finite (got {self.mass_g})")
        for label, value in (("toe_mm", self.toe_mm), ("crown_mm", self.crown_mm), ("back_mm", self.back_mm)):
            if not math.isfinite(value):
                raise ValueError(f"{self.name}: {label} must be finite")

    @property
    def position_m(self) -> np.ndarray:
        return position_from_toe_crown_back_mm(self.toe_mm, self.crown_mm, self.back_mm)


@dataclass
class HeadDesign:
    """Seven numbers, a hosel and a list of weights. That is the whole design.

    Industry units, because this is the designer's boundary: millimetres and
    grams. Everything derived from it is SI.
    """

    name: str
    half_width_mm: float        # a: ellipsoid semi-axis, heel-toe
    half_height_mm: float       # b: sole-crown
    half_depth_mm: float        # c: face-back
    face_width_mm: float        # where the face plane cuts the ellipsoid; < 2a
    crown_mass_g: float         # shell above y = 0
    sole_mass_g: float          # shell below y = 0
    face_mass_g: float
    hosel: PointMass
    weights: list = field(default_factory=list)
    mesh: MeshResolution = field(default_factory=MeshResolution)

    def __post_init__(self):
        if not self.name:
            raise ValueError("a design needs a name (a design name, never a product's)")
        for label, value in (("half_width_mm", self.half_width_mm),
                             ("half_height_mm", self.half_height_mm),
                             ("half_depth_mm", self.half_depth_mm)):
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{label} must be positive and finite (got {value})")
        if not 0.0 < self.face_width_mm < 2.0 * self.half_width_mm:
            raise ValueError(
                f"face_width_mm must lie in (0, 2 x half_width_mm): the face plane has to "
                f"cut the ellipsoid, and a face as wide as the head is a tangent line, not "
                f"a face (got {self.face_width_mm} with half_width_mm={self.half_width_mm})"
            )
        for label, value in (("crown_mass_g", self.crown_mass_g),
                             ("sole_mass_g", self.sole_mass_g),
                             ("face_mass_g", self.face_mass_g)):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{label} must be non-negative and finite (got {value})")
        if self.total_mass_g <= 0.0:
            raise ValueError("the design has no mass")

        # A point mass outside the head's bounding box is a typo, not a design.
        # (Outside the ellipsoid surface but inside the box is a warning: a
        # hosel legitimately protrudes.)
        depth_mm = self.face_offset_mm + self.half_depth_mm
        for part in [self.hosel, *self.weights]:
            if abs(part.toe_mm) > self.half_width_mm or abs(part.crown_mm) > self.half_height_mm \
                    or not 0.0 <= part.back_mm <= depth_mm:
                raise ValueError(
                    f"{part.name} at (toe {part.toe_mm}, crown {part.crown_mm}, back {part.back_mm}) mm "
                    f"lies outside the head's bounding box "
                    f"(|toe| <= {self.half_width_mm}, |crown| <= {self.half_height_mm}, "
                    f"0 <= back <= {depth_mm:.1f})"
                )

    # -- derived, never typed ---------------------------------------------

    @property
    def face_offset_mm(self) -> float:
        """z_f: how far the face plane sits in front of the ellipsoid centre."""
        ratio = self.face_width_mm / (2.0 * self.half_width_mm)
        return self.half_depth_mm * math.sqrt(1.0 - ratio * ratio)

    @property
    def face_half_width_mm(self) -> float:
        return self.face_width_mm / 2.0

    @property
    def face_half_height_mm(self) -> float:
        scale = math.sqrt(1.0 - (self.face_offset_mm / self.half_depth_mm) ** 2)
        return self.half_height_mm * scale

    @property
    def face_to_back_mm(self) -> float:
        """Face plane to back pole -- what the Rules call face-to-back."""
        return self.face_offset_mm + self.half_depth_mm

    @property
    def total_mass_g(self) -> float:
        return (self.crown_mass_g + self.sole_mass_g + self.face_mass_g
                + self.hosel.mass_g + sum(w.mass_g for w in self.weights))

    def cap_volume_mm3(self) -> float:
        """Volume of the ellipsoid in front of the face plane (removed).

        Integrating the cross-section pi a b (1 - z^2/c^2) from z_f to c:
        V = pi a b (2c/3 - z_f + z_f^3 / (3 c^2)). Verified against Monte
        Carlo to 0.02% and exact at both endpoints (see the architecture doc).
        """
        a, b, c, z = self.half_width_mm, self.half_height_mm, self.half_depth_mm, self.face_offset_mm
        return math.pi * a * b * (2.0 * c / 3.0 - z + z ** 3 / (3.0 * c * c))

    def volume_cc(self) -> float:
        a, b, c = self.half_width_mm, self.half_height_mm, self.half_depth_mm
        return (4.0 / 3.0 * math.pi * a * b * c - self.cap_volume_mm3()) / 1000.0

    def is_inside_ellipsoid(self, position_m: np.ndarray) -> bool:
        x, y, z = m_to_mm(position_m[0]), m_to_mm(position_m[1]), m_to_mm(position_m[2])
        z_ellipsoid = z + self.face_offset_mm       # head frame -> ellipsoid frame
        return ((x / self.half_width_mm) ** 2 + (y / self.half_height_mm) ** 2
                + (z_ellipsoid / self.half_depth_mm) ** 2) <= 1.0 + 1e-9


# ---------------------------------------------------------------------------
# PARTS AND ASSEMBLY
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Part:
    """One component about its own centre of gravity, in the head frame, SI."""

    name: str
    mass_kg: float
    cg_m: np.ndarray
    inertia_about_own_cg: np.ndarray


@dataclass(frozen=True)
class PartContribution:
    """What one part adds to the assembled head. The shares are a partition:
    across all parts they sum to 1, and the CG pulls sum to zero.
    """

    name: str
    mass_g: float
    mass_share: float
    cg_pull_mm: np.ndarray          # m_i (r_i - r_cg) / M, in mm
    inertia_g_cm2: np.ndarray       # this part's term of I_cg (own tensor + parallel axis)
    ixx_share: float
    iyy_share: float


def assemble(parts: list) -> tuple:
    """Superpose parts about a common point: (mass, cg, inertia_about_cg, contributions).

    I_cg = sum_i [ I_i + m_i ( |d_i|^2 1 - d_i d_i^T ) ],  d_i = r_i - r_cg.
    """
    mass = sum(p.mass_kg for p in parts)
    if mass <= 0.0:
        raise ValueError("nothing to assemble")
    cg = sum(p.mass_kg * p.cg_m for p in parts) / mass

    terms = []
    for p in parts:
        d = p.cg_m - cg
        terms.append(p.inertia_about_own_cg + p.mass_kg * (float(d @ d) * np.eye(3) - np.outer(d, d)))
    inertia = sum(terms)

    contributions = [
        PartContribution(
            name=p.name,
            mass_g=kg_to_grams(p.mass_kg),
            mass_share=p.mass_kg / mass,
            cg_pull_mm=m_to_mm(p.mass_kg * (p.cg_m - cg) / mass),
            inertia_g_cm2=kg_m2_to_g_cm2(term),
            ixx_share=float(term[0, 0] / inertia[0, 0]),
            iyy_share=float(term[1, 1] / inertia[1, 1]),
        )
        for p, term in zip(parts, terms)
    ]
    return mass, cg, inertia, contributions


def shell_parts(design: HeadDesign) -> tuple:
    """The crown and sole halves of the truncated shell, as two parts."""
    a, b, c = (mm_to_m(v) for v in (design.half_width_mm, design.half_height_mm, design.half_depth_mm))
    z_f = mm_to_m(design.face_offset_mm)

    vertices, triangles, region = ellipsoid_surface_mesh(
        a, b, c, design.mesh.n_theta, design.mesh.n_phi, z_max=z_f)
    vertices = vertices + np.array([0.0, 0.0, -z_f])     # ellipsoid frame -> head frame
    areas = triangle_areas(vertices, triangles)

    parts = []
    for label, tag, mass_g in (("crown shell", CROWN, design.crown_mass_g),
                               ("sole shell", SOLE, design.sole_mass_g)):
        if mass_g <= 0.0:
            continue
        chosen = region == tag
        masses = grams_to_kg(mass_g) * areas[chosen] / areas[chosen].sum()
        props = surface_mass_properties(vertices, triangles[chosen], masses)
        parts.append(Part(label, props.mass_kg, props.cg_m, props.inertia_about_cg))
    return tuple(parts)


def face_plate_part(design: HeadDesign) -> Part:
    """Thin elliptical plate at the origin: I = m/4 (b_f^2, a_f^2, a_f^2 + b_f^2)."""
    m = grams_to_kg(design.face_mass_g)
    a_f, b_f = mm_to_m(design.face_half_width_mm), mm_to_m(design.face_half_height_mm)
    inertia = m / 4.0 * np.diag([b_f * b_f, a_f * a_f, a_f * a_f + b_f * b_f])
    return Part("face plate", m, np.zeros(3), inertia)


def point_mass_part(point: PointMass) -> Part:
    return Part(point.name, grams_to_kg(point.mass_g), point.position_m, np.zeros((3, 3)))


# ---------------------------------------------------------------------------
# THE RESULT
# ---------------------------------------------------------------------------

@dataclass
class DesignResult:
    head: HeadMassProperties
    breakdown: list
    conformance: dict
    warnings: list
    design: HeadDesign


def design_mass_properties(design: HeadDesign) -> DesignResult:
    """Everything the impact model needs, derived from the design. Pure."""
    parts = [*shell_parts(design)]
    if design.face_mass_g > 0.0:
        parts.append(face_plate_part(design))
    for point in [design.hosel, *design.weights]:
        if point.mass_g > 0.0:
            parts.append(point_mass_part(point))

    mass, cg, inertia, breakdown = assemble(parts)

    face = FaceGeometry(mm_to_m(design.face_half_width_mm), mm_to_m(design.face_half_height_mm),
                        outline_source="design", shape="ellipse")
    head = HeadMassProperties(mass_kg=mass, cg_m=cg, inertia_about_cg=inertia, face=face)

    return DesignResult(head=head, breakdown=breakdown,
                        conformance=conformance_trio(design, head),
                        warnings=design_warnings(design), design=design)


def conformance_trio(design: HeadDesign, head: HeadMassProperties) -> dict:
    """Dimensions, volume and MOI against the Equipment Rules. A report."""
    moi = head.conformance_report()
    heel_toe = 2.0 * design.half_width_mm
    sole_crown = 2.0 * design.half_height_mm
    volume = design.volume_cc()
    return {
        "heel_toe_mm": heel_toe,
        "heel_toe_conforms": heel_toe <= RULES_MAX_HEEL_TOE_MM,
        "sole_crown_mm": sole_crown,
        "sole_crown_conforms": sole_crown <= RULES_MAX_SOLE_CROWN_MM,
        "face_to_back_mm": design.face_to_back_mm,
        "proportion_conforms": heel_toe > design.face_to_back_mm,
        "volume_cc": volume,
        "volume_conforms": volume <= RULES_MAX_VOLUME_CC + RULES_VOLUME_TOLERANCE_CC,
        "rules_frame_moi_g_cm2": moi["rules_frame_moi_g_cm2"],
        "moi_conforms": moi["conforms"],
        "conforms": all([heel_toe <= RULES_MAX_HEEL_TOE_MM, sole_crown <= RULES_MAX_SOLE_CROWN_MM,
                         heel_toe > design.face_to_back_mm,
                         volume <= RULES_MAX_VOLUME_CC + RULES_VOLUME_TOLERANCE_CC, moi["conforms"]]),
        "citation": RULES_CITATION,
    }


def design_warnings(design: HeadDesign) -> list:
    warnings = []
    for point in [design.hosel, *design.weights]:
        if point.mass_g > 0.0 and not design.is_inside_ellipsoid(point.position_m):
            warnings.append(f"{point.name} sits outside the shell surface (inside the box, so allowed)")
    low, high = PLAUSIBLE_HEAD_MASS_G
    if not low <= design.total_mass_g <= high:
        warnings.append(f"total mass {design.total_mass_g:.0f} g is outside the {low:.0f}-{high:.0f} g "
                        f"a driver head usually weighs")
    return warnings


def default_design() -> HeadDesign:
    """A placeholder design the tools open on. NOT a product: every number is
    a round design-intent value chosen so the tool opens on a plausible map.
    Edit it; that is what it is for.
    """
    return HeadDesign(
        name="design_v1 (placeholder, edit me)",
        half_width_mm=60.0, half_height_mm=32.0, half_depth_mm=55.0,
        face_width_mm=100.0,
        crown_mass_g=50.0, sole_mass_g=80.0, face_mass_g=30.0,
        hosel=PointMass("hosel", 12.0, toe_mm=-45.0, crown_mm=20.0, back_mm=20.0),
        weights=[PointMass("toe weight", 14.0, toe_mm=40.0, crown_mm=-10.0, back_mm=65.0),
                 PointMass("heel weight", 14.0, toe_mm=-40.0, crown_mm=-10.0, back_mm=65.0)],
    )
