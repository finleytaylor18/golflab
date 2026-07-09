from club_specification import ClubSpecification
from swing_weight import calculate_moment


def test_calculate_moment_for_standard_driver():
    driver = ClubSpecification(
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )

    result = calculate_moment(driver)

    assert result == 6418.75