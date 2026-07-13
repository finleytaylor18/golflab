from club_specification import ClubSpecification
from swing_weight import calculate_moment, moment_to_swing_weight
from moment_of_inertia import calculate_moi
from club_repository import save_club, load_club, list_club_names
from club_comparison import compare_clubs
from club_diagram import plot_club_diagram


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


def print_comparison(comparison) -> None:
    print()
    print(f"Comparing '{comparison.name_a}' vs '{comparison.name_b}'")
    print("-" * 40)
    print(f"Swing weight: {comparison.swing_weight_a}  vs  {comparison.swing_weight_b}")
    print(f"Moment:       {comparison.moment_a:.2f}  vs  {comparison.moment_b:.2f}   (delta: {comparison.moment_delta:+.2f})")
    print(f"MOI:          {comparison.moi_a:.2f}  vs  {comparison.moi_b:.2f}   (delta: {comparison.moi_delta:+.2f})")


def compare_saved_clubs() -> None:
    names = list_club_names()
    if len(names) < 2:
        print("You need at least 2 saved clubs to compare.")
        return

    print("Saved clubs:", ", ".join(names))
    name_a = input("Enter the first club's name: ")
    name_b = input("Enter the second club's name: ")

    try:
        club_a = load_club(name_a)
        club_b = load_club(name_b)
    except KeyError as error:
        print(error)
        return

    comparison = compare_clubs(name_a, club_a, name_b, club_b)
    print_comparison(comparison)


def main():
    print("GolfLab Club Analyzer")
    print("----------------------")

    while True:
        print("1. Analyze a new club")
        print("2. Load a saved club")
        print("3. Compare two saved clubs")
        print("4. Generate a diagram for a saved club")
        print("5. Quit")
        choice = input("Choose an option: ")

        if choice == "1":
            analyze_new_club()
        elif choice == "2":
            load_and_analyze_saved_club()
        elif choice == "3":
            compare_saved_clubs()
        elif choice == "4":
            generate_diagram_for_saved_club()
        elif choice == "5":
            print("Goodbye.")
            break
        else:
            print("Invalid option, please choose 1, 2, 3, 4, or 5.")

def generate_diagram_for_saved_club() -> None:
    names = list_club_names()
    if not names:
        print("No saved clubs found.")
        return

    print("Saved clubs:", ", ".join(names))
    name = input("Enter the name of the club to diagram: ")

    try:
        club = load_club(name)
    except KeyError as error:
        print(error)
        return

    output_path = f"{name.replace(' ', '_')}_diagram.png"
    plot_club_diagram(club, output_path=output_path)

if __name__ == "__main__":
    main()