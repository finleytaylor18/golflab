import matplotlib.pyplot as plt
from clubhead_composition import ClubHeadComposition, WeightPort, calculate_head_cg

MASS_TO_MARKER_SIZE = 25  # points^2 per gram, for visually scaling port markers by mass


def plot_head_composition(composition: ClubHeadComposition, output_path: str = "clubhead_diagram.png") -> None:
    cg_toe_heel, cg_face_back = calculate_head_cg(composition)

    fig, ax = plt.subplots(figsize=(6, 6))

    ax.axhline(0, color="gray", linewidth=1, linestyle="--", zorder=1)
    ax.axvline(0, color="gray", linewidth=1, linestyle="--", zorder=1)

    for port in composition.weight_ports:
        ax.scatter(
            port.toe_heel,
            port.face_back,
            s=port.mass * MASS_TO_MARKER_SIZE,
            color="steelblue",
            alpha=0.7,
            zorder=2,
        )
        ax.annotate(
            f"{port.name}\n{port.mass:.1f}g",
            xy=(port.toe_heel, port.face_back),
            ha="center",
            va="center",
            fontsize=8,
        )

    ax.scatter(cg_toe_heel, cg_face_back, color="green", s=150, marker="^", zorder=3, label="Head CG")
    ax.annotate(
        f"CG ({cg_toe_heel:.2f}, {cg_face_back:.2f})",
        xy=(cg_toe_heel, cg_face_back),
        xytext=(cg_toe_heel, cg_face_back - 0.25),
        ha="center",
        fontsize=9,
        fontweight="bold",
    )

    coords = [(p.toe_heel, p.face_back) for p in composition.weight_ports] + [(cg_toe_heel, cg_face_back)]
    max_extent = max(abs(value) for point in coords for value in point)
    limit = max_extent + 0.75

    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal")
    ax.set_xlabel("Toe (+) / Heel (−), inches from head center")
    ax.set_ylabel("Back (+) / Face (−), inches from head center")
    ax.set_title("Clubhead Weight Distribution")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15))

    plt.savefig(output_path, bbox_inches="tight")
    print(f"Diagram saved to {output_path}")


if __name__ == "__main__":
    driver_head = ClubHeadComposition(weight_ports=[
        WeightPort(name="Heel port", mass=8.0, toe_heel=-1.1, face_back=-0.3),
        WeightPort(name="Toe port", mass=6.0, toe_heel=1.2, face_back=-0.2),
        WeightPort(name="Back port", mass=10.0, toe_heel=0.0, face_back=1.3),
    ])
    plot_head_composition(driver_head)
