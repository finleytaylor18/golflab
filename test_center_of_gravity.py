import pytest
from club_specification import ClubSpecification, ClubType
from center_of_gravity import calculate_balance_point


def test_calculate_balance_point_for_standard_driver():
    driver = ClubSpecification(
        club_type=ClubType.DRIVER,
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
        loft=10.5,
        lie_angle=58.0,
    )

    result = calculate_balance_point(driver)

    assert result == pytest.approx(34.38, abs=0.01)