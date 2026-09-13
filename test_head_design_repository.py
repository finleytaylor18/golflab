"""Tests for design persistence, isolated with tmp_path."""

import json
from dataclasses import replace

import pytest

from head_design_repository import list_design_names, load_design, save_design
from head_geometry import MeshResolution, PointMass, default_design, design_mass_properties


def test_a_saved_design_comes_back_identical(tmp_path):
    """Proves the round trip is lossless, nested parts included: the same
    design must derive the same head to machine precision after reload.
    """
    data_file = tmp_path / "designs.json"
    original = replace(default_design(), mesh=MeshResolution(60, 120))
    save_design("v1", original, data_file)
    restored = load_design("v1", data_file)

    assert restored == original
    before = design_mass_properties(original).head
    after = design_mass_properties(restored).head
    assert after.inertia_about_cg == pytest.approx(before.inertia_about_cg, rel=1e-15)


def test_the_file_is_in_the_designers_units(tmp_path):
    """Proves the file is readable by eye: millimetres and grams, with the
    point masses stored the way a designer describes them.
    """
    data_file = tmp_path / "designs.json"
    save_design("v1", default_design(), data_file)
    stored = json.loads(data_file.read_text())["v1"]

    assert stored["half_width_mm"] == 60.0
    assert stored["face_width_mm"] == 100.0
    assert stored["hosel"]["toe_mm"] == -45.0
    assert stored["weights"][0]["mass_g"] == 14.0
    assert "inertia" not in json.dumps(stored)            # derived, never stored


def test_saving_more_designs_keeps_the_earlier_ones(tmp_path):
    data_file = tmp_path / "designs.json"
    save_design("one", default_design(), data_file)
    save_design("two", replace(default_design(), sole_mass_g=90.0), data_file)
    assert list_design_names(data_file) == ["one", "two"]


def test_a_missing_design_and_a_missing_file_fail_clearly(tmp_path):
    data_file = tmp_path / "designs.json"
    assert list_design_names(data_file) == []
    with pytest.raises(KeyError, match="No saved design"):
        load_design("nope", data_file)


def test_a_hand_edited_file_is_still_validated(tmp_path):
    """Proves the file is not a way around the design rules: a weight moved
    outside the head's box must fail on load, not derive a head anyway.
    """
    data_file = tmp_path / "designs.json"
    save_design("v1", default_design(), data_file)

    corrupted = json.loads(data_file.read_text())
    corrupted["v1"]["weights"][0]["back_mm"] = 500.0
    data_file.write_text(json.dumps(corrupted))

    with pytest.raises(ValueError, match="outside the head's bounding box"):
        load_design("v1", data_file)


def test_a_design_without_weights_or_mesh_keys_loads_with_defaults(tmp_path):
    """Proves older or hand-written files can omit the optional parts."""
    data_file = tmp_path / "designs.json"
    save_design("v1", default_design(), data_file)
    trimmed = json.loads(data_file.read_text())
    del trimmed["v1"]["weights"]
    del trimmed["v1"]["mesh"]
    data_file.write_text(json.dumps(trimmed))

    restored = load_design("v1", data_file)
    assert restored.weights == []
    assert restored.mesh == MeshResolution()
    assert isinstance(restored.hosel, PointMass)
