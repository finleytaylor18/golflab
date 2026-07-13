from club_specification import ClubSpecification
from club_comparison import compare_clubs


def test_compare_clubs_calculates_correct_deltas():
    club_a = ClubSpecification(
        head_mass=200, shaft_mass=65, shaft_length=45.5, grip_mass=50, club_length=45.5,
    )
    club_b = ClubSpecification(
        head_mass=195, shaft_mass=60, shaft_length=45.5, grip_mass=48, club_length=45.75,
    )

    result = compare_clubs("A", club_a, "B", club_b)

    assert result.moment_a == 6418.75
    assert result.moment_b == 6284.25
    assert result.moment_delta == -134.5
    assert result.swing_weight_a == "G0"
    assert result.swing_weight_b == "F8"