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
