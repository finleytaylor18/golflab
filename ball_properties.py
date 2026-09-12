"""Golf ball mass properties and contact constants.

Every number here is a SourcedConstant, so it cannot exist without a unit and
a citation (standing rule 3). Where a value is not sourced it is flagged
`is_estimate=True` and says so in its own citation string -- currently that is
the ball's moment of inertia and nothing else.

Two constants here are speed-dependent in reality and single-valued in v1
(assumptions 4 and 6, docs/impact_model.md section 8): the coefficient of
restitution and the ball-face friction coefficient. Each therefore records the
speed it was measured at, because quoting either without its speed is
meaningless -- COR alone spans 0.85 to 0.78 across the range a driver sees.
"""

import math
from dataclasses import dataclass

from sourced_constant import SourcedConstant
from units import grams_to_kg, mm_to_m

_RULES = "R&A/USGA Equipment Rules"
_PENNER = "Penner 2003, 'The physics of golf', Rep. Prog. Phys. 66"

# --- Equipment Rules limits -------------------------------------------------
# The Rules give a maximum mass and a minimum diameter. They state explicitly
# that there is NO minimum mass, so 45.93 g is a ceiling, not a nominal value.
BALL_MASS_MAX_G = SourcedConstant(
    45.93, "g", f"{_RULES} Part 4 section 2, p.69",
    note="maximum permitted mass (1.620 oz); the Rules state there is no minimum",
)
BALL_DIAMETER_MIN_MM = SourcedConstant(
    42.67, "mm", f"{_RULES} Part 4 section 3, p.69",
    note="minimum permitted diameter (1.680 in)",
)

# --- Contact constants ------------------------------------------------------
# Penner p.144 reports COR falling from 0.85 at 20 m/s to 0.78 at 45 m/s
# (Chou et al 1994). A driver strike is at the top of that range, so 0.78 is
# the right single value for a driver model -- and the wrong one for a wedge.
BALL_COR_AT_45_MPS = SourcedConstant(
    0.78, "dimensionless", f"{_PENNER}, p.144 (Chou et al 1994)",
    note="measured at 45 m/s impact speed; rises to 0.85 at 20 m/s",
)

# Penner p.149 (Gobush 1996a). Construction matters more than anything else
# here: a soft three-piece cover grips roughly 2.5x harder than a hard
# two-piece one, which is why ball choice changes spin at all.
BALL_FRICTION_THREE_PIECE = SourcedConstant(
    0.38, "dimensionless", f"{_PENNER}, p.149 (Gobush 1996a)",
    note="soft-cover three-piece ball at 12.8 m/s tangential speed; "
         "falls to 0.29 by ~26.8 m/s",
)
BALL_FRICTION_TWO_PIECE = SourcedConstant(
    0.16, "dimensionless", f"{_PENNER}, p.149 (Gobush 1996a)",
    note="hard-cover two-piece ball at 12.8 m/s tangential speed; "
         "falls to 0.075 by ~26.8 m/s",
)

# --- Estimate ---------------------------------------------------------------
# The one number in the model with no measured source. A real ball is not
# uniform -- a three-piece ball has a distinct core density -- so the true
# value differs, but no measurement was found in the sources read. See
# docs/impact_model.md section 9 for the sensitivity: a 10% error in alpha
# moves spin by roughly 3%.
BALL_INERTIA_RATIO = SourcedConstant(
    2.0 / 5.0, "dimensionless",
    "ESTIMATE -- uniform solid sphere, I = (2/5) m R^2; no measured value "
    "found in the sources read. See docs/impact_model.md section 9.",
    note="alpha in I_ball = alpha * m * R^2",
    is_estimate=True,
)


@dataclass(frozen=True)
class BallProperties:
    """A golf ball as the impact model sees it: mass, radius, and how it grips.

    The ball is treated as a rigid sphere in the tangential problem
    (assumption 7), so its inertia is isotropic and one scalar describes it.
    """

    mass_kg: float
    radius_m: float
    cor: float
    friction_coefficient: float
    inertia_ratio: float = BALL_INERTIA_RATIO
    description: str = "unspecified ball"

    def __post_init__(self):
        for name, value in (("mass_kg", self.mass_kg),
                            ("radius_m", self.radius_m)):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite (got {value})")
        if not 0.0 < self.cor <= 1.0:
            raise ValueError(
                f"cor must lie in (0, 1] -- a COR above 1 would create energy "
                f"from nothing (got {self.cor})"
            )
        if not math.isfinite(self.friction_coefficient) or self.friction_coefficient < 0:
            raise ValueError(
                f"friction_coefficient must be non-negative and finite "
                f"(got {self.friction_coefficient})"
            )
        # A solid body's inertia ratio cannot exceed 2/3, which is the thin
        # spherical shell -- all the mass at maximum radius. Anything higher is
        # not a sphere.
        if not 0.0 < self.inertia_ratio <= 2.0 / 3.0:
            raise ValueError(
                f"inertia_ratio must lie in (0, 2/3]; 2/5 is a uniform sphere and "
                f"2/3 is a thin shell, the physical maximum (got {self.inertia_ratio})"
            )

    @property
    def inertia_kg_m2(self) -> float:
        """Moment of inertia about any axis through the centre (isotropic)."""
        return self.inertia_ratio * self.mass_kg * self.radius_m ** 2

    def provenance(self) -> list[str]:
        """Every sourced value behind this ball, for the write-up and audits."""
        lines = []
        for name in ("mass_kg", "radius_m", "cor", "friction_coefficient",
                     "inertia_ratio"):
            value = getattr(self, name)
            if isinstance(value, SourcedConstant):
                lines.append(f"{name}: {value.provenance()}")
            else:
                lines.append(f"{name}: {value} -- derived or caller-supplied")
        return lines


def conforming_three_piece_tour_ball() -> BallProperties:
    """A rules-limit three-piece tour ball, as used for the driver model.

    Mass and diameter are set at the Rules limits. That is an ASSUMPTION, not
    a measurement: manufacturers build to the maximum mass and minimum
    diameter because both help ball speed and carry, but this is not a
    specific commercial ball and must never be presented as one.
    """
    return BallProperties(
        mass_kg=SourcedConstant(
            grams_to_kg(BALL_MASS_MAX_G), "kg", BALL_MASS_MAX_G.citation,
            note="assumed built to the Rules maximum mass",
        ),
        radius_m=SourcedConstant(
            mm_to_m(BALL_DIAMETER_MIN_MM) / 2.0, "m", BALL_DIAMETER_MIN_MM.citation,
            note="assumed built to the Rules minimum diameter",
        ),
        cor=BALL_COR_AT_45_MPS,
        friction_coefficient=BALL_FRICTION_THREE_PIECE,
        description="conforming three-piece tour ball at the Rules limits "
                    "(generic, not a commercial product)",
    )
