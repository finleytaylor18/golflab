from club_specification import ClubSpecification
from club_repository import save_club, load_club


def test_save_and_load_club_round_trip(tmp_path):
    test_file = tmp_path / "test_clubs.json"

    original = ClubSpecification(
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )

    save_club("test_driver", original, data_file=test_file)
    loaded = load_club("test_driver", data_file=test_file)

    assert loaded == original