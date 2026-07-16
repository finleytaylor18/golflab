import pytest
from club_specification import ClubSpecification, ClubType
from swing_profile import SwingProfile
from ball_flight import calculate_launch_conditions, simulate_trajectory

# Launch conditions are closed-form formulas, so they're tested the same way
# as the rest of the codebase: hand-verified reference values via
# pytest.approx. simulate_trajectory is a numerically integrated ODE, not a
# closed-form formula, so there's no reasonable hand calculation to assert
# against -- those tests below are deliberately sanity/property checks
# (does carry distance respond to clubhead speed the right way, does an open
# face curve the ball right, etc.) rather than exact-value assertions.


def _standard_driver() -> ClubSpecification:
    return ClubSpecification(
        club_type=ClubType.DRIVER,
        head_mass=200, shaft_mass=65, shaft_length=45.5, grip_mass=50,
        club_length=45.5, loft=10.5, lie_angle=58.0,
    )


def test_calculate_launch_conditions_for_standard_driver_swing():
    swing = SwingProfile(clubhead_speed=110, attack_angle=2, swing_path=1.0, face_angle=0.5, dynamic_loft=13)

    launch = calculate_launch_conditions(_standard_driver(), swing)

    assert launch.ball_speed == pytest.approx(160.51, abs=0.01)
    assert launch.launch_angle == pytest.approx(11.75, abs=0.01)
    assert launch.launch_direction == pytest.approx(0.6, abs=0.01)
    assert launch.backspin == pytest.approx(2675.04, abs=0.5)
    assert launch.sidespin == pytest.approx(-23.34, abs=0.5)
    assert launch.effective_deloft == -2.5


def test_realistic_driver_shot_carries_a_realistic_distance():
    # Calibration reference for LIFT_COEFFICIENT_PER_SPIN_RATIO (see ball_flight.py) --
    # a ~110 mph clubhead speed driver shot should land near widely known
    # tour-average figures (roughly 270-290 yard carry, ~28-35 yard peak height).
    swing = SwingProfile(clubhead_speed=110, attack_angle=2, swing_path=1.0, face_angle=0.5, dynamic_loft=13)

    trajectory = simulate_trajectory(_standard_driver(), swing)

    assert trajectory.carry_distance == pytest.approx(283, abs=15)
    assert trajectory.peak_height == pytest.approx(32, abs=8)


def test_straight_swing_produces_zero_lateral_deviation():
    swing = SwingProfile(clubhead_speed=110, attack_angle=2, swing_path=0.0, face_angle=0.0, dynamic_loft=13)

    trajectory = simulate_trajectory(_standard_driver(), swing)

    assert trajectory.lateral_deviation == 0.0
    assert trajectory.shot_shape == "straight"


def test_open_face_relative_to_path_curves_the_ball_right():
    swing = SwingProfile(clubhead_speed=95, attack_angle=-1, swing_path=-4, face_angle=6, dynamic_loft=12)

    trajectory = simulate_trajectory(_standard_driver(), swing)

    assert trajectory.lateral_deviation > 0
    assert trajectory.shot_shape in ("fade", "slice")


def test_closed_face_relative_to_path_curves_the_ball_left():
    swing = SwingProfile(clubhead_speed=105, attack_angle=1, swing_path=3, face_angle=-2, dynamic_loft=11)

    trajectory = simulate_trajectory(_standard_driver(), swing)

    assert trajectory.lateral_deviation < 0
    assert trajectory.shot_shape in ("draw", "hook")


def test_higher_clubhead_speed_increases_carry_distance():
    slow_swing = SwingProfile(clubhead_speed=85, attack_angle=2, swing_path=0.0, face_angle=0.0, dynamic_loft=13)
    fast_swing = SwingProfile(clubhead_speed=115, attack_angle=2, swing_path=0.0, face_angle=0.0, dynamic_loft=13)

    slow_trajectory = simulate_trajectory(_standard_driver(), slow_swing)
    fast_trajectory = simulate_trajectory(_standard_driver(), fast_swing)

    assert fast_trajectory.carry_distance > slow_trajectory.carry_distance


def test_trajectory_points_start_at_origin_and_end_at_ground_level():
    swing = SwingProfile(clubhead_speed=110, attack_angle=2, swing_path=0.0, face_angle=0.0, dynamic_loft=13)

    trajectory = simulate_trajectory(_standard_driver(), swing)

    assert trajectory.points[0] == (0.0, 0.0, 0.0)
    assert trajectory.points[-1][2] == 0.0
    assert len(trajectory.points) > 2
