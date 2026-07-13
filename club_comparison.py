from dataclasses import dataclass
from club_specification import ClubSpecification
from swing_weight import calculate_moment, moment_to_swing_weight
from moment_of_inertia import calculate_moi


@dataclass
class ClubComparison:
    name_a: str
    name_b: str
    moment_a: float
    moment_b: float
    moment_delta: float
    swing_weight_a: str
    swing_weight_b: str
    moi_a: float
    moi_b: float
    moi_delta: float


def compare_clubs(name_a: str, club_a: ClubSpecification, name_b: str, club_b: ClubSpecification) -> ClubComparison:
    moment_a = calculate_moment(club_a)
    moment_b = calculate_moment(club_b)

    moi_a = calculate_moi(club_a)
    moi_b = calculate_moi(club_b)

    return ClubComparison(
        name_a=name_a,
        name_b=name_b,
        moment_a=moment_a,
        moment_b=moment_b,
        moment_delta=moment_b - moment_a,
        swing_weight_a=moment_to_swing_weight(moment_a),
        swing_weight_b=moment_to_swing_weight(moment_b),
        moi_a=moi_a,
        moi_b=moi_b,
        moi_delta=moi_b - moi_a,
    )