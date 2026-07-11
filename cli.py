from club_specification import ClubSpecification
from swing_weight import calculate_moment, moment_to_swing_weight
from moment_of_inertia import calculate_moi
from club_repository import save_club, load_club, list_club_names


def get_valid_float(prompt: str) -> float:
    while True:
        raw_value = input(prompt)
        try:
            return float(raw_value)
        except ValueError:
            print("That's not a valid number, please try again.")


def print_results(club: ClubSpecification) -> None:
    moment = calculate_moment(club)
    swing_weight = moment_to_swing_weight(moment)
    moi = calculate_moi(club)

    print()
    print("Results")
    print("-------")
    print(f"Swing weight: {swing_weight} ({moment:.2f} gram-inches)")
    print(f"MOI: {moi:.2f} gram-inches^2")


def analyze_new_club() -> None:
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

    print_results(club)

    save_choice = input("Save this club? (y/n): ")
    if save_choice.lower() == "y":
        name = input("Enter a name for this club: ")
        save_club(name, club)
        print(f"Saved as '{name}'.")


def load_and_analyze_saved_club() -> None:
    names = list_club_names()
    if not names:
        print("No saved clubs found.")
        return

    print("Saved clubs:", ", ".join(names))
    name = input("Enter the name of the club to load: ")

    try:
        club = load_club(name)
    except KeyError as error:
        print(error)
        return

    print_results(club)


def main():
    print("GolfLab Club Analyzer")
    print("----------------------")

    while True:
        print()
        print("1. Analyze a new club")
        print("2. Load a saved club")
        print("3. Quit")
        choice = input("Choose an option: ")

        if choice == "1":
            analyze_new_club()
        elif choice == "2":
            load_and_analyze_saved_club()
        elif choice == "3":
            print("Goodbye.")
            break
        else:
            print("Invalid option, please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()