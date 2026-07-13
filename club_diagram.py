import matplotlib.pyplot as plt
from club_specification import ClubSpecification
from center_of_gravity import calculate_balance_point, GRIP_CENTER_FROM_BUTT

GRIP_LENGTH = 10.0  # inches, typical standard grip length
HEAD_VISUAL_LENGTH = 4.0  # inches, approximate driver head length — for diagram only, not used in any calculation

def plot_club_diagram(club: ClubSpecification, output_path: str = "club_diagram.png") -> None:
    head_position = club.club_length
    shaft_position = club.shaft_length / 2
    grip_position = GRIP_CENTER_FROM_BUTT
    balance_point = calculate_balance_point(club)

    fig, ax = plt.subplots(figsize=(10, 3))

    ax.plot([0, club.club_length], [0, 0], color="black", linewidth=2)

    ax.plot(
        [0, GRIP_LENGTH],
        [0, 0],
        color="blue",
        linewidth=8,
        solid_capstyle="butt",
        zorder=2,
        label="Grip",
    )
    ax.plot(
        [head_position - HEAD_VISUAL_LENGTH, head_position],
        [0, 0],
        color="red",
        linewidth=8,
        solid_capstyle="butt",
        alpha=0.4,
        zorder=1,
        label="Head (approximate extent)",
    )
    ax.scatter(shaft_position, 0, color="gray", s=100, zorder=3, label="Shaft midpoint")
    ax.scatter(head_position, 0, color="red", s=150, zorder=3, label="Head")
    ax.scatter(balance_point, 0, color="green", s=200, marker="^", zorder=4, label="Balance point")
    ax.annotate(
        f"{balance_point:.2f}\"",
        xy=(balance_point, 0),
        xytext=(balance_point, 0.15),
        ha="center",
        fontsize=10,
        fontweight="bold",
    )

    ax.set_xlabel("Distance from butt end (inches)")
    ax.set_yticks([])
    ax.set_ylim(-1, 1)
    ax.set_title("Club Component Diagram")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=4)

    plt.savefig(output_path, bbox_inches="tight")
    print(f"Diagram saved to {output_path}")


if __name__ == "__main__":
    driver = ClubSpecification(
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )
    plot_club_diagram(driver)