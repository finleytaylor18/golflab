import os
from club_specification import ClubSpecification
from club_repository import save_club, load_club, list_club_names, DATA_FILE


def test_save_and_load_club_round_trip():
    original = ClubSpecification(
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )

    save_club("test_driver", original)
    loaded = load_club("test_driver")

    assert loaded == original

    if DATA_FILE.exists():
        os.remove(DATA_FILE)