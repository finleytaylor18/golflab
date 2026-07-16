from club_specification import ClubSpecification
from swing_weight import calculate_moment, moment_to_swing_weight
from moment_of_inertia import calculate_moi
from club_repository import save_club, load_club, list_club_names
from club_comparison import compare_clubs
from club_diagram import plot_club_diagram
from club_specification import ClubSpecification, ClubType, CLUB_TYPE_LABELS, CLUB_TYPE_CATEGORIES
from clubhead_composition import WeightPort, ClubHeadComposition, calculate_head_cg
from clubhead_diagram import plot_head_composition


def _choose_from(prompt: str, options: list) -> int:
    """Prints a numbered list of options and returns the chosen index."""
    while True:
        raw_choice = input(prompt)
        try:
            choice_index = int(raw_choice) - 1
            if 0 <= choice_index < len(options):
                return choice_index
        except ValueError:
            pass
        print("Invalid choice, please try again.")


def get_valid_club_type() -> ClubType:
    # A flat list of all 25 specific club types is unusable as a single menu,
    # so this asks for a category first (Driver/Wood/Hybrid/Iron/Wedge), then
    # the specific club within it -- skipping straight through for Driver
    # since it has no sub-options.
    category_names = list(CLUB_TYPE_CATEGORIES.keys())
    print("Club category:")
    for index, name in enumerate(category_names, start=1):
        print(f"  {index}. {name}")
    category = category_names[_choose_from("Choose a category (number): ", category_names)]

    members = CLUB_TYPE_CATEGORIES[category]
    if len(members) == 1:
        return members[0]

    print(f"{category}:")
    for index, member in enumerate(members, start=1):
        print(f"  {index}. {CLUB_TYPE_LABELS[member]}")
    return members[_choose_from("Choose a specific club (number): ", members)]


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
    club_type = get_valid_club_type()
    head_mass = get_valid_float("Head mass (grams): ")
    shaft_mass = get_valid_float("Shaft mass (grams): ")
    shaft_length = get_valid_float("Shaft length (inches): ")
    grip_mass = get_valid_float("Grip mass (grams): ")
    club_length = get_valid_float("Club length (inches): ")
    loft = get_valid_float("Loft (degrees): ")
    lie_angle = get_valid_float("Lie angle (degrees): ")

    try:
        club = ClubSpecification(
            club_type=club_type,
            head_mass=head_mass,
            shaft_mass=shaft_mass,
            shaft_length=shaft_length,
            grip_mass=grip_mass,
            club_length=club_length,
            loft=loft,
            lie_angle=lie_angle,
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


def design_clubhead_composition() -> None:
    print("Enter weight ports one at a time. Enter a blank name when done.")
    ports = []
    while True:
        name = input(f"Port {len(ports) + 1} name (blank to finish): ")
        if not name:
            break
        mass = get_valid_float("  Mass (grams): ")
        toe_heel = get_valid_float("  Toe(+)/Heel(-) position (inches from head center): ")
        face_back = get_valid_float("  Back(+)/Face(-) position (inches from head center): ")
        try:
            ports.append(WeightPort(name=name, mass=mass, toe_heel=toe_heel, face_back=face_back))
        except ValueError as error:
            print(f"Invalid weight port: {error}")

    try:
        composition = ClubHeadComposition(weight_ports=ports)
    except ValueError as error:
        print(f"Invalid clubhead composition: {error}")
        return

    toe_heel_cg, face_back_cg = calculate_head_cg(composition)
    print()
    print(f"Head CG: toe/heel {toe_heel_cg:+.3f}\", face/back {face_back_cg:+.3f}\" (from head center)")

    diagram_choice = input("Generate a diagram? (y/n): ")
    if diagram_choice.lower() == "y":
        plot_head_composition(composition)


def main():
    print("GolfLab Club Analyzer")
    print("----------------------")

    while True:
        print("1. Analyze a new club")
        print("2. Load a saved club")
        print("3. Compare two saved clubs")
        print("4. Generate a diagram for a saved club")
        print("5. Design clubhead weight distribution")
        print("6. Quit")
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
            design_clubhead_composition()
        elif choice == "6":
            print("Goodbye.")
            break
        else:
            print("Invalid option, please choose 1, 2, 3, 4, 5, or 6.")

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