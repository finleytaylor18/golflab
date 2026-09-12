"""Tests for clubhead persistence, isolated with tmp_path."""

import json

import numpy as np
import pytest

from head_mass_properties import FaceGeometry, HeadMassProperties
from head_repository import list_head_names, load_head, save_head
from impact_fixtures import fixture_offset_cg_head, fixture_symmetric_head


def test_a_saved_head_comes_back_unchanged(tmp_path):
    """Proves a head survives the round trip through JSON exactly.

    This matters more than it looks: the file stores industry units and the
    object holds SI, so every save and load crosses the unit boundary twice.
    A factor-of-1000 slip in either direction would show up here.
    """
    data_file = tmp_path / "heads.json"
    original = fixture_offset_cg_head()
    save_head("test head", original, data_file)
    restored = load_head("test head", data_file)

    assert restored.mass_kg == pytest.approx(original.mass_kg, rel=1e-12)
    assert restored.cg_m == pytest.approx(original.cg_m, rel=1e-12)
    assert restored.inertia_about_cg == pytest.approx(original.inertia_about_cg, rel=1e-12)
    assert restored.cg_depth_m == pytest.approx(original.cg_depth_m, rel=1e-12)


def test_the_file_holds_industry_units(tmp_path):
    """Proves the stored numbers are the ones a spec sheet or Fusion panel
    shows, so a saved head can be checked by eye against its source.
    """
    data_file = tmp_path / "heads.json"
    save_head("test head", fixture_symmetric_head(), data_file)
    stored = json.loads(data_file.read_text())["test head"]

    assert stored["mass_g"] == pytest.approx(200.0, rel=1e-12)
    assert stored["cg_mm"][2] == pytest.approx(-35.0, rel=1e-12)
    assert stored["inertia_g_cm2"][1][1] == pytest.approx(5000.0, rel=1e-9)


def test_the_face_outline_and_its_provenance_survive(tmp_path):
    """Proves "this outline was measured" is not quietly lost on save. A map
    drawn from a reloaded head must still say whether its area can be trusted.
    """
    data_file = tmp_path / "heads.json"
    head = HeadMassProperties.from_industry_units(
        200.0, (0.0, 0.0, -35.0), np.diag([3000.0, 5000.0, 4000.0]))
    head.face = FaceGeometry(0.057, 0.029, outline_is_measured=True, shape="ellipse")

    save_head("measured head", head, data_file)
    restored = load_head("measured head", data_file)

    assert restored.face.outline_is_measured is True
    assert restored.face.shape == "ellipse"
    assert restored.face.half_width_m == pytest.approx(0.057, rel=1e-12)


def test_saving_a_second_head_keeps_the_first(tmp_path):
    """Proves the store accumulates rather than overwriting, which is what a
    two-head comparison needs.
    """
    data_file = tmp_path / "heads.json"
    save_head("head one", fixture_symmetric_head(), data_file)
    save_head("head two", fixture_offset_cg_head(), data_file)

    assert list_head_names(data_file) == ["head one", "head two"]


def test_a_missing_head_and_a_missing_file_fail_clearly(tmp_path):
    """Proves a typo produces a named error rather than an empty head."""
    data_file = tmp_path / "heads.json"
    assert list_head_names(data_file) == []
    with pytest.raises(KeyError, match="No saved head"):
        load_head("not saved", data_file)

    save_head("head one", fixture_symmetric_head(), data_file)
    with pytest.raises(KeyError, match="No saved head"):
        load_head("head won", data_file)


def test_a_reloaded_head_is_still_validated(tmp_path):
    """Proves the file is not a way around the domain rules. A hand-edited
    heads.json with an impossible tensor must fail on load, not silently
    produce a map of a head that cannot exist.
    """
    data_file = tmp_path / "heads.json"
    save_head("head one", fixture_symmetric_head(), data_file)

    corrupted = json.loads(data_file.read_text())
    corrupted["head one"]["inertia_g_cm2"] = [[1000.0, 0, 0], [0, 1000.0, 0], [0, 0, 9000.0]]
    data_file.write_text(json.dumps(corrupted))

    with pytest.raises(ValueError, match="triangle inequality"):
        load_head("head one", data_file)
