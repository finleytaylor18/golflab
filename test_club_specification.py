import pytest
from club_specification import ClubSpecification


def test_valid_club_specification_is_created_successfully():
    club = ClubSpecification(
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )
    assert club.head_mass == 200


def test_club_length_out_of_range_raises_value_error():
    with pytest.raises(ValueError):
        ClubSpecification(
            head_mass=200,
            shaft_mass=65,
            shaft_length=45.5,
            grip_mass=50,
            club_length=3443,
        )


def test_head_mass_out_of_range_raises_value_error():
    with pytest.raises(ValueError):
        ClubSpecification(
            head_mass=5555,
            shaft_mass=65,
            shaft_length=45.5,
            grip_mass=50,
            club_length=45.5,
        )