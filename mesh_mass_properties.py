"""Mass properties of triangle meshes. Knows nothing about golf.

Two modes, because two things will call it:

  surface mode   a THIN SHELL: every triangle is a flat lamina carrying a
                 known mass. Used by the parametric head's body shell.
  solid mode     a CLOSED mesh bounding a volume, uniform density inside.
                 Not used by the parametric head at all -- it is the future
                 STL importer, and building the surface mode without it would
                 have meant two integrators later.

Both return the same thing: mass, centre of gravity, and the inertia tensor
about that centre, in SI, about the caller's origin and axes. Unit
conversion belongs to the callers.

THE ONE TRICK BOTH MODES SHARE
------------------------------
Work with the second-moment matrix S = integral of (x x^T) dm rather than
the inertia tensor directly. S is exactly integrable per triangle (and per
tetrahedron), it shifts between reference points with a single outer
product, and the inertia tensor is then I = tr(S) 1 - S. Doing it this way
means the parallel-axis theorem appears exactly once, at the very end.
"""

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MassProperties:
    mass_kg: float
    cg_m: np.ndarray                # (3,) about the caller's origin
    inertia_about_cg: np.ndarray    # (3, 3) kg*m^2, about cg_m, caller's axes


def inertia_from_second_moment(second_moment: np.ndarray) -> np.ndarray:
    """I = tr(S) 1 - S, the identity that links the two descriptions."""
    return np.trace(second_moment) * np.eye(3) - second_moment


def _finish(mass: float, first_moment: np.ndarray,
            second_moment_about_origin: np.ndarray) -> MassProperties:
    """Shift from the origin to the centre of gravity and build the tensor.

    S_origin = S_cg + M c c^T, so S_cg = S_origin - M c c^T. That subtraction
    IS the parallel-axis theorem, in its second-moment form.
    """
    if mass <= 0.0:
        raise ValueError(f"total mass must be positive (got {mass})")
    cg = first_moment / mass
    second_moment_cg = second_moment_about_origin - mass * np.outer(cg, cg)
    return MassProperties(mass_kg=float(mass), cg_m=cg,
                          inertia_about_cg=inertia_from_second_moment(second_moment_cg))


def _check_mesh(vertices: np.ndarray, triangles: np.ndarray) -> tuple:
    vertices = np.asarray(vertices, dtype=float)
    triangles = np.asarray(triangles, dtype=int)
    if vertices.ndim != 2 or vertices.shape[1] != 3:
        raise ValueError(f"vertices must be (n, 3) (got {vertices.shape})")
    if triangles.ndim != 2 or triangles.shape[1] != 3:
        raise ValueError(f"triangles must be (m, 3) (got {triangles.shape})")
    if triangles.size and (triangles.min() < 0 or triangles.max() >= len(vertices)):
        raise ValueError("triangles index vertices that do not exist")
    return vertices, triangles


# ---------------------------------------------------------------------------
# SURFACE MODE
# ---------------------------------------------------------------------------

def triangle_areas(vertices: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    vertices, triangles = _check_mesh(vertices, triangles)
    p1, p2, p3 = (vertices[triangles[:, k]] for k in range(3))
    return 0.5 * np.linalg.norm(np.cross(p2 - p1, p3 - p1), axis=1)


def surface_mass_properties(vertices: np.ndarray, triangles: np.ndarray,
                            triangle_masses: np.ndarray) -> MassProperties:
    """A thin shell: each triangle is a flat lamina of the given mass.

    For a uniform lamina with vertices p1, p2, p3 and mass m, the second
    moment about the origin is exactly

        S = (m / 12) [ p1 p1^T + p2 p2^T + p3 p3^T + (p1+p2+p3)(p1+p2+p3)^T ]

    so the only approximation anywhere is the tessellation of a curved
    surface into flat pieces -- and that converges as the mesh is refined.
    """
    vertices, triangles = _check_mesh(vertices, triangles)
    masses = np.asarray(triangle_masses, dtype=float)
    if masses.shape != (len(triangles),):
        raise ValueError("one mass per triangle is required")
    if np.any(masses < 0.0):
        raise ValueError("triangle masses must be non-negative")

    p1, p2, p3 = (vertices[triangles[:, k]] for k in range(3))
    total = p1 + p2 + p3

    mass = float(masses.sum())
    first_moment = (masses[:, None] * total / 3.0).sum(axis=0)
    second_moment = (
        np.einsum("k,ki,kj->ij", masses, p1, p1)
        + np.einsum("k,ki,kj->ij", masses, p2, p2)
        + np.einsum("k,ki,kj->ij", masses, p3, p3)
        + np.einsum("k,ki,kj->ij", masses, total, total)
    ) / 12.0
    return _finish(mass, first_moment, second_moment)


CROWN, SOLE = 1, -1


def ellipsoid_surface_mesh(a: float, b: float, c: float, n_theta: int, n_phi: int,
                           z_max: float = None) -> tuple:
    """Tessellate the ellipsoid x^2/a^2 + y^2/b^2 + z^2/c^2 = 1, about its centre.

    Parametrised as x = a sin(th) cos(ph), y = b sin(th) sin(ph), z = c cos(th).
    Two properties of this choice are the reason for it:

      * A plane z = z_max is the level set th = arccos(z_max / c). Keeping
        th in [th_max, pi] clips the mesh at that plane EXACTLY: no triangle
        straddles it.
      * With n_phi even, ph = 0 and ph = pi are grid lines, so the plane
        y = 0 is made of mesh edges and every triangle lies wholly on the
        crown (y > 0) or sole (y < 0) side. The returned `region` says which.

    Triangles are wound so their normals point outward, which is what solid
    mode needs. The back pole (and the front pole, when unclipped) is a
    single shared vertex with a fan of triangles, so the closed mesh is
    watertight in the topological sense that assert_watertight checks.

    Returns (vertices, triangles, region) with region in {CROWN, SOLE}.
    """
    for name, value in (("a", a), ("b", b), ("c", c)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be positive and finite (got {value})")
    if n_theta < 2 or n_phi < 4 or n_phi % 2:
        raise ValueError("need n_theta >= 2 and an even n_phi >= 4")

    if z_max is None:
        theta_start = 0.0
    else:
        if not -c < z_max < c:
            raise ValueError(f"z_max must lie strictly inside (-c, c) (got {z_max})")
        theta_start = math.acos(z_max / c)

    theta = np.linspace(theta_start, math.pi, n_theta + 1)
    phi = np.arange(n_phi) * (2.0 * math.pi / n_phi)

    # Vertex rows. A pole row (th = 0 or th = pi) collapses to one vertex.
    rows = []
    vertices = []
    for th in theta:
        if abs(math.sin(th)) < 1e-12:
            rows.append(np.array([len(vertices)]))
            vertices.append([0.0, 0.0, c * math.cos(th)])
        else:
            start = len(vertices)
            rows.append(start + np.arange(n_phi))
            vertices.extend(
                [a * math.sin(th) * math.cos(p), b * math.sin(th) * math.sin(p), c * math.cos(th)]
                for p in phi
            )
    vertices = np.array(vertices)

    triangles = []
    for upper, lower in zip(rows[:-1], rows[1:]):
        for j in range(n_phi):
            jn = (j + 1) % n_phi
            u0 = upper[j % len(upper)]
            u1 = upper[jn % len(upper)]
            l0 = lower[j % len(lower)]
            l1 = lower[jn % len(lower)]
            # Outward winding: (dP/dtheta) x (dP/dphi) points outward for
            # this parametrisation, and theta increases from upper to lower.
            if len(upper) == 1:                 # fan from the front pole
                triangles.append([u0, l0, l1])
            elif len(lower) == 1:               # fan to the back pole
                triangles.append([u0, l0, u1])
            else:
                triangles.append([u0, l0, l1])
                triangles.append([u0, l1, u1])
    triangles = np.array(triangles)

    centroid_y = vertices[triangles].mean(axis=1)[:, 1]
    region = np.where(centroid_y >= 0.0, CROWN, SOLE)
    return vertices, triangles, region


# ---------------------------------------------------------------------------
# SOLID MODE
# ---------------------------------------------------------------------------

def assert_watertight(vertices: np.ndarray, triangles: np.ndarray) -> None:
    """Refuse a mesh that does not enclose a volume.

    Closed and consistently oriented means: every directed edge (i -> j)
    appears in exactly one triangle, and its reverse (j -> i) in exactly one
    other. Solid mode silently returns nonsense on anything else, which is
    why this is a hard check and not a warning.
    """
    vertices, triangles = _check_mesh(vertices, triangles)
    n = len(vertices)
    directed = np.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
    if np.any(directed[:, 0] == directed[:, 1]):
        raise ValueError("mesh has a degenerate edge (a triangle repeats a vertex)")
    keys = directed[:, 0] * n + directed[:, 1]
    unique, counts = np.unique(keys, return_counts=True)
    if np.any(counts != 1):
        raise ValueError("mesh is not consistently oriented: a directed edge is used twice")
    reverse = directed[:, 1] * n + directed[:, 0]
    if not np.array_equal(np.sort(reverse), unique):
        raise ValueError("mesh is not closed: an edge has no partner in the opposite direction")


def solid_mass_properties(vertices: np.ndarray, triangles: np.ndarray,
                          mass_kg: float = None, density_kg_m3: float = None) -> MassProperties:
    """A closed mesh filled with uniform density.

    Each triangle and the origin form a signed tetrahedron. Summing signed
    volumes, first moments and second moments over all of them gives the
    solid's integrals -- everything outside the surface cancels. For a
    tetrahedron with vertices 0, p1, p2, p3 the second moment is

        S = (V / 20) [ p1 p1^T + p2 p2^T + p3 p3^T + (p1+p2+p3)(p1+p2+p3)^T ]

    the volume analogue of the lamina's /12. Give either a total mass (the
    usual case: the scale) or a density with a citation, never both.
    """
    if (mass_kg is None) == (density_kg_m3 is None):
        raise ValueError("give exactly one of mass_kg or density_kg_m3")
    assert_watertight(vertices, triangles)
    vertices, triangles = _check_mesh(vertices, triangles)

    p1, p2, p3 = (vertices[triangles[:, k]] for k in range(3))
    signed_volume = np.einsum("ki,ki->k", p1, np.cross(p2, p3)) / 6.0
    total = p1 + p2 + p3

    volume = float(signed_volume.sum())
    if volume < 0.0:
        # Consistently inward-wound: flip the sign convention rather than
        # fail, since assert_watertight already proved consistency.
        signed_volume = -signed_volume
        volume = -volume
    if volume <= 0.0:
        raise ValueError("mesh encloses no volume")

    first_moment = (signed_volume[:, None] * total / 4.0).sum(axis=0)
    second_moment = (
        np.einsum("k,ki,kj->ij", signed_volume, p1, p1)
        + np.einsum("k,ki,kj->ij", signed_volume, p2, p2)
        + np.einsum("k,ki,kj->ij", signed_volume, p3, p3)
        + np.einsum("k,ki,kj->ij", signed_volume, total, total)
    ) / 20.0

    density = density_kg_m3 if density_kg_m3 is not None else mass_kg / volume
    if not math.isfinite(density) or density <= 0.0:
        raise ValueError(f"density must be positive and finite (got {density})")
    return _finish(density * volume, density * first_moment, density * second_moment)


def enclosed_volume(vertices: np.ndarray, triangles: np.ndarray) -> float:
    """Volume of a closed mesh, for conformance reporting and for tests."""
    assert_watertight(vertices, triangles)
    vertices, triangles = _check_mesh(vertices, triangles)
    p1, p2, p3 = (vertices[triangles[:, k]] for k in range(3))
    return abs(float(np.einsum("ki,ki->k", p1, np.cross(p2, p3)).sum()) / 6.0)
