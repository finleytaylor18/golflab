"""Saving and loading clubhead mass properties.

Mirrors `club_repository.py`: module-level functions, JSON on disk, and the
data file injected as an argument so tests can point it at `tmp_path` instead
of the real one.

Stored in INDUSTRY UNITS -- grams, millimetres, g*cm^2. The file is an input
and output boundary, so industry units are the correct ones there (standing
rule 6), and it means a saved head can be read against a Fusion properties
panel or a spec sheet without converting anything in your head. Conversion to
SI happens on the way out, through `HeadMassProperties.from_industry_units`.
"""

import json
from pathlib import Path

import numpy as np

from head_mass_properties import HeadMassProperties
from units import kg_m2_to_g_cm2, kg_to_grams, m_to_mm

DATA_FILE = Path("heads.json")


def _load_all_raw(data_file: Path = DATA_FILE) -> dict:
    if not data_file.exists():
        return {}
    return json.loads(data_file.read_text())


def save_head(name: str, head: HeadMassProperties, data_file: Path = DATA_FILE) -> None:
    heads = _load_all_raw(data_file)
    heads[name] = {
        "mass_g": kg_to_grams(head.mass_kg),
        "cg_mm": [m_to_mm(value) for value in head.cg_m],
        "inertia_g_cm2": [[kg_m2_to_g_cm2(value) for value in row]
                          for row in head.inertia_about_cg],
        "face_half_width_mm": m_to_mm(head.face.half_width_m),
        "face_half_height_mm": m_to_mm(head.face.half_height_m),
        "face_shape": head.face.shape,
        "face_outline_is_measured": head.face.outline_is_measured,
    }
    data_file.write_text(json.dumps(heads, indent=2))


def load_head(name: str, data_file: Path = DATA_FILE) -> HeadMassProperties:
    heads = _load_all_raw(data_file)
    if name not in heads:
        raise KeyError(f"No saved head found with name '{name}'")

    data = heads[name]
    head = HeadMassProperties.from_industry_units(
        mass_g=data["mass_g"],
        cg_mm=data["cg_mm"],
        inertia_g_cm2=np.array(data["inertia_g_cm2"], dtype=float),
        face_half_width_mm=data["face_half_width_mm"],
        face_half_height_mm=data["face_half_height_mm"],
    )
    head.face.shape = data.get("face_shape", "ellipse")
    head.face.outline_is_measured = data.get("face_outline_is_measured", False)
    return head


def list_head_names(data_file: Path = DATA_FILE) -> list[str]:
    return list(_load_all_raw(data_file).keys())
