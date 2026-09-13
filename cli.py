from club_specification import ClubSpecification
from swing_weight import calculate_moment, moment_to_swing_weight
from moment_of_inertia import calculate_moi
from club_repository import save_club, load_club, list_club_names
from club_comparison import compare_clubs
from club_diagram import plot_club_diagram
from club_specification import ClubSpecification, ClubType, CLUB_TYPE_LABELS, CLUB_TYPE_CATEGORIES
from clubhead_composition import WeightPort, ClubHeadComposition, calculate_head_cg
from clubhead_diagram import plot_head_composition
from head_mass_properties import HeadMassProperties
from head_repository import save_head, load_head, list_head_names
from ball_properties import conforming_three_piece_tour_ball
from impact_model import SwingConditions
from forgiveness_map import MapSettings, compute_forgiveness_map, compare_maps
from forgiveness_diagram import plot_forgiveness_map, plot_map_comparison
from units import mph_to_mps, degrees_to_radians
from head_geometry import HeadDesign, PointMass, default_design, design_mass_properties
from head_design_repository import save_design, load_design, list_design_names


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
        print("6. Forgiveness map for a clubhead")
        print("7. Compare two saved clubheads")
        print("8. Design a clubhead parametrically")
        print("9. Quit")
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
            generate_forgiveness_map()
        elif choice == "7":
            compare_saved_heads()
        elif choice == "8":
            design_clubhead_parametrically()
        elif choice == "9":
            print("Goodbye.")
            break
        else:
            print("Invalid option, please choose 1 to 9.")

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


# ---------------------------------------------------------------------------
# IMPACT MODEL AND FORGIVENESS MAPS
# ---------------------------------------------------------------------------

def get_head_mass_properties() -> HeadMassProperties:
    """Collect a clubhead's mass properties in the units Fusion reports them.

    The inertia tensor is asked for as its six INDEPENDENT components rather
    than as nine numbers. A real tensor is symmetric, so asking for all nine
    would invite someone to type an asymmetric one -- which the domain model
    would then reject after they had entered everything else.
    """
    print()
    print("Head mass properties, in the head frame:")
    print("  x: toe -> HEEL (a toe strike is negative x)")
    print("  y: sole -> crown")
    print("  z: outward face normal, so the CG depth is entered as negative")
    print()

    mass_g = get_valid_float("Head mass (g): ")
    cg_x = get_valid_float("CG toe-heel position (mm, + toward heel): ")
    cg_y = get_valid_float("CG height (mm, + toward crown): ")
    cg_z = get_valid_float("CG depth (mm, NEGATIVE, e.g. -35): ")

    print()
    print("Inertia tensor about the CG (g.cm^2). Products of inertia are zero")
    print("for a symmetric head; enter 0 if you do not have them.")
    i_xx = get_valid_float("  Ixx (about the toe-heel axis): ")
    i_yy = get_valid_float("  Iyy (about the sole-crown axis): ")
    i_zz = get_valid_float("  Izz (about the face normal): ")
    i_xy = get_valid_float("  Ixy: ")
    i_xz = get_valid_float("  Ixz: ")
    i_yz = get_valid_float("  Iyz: ")

    tensor = [[i_xx, i_xy, i_xz],
              [i_xy, i_yy, i_yz],
              [i_xz, i_yz, i_zz]]

    print()
    half_width = get_valid_float("Face half-width (mm, toe to centre): ")
    half_height = get_valid_float("Face half-height (mm, centre to crown): ")

    head = HeadMassProperties.from_industry_units(
        mass_g=mass_g, cg_mm=(cg_x, cg_y, cg_z), inertia_g_cm2=tensor,
        face_half_width_mm=half_width, face_half_height_mm=half_height)

    measured = input("Is that face outline measured from real geometry? (y/n): ")
    head.face.outline_source = "measured" if measured.lower() == "y" else "assumed"

    report = head.conformance_report()
    print()
    print(f"Rules-frame MOI: {report['rules_frame_moi_g_cm2']:.0f} g.cm^2 "
          f"(limit {report['limit_g_cm2']:.0f} + {100:.0f} tolerance) -- "
          f"{'conforming' if report['conforms'] else 'NON-CONFORMING'}")
    print(f"  measured about the vertical axis at a 60 degree lie, per "
          f"{report['citation']}")
    print("  A wildly wrong number here usually means the tensor was entered "
          "in the wrong units.")
    return head


def get_swing_conditions() -> SwingConditions:
    speed_mph = get_valid_float("Clubhead speed (mph): ")
    loft_deg = get_valid_float("Delivered loft (degrees): ")
    return SwingConditions(head_speed_mps=mph_to_mps(speed_mph),
                           loft_rad=degrees_to_radians(loft_deg))


def choose_or_enter_head(prompt: str) -> tuple:
    """Load a saved head or collect a new one. Returns (name, head)."""
    names = list_head_names()
    if names:
        print("Saved clubheads:", ", ".join(names))
        name = input(f"{prompt} (blank to enter a new one): ")
        if name:
            try:
                return name, load_head(name)
            except (KeyError, ValueError) as error:
                print(error)
                return None, None

    head = get_head_mass_properties()
    name = input("Name for this clubhead (blank to skip saving): ")
    if name:
        save_head(name, head)
        print(f"Saved '{name}'.")
    return name or "unnamed head", head


def generate_forgiveness_map() -> None:
    name, head = choose_or_enter_head("Clubhead to map")
    if head is None:
        return

    conditions = get_swing_conditions()
    ball = conforming_three_piece_tour_ball()
    print(f"Ball: {ball.description}")

    fmap = compute_forgiveness_map(head, ball, conditions, MapSettings())
    print_map_summary(name, fmap)

    output_path = f"{name.replace(' ', '_')}_forgiveness.png"
    plot_forgiveness_map(fmap, output_path=output_path,
                         title=f"Forgiveness map - {name}")


def compare_saved_heads() -> None:
    names = list_head_names()
    if len(names) < 2:
        print("You need at least 2 saved clubheads to compare.")
        return

    print("Saved clubheads:", ", ".join(names))
    name_a = input("Enter the first clubhead's name: ")
    name_b = input("Enter the second clubhead's name: ")

    try:
        head_a = load_head(name_a)
        head_b = load_head(name_b)
    except (KeyError, ValueError) as error:
        print(error)
        return

    conditions = get_swing_conditions()
    ball = conforming_three_piece_tour_ball()
    settings = MapSettings()

    map_a = compute_forgiveness_map(head_a, ball, conditions, settings)
    map_b = compute_forgiveness_map(head_b, ball, conditions, settings)

    try:
        comparison = compare_maps(name_a, map_a, name_b, map_b)
    except ValueError as error:
        print(error)
        return

    print_map_summary(name_a, map_a)
    print_map_summary(name_b, map_b)
    print()
    print(f"Difference is {name_b} minus {name_a}, matching the project's "
          f"existing delta convention.")

    plot_map_comparison(comparison,
                        output_path=f"{name_a.replace(' ', '_')}_vs_"
                                    f"{name_b.replace(' ', '_')}_forgiveness.png")


def print_map_summary(name: str, fmap) -> None:
    summary = fmap.summary()
    threshold = summary["threshold_pct"]

    print()
    print(f"Forgiveness summary - {name}")
    print("-" * 40)
    print(f"Sweet spot at ({fmap.sweet_spot_mm[0]:+.1f}, {fmap.sweet_spot_mm[1]:+.1f}) mm "
          f"from the face centre")
    print(f"Sweet-spot ball speed: {summary['sweet_spot_ball_speed_mph']:.1f} mph")
    print(f"Area keeping >= {threshold:.0f}% of that speed: "
          f"{summary['forgiving_area_mm2']:.0f} mm^2 of "
          f"{summary['face_area_mm2']:.0f} mm^2 swept "
          f"({100 * summary['forgiving_area_fraction']:.0f}%)")
    print(f"  NOTE: the {threshold:.0f}% threshold is a chosen setting, not an "
          f"industry standard.")
    print(f"Worst retention on the face: {summary['worst_retention_pct']:.1f}%")
    print(f"Backspin range: {summary['backspin_range_rpm'][0]:.0f} to "
          f"{summary['backspin_range_rpm'][1]:.0f} rpm")
    print(f"Largest sidespin: {summary['max_abs_sidespin_rpm']:.0f} rpm")
    print(f"Face outline: {summary['face_description']}")

    if summary["points_needing_more_friction"]:
        print(f"  WARNING: {summary['points_needing_more_friction']} grid points need "
              f"more friction than the sourced coefficient allows.")
    if summary["points_with_reversed_backspin"]:
        print(f"  WARNING: {summary['points_with_reversed_backspin']} grid points show "
              f"topspin -- the flat-face assumption has broken down there.")
    print("  The v1 face is flat: real bulge and roll counteract the gear effect "
          "shown here, so curvature is overstated toward the rim.")


# ---------------------------------------------------------------------------
# PARAMETRIC HEAD DESIGN
# ---------------------------------------------------------------------------

def get_point_mass(label: str, default: PointMass) -> PointMass:
    """Collect a hosel or a weight in the designer's own words."""
    print(f"{label} (Enter keeps the default in brackets)")
    def ask(prompt, current):
        raw = input(f"  {prompt} [{current:g}]: ")
        return float(raw) if raw.strip() else current
    mass = ask("mass (g)", default.mass_g)
    toe = ask("toward the toe (mm, negative = heel)", default.toe_mm)
    crown = ask("toward the crown (mm, negative = sole)", default.crown_mm)
    back = ask("back from the face (mm)", default.back_mm)
    return PointMass(default.name, mass, toe, crown, back)


def get_head_design() -> HeadDesign:
    """Collect a design. Defaults come from the placeholder design_v1 so a
    designer can change one number and see what it does."""
    base = default_design()
    print()
    print("Parametric head: a thin ellipsoidal shell cut at the face plane, a face")
    print("plate, a hosel and weights. Masses, not thicknesses -- the total is")
    print("checked against what a driver head weighs. Enter keeps the default.")
    print()
    def ask(prompt, current):
        raw = input(f"{prompt} [{current:g}]: ")
        return float(raw) if raw.strip() else current

    name = input(f"Design name [{base.name}]: ").strip() or base.name
    a = ask("Half-width, heel to centre (mm)", base.half_width_mm)
    b = ask("Half-height, centre to crown (mm)", base.half_height_mm)
    c = ask("Half-depth, centre to back (mm)", base.half_depth_mm)
    w = ask("Face width (mm)", base.face_width_mm)
    crown = ask("Crown shell mass (g)", base.crown_mass_g)
    sole = ask("Sole shell mass (g)", base.sole_mass_g)
    face = ask("Face plate mass (g)", base.face_mass_g)
    hosel = get_point_mass("Hosel", base.hosel)

    weights = []
    for default_weight in base.weights:
        keep = input(f"Include '{default_weight.name}'? (y/n) [y]: ").strip().lower()
        if keep in ("", "y"):
            weights.append(get_point_mass(default_weight.name, default_weight))
    while True:
        extra = input("Add another weight? Enter a name, or blank to finish: ").strip()
        if not extra:
            break
        weights.append(get_point_mass(extra, PointMass(extra, 10.0, 0.0, -10.0, 60.0)))

    return HeadDesign(name=name, half_width_mm=a, half_height_mm=b, half_depth_mm=c,
                      face_width_mm=w, crown_mass_g=crown, sole_mass_g=sole, face_mass_g=face,
                      hosel=hosel, weights=weights)


def print_design_result(result) -> None:
    head, c = result.head, result.conformance
    cg = head.cg_m
    print()
    print(f"Derived head - {result.design.name}")
    print("-" * 40)
    print(f"Mass {head.mass_kg * 1000:.1f} g | CG {-cg[0] * 1000:+.1f} mm toward toe, "
          f"{cg[1] * 1000:+.1f} mm up, {head.cg_depth_m * 1000:.1f} mm deep")
    ixx, iyy, izz = (head.inertia_about_cg[i][i] * 1e7 for i in range(3))
    print(f"Inertia about the CG: Ixx {ixx:.0f}, Iyy {iyy:.0f}, Izz {izz:.0f} g.cm^2")
    print(f"Sweet spot: {-head.sweet_spot_m[0] * 1000:+.1f} mm toward toe, "
          f"{head.sweet_spot_m[1] * 1000:+.1f} mm up from the face centre")
    print()
    print(f"{'part':<14}{'mass g':>8}{'mass%':>7}{'Ixx%':>7}{'Iyy%':>7}")
    for part in result.breakdown:
        print(f"{part.name:<14}{part.mass_g:>8.1f}{100 * part.mass_share:>7.0f}"
              f"{100 * part.ixx_share:>7.1f}{100 * part.iyy_share:>7.1f}")
    print()
    print(f"Rules: heel-toe {c['heel_toe_mm']:.0f} mm (limit 127), sole-crown "
          f"{c['sole_crown_mm']:.0f} mm (limit 71.12), face-back {c['face_to_back_mm']:.0f} mm, "
          f"volume {c['volume_cc']:.0f} cc (limit 460+10), MOI {c['rules_frame_moi_g_cm2']:.0f} "
          f"g.cm^2 (limit 5900+100) -- {'conforming' if c['conforms'] else 'NON-CONFORMING'}")
    print(f"  {c['citation']}")
    for warning in result.warnings:
        print(f"  WARNING: {warning}")
    print("  The shell is an idealised ellipsoid: trends and ratios are trustworthy,")
    print("  absolute values only to the extent the idealisation holds. Not a product.")


def design_clubhead_parametrically() -> None:
    names = list_design_names()
    design = None
    if names:
        print("Saved designs:", ", ".join(names))
        chosen = input("Design to load (blank to enter a new one): ").strip()
        if chosen:
            try:
                design = load_design(chosen)
            except (KeyError, ValueError) as error:
                print(error)
                return
    if design is None:
        try:
            design = get_head_design()
        except ValueError as error:
            print(error)
            return

    try:
        result = design_mass_properties(design)
    except ValueError as error:
        print(error)
        return
    print_design_result(result)

    if input("Save this design? (y/n): ").strip().lower() == "y":
        save_design(design.name, design)
        print(f"Saved design '{design.name}'.")
    if input("Export the derived head so options 6 and 7 can use it? (y/n): ").strip().lower() == "y":
        head_name = input(f"Name for the head [{design.name}]: ").strip() or design.name
        save_head(head_name, result.head)
        print(f"Saved head '{head_name}'.")
    if input("Run a forgiveness map on it now? (y/n): ").strip().lower() == "y":
        conditions = get_swing_conditions()
        fmap = compute_forgiveness_map(result.head, conforming_three_piece_tour_ball(),
                                       conditions, MapSettings())
        print_map_summary(design.name, fmap)
        plot_forgiveness_map(fmap, output_path=f"{design.name.replace(' ', '_')}_forgiveness.png",
                             title=f"Forgiveness map - {design.name} (parametric design)")


if __name__ == "__main__":
    main()
