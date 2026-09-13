import math

import numpy as np
from pydantic import BaseModel
from club_specification import ClubSpecification, ClubType
from swing_profile import SwingProfile
from clubhead_composition import WeightPort, ClubHeadComposition
from head_mass_properties import HeadMassProperties
from impact_model import SwingConditions
from forgiveness_map import ForgivenessMap, MapComparison, MapSettings
from units import degrees_to_radians, mph_to_mps


class ClubSpecificationRequest(BaseModel):
    club_type: str
    head_mass: float
    shaft_mass: float
    shaft_length: float
    grip_mass: float
    club_length: float
    loft: float
    lie_angle: float


def to_club_specification(request: ClubSpecificationRequest) -> ClubSpecification:
    return ClubSpecification(
        club_type=ClubType(request.club_type),
        head_mass=request.head_mass,
        shaft_mass=request.shaft_mass,
        shaft_length=request.shaft_length,
        grip_mass=request.grip_mass,
        club_length=request.club_length,
        loft=request.loft,
        lie_angle=request.lie_angle,
    )


class SwingProfileRequest(BaseModel):
    clubhead_speed: float
    attack_angle: float
    swing_path: float
    face_angle: float
    dynamic_loft: float


def to_swing_profile(request: SwingProfileRequest) -> SwingProfile:
    return SwingProfile(
        clubhead_speed=request.clubhead_speed,
        attack_angle=request.attack_angle,
        swing_path=request.swing_path,
        face_angle=request.face_angle,
        dynamic_loft=request.dynamic_loft,
    )


class WeightPortRequest(BaseModel):
    name: str
    mass: float
    toe_heel: float
    face_back: float


class ClubHeadCompositionRequest(BaseModel):
    weight_ports: list[WeightPortRequest]


def to_clubhead_composition(request: ClubHeadCompositionRequest) -> ClubHeadComposition:
    return ClubHeadComposition(weight_ports=[
        WeightPort(name=port.name, mass=port.mass, toe_heel=port.toe_heel, face_back=port.face_back)
        for port in request.weight_ports
    ])


class CompareRequest(BaseModel):
    name_a: str
    club_a: ClubSpecificationRequest
    name_b: str
    club_b: ClubSpecificationRequest


class BallFlightRequest(BaseModel):
    club: ClubSpecificationRequest
    swing: SwingProfileRequest


class SaveClubRequest(BaseModel):
    name: str
    club: ClubSpecificationRequest


# ---------------------------------------------------------------------------
# IMPACT MODEL AND FORGIVENESS MAPS
# ---------------------------------------------------------------------------
#
# The API is a unit BOUNDARY (standing rule 6), so every field here is in the
# units a spec sheet or a CAD properties panel uses -- grams, millimetres,
# g*cm^2, mph, degrees -- and conversion to SI happens on the way in. Nothing
# in this file does physics; it translates.


class HeadMassPropertiesRequest(BaseModel):
    """A clubhead as the wire sees it.

    The inertia tensor arrives as its six INDEPENDENT components rather than
    as nine numbers. A real tensor is symmetric, so accepting nine would let a
    client send an asymmetric one and get a 422 back for a mistake the schema
    could have made impossible.
    """

    mass_g: float
    cg_x_mm: float          # + toward the HEEL
    cg_y_mm: float          # + toward the crown
    cg_z_mm: float          # negative: the CG lies behind the face plane
    i_xx_g_cm2: float
    i_yy_g_cm2: float
    i_zz_g_cm2: float
    i_xy_g_cm2: float = 0.0
    i_xz_g_cm2: float = 0.0
    i_yz_g_cm2: float = 0.0
    face_half_width_mm: float = 50.0
    face_half_height_mm: float = 30.0
    face_shape: str = "ellipse"
    face_outline_source: str = "assumed"        # "assumed" | "design" | "measured"
    face_outline_is_measured: bool | None = None   # legacy clients; True means "measured"


def to_head_mass_properties(request: HeadMassPropertiesRequest) -> HeadMassProperties:
    tensor = np.array([
        [request.i_xx_g_cm2, request.i_xy_g_cm2, request.i_xz_g_cm2],
        [request.i_xy_g_cm2, request.i_yy_g_cm2, request.i_yz_g_cm2],
        [request.i_xz_g_cm2, request.i_yz_g_cm2, request.i_zz_g_cm2],
    ], dtype=float)

    head = HeadMassProperties.from_industry_units(
        mass_g=request.mass_g,
        cg_mm=(request.cg_x_mm, request.cg_y_mm, request.cg_z_mm),
        inertia_g_cm2=tensor,
        face_half_width_mm=request.face_half_width_mm,
        face_half_height_mm=request.face_half_height_mm,
    )
    head.face.shape = request.face_shape
    head.face.outline_source = request.face_outline_source
    if request.face_outline_is_measured is True:
        head.face.outline_source = "measured"
    # Re-run the outline's own validation, which the assignments above bypassed.
    head.face.__post_init__()
    return head


class ImpactConditionsRequest(BaseModel):
    """How the head arrives.

    `loft_deg` is the DELIVERED loft measured against the head's path, not
    against the horizon. For a client holding a swing profile that is
    dynamic loft minus attack angle -- the angle between the face normal and
    the direction the head is actually travelling, which is the only one the
    impact cares about.
    """

    clubhead_speed_mph: float
    loft_deg: float


def to_swing_conditions(request: ImpactConditionsRequest) -> SwingConditions:
    return SwingConditions(
        head_speed_mps=mph_to_mps(request.clubhead_speed_mph),
        loft_rad=degrees_to_radians(request.loft_deg),
    )


class MapSettingsRequest(BaseModel):
    spacing_mm: float = 2.0
    retention_threshold_pct: float = 97.0


def to_map_settings(request: MapSettingsRequest) -> MapSettings:
    return MapSettings(spacing_mm=request.spacing_mm,
                       retention_threshold_pct=request.retention_threshold_pct)


class ImpactRequest(BaseModel):
    head: HeadMassPropertiesRequest
    conditions: ImpactConditionsRequest
    strike_toe_mm: float = 0.0      # + toward the toe, as a golfer describes it
    strike_crown_mm: float = 0.0    # + toward the crown


class ForgivenessMapRequest(BaseModel):
    head: HeadMassPropertiesRequest
    conditions: ImpactConditionsRequest
    settings: MapSettingsRequest = MapSettingsRequest()


class ForgivenessCompareRequest(BaseModel):
    name_a: str
    head_a: HeadMassPropertiesRequest
    name_b: str
    head_b: HeadMassPropertiesRequest
    conditions: ImpactConditionsRequest
    settings: MapSettingsRequest = MapSettingsRequest()


class SaveHeadRequest(BaseModel):
    name: str
    head: HeadMassPropertiesRequest


def head_to_request_payload(head: HeadMassProperties) -> dict:
    """A stored head, back in the wire's units, ready to repopulate a form."""
    from units import kg_m2_to_g_cm2, kg_to_grams, m_to_mm

    tensor = head.inertia_about_cg
    return {
        "mass_g": kg_to_grams(head.mass_kg),
        "cg_x_mm": m_to_mm(head.cg_m[0]),
        "cg_y_mm": m_to_mm(head.cg_m[1]),
        "cg_z_mm": m_to_mm(head.cg_m[2]),
        "i_xx_g_cm2": kg_m2_to_g_cm2(tensor[0][0]),
        "i_yy_g_cm2": kg_m2_to_g_cm2(tensor[1][1]),
        "i_zz_g_cm2": kg_m2_to_g_cm2(tensor[2][2]),
        "i_xy_g_cm2": kg_m2_to_g_cm2(tensor[0][1]),
        "i_xz_g_cm2": kg_m2_to_g_cm2(tensor[0][2]),
        "i_yz_g_cm2": kg_m2_to_g_cm2(tensor[1][2]),
        "face_half_width_mm": m_to_mm(head.face.half_width_m),
        "face_half_height_mm": m_to_mm(head.face.half_height_m),
        "face_shape": head.face.shape,
        "face_outline_source": head.face.outline_source,
    }


def _grid_to_json(values: np.ndarray, digits: int = 3) -> list:
    """A 2D float grid as nested lists, with NaN turned into null.

    JSON has no NaN. Python's encoder will happily emit the bare token `NaN`,
    which is invalid JSON and which JSON.parse rejects outright -- so the
    off-face cells have to become null here or the whole response fails to
    parse in the browser. Rounding keeps the payload small; three decimals is
    far finer than anything the map can resolve.
    """
    return [[None if (value is None or math.isnan(value)) else round(float(value), digits)
             for value in row] for row in values]


def forgiveness_map_to_payload(fmap: ForgivenessMap) -> dict:
    """Serialise a map for the browser to draw itself.

    Deliberately the NUMBERS, not a picture. matplotlib is the CLI's display
    adapter; the browser is another one, and shipping a server-rendered PNG
    would make the web view a screenshot of the terminal's view rather than
    its own. It also keeps every honesty flag as structured data the UI can
    act on instead of text baked into an image.
    """
    return {
        "x_mm": [round(float(value), 3) for value in fmap.x_mm],
        "y_mm": [round(float(value), 3) for value in fmap.y_mm],
        "on_face": [[bool(value) for value in row] for row in fmap.on_face],
        "ball_speed_mph": _grid_to_json(fmap.ball_speed_mph),
        "speed_retention_pct": _grid_to_json(fmap.speed_retention_pct),
        "backspin_rpm": _grid_to_json(fmap.backspin_rpm, digits=1),
        "sidespin_rpm": _grid_to_json(fmap.sidespin_rpm, digits=1),
        "spin_axis_deg": _grid_to_json(fmap.spin_axis_deg),
        "launch_angle_deg": _grid_to_json(fmap.launch_angle_deg),
        "required_friction": _grid_to_json(fmap.required_friction, digits=4),
        "exceeds_friction": [[bool(value) for value in row] for row in fmap.exceeds_friction],
        "backspin_reversed": [[bool(value) for value in row] for row in fmap.backspin_reversed],
        "sweet_spot_mm": [round(value, 3) for value in fmap.sweet_spot_mm],
        "face_centre_mm": list(fmap.face_centre_mm),
        "summary": fmap.summary(),
        "head_description": fmap.head_description,
        "ball_description": fmap.ball_description,
        "conditions_description": fmap.conditions_description,
        "face_description": fmap.face_description,
    }


def map_comparison_to_payload(comparison: MapComparison) -> dict:
    """Serialise a B - A difference map. Sign matches club_comparison.py."""
    return {
        "name_a": comparison.name_a,
        "name_b": comparison.name_b,
        "x_mm": [round(float(value), 3) for value in comparison.x_mm],
        "y_mm": [round(float(value), 3) for value in comparison.y_mm],
        "on_face": [[bool(value) for value in row] for row in comparison.on_face],
        "delta_speed_retention_pct": _grid_to_json(comparison.delta_speed_retention_pct),
        "delta_ball_speed_mph": _grid_to_json(comparison.delta_ball_speed_mph),
        "delta_backspin_rpm": _grid_to_json(comparison.delta_backspin_rpm, digits=1),
        "delta_sidespin_rpm": _grid_to_json(comparison.delta_sidespin_rpm, digits=1),
        "delta_launch_angle_deg": _grid_to_json(comparison.delta_launch_angle_deg),
        "summary_a": comparison.summary_a,
        "summary_b": comparison.summary_b,
    }
