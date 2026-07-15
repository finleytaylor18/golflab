import json
from pathlib import Path
from dataclasses import asdict
from club_specification import ClubSpecification, ClubType

DATA_FILE = Path("clubs.json")


def _load_all_raw(data_file: Path = DATA_FILE) -> dict:
    if not data_file.exists():
        return {}
    return json.loads(data_file.read_text())


def save_club(name: str, club: ClubSpecification, data_file: Path = DATA_FILE) -> None:
    clubs = _load_all_raw(data_file)
    club_dict = asdict(club)
    club_dict["club_type"] = club.club_type.value
    clubs[name] = club_dict
    data_file.write_text(json.dumps(clubs, indent=2))


def load_club(name: str, data_file: Path = DATA_FILE) -> ClubSpecification:
    clubs = _load_all_raw(data_file)
    if name not in clubs:
        raise KeyError(f"No saved club found with name '{name}'")
    club_data = dict(clubs[name])
    club_data["club_type"] = ClubType(club_data["club_type"])
    return ClubSpecification(**club_data)


def list_club_names(data_file: Path = DATA_FILE) -> list[str]:
    return list(_load_all_raw(data_file).keys())