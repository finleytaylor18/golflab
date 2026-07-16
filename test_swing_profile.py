import pytest
from swing_profile import SwingProfile


def test_valid_swing_profile_is_created_successfully():
    swing = SwingProfile(
        clubhead_speed=110,
        attack_angle=2,
        swing_path=1.0,
        face_angle=0.5,
        dynamic_loft=13,
    )
    assert swing.clubhead_speed == 110


def test_clubhead_speed_out_of_range_raises_value_error():
    with pytest.raises(ValueError):
        SwingProfile(
            clubhead_speed=500,
            attack_angle=2,
            swing_path=1.0,
            face_angle=0.5,
            dynamic_loft=13,
        )


def test_attack_angle_out_of_range_raises_value_error():
    with pytest.raises(ValueError):
        SwingProfile(
            clubhead_speed=110,
            attack_angle=-45,
            swing_path=1.0,
            face_angle=0.5,
            dynamic_loft=13,
        )


def test_dynamic_loft_out_of_range_raises_value_error():
    with pytest.raises(ValueError):
        SwingProfile(
            clubhead_speed=110,
            attack_angle=2,
            swing_path=1.0,
            face_angle=0.5,
            dynamic_loft=90,
        )
