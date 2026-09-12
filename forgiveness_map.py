"""Sweep the strike location across the face and report what changes.

This is the payoff of the impact model. One impact tells you what a strike
does; a sweep tells you what the HEAD does -- how fast the penalty grows as
the golfer misses, and in which direction the misses hurt least. That is the
quantity a designer is actually trading MOI and CG position against.

Computation only. Nothing here draws anything; forgiveness_diagram.py does
that, keeping the project's calculation/display separation.

TWO THINGS THIS MAP WILL NOT TELL YOU
-------------------------------------
1. It is a map of LAUNCH conditions, not of outcomes. A toe strike that keeps
   98% of its ball speed but adds 900 rpm of hook spin may well finish further
   from the target than a slower, straighter one. Ranking misses by distance
   needs ball flight, which is out of scope for this step.
2. v1 applies one COR everywhere on the face. A real face is more lively in
   the centre and stiffer at the perimeter, so a real head loses MORE ball
   speed off-centre than this map shows. The map is therefore optimistic
   about forgiveness, and consistently so -- see docs/impact_model.md
   section 9.

AND THE BIGGEST CAVEAT OF ALL: v1 HAS NO BULGE OR ROLL
------------------------------------------------------
The face is flat. Real drivers are curved horizontally (bulge) and vertically
(roll), and that curvature exists for exactly one reason: to counteract the
gear effect this model computes. A toe strike on a real driver meets a face
that is already aimed right of target, which offsets the draw spin the gear
effect puts on it.

So the further a grid point sits from the sweet spot, the more this map
overstates the curvature a real head would produce. The edges are the least
trustworthy part of the picture, and they are also the part that looks most
dramatic. At the extreme crown edge the vertical gear effect here is strong
enough to cancel loft-induced backspin entirely and go to topspin -- a real
lofted roll would not let that happen. Read the centre of the map with
confidence and the rim with suspicion.
"""

import math
from dataclasses import dataclass, field

import numpy as np

from ball_properties import BallProperties
from head_mass_properties import HeadMassProperties
from impact_model import SwingConditions, solve_impact
from units import m_to_mm, mm_to_m, mps_to_mph, rad_s_to_rpm, radians_to_degrees

# The retention threshold for the summary metric. This is a CHOSEN SETTING,
# not a sourced or industry-standard figure: no governing body or publication
# read for this project defines a "forgiveness area". It is reported alongside
# its own value everywhere it appears so it can never be mistaken for one.
DEFAULT_RETENTION_THRESHOLD_PCT = 97.0


@dataclass(frozen=True)
class MapSettings:
    """How finely to sweep, and what counts as an acceptable miss."""

    spacing_mm: float = 2.0
    retention_threshold_pct: float = DEFAULT_RETENTION_THRESHOLD_PCT

    def __post_init__(self):
        if not math.isfinite(self.spacing_mm) or self.spacing_mm <= 0:
            raise ValueError(f"spacing_mm must be positive (got {self.spacing_mm})")
        if not 0.0 < self.retention_threshold_pct <= 100.0:
            raise ValueError(
                f"retention_threshold_pct must lie in (0, 100] "
                f"(got {self.retention_threshold_pct})"
            )


@dataclass
class ForgivenessMap:
    """A grid of launch conditions over the face, plus where the model strains.

    Every 2D array is indexed [row, column] = [y, x] and holds NaN at grid
    points that fall outside the face outline, so a plot shows the face shape
    without any masking work. Arrays are in DISPLAY units (mm, mph, rpm,
    degrees): this object exists to be read and drawn, and it sits on the
    output side of the unit boundary.
    """

    x_mm: np.ndarray                 # (nx,) grid axis, +x toward the HEEL
    y_mm: np.ndarray                 # (ny,) grid axis, +y toward the CROWN
    on_face: np.ndarray              # (ny, nx) bool
    ball_speed_mph: np.ndarray
    speed_retention_pct: np.ndarray
    backspin_rpm: np.ndarray
    sidespin_rpm: np.ndarray
    spin_axis_deg: np.ndarray
    launch_angle_deg: np.ndarray
    horizontal_launch_deg: np.ndarray
    required_friction: np.ndarray
    exceeds_friction: np.ndarray     # (ny, nx) bool: model extrapolating here
    backspin_reversed: np.ndarray    # (ny, nx) bool: gear effect has beaten loft
    sweet_spot_mm: tuple
    face_centre_mm: tuple = (0.0, 0.0)
    sweet_spot_ball_speed_mph: float = 0.0
    settings: MapSettings = field(default_factory=MapSettings)
    face_description: str = ""
    head_description: str = ""
    ball_description: str = ""
    conditions_description: str = ""

    @property
    def point_area_mm2(self) -> float:
        return self.settings.spacing_mm ** 2

    def forgiving_area_mm2(self, threshold_pct: float = None) -> float:
        """Face area keeping at least `threshold_pct` of sweet-spot ball speed.

        Computed by counting grid cells, so it is only as precise as the grid
        spacing. That is deliberate: a smooth contour would look more exact
        than the underlying face outline, which is usually assumed, deserves.
        """
        threshold = (self.settings.retention_threshold_pct
                     if threshold_pct is None else threshold_pct)
        keeping = np.logical_and(self.on_face, self.speed_retention_pct >= threshold)
        return float(np.count_nonzero(keeping)) * self.point_area_mm2

    def face_area_mm2(self) -> float:
        """Swept face area by the same cell count, so the ratio is consistent."""
        return float(np.count_nonzero(self.on_face)) * self.point_area_mm2

    def forgiving_area_fraction(self, threshold_pct: float = None) -> float:
        face = self.face_area_mm2()
        return self.forgiving_area_mm2(threshold_pct) / face if face > 0.0 else 0.0

    def summary(self) -> dict:
        """The headline numbers, each carrying the setting that produced it."""
        threshold = self.settings.retention_threshold_pct
        on = self.on_face
        return {
            "threshold_pct": threshold,
            "threshold_is_a_chosen_setting": True,
            "forgiving_area_mm2": self.forgiving_area_mm2(),
            "face_area_mm2": self.face_area_mm2(),
            "forgiving_area_fraction": self.forgiving_area_fraction(),
            "sweet_spot_ball_speed_mph": self.sweet_spot_ball_speed_mph,
            "worst_retention_pct": float(np.nanmin(np.where(on, self.speed_retention_pct, np.nan))),
            "max_abs_sidespin_rpm": float(np.nanmax(np.abs(np.where(on, self.sidespin_rpm, np.nan)))),
            "backspin_range_rpm": (
                float(np.nanmin(np.where(on, self.backspin_rpm, np.nan))),
                float(np.nanmax(np.where(on, self.backspin_rpm, np.nan))),
            ),
            "points_needing_more_friction": int(np.count_nonzero(self.exceeds_friction)),
            "points_with_reversed_backspin": int(np.count_nonzero(self.backspin_reversed)),
            "face_description": self.face_description,
        }


def _grid_axis(half_extent_m: float, spacing_mm: float) -> np.ndarray:
    """Symmetric axis through zero, so the face centre is always a grid point.

    Keeping zero on the grid matters: the face centre and, on a symmetric
    head, the sweet spot are the two reference points the map is read
    against, and interpolating to them would blur the comparison.
    """
    half_extent_mm = m_to_mm(half_extent_m)
    steps = int(math.floor(half_extent_mm / spacing_mm))
    return np.arange(-steps, steps + 1, dtype=float) * spacing_mm


def compute_forgiveness_map(head: HeadMassProperties, ball: BallProperties,
                            conditions: SwingConditions,
                            settings: MapSettings = None) -> ForgivenessMap:
    """Solve the impact at every grid point inside the face outline.

    Pure: it reads the three inputs and returns a new map, touching nothing.
    """
    settings = settings or MapSettings()

    x_mm = _grid_axis(head.face.half_width_m, settings.spacing_mm)
    y_mm = _grid_axis(head.face.half_height_m, settings.spacing_mm)
    shape = (len(y_mm), len(x_mm))

    blank = lambda: np.full(shape, np.nan)
    on_face = np.zeros(shape, dtype=bool)
    exceeds = np.zeros(shape, dtype=bool)
    reversed_spin = np.zeros(shape, dtype=bool)
    speed, backspin, sidespin = blank(), blank(), blank()
    spin_axis, launch, horizontal, friction = blank(), blank(), blank(), blank()

    # Baseline is the sweet spot, which the model guarantees is the fastest
    # point on the face -- so every retention figure is at most 100%. It is
    # solved directly rather than read off the grid, because on a head with
    # an off-centre CG the sweet spot will not land on a grid point.
    baseline = solve_impact(head, ball, conditions, head.sweet_spot_m)

    for row, y in enumerate(y_mm):
        for column, x in enumerate(x_mm):
            point_m = np.array([mm_to_m(x), mm_to_m(y), 0.0])
            if not head.face.contains(point_m[0], point_m[1]):
                continue

            result = solve_impact(head, ball, conditions, point_m)
            on_face[row, column] = True
            speed[row, column] = result.ball_speed_mps
            backspin[row, column] = rad_s_to_rpm(result.backspin_rad_s)
            sidespin[row, column] = rad_s_to_rpm(result.sidespin_rad_s)
            launch[row, column] = radians_to_degrees(result.launch_angle_rad)
            horizontal[row, column] = radians_to_degrees(result.horizontal_launch_rad)
            friction[row, column] = result.required_friction
            exceeds[row, column] = not result.is_rolling

            # Spin axis is how a launch monitor reports the same information:
            # the angle the spin vector is tilted from pure backspin. Positive
            # tilts right, which is the direction the ball will curve.
            #
            # It is only defined while there IS backspin. Where the vertical
            # gear effect has overwhelmed the loft the ball leaves with
            # topspin, atan2 wraps past +/-90 degrees, and a "tilt" of 175
            # degrees is not a fade -- it is a different animal. Those points
            # are left as NaN and flagged instead of being quietly plotted.
            if result.backspin_rad_s > 0.0:
                spin_axis[row, column] = radians_to_degrees(
                    math.atan2(result.sidespin_rad_s, result.backspin_rad_s))
            else:
                reversed_spin[row, column] = True

    ball_speed_mph = np.vectorize(mps_to_mph)(speed)
    baseline_mph = mps_to_mph(baseline.ball_speed_mps)

    return ForgivenessMap(
        x_mm=x_mm, y_mm=y_mm, on_face=on_face,
        ball_speed_mph=ball_speed_mph,
        speed_retention_pct=100.0 * speed / baseline.ball_speed_mps,
        backspin_rpm=backspin, sidespin_rpm=sidespin, spin_axis_deg=spin_axis,
        launch_angle_deg=launch, horizontal_launch_deg=horizontal,
        required_friction=friction, exceeds_friction=exceeds,
        backspin_reversed=reversed_spin,
        sweet_spot_mm=(m_to_mm(head.sweet_spot_m[0]), m_to_mm(head.sweet_spot_m[1])),
        sweet_spot_ball_speed_mph=baseline_mph,
        settings=settings,
        face_description=head.face.describe(),
        head_description=f"{head.mass_kg * 1000:.0f} g head, "
                         f"CG depth {m_to_mm(head.cg_depth_m):.1f} mm",
        ball_description=ball.description,
        conditions_description=f"{conditions.head_speed_mps:.1f} m/s, "
                               f"{radians_to_degrees(conditions.loft_rad):.1f} deg loft",
    )


@dataclass
class MapComparison:
    """Head B minus head A, point by point.

    SIGN CONVENTION: delta = B - A, matching `club_comparison.py`, where
    `moi_delta = moi_b - moi_a`. So a positive delta means B is the larger.
    Read "delta_speed_retention_pct > 0" as "B holds its ball speed better
    here than A does".
    """

    x_mm: np.ndarray
    y_mm: np.ndarray
    on_face: np.ndarray                  # points on BOTH faces
    delta_speed_retention_pct: np.ndarray
    delta_ball_speed_mph: np.ndarray
    delta_backspin_rpm: np.ndarray
    delta_sidespin_rpm: np.ndarray
    delta_launch_angle_deg: np.ndarray
    name_a: str = "A"
    name_b: str = "B"
    summary_a: dict = field(default_factory=dict)
    summary_b: dict = field(default_factory=dict)


def compare_maps(name_a: str, map_a: ForgivenessMap,
                 name_b: str, map_b: ForgivenessMap) -> MapComparison:
    """Subtract two maps computed on the same grid.

    The grids must match exactly. Silently interpolating one onto the other
    would be the easy thing to do and would hide a genuine mistake -- two
    heads with different face sizes are not comparable point by point, and a
    difference map that pretends otherwise is worse than no map.
    """
    if not (np.array_equal(map_a.x_mm, map_b.x_mm)
            and np.array_equal(map_a.y_mm, map_b.y_mm)):
        raise ValueError(
            "the two maps use different grids, so they cannot be compared point "
            "by point; recompute both with the same face size and spacing"
        )

    shared = np.logical_and(map_a.on_face, map_b.on_face)
    difference = lambda a, b: np.where(shared, b - a, np.nan)

    return MapComparison(
        x_mm=map_a.x_mm, y_mm=map_a.y_mm, on_face=shared,
        delta_speed_retention_pct=difference(map_a.speed_retention_pct,
                                             map_b.speed_retention_pct),
        delta_ball_speed_mph=difference(map_a.ball_speed_mph, map_b.ball_speed_mph),
        delta_backspin_rpm=difference(map_a.backspin_rpm, map_b.backspin_rpm),
        delta_sidespin_rpm=difference(map_a.sidespin_rpm, map_b.sidespin_rpm),
        delta_launch_angle_deg=difference(map_a.launch_angle_deg, map_b.launch_angle_deg),
        name_a=name_a, name_b=name_b,
        summary_a=map_a.summary(), summary_b=map_b.summary(),
    )
