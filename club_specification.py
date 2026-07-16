from dataclasses import dataclass
from enum import Enum


class ClubType(Enum):
    DRIVER = "driver"
    WOOD_3 = "wood_3"
    WOOD_5 = "wood_5"
    WOOD_7 = "wood_7"
    HYBRID_2 = "hybrid_2"
    HYBRID_3 = "hybrid_3"
    HYBRID_4 = "hybrid_4"
    IRON_2 = "iron_2"
    IRON_3 = "iron_3"
    IRON_4 = "iron_4"
    IRON_5 = "iron_5"
    IRON_6 = "iron_6"
    IRON_7 = "iron_7"
    IRON_8 = "iron_8"
    IRON_9 = "iron_9"
    WEDGE_46 = "wedge_46"
    WEDGE_48 = "wedge_48"
    WEDGE_50 = "wedge_50"
    WEDGE_52 = "wedge_52"
    WEDGE_54 = "wedge_54"
    WEDGE_56 = "wedge_56"
    WEDGE_58 = "wedge_58"
    WEDGE_60 = "wedge_60"
    WEDGE_62 = "wedge_62"
    WEDGE_64 = "wedge_64"


# Each specific club's range is a slice of what used to be one broad
# category range (driver/wood/hybrid/iron/wedge) -- the category envelopes
# haven't changed, they're just subdivided now instead of being one bucket.
#
# Irons and woods/hybrids split BOTH length and loft by number, because
# both genuinely and reliably vary by number in real graduated sets (a
# 9-iron is shorter AND more lofted than a 5-iron across virtually every
# manufacturer). Slices step in clean, even increments per number
# (0.5in/4deg for irons) rather than dividing the range into equal
# mathematical fractions, which produced ugly, falsely-precise boundaries
# for no real benefit.
#
# Wedges split only by loft, using real industry-standard 2-degree
# increments (this is how wedges actually ship) -- every wedge keeps the
# full original wedge length range (34.5-36.5in), because wedge length
# doesn't reliably correlate with loft the way iron length does; it's
# much more a matter of player/fitter preference. Narrowing it per-loft
# would be fabricating a precision that doesn't reflect real equipment.
CLUB_LENGTH_RANGES = {
    ClubType.DRIVER: (43.0, 48.0),
    ClubType.WOOD_3: (42.875, 43.5),
    ClubType.WOOD_5: (41.625, 42.875),
    ClubType.WOOD_7: (41.0, 41.625),
    ClubType.HYBRID_2: (40.25, 41.0),
    ClubType.HYBRID_3: (38.75, 40.25),
    ClubType.HYBRID_4: (38.0, 38.75),
    ClubType.IRON_2: (38.75, 39.0),
    ClubType.IRON_3: (38.25, 38.75),
    ClubType.IRON_4: (37.75, 38.25),
    ClubType.IRON_5: (37.25, 37.75),
    ClubType.IRON_6: (36.75, 37.25),
    ClubType.IRON_7: (36.25, 36.75),
    ClubType.IRON_8: (35.75, 36.25),
    ClubType.IRON_9: (35.5, 35.75),
    ClubType.WEDGE_46: (34.5, 36.5),
    ClubType.WEDGE_48: (34.5, 36.5),
    ClubType.WEDGE_50: (34.5, 36.5),
    ClubType.WEDGE_52: (34.5, 36.5),
    ClubType.WEDGE_54: (34.5, 36.5),
    ClubType.WEDGE_56: (34.5, 36.5),
    ClubType.WEDGE_58: (34.5, 36.5),
    ClubType.WEDGE_60: (34.5, 36.5),
    ClubType.WEDGE_62: (34.5, 36.5),
    ClubType.WEDGE_64: (34.5, 36.5),
}  # inches

LOFT_RANGES = {
    ClubType.DRIVER: (8.0, 12.0),
    ClubType.WOOD_3: (13.0, 15.0),
    ClubType.WOOD_5: (15.0, 19.0),
    ClubType.WOOD_7: (19.0, 21.0),
    ClubType.HYBRID_2: (16.0, 19.0),
    ClubType.HYBRID_3: (19.0, 25.0),
    ClubType.HYBRID_4: (25.0, 28.0),
    ClubType.IRON_2: (18.0, 20.0),
    ClubType.IRON_3: (20.0, 24.0),
    ClubType.IRON_4: (24.0, 28.0),
    ClubType.IRON_5: (28.0, 32.0),
    ClubType.IRON_6: (32.0, 36.0),
    ClubType.IRON_7: (36.0, 40.0),
    ClubType.IRON_8: (40.0, 44.0),
    ClubType.IRON_9: (44.0, 47.0),
    ClubType.WEDGE_46: (46.0, 47.0),
    ClubType.WEDGE_48: (47.0, 49.0),
    ClubType.WEDGE_50: (49.0, 51.0),
    ClubType.WEDGE_52: (51.0, 53.0),
    ClubType.WEDGE_54: (53.0, 55.0),
    ClubType.WEDGE_56: (55.0, 57.0),
    ClubType.WEDGE_58: (57.0, 59.0),
    ClubType.WEDGE_60: (59.0, 61.0),
    ClubType.WEDGE_62: (61.0, 63.0),
    ClubType.WEDGE_64: (63.0, 64.0),
}  # degrees

# Display labels and category grouping -- shared metadata for any menu that
# needs to present these 25 types sensibly (a flat list is unusable), not
# used in any calculation. CLI and frontend both consume CLUB_TYPE_CATEGORIES
# instead of each hardcoding their own grouping.
CLUB_TYPE_LABELS = {
    ClubType.DRIVER: "Driver",
    ClubType.WOOD_3: "3 Wood",
    ClubType.WOOD_5: "5 Wood",
    ClubType.WOOD_7: "7 Wood",
    ClubType.HYBRID_2: "2 Hybrid",
    ClubType.HYBRID_3: "3 Hybrid",
    ClubType.HYBRID_4: "4 Hybrid",
    ClubType.IRON_2: "2 Iron",
    ClubType.IRON_3: "3 Iron",
    ClubType.IRON_4: "4 Iron",
    ClubType.IRON_5: "5 Iron",
    ClubType.IRON_6: "6 Iron",
    ClubType.IRON_7: "7 Iron",
    ClubType.IRON_8: "8 Iron",
    ClubType.IRON_9: "9 Iron",
    ClubType.WEDGE_46: "46° Wedge",
    ClubType.WEDGE_48: "48° Wedge",
    ClubType.WEDGE_50: "50° Wedge",
    ClubType.WEDGE_52: "52° Wedge",
    ClubType.WEDGE_54: "54° Wedge",
    ClubType.WEDGE_56: "56° Wedge",
    ClubType.WEDGE_58: "58° Wedge",
    ClubType.WEDGE_60: "60° Wedge",
    ClubType.WEDGE_62: "62° Wedge",
    ClubType.WEDGE_64: "64° Wedge",
}

CLUB_TYPE_CATEGORIES = {
    "Driver": [ClubType.DRIVER],
    "Wood": [ClubType.WOOD_3, ClubType.WOOD_5, ClubType.WOOD_7],
    "Hybrid": [ClubType.HYBRID_2, ClubType.HYBRID_3, ClubType.HYBRID_4],
    "Iron": [
        ClubType.IRON_2, ClubType.IRON_3, ClubType.IRON_4, ClubType.IRON_5,
        ClubType.IRON_6, ClubType.IRON_7, ClubType.IRON_8, ClubType.IRON_9,
    ],
    "Wedge": [
        ClubType.WEDGE_46, ClubType.WEDGE_48, ClubType.WEDGE_50, ClubType.WEDGE_52,
        ClubType.WEDGE_54, ClubType.WEDGE_56, ClubType.WEDGE_58, ClubType.WEDGE_60,
        ClubType.WEDGE_62, ClubType.WEDGE_64,
    ],
}

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
