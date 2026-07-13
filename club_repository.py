import json
from pathlib import Path
from dataclasses import asdict
from club_specification import ClubSpecification

DATA_FILE = Path("clubs.json")


def _load_all_raw(data_file: Path = DATA_FILE) -> dict:
    if not data_file.exists():
        return {}
    return json.loads(data_file.read_text())


def save_club(name: str, club: ClubSpecification, data_file: Path = DATA_FILE) -> None:
    clubs = _load_all_raw(data_file)
    clubs[name] = asdict(club)
    data_file.write_text(json.dumps(clubs, indent=2))


def load_club(name: str, data_file: Path = DATA_FILE) -> ClubSpecification:
    clubs = _load_all_raw(data_file)
    if name not in clubs:
        raise KeyError(f"No saved club found with name '{name}'")
    return ClubSpecification(**clubs[name])


def list_club_names(data_file: Path = DATA_FILE) -> list[str]:
    return list(_load_all_raw(data_file).keys())