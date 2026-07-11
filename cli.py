from club_specification import ClubSpecification
from swing_weight import calculate_moment, moment_to_swing_weight
from moment_of_inertia import calculate_moi


def get_valid_float(prompt: str) -> float:
    while True:
        raw_value = input(prompt)
        try:
            return float(raw_value)
        except ValueError:
            print("That's not a valid number, please try again.")


def main():
    print("GolfLab Club Analyzer")
    print("----------------------")

    head_mass = get_valid_float("Head mass (grams): ")
    shaft_mass = get_valid_float("Shaft mass (grams): ")
    shaft_length = get_valid_float("Shaft length (inches): ")
    grip_mass = get_valid_float("Grip mass (grams): ")
    club_length = get_valid_float("Club length (inches): ")

    try:
        club = ClubSpecification(
            head_mass=head_mass,
            shaft_mass=shaft_mass,
            shaft_length=shaft_length,
            grip_mass=grip_mass,
            club_length=club_length,
        )
    except ValueError as error:
        print(f"Invalid club specification: {error}")
        return

    moment = calculate_moment(club)
    swing_weight = moment_to_swing_weight(moment)
    moi = calculate_moi(club)

    print()
    print("Results")
    print("-------")
    print(f"Swing weight: {swing_weight} ({moment:.2f} gram-inches)")
    print(f"MOI: {moi:.2f} gram-inches^2")


if __name__ == "__main__":
    main()