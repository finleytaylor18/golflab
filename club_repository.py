import json
from pathlib import Path
from dataclasses import asdict
from club_specification import ClubSpecification

DATA_FILE = Path("clubs.json")


def _load_all_raw() -> dict:
    if not DATA_FILE.exists():
        return {}
    return json.loads(DATA_FILE.read_text())


def save_club(name: str, club: ClubSpecification) -> None:
    clubs = _load_all_raw()
    clubs[name] = asdict(club)
    DATA_FILE.write_text(json.dumps(clubs, indent=2))


def load_club(name: str) -> ClubSpecification:
    clubs = _load_all_raw()
    if name not in clubs:
        raise KeyError(f"No saved club found with name '{name}'")
    return ClubSpecification(**clubs[name])


def list_club_names() -> list[str]:
    return list(_load_all_raw().keys())