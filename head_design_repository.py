"""Saving and loading parametric head designs.

Mirrors head_repository.py: module-level functions, JSON on disk, the data
file injected so tests can point it at tmp_path. Designs are stored in the
designer's own units (mm, g) because the file is an input boundary and a
design should be readable, and editable, by eye.

A design is a different thing from a head: the design is the seven numbers
and the point masses; the head is what design_mass_properties derives from
them. Store the design, re-derive the head -- never store both, or they can
drift apart.
"""

import json
from dataclasses import asdict
from pathlib import Path

from head_geometry import HeadDesign, MeshResolution, PointMass

DATA_FILE = Path("designs.json")


def _load_all_raw(data_file: Path = DATA_FILE) -> dict:
    if not data_file.exists():
        return {}
    return json.loads(data_file.read_text())


def save_design(name: str, design: HeadDesign, data_file: Path = DATA_FILE) -> None:
    designs = _load_all_raw(data_file)
    designs[name] = asdict(design)
    data_file.write_text(json.dumps(designs, indent=2))


def load_design(name: str, data_file: Path = DATA_FILE) -> HeadDesign:
    designs = _load_all_raw(data_file)
    if name not in designs:
        raise KeyError(f"No saved design found with name '{name}'")

    data = dict(designs[name])
    # Rebuilding through the dataclasses re-runs every validation rule, so a
    # hand-edited file that no longer describes a design fails here, loudly.
    data["hosel"] = PointMass(**data["hosel"])
    data["weights"] = [PointMass(**w) for w in data.get("weights", [])]
    data["mesh"] = MeshResolution(**data.get("mesh", {}))
    return HeadDesign(**data)


def list_design_names(data_file: Path = DATA_FILE) -> list[str]:
    return list(_load_all_raw(data_file).keys())
