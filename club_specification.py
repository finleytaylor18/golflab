from dataclasses import dataclass


@dataclass
class ClubSpecification:
    head_mass: float          # grams
    shaft_mass: float         # grams
    shaft_length: float       # inches
    grip_mass: float          # grams
    club_length: float        # inches


if __name__ == "__main__":
    driver = ClubSpecification(
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )
    print(driver)

from dataclasses import dataclass

MIN_CLUB_LENGTH = 24.0   # inches, roughly shortest realistic putter
MAX_CLUB_LENGTH = 48.0   # inches, roughly longest realistic driver
MIN_MASS = 1.0            # grams, nothing realistically weighs less
MAX_MASS = 500.0          # grams, generous upper bound for any component


@dataclass
class ClubSpecification:
    head_mass: float          # grams
    shaft_mass: float         # grams
    shaft_length: float       # inches
    grip_mass: float          # grams
    club_length: float        # inches

    def __post_init__(self):
        if not (MIN_CLUB_LENGTH <= self.club_length <= MAX_CLUB_LENGTH):
            raise ValueError(
                f"club_length {self.club_length} is outside realistic range "
                f"({MIN_CLUB_LENGTH}-{MAX_CLUB_LENGTH} inches)"
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