from club_specification import ClubSpecification
from moment_of_inertia import calculate_moi


def test_calculate_moi_for_standard_driver():
    driver = ClubSpecification(
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )

    result = calculate_moi(driver)

    assert result == 448941.5625