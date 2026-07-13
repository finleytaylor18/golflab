import pytest
from club_specification import ClubSpecification
from center_of_gravity import calculate_balance_point


def test_calculate_balance_point_for_standard_driver():
    driver = ClubSpecification(
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )

    result = calculate_balance_point(driver)

    assert result == pytest.approx(34.38, abs=0.01)