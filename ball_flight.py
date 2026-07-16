import math
from dataclasses import dataclass
from club_specification import ClubSpecification, ClubType
from swing_profile import SwingProfile

# --- Physical constants (standard, sourced values) ---
GRAVITY = 9.81            # m/s^2
AIR_DENSITY = 1.225       # kg/m^3, standard sea-level air density at 15 degC
BALL_MASS = 0.0459        # kg, USGA/R&A minimum golf ball mass spec (45.93 g)
BALL_DIAMETER = 0.04267   # m, USGA/R&A minimum golf ball diameter spec (1.680 in)
BALL_RADIUS = BALL_DIAMETER / 2
BALL_CROSS_SECTION_AREA = math.pi * BALL_RADIUS ** 2

MPH_TO_MS = 0.44704
M_TO_YARDS = 1.09361

# --- Aerodynamic approximations ---
# These are physically-motivated but deliberately simplified, flagged the
# same way this project flagged its swing-weight constants: order-of-magnitude
# correct, not a precisely fitted or manufacturer-sourced aerodynamic curve.

DRAG_COEFFICIENT = 0.25
# Typical order-of-magnitude drag coefficient for a dimpled golf ball in
# flight. Real Cd varies with Reynolds number and spin; treated as constant.

LIFT_COEFFICIENT_PER_SPIN_RATIO = 1.5
# Approximate linear relationship between lift coefficient and spin ratio
# (ball surface speed / ball velocity). The real relationship is nonlinear
# and this project doesn't have a verified source for a precise curve, so
# this was calibrated the same way swing_weight.py's constants were: against
# one known reference outcome rather than presented as textbook-exact. A
# ~110 mph clubhead speed driver shot (the __main__ example below) should
# carry roughly 270-290 yards with a ~30 yard peak height -- widely known
# tour-average figures. This coefficient reproduces that (see test_ball_flight.py's
# realistic-driver-shot sanity test). Do not retune this to force a different
# single example to match "more precisely" -- that would fabricate false
# precision, the exact mistake this project already corrected once before.
MAX_LIFT_COEFFICIENT = 0.45  # clamp -- the linear approximation above only holds for typical golf spin ratios

# --- Smash factor: linearly interpolated between two commonly cited reference points ---
_SMASH_FACTOR_LOW_LOFT, _SMASH_FACTOR_LOW_VALUE = 10.0, 1.48    # driver, ~10 deg loft
_SMASH_FACTOR_HIGH_LOFT, _SMASH_FACTOR_HIGH_VALUE = 46.0, 1.23  # pitching wedge, ~46 deg loft
# Commonly published TrackMan average smash-factor figures for these two
# reference clubs, linearly interpolated in between. Not a manufacturer-
# verified curve, and does not account for strike centeredness.
_SMASH_FACTOR_SLOPE = (
    (_SMASH_FACTOR_HIGH_VALUE - _SMASH_FACTOR_LOW_VALUE)
    / (_SMASH_FACTOR_HIGH_LOFT - _SMASH_FACTOR_LOW_LOFT)
)

# --- Launch angle: approximate rules of thumb from golf instruction / launch-monitor literature ---
LAUNCH_ANGLE_LOFT_FACTOR = 0.85
# Roughly 80-85% of dynamic loft converts to launch angle; the remainder
# contributes to spin loft rather than launch. A commonly cited rule of
# thumb, not a precise derivation from impact dynamics.
LAUNCH_ANGLE_ATTACK_FACTOR = 0.35
# A portion of attack angle also raises launch angle (an ascending strike
# launches the ball somewhat higher for the same loft). Also a rule-of-thumb
# figure, not precisely derived.

# --- Spin rate: calibrated from a single commonly cited reference point ---
_SPIN_RATE_REFERENCE_SPIN_LOFT = 11.0    # degrees
_SPIN_RATE_REFERENCE_BALL_SPEED = 150.0  # mph
_SPIN_RATE_REFERENCE_RPM = 2500.0
# A commonly cited driver reference point (~11 deg spin loft, ~150 mph ball
# speed -> ~2500 rpm backspin), used to calibrate a simple proportional
# model. Not a manufacturer curve; real spin rate also depends on strike
# location and club design, which this model does not capture.
SPIN_RATE_CONSTANT = _SPIN_RATE_REFERENCE_RPM / (_SPIN_RATE_REFERENCE_SPIN_LOFT * _SPIN_RATE_REFERENCE_BALL_SPEED)

# --- Initial direction: approximate face/path split ---
FACE_ANGLE_WEIGHT = 0.80
SWING_PATH_WEIGHT = 0.20
# Initial ball direction is dominated by face angle at impact, with path
# contributing the remainder -- popularized publicly by TrackMan's "ball
# flight laws" research. The exact split varies by club and impact
# conditions; treated as constant here.

TIME_STEP = 0.0005      # s, numerical integration step
SAMPLE_INTERVAL = 0.02  # s, how often a trajectory point is recorded for output/plotting
MAX_FLIGHT_TIME = 15.0  # s, safety cutoff

STRAIGHT_THRESHOLD_YARDS = 10.0
CURVE_THRESHOLD_YARDS = 30.0
# Illustrative thresholds for labeling shot shape from lateral deviation at
# landing -- not a precise industry standard, just bucketing for a readable label.


@dataclass
class LaunchConditions:
    ball_speed: float          # mph
    launch_angle: float        # degrees, vertical
    launch_direction: float    # degrees, horizontal, relative to target line; positive = right
    backspin: float            # rpm
    sidespin: float            # rpm; positive = curves right (right-handed golfer convention)
    effective_deloft: float    # degrees; club.loft - swing.dynamic_loft, informative only (see calculate_launch_conditions)


@dataclass
class TrajectoryResult:
    points: list                # list of (distance, lateral, height) tuples, yards, sampled along the flight
    carry_distance: float       # yards
    peak_height: float          # yards
    lateral_deviation: float    # yards at landing; positive = right of target
    shot_shape: str


def calculate_launch_conditions(club: ClubSpecification, swing: SwingProfile) -> LaunchConditions:
    smash_factor = _SMASH_FACTOR_LOW_VALUE + _SMASH_FACTOR_SLOPE * (swing.dynamic_loft - _SMASH_FACTOR_LOW_LOFT)
    smash_factor = max(1.0, min(1.50, smash_factor))
    ball_speed = swing.clubhead_speed * smash_factor

    launch_angle = LAUNCH_ANGLE_LOFT_FACTOR * swing.dynamic_loft + LAUNCH_ANGLE_ATTACK_FACTOR * swing.attack_angle
    launch_direction = FACE_ANGLE_WEIGHT * swing.face_angle + SWING_PATH_WEIGHT * swing.swing_path

    spin_loft = max(0.0, swing.dynamic_loft - swing.attack_angle)
    total_spin = SPIN_RATE_CONSTANT * spin_loft * ball_speed

    face_to_path = swing.face_angle - swing.swing_path
    backspin = total_spin * math.cos(math.radians(face_to_path))
    sidespin = total_spin * math.sin(math.radians(face_to_path))

    effective_deloft = club.loft - swing.dynamic_loft
    # Purely informative (e.g. "this player delofts the driver by 3 degrees
    # through impact") -- it does not feed into the trajectory calculation,
    # since dynamic_loft already is the loft physically presented to the
    # ball at impact.

    return LaunchConditions(
        ball_speed=ball_speed,
        launch_angle=launch_angle,
        launch_direction=launch_direction,
        backspin=backspin,
        sidespin=sidespin,
        effective_deloft=effective_deloft,
    )


def _classify_shot_shape(lateral_deviation: float) -> str:
    if abs(lateral_deviation) < STRAIGHT_THRESHOLD_YARDS:
        return "straight"
    if lateral_deviation >= CURVE_THRESHOLD_YARDS:
        return "slice"
    if lateral_deviation > 0:
        return "fade"
    if lateral_deviation <= -CURVE_THRESHOLD_YARDS:
        return "hook"
    return "draw"


def simulate_trajectory(club: ClubSpecification, swing: SwingProfile) -> TrajectoryResult:
    launch = calculate_launch_conditions(club, swing)

    v0 = launch.ball_speed * MPH_TO_MS
    launch_angle_rad = math.radians(launch.launch_angle)
    launch_direction_rad = math.radians(launch.launch_direction)

    horizontal_speed = v0 * math.cos(launch_angle_rad)
    vx = horizontal_speed * math.cos(launch_direction_rad)
    vy = horizontal_speed * math.sin(launch_direction_rad)
    vz = v0 * math.sin(launch_angle_rad)

    total_spin = math.hypot(launch.backspin, launch.sidespin)
    backspin_fraction = launch.backspin / total_spin if total_spin > 0 else 0.0
    sidespin_fraction = launch.sidespin / total_spin if total_spin > 0 else 0.0
    spin_angular_velocity = 2 * math.pi * total_spin / 60  # rad/s

    # Lift is decomposed into a vertical component (from backspin, opposing
    # gravity) and a lateral component (from sidespin, curving the shot),
    # each applied along fixed world axes rather than fully rotated relative
    # to the instantaneous 3D velocity vector. True Magnus force is precisely
    # perpendicular to velocity, not to a fixed axis -- this is a
    # simplification, but it captures the two observable effects that matter
    # (more backspin -> more lift/carry; more sidespin -> progressive lateral
    # curve) without the added complexity of full vector rotation.

    x = y = z = 0.0
    points = [(0.0, 0.0, 0.0)]
    peak_height_m = 0.0
    time_elapsed = 0.0
    time_since_last_sample = 0.0

    while time_elapsed < MAX_FLIGHT_TIME:
        speed = math.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        if speed < 1e-6:
            break

        drag_force = 0.5 * DRAG_COEFFICIENT * AIR_DENSITY * BALL_CROSS_SECTION_AREA * speed ** 2

        spin_ratio = BALL_RADIUS * spin_angular_velocity / speed
        lift_coefficient = min(MAX_LIFT_COEFFICIENT, LIFT_COEFFICIENT_PER_SPIN_RATIO * spin_ratio)
        lift_force = 0.5 * lift_coefficient * AIR_DENSITY * BALL_CROSS_SECTION_AREA * speed ** 2

        ax = -drag_force * (vx / speed) / BALL_MASS
        ay = -drag_force * (vy / speed) / BALL_MASS + (lift_force * sidespin_fraction) / BALL_MASS
        az = -drag_force * (vz / speed) / BALL_MASS + (lift_force * backspin_fraction) / BALL_MASS - GRAVITY

        vx += ax * TIME_STEP
        vy += ay * TIME_STEP
        vz += az * TIME_STEP

        x += vx * TIME_STEP
        y += vy * TIME_STEP
        z += vz * TIME_STEP

        time_elapsed += TIME_STEP
        time_since_last_sample += TIME_STEP
        peak_height_m = max(peak_height_m, z)

        if z <= 0.0:
            points.append((x * M_TO_YARDS, y * M_TO_YARDS, 0.0))
            break

        if time_since_last_sample >= SAMPLE_INTERVAL:
            points.append((x * M_TO_YARDS, y * M_TO_YARDS, z * M_TO_YARDS))
            time_since_last_sample = 0.0

    carry_distance = points[-1][0]
    lateral_deviation = points[-1][1]
    peak_height = peak_height_m * M_TO_YARDS

    return TrajectoryResult(
        points=points,
        carry_distance=carry_distance,
        peak_height=peak_height,
        lateral_deviation=lateral_deviation,
        shot_shape=_classify_shot_shape(lateral_deviation),
    )


if __name__ == "__main__":
    driver = ClubSpecification(
        club_type=ClubType.DRIVER,
        head_mass=200, shaft_mass=65, shaft_length=45.5, grip_mass=50,
        club_length=45.5, loft=10.5, lie_angle=58.0,
    )
    swing = SwingProfile(
        clubhead_speed=110, attack_angle=2, swing_path=1.0, face_angle=0.5, dynamic_loft=13,
    )

    launch = calculate_launch_conditions(driver, swing)
    print(f"Ball speed: {launch.ball_speed:.1f} mph")
    print(f"Launch angle: {launch.launch_angle:.1f} deg")
    print(f"Backspin: {launch.backspin:.0f} rpm, Sidespin: {launch.sidespin:.0f} rpm")

    trajectory = simulate_trajectory(driver, swing)
    print(f"Carry distance: {trajectory.carry_distance:.1f} yards")
    print(f"Peak height: {trajectory.peak_height:.1f} yards")
    print(f"Lateral deviation: {trajectory.lateral_deviation:.1f} yards")
    print(f"Shot shape: {trajectory.shot_shape}")
