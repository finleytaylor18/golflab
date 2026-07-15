from club_specification import ClubSpecification, ClubType
from moment_of_inertia import calculate_moi


def test_calculate_moi_for_standard_driver():
    driver = ClubSpecification(
        club_type=ClubType.DRIVER,
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )

    result = calculate_moi(driver)

    assert result == 448941.5625