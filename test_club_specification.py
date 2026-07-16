import pytest
from club_specification import ClubSpecification, ClubType


def test_valid_club_specification_is_created_successfully():
    club = ClubSpecification(
        club_type=ClubType.DRIVER,
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
        loft=10.5,
        lie_angle=58.0,
    )
    assert club.head_mass == 200


def test_club_length_out_of_range_raises_value_error():
    with pytest.raises(ValueError):
        ClubSpecification(
            club_type=ClubType.DRIVER,
            head_mass=200,
            shaft_mass=65,
            shaft_length=45.5,
            grip_mass=50,
            club_length=3443,
            loft=10.5,
            lie_angle=58.0,
        )


def test_head_mass_out_of_range_raises_value_error():
    with pytest.raises(ValueError):
        ClubSpecification(
            club_type=ClubType.DRIVER,
            head_mass=5555,
            shaft_mass=65,
            shaft_length=45.5,
            grip_mass=50,
            club_length=45.5,
            loft=10.5,
            lie_angle=58.0,
        )