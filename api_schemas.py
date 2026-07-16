from pydantic import BaseModel
from club_specification import ClubSpecification, ClubType
from swing_profile import SwingProfile
from clubhead_composition import WeightPort, ClubHeadComposition


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
