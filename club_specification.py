from dataclasses import dataclass
from enum import Enum


class ClubType(Enum):
    DRIVER = "driver"
    WOOD = "wood"
    HYBRID = "hybrid"
    IRON = "iron"
    WEDGE = "wedge"


CLUB_LENGTH_RANGES = {
    ClubType.DRIVER: (43.0, 48.0),
    ClubType.WOOD: (41.0, 43.5),
    ClubType.HYBRID: (38.0, 41.0),
    ClubType.IRON: (35.5, 39.0),
    ClubType.WEDGE: (34.5, 36.5),
}  # inches, approximate industry-typical ranges per club type

LOFT_RANGES = {
    ClubType.DRIVER: (8.0, 12.0),
    ClubType.WOOD: (13.0, 21.0),
    ClubType.HYBRID: (16.0, 28.0),
    ClubType.IRON: (18.0, 47.0),   # spans the whole iron set (3-iron through PW) since ClubType doesn't distinguish individual iron numbers
    ClubType.WEDGE: (46.0, 64.0),
}  # degrees, approximate industry-typical ranges per club type

MIN_MASS = 1.0    # grams
MAX_MASS = 500.0  # grams, kept generous and global across types for now

MIN_LIE_ANGLE = 55.0  # degrees
MAX_LIE_ANGLE = 72.0  # degrees, kept generous and global across types for now, same documented gap as MIN_MASS/MAX_MASS


@dataclass
class ClubSpecification:
    club_type: ClubType
    head_mass: float          # grams
    shaft_mass: float         # grams
    shaft_length: float       # inches
    grip_mass: float          # grams
    club_length: float        # inches
    loft: float                # degrees
    lie_angle: float           # degrees

    def __post_init__(self):
        min_length, max_length = CLUB_LENGTH_RANGES[self.club_type]
        if not (min_length <= self.club_length <= max_length):
            raise ValueError(
                f"club_length {self.club_length} is outside realistic range "
                f"for {self.club_type.value} ({min_length}-{max_length} inches)"
            )

        min_loft, max_loft = LOFT_RANGES[self.club_type]
        if not (min_loft <= self.loft <= max_loft):
            raise ValueError(
                f"loft {self.loft} is outside realistic range "
                f"for {self.club_type.value} ({min_loft}-{max_loft} degrees)"
            )

        if not (MIN_LIE_ANGLE <= self.lie_angle <= MAX_LIE_ANGLE):
            raise ValueError(
                f"lie_angle {self.lie_angle} is outside realistic range "
                f"({MIN_LIE_ANGLE}-{MAX_LIE_ANGLE} degrees)"
            )

        for mass_name, mass_value in [
            ("head_mass", self.head_mass),
            ("shaft_mass", self.shaft_mass),
            ("grip_mass", self.grip_mass),
        ]:
            if not (MIN_MASS <= mass_value <= MAX_MASS):
                raise ValueError(
                    f"{mass_name} {mass_value} is outside realistic range "
                    f"({MIN_MASS}-{MAX_MASS} grams)"
                )