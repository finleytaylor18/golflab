"""Tests for the impact model's API boundary.

The endpoints in main.py are thin: they validate, call a pure function and
serialise. Everything that can actually go wrong lives here -- unit
conversion on the way in, and JSON serialisation on the way out.
"""

import json
import math

import pytest

from api_schemas import (ForgivenessMapRequest, HeadMassPropertiesRequest,
                         ImpactConditionsRequest, MapSettingsRequest,
                         forgiveness_map_to_payload, head_to_request_payload,
                         map_comparison_to_payload, to_head_mass_properties,
                         to_map_settings, to_swing_conditions)
from ball_properties import conforming_three_piece_tour_ball
from forgiveness_map import compare_maps, compute_forgiveness_map
from impact_fixtures import fixture_near_rigid_head, fixture_offset_cg_head


def a_head(**overrides) -> HeadMassPropertiesRequest:
    fields = dict(mass_g=200.0, cg_x_mm=0.0, cg_y_mm=0.0, cg_z_mm=-35.0,
                  i_xx_g_cm2=3000.0, i_yy_g_cm2=5000.0, i_zz_g_cm2=4000.0)
    fields.update(overrides)
    return HeadMassPropertiesRequest(**fields)


@pytest.fixture
def sample_map():
    head = to_head_mass_properties(a_head())
    conditions = to_swing_conditions(
        ImpactConditionsRequest(clubhead_speed_mph=100.7, loft_deg=10.5))
    settings = to_map_settings(MapSettingsRequest(spacing_mm=5.0))
    return compute_forgiveness_map(head, conforming_three_piece_tour_ball(),
                                   conditions, settings)


# ---------------------------------------------------------------------------
# INTO THE CORE: THE UNIT BOUNDARY
# ---------------------------------------------------------------------------

def test_a_head_request_arrives_in_industry_units_and_lands_in_si():
    """Proves standing rule 6 holds across the wire. The API speaks grams,
    millimetres and g*cm^2; everything past this point is SI and never has to
    ask which it is looking at.
    """
    head = to_head_mass_properties(a_head())

    assert head.mass_kg == pytest.approx(0.200, rel=1e-15)
    assert head.cg_m[2] == pytest.approx(-0.035, rel=1e-15)
    assert head.inertia_about_cg[1][1] == pytest.approx(5.0e-4, rel=1e-12)
    assert head.cg_depth_m == pytest.approx(0.035, rel=1e-15)


def test_six_components_become_a_symmetric_tensor():
    """Proves the schema makes an asymmetric tensor unrepresentable.

    A client sends the six independent components; the pair positions are
    filled from the same number. Accepting nine would let a caller send a
    tensor no rigid body has and get a 422 for a mistake the schema could
    have prevented.
    """
    head = to_head_mass_properties(a_head(i_xy_g_cm2=250.0, i_yz_g_cm2=-120.0))
    tensor = head.inertia_about_cg

    assert tensor[0][1] == tensor[1][0]
    assert tensor[1][2] == tensor[2][1]
    assert tensor[0][1] == pytest.approx(250.0e-7, rel=1e-12)
    assert tensor[1][2] == pytest.approx(-120.0e-7, rel=1e-12)


def test_a_physically_impossible_head_is_rejected_at_the_boundary():
    """Proves the domain rules still apply to data arriving over HTTP.

    Each of these raises ValueError, which main.py turns into a 422: the
    request was well-formed JSON but did not describe a clubhead.
    """
    with pytest.raises(ValueError, match="behind the face plane"):
        to_head_mass_properties(a_head(cg_z_mm=35.0))
    with pytest.raises(ValueError, match="triangle inequality"):
        to_head_mass_properties(a_head(i_xx_g_cm2=1000.0, i_yy_g_cm2=1000.0,
                                       i_zz_g_cm2=9000.0))
    with pytest.raises(ValueError, match="positive-definite"):
        to_head_mass_properties(a_head(i_yy_g_cm2=-5000.0))
    with pytest.raises(ValueError, match="mass_kg"):
        to_head_mass_properties(a_head(mass_g=0.0))


def test_an_unknown_face_shape_is_rejected():
    """Proves the outline is validated too. The shape is assigned after the
    head is built, which bypasses the dataclass's own check -- so the
    converter re-runs it rather than letting a typo through to the sweep.
    """
    with pytest.raises(ValueError, match="ellipse"):
        to_head_mass_properties(a_head(face_shape="hexagon"))


def test_swing_conditions_convert_mph_and_degrees():
    """Proves the conditions cross the boundary too: the wire is mph and
    degrees, the core is m/s and radians.
    """
    conditions = to_swing_conditions(
        ImpactConditionsRequest(clubhead_speed_mph=100.0, loft_deg=90.0 / math.pi * math.pi / 2))

    assert conditions.head_speed_mps == pytest.approx(44.704, rel=1e-12)
    assert conditions.loft_rad == pytest.approx(math.radians(45.0), rel=1e-12)


def test_impossible_conditions_and_settings_are_rejected():
    """Proves bad request values fail here rather than deep inside the solver."""
    with pytest.raises(ValueError, match="head_speed_mps"):
        to_swing_conditions(ImpactConditionsRequest(clubhead_speed_mph=0.0, loft_deg=10.0))
    with pytest.raises(ValueError, match="loft_rad"):
        to_swing_conditions(ImpactConditionsRequest(clubhead_speed_mph=100.0, loft_deg=95.0))
    with pytest.raises(ValueError, match="spacing_mm"):
        to_map_settings(MapSettingsRequest(spacing_mm=0.0))
    with pytest.raises(ValueError, match="retention_threshold_pct"):
        to_map_settings(MapSettingsRequest(retention_threshold_pct=101.0))


def test_a_head_round_trips_through_the_wire_format():
    """Proves a stored head can repopulate a form and rebuild identically.

    The payload crosses the unit boundary twice -- SI out to industry units
    and back -- so a factor-of-1000 slip in either direction shows up here.
    """
    original = fixture_offset_cg_head()
    rebuilt = to_head_mass_properties(
        HeadMassPropertiesRequest(**head_to_request_payload(original)))

    assert rebuilt.mass_kg == pytest.approx(original.mass_kg, rel=1e-12)
    assert rebuilt.cg_m == pytest.approx(original.cg_m, rel=1e-12)
    assert rebuilt.inertia_about_cg == pytest.approx(original.inertia_about_cg, rel=1e-12)
    assert rebuilt.face.shape == original.face.shape


# ---------------------------------------------------------------------------
# OUT TO THE BROWSER: SERIALISATION
# ---------------------------------------------------------------------------

def test_the_map_payload_is_valid_json_with_no_nan(sample_map):
    """Proves the single serialisation bug that would break the whole page.

    Off-face grid points are NaN, and JSON has no NaN. Python's encoder emits
    the bare token `NaN` quite happily, which is invalid JSON and which the
    browser's JSON.parse rejects outright -- so the response would fail to
    parse entirely, not merely show a gap. `allow_nan=False` makes that
    failure impossible to miss here instead of in the browser.
    """
    payload = forgiveness_map_to_payload(sample_map)
    text = json.dumps(payload, allow_nan=False)

    assert len(text) > 1000
    assert "NaN" not in text and "Infinity" not in text


def test_off_face_points_serialise_as_null_and_on_face_as_numbers(sample_map):
    """Proves the mask survives the wire. The browser needs to know which
    cells are face and which are blank; null carries exactly that, and the
    on_face grid says the same thing again so the two can be checked.
    """
    payload = forgiveness_map_to_payload(sample_map)

    for row_index, row in enumerate(payload["on_face"]):
        for column_index, on_face in enumerate(row):
            value = payload["speed_retention_pct"][row_index][column_index]
            if on_face:
                assert isinstance(value, float)
            else:
                assert value is None


def test_the_payload_grid_matches_its_own_axes(sample_map):
    """Proves the arrays are indexed [y][x] consistently. A transposed grid
    would still render -- as a mirrored, wrong map -- so the shape is checked
    against the axes rather than assumed.
    """
    payload = forgiveness_map_to_payload(sample_map)
    rows, columns = len(payload["y_mm"]), len(payload["x_mm"])

    for key in ("on_face", "speed_retention_pct", "backspin_rpm", "sidespin_rpm",
                "launch_angle_deg", "exceeds_friction", "backspin_reversed"):
        assert len(payload[key]) == rows, key
        assert all(len(row) == columns for row in payload[key]), key


def test_the_payload_carries_every_honesty_flag(sample_map):
    """Proves the web view cannot be an unlabelled version of the figure.

    The threshold's status, the assumed outline, the friction and topspin
    counts all travel as structured data, so the UI can act on them rather
    than a reader having to know the caveats already.
    """
    payload = forgiveness_map_to_payload(sample_map)
    summary = payload["summary"]

    assert summary["threshold_is_a_chosen_setting"] is True
    assert "ASSUMED" in payload["face_description"]
    assert "points_needing_more_friction" in summary
    assert summary["points_with_reversed_backspin"] > 0
    assert "not a commercial product" in payload["ball_description"]

    # And the per-point flags, so the map can mark exactly where.
    assert any(any(row) for row in payload["backspin_reversed"])


def test_the_spin_axis_is_null_exactly_where_backspin_reversed(sample_map):
    """Proves an undefined angle reaches the browser as null rather than as a
    wrapped number. Those points carry topspin, where "spin axis tilt" stops
    meaning what a reader thinks it means.
    """
    payload = forgiveness_map_to_payload(sample_map)

    for row_index, row in enumerate(payload["backspin_reversed"]):
        for column_index, reversed_spin in enumerate(row):
            if reversed_spin:
                assert payload["spin_axis_deg"][row_index][column_index] is None


def test_a_comparison_payload_is_json_safe_and_keeps_both_summaries(sample_map):
    """Proves the difference map serialises too, and that it carries each
    head's own summary so the two can be compared numerically and not only
    by colour.
    """
    other = compute_forgiveness_map(
        fixture_near_rigid_head(), conforming_three_piece_tour_ball(),
        to_swing_conditions(ImpactConditionsRequest(clubhead_speed_mph=100.7, loft_deg=10.5)),
        to_map_settings(MapSettingsRequest(spacing_mm=5.0)))
    payload = map_comparison_to_payload(compare_maps("a", sample_map, "b", other))

    json.dumps(payload, allow_nan=False)
    assert payload["name_a"] == "a" and payload["name_b"] == "b"
    assert payload["summary_a"]["forgiving_area_mm2"] < payload["summary_b"]["forgiving_area_mm2"]


def test_the_default_map_request_is_usable_as_sent():
    """Proves a client can post only a head and conditions and get a sensible
    sweep, without having to know what a good grid spacing is.
    """
    request = ForgivenessMapRequest(head=a_head(),
                                    conditions=ImpactConditionsRequest(
                                        clubhead_speed_mph=100.0, loft_deg=10.5))
    settings = to_map_settings(request.settings)

    assert settings.spacing_mm == 2.0
    assert settings.retention_threshold_pct == 97.0


# ---------------------------------------------------------------------------
# PARAMETRIC HEAD DESIGN
# ---------------------------------------------------------------------------

from api_schemas import (HeadDesignRequest, SaveDesignRequest, design_result_to_payload,
                         design_to_payload, to_head_design)
from head_geometry import MeshResolution, default_design, design_mass_properties


def test_a_design_round_trips_through_the_wire_format():
    """Proves the request model carries the whole design and nothing else:
    serialise, rebuild, and the dataclass compares equal.
    """
    original = default_design()
    rebuilt = to_head_design(HeadDesignRequest(**design_to_payload(original)))
    assert rebuilt == original


def test_an_impossible_design_is_rejected_at_the_boundary():
    """Proves the design rules apply to data arriving over HTTP; each raises
    ValueError, which the endpoint turns into a 422.
    """
    payload = design_to_payload(default_design())
    payload["face_width_mm"] = 120.0                        # equals 2a
    with pytest.raises(ValueError, match="face_width_mm"):
        to_head_design(HeadDesignRequest(**payload))

    payload = design_to_payload(default_design())
    payload["weights"][0]["back_mm"] = 400.0
    with pytest.raises(ValueError, match="outside the head's bounding box"):
        to_head_design(HeadDesignRequest(**payload))


def test_the_design_payload_is_json_safe_and_feeds_the_map_directly():
    """Proves the derived head comes back in the exact shape the forgiveness
    map request accepts, so the browser can post it on unchanged -- and that
    the whole payload is valid JSON.
    """
    from dataclasses import replace
    result = design_mass_properties(replace(default_design(), mesh=MeshResolution(60, 120)))
    payload = design_result_to_payload(result)
    json.dumps(payload, allow_nan=False)

    head = to_head_mass_properties(HeadMassPropertiesRequest(**payload["head"]))
    assert head.mass_kg == pytest.approx(result.head.mass_kg, rel=1e-12)
    assert head.face.outline_source == "design"
    assert abs(sum(p["mass_share"] for p in payload["breakdown"]) - 1.0) < 1e-12
    assert payload["conformance"]["conforms"] is True
    assert payload["design"]["name"] == default_design().name


def test_a_save_design_request_carries_the_name_separately():
    request = SaveDesignRequest(name="my design", design=HeadDesignRequest(**design_to_payload(default_design())))
    assert to_head_design(request.design) == default_design()
    assert request.name == "my design"
