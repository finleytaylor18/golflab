"""Matplotlib rendering of forgiveness maps. Display only -- no physics here.

Every map is drawn FACE-ON, the way a launch monitor draws an impact pattern
and the way a driver is photographed: +x rightward is the heel, so the toe is
on the left. The axis labels say so on every panel, because the repo's older
`clubhead_diagram.py` uses the opposite sign for its own toe-heel axis and the
two must never be read as the same convention.

Two things are always drawn, because leaving either out makes a map
misleading:

  * the geometric face centre AND the sweet spot, separately. They coincide
    only when the CG sits dead behind the middle of the face, and the offset
    between them is a real design output, not an error.
  * a marker on any grid point where the no-slip solution demanded more
    friction than the sourced coefficient allows. In that region the model is
    extrapolating beyond its own stated validity, and the map should say so
    rather than quietly present a number.
"""

import matplotlib
import numpy as np

matplotlib.use("Agg")           # save to file; never needs a display
import matplotlib.pyplot as plt  # noqa: E402

from forgiveness_map import ForgivenessMap, MapComparison  # noqa: E402

X_LABEL = "toe  ←   strike position (mm)   →  heel"
Y_LABEL = "sole  ←   strike height (mm)   →  crown"


def _draw_panel(axes, fmap_x, fmap_y, values, on_face, title, unit,
                colour_map, diverging=False):
    """One heat map panel, masked to the face outline."""
    masked = np.where(on_face, values, np.nan)
    spacing_x = (fmap_x[1] - fmap_x[0]) / 2.0 if len(fmap_x) > 1 else 1.0
    spacing_y = (fmap_y[1] - fmap_y[0]) / 2.0 if len(fmap_y) > 1 else 1.0
    extent = (fmap_x[0] - spacing_x, fmap_x[-1] + spacing_x,
              fmap_y[0] - spacing_y, fmap_y[-1] + spacing_y)

    limits = {}
    if diverging:
        # A diverging quantity must be centred on zero or the colour lies
        # about which side of neutral a point is on.
        extreme = np.nanmax(np.abs(masked)) if np.any(on_face) else 1.0
        extreme = extreme if np.isfinite(extreme) and extreme > 0 else 1.0
        limits = {"vmin": -extreme, "vmax": extreme}

    image = axes.imshow(masked, origin="lower", extent=extent, aspect="equal",
                        cmap=colour_map, interpolation="nearest", **limits)
    axes.set_title(title, fontsize=10)
    axes.set_xlabel(X_LABEL, fontsize=7)
    axes.set_ylabel(Y_LABEL, fontsize=7)
    axes.tick_params(labelsize=7)
    bar = axes.figure.colorbar(image, ax=axes, shrink=0.85)
    bar.set_label(unit, fontsize=7)
    bar.ax.tick_params(labelsize=7)
    return image


def _mark_reference_points(axes, face_centre_mm, sweet_spot_mm):
    axes.plot(*face_centre_mm, marker="x", color="black", markersize=8,
              markeredgewidth=1.6, linestyle="none", label="face centre", zorder=4)
    axes.plot(*sweet_spot_mm, marker="*", color="white", markersize=13,
              markeredgecolor="black", markeredgewidth=0.8, linestyle="none",
              label="sweet spot", zorder=5)


def _mark_friction_limit(axes, fmap: ForgivenessMap):
    """Dot every point where the model is extrapolating past its sourced mu."""
    if not np.any(fmap.exceeds_friction):
        return
    rows, columns = np.nonzero(fmap.exceeds_friction)
    axes.plot(fmap.x_mm[columns], fmap.y_mm[rows], marker=".", color="black",
              markersize=2.5, linestyle="none", zorder=3,
              label="needs more friction than sourced μ")


def _mark_reversed_backspin(axes, fmap: ForgivenessMap):
    """Ring every point where the gear effect has beaten the loft entirely.

    These points carry topspin. A real driver's roll would almost certainly
    prevent that, so they mark where the flat-face assumption has broken down
    rather than a result to design around.
    """
    if not np.any(fmap.backspin_reversed):
        return
    rows, columns = np.nonzero(fmap.backspin_reversed)
    axes.plot(fmap.x_mm[columns], fmap.y_mm[rows], marker="o", color="none",
              markeredgecolor="black", markeredgewidth=0.9, markersize=4,
              linestyle="none", zorder=3, label="topspin — flat-face limit")


def plot_forgiveness_map(fmap: ForgivenessMap,
                         output_path: str = "forgiveness_map.png",
                         title: str = "Forgiveness map") -> str:
    """Draw the four launch-condition heat maps and save them to one figure."""
    figure, axes_grid = plt.subplots(2, 2, figsize=(12.5, 9.5))

    panels = [
        (axes_grid[0][0], fmap.speed_retention_pct,
         "Ball speed retention", "% of sweet-spot ball speed", "viridis", False),
        # Sidespin rather than spin axis tilt: both were permitted, and
        # sidespin is the one that cannot wrap. Spin axis tilt is still
        # computed and carried on the map for anyone who wants it, but as an
        # angle it becomes meaningless the moment backspin goes negative,
        # and a heat map has no way to show that.
        (axes_grid[0][1], fmap.sidespin_rpm,
         "Sidespin  (+ curves right)", "rpm", "RdBu_r", True),
        (axes_grid[1][0], fmap.backspin_rpm,
         "Backspin", "rpm", "plasma", False),
        (axes_grid[1][1], fmap.launch_angle_deg,
         "Launch angle", "degrees", "cividis", False),
    ]

    for axes, values, panel_title, unit, colour_map, diverging in panels:
        _draw_panel(axes, fmap.x_mm, fmap.y_mm, values, fmap.on_face,
                    panel_title, unit, colour_map, diverging)
        _mark_reference_points(axes, fmap.face_centre_mm, fmap.sweet_spot_mm)
        _mark_friction_limit(axes, fmap)
        _mark_reversed_backspin(axes, fmap)

    handles, labels = axes_grid[1][0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=3, fontsize=8,
                  frameon=False, bbox_to_anchor=(0.5, 0.055))

    summary = fmap.summary()
    figure.suptitle(title, fontsize=14, y=0.985)
    for offset, line in enumerate(_provenance_lines(fmap)):
        figure.text(0.5, 0.955 - 0.018 * offset, line, ha="center", fontsize=8,
                    color="#333333")

    footer = _summary_lines(summary)
    for offset, line in enumerate(footer):
        figure.text(0.5, 0.052 - 0.016 * offset, line, ha="center", fontsize=8,
                    color="#333333")
    figure.text(0.5, 0.052 - 0.016 * len(footer), FLAT_FACE_CAVEAT, ha="center",
                fontsize=8, color="#8a4a00")

    figure.tight_layout(rect=(0, 0.075 + 0.016 * len(footer), 1, 0.945))
    figure.savefig(output_path, dpi=130)
    plt.close(figure)
    print(f"Forgiveness map saved to {output_path}")
    return output_path


def _provenance_lines(fmap: ForgivenessMap) -> list:
    """Where every number on this figure came from, split to fit the width."""
    return [
        f"{fmap.head_description}   |   {fmap.conditions_description}   |   "
        f"face: {fmap.face_description}",
        f"ball: {fmap.ball_description}",
    ]


def _summary_lines(summary: dict) -> list:
    """The headline number and any warnings, one short line each."""
    threshold = summary["threshold_pct"]
    lines = [
        f"Area keeping ≥ {threshold:.0f}% of sweet-spot ball speed: "
        f"{summary['forgiving_area_mm2']:.0f} mm² of "
        f"{summary['face_area_mm2']:.0f} mm² swept "
        f"({100 * summary['forgiving_area_fraction']:.0f}%).  "
        f"The {threshold:.0f}% threshold is a CHOSEN SETTING, not a standard."
    ]
    if summary["points_needing_more_friction"]:
        lines.append(f"⚠ {summary['points_needing_more_friction']} grid points need more "
                     f"friction than the sourced μ — the model is extrapolating there.")
    if summary.get("points_with_reversed_backspin"):
        lines.append(f"⚠ {summary['points_with_reversed_backspin']} grid points show topspin "
                     f"— the flat-face assumption has broken down there.")
    return lines


FLAT_FACE_CAVEAT = ("v1 face is FLAT — no bulge or roll. Real face curvature exists to "
                    "counteract the gear effect shown here, so curvature is overstated "
                    "toward the rim. Trust the centre; treat the edges as an upper bound.")


def plot_map_comparison(comparison: MapComparison,
                        output_path: str = "forgiveness_comparison.png") -> str:
    """Draw B minus A for four quantities.

    Sign convention is the project's existing one (`club_comparison.py`:
    `moi_delta = moi_b - moi_a`), so every panel is B - A and blue/red read
    as "B is lower/higher here". The title states it outright, because a
    difference map with an unstated sign is worse than no map at all.
    """
    figure, axes_grid = plt.subplots(2, 2, figsize=(12.5, 9.5))

    panels = [
        (axes_grid[0][0], comparison.delta_speed_retention_pct,
         "Δ ball speed retention", "percentage points"),
        (axes_grid[0][1], comparison.delta_sidespin_rpm,
         "Δ sidespin", "rpm"),
        (axes_grid[1][0], comparison.delta_backspin_rpm,
         "Δ backspin", "rpm"),
        (axes_grid[1][1], comparison.delta_launch_angle_deg,
         "Δ launch angle", "degrees"),
    ]

    for axes, values, panel_title, unit in panels:
        _draw_panel(axes, comparison.x_mm, comparison.y_mm, values,
                    comparison.on_face, panel_title, unit, "RdBu_r", diverging=True)

    figure.suptitle(
        f"Forgiveness comparison:  {comparison.name_b}  minus  {comparison.name_a}",
        fontsize=14, y=0.98)
    figure.text(0.5, 0.945,
                f"Positive (red) means {comparison.name_b} is HIGHER than "
                f"{comparison.name_a} at that point.",
                ha="center", fontsize=8, color="#333333")
    figure.text(0.5, 0.928,
                "Sign follows club_comparison.py: delta = B − A.",
                ha="center", fontsize=8, color="#333333")

    a_area = comparison.summary_a.get("forgiving_area_mm2", 0.0)
    b_area = comparison.summary_b.get("forgiving_area_mm2", 0.0)
    threshold = comparison.summary_a.get("threshold_pct", 0.0)
    figure.text(0.5, 0.030,
                f"Area keeping ≥ {threshold:.0f}% ball speed — "
                f"{comparison.name_a}: {a_area:.0f} mm²,  "
                f"{comparison.name_b}: {b_area:.0f} mm²,  "
                f"difference: {b_area - a_area:+.0f} mm²",
                ha="center", fontsize=8, color="#333333")
    figure.text(0.5, 0.010, FLAT_FACE_CAVEAT, ha="center", fontsize=8,
                color="#8a4a00")

    figure.tight_layout(rect=(0, 0.055, 1, 0.918))
    figure.savefig(output_path, dpi=130)
    plt.close(figure)
    print(f"Comparison map saved to {output_path}")
    return output_path
