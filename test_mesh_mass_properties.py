"""Oracle tests for the mesh integrator.

An integrator is only worth trusting on a shape it cannot be checked against
once it has reproduced the shapes it can. Each oracle here is either an
exact closed form (sphere, plate, cube, solid ellipsoid) or an independent
numerical method (Gauss-Legendre quadrature on the parametrised surface),
so agreement is evidence about the machinery and not about the mesh.
"""

import math

import numpy as np
import pytest

from mesh_mass_properties import (CROWN, SOLE, MassProperties, assert_watertight,
                                  ellipsoid_surface_mesh, enclosed_volume,
                                  inertia_from_second_moment, solid_mass_properties,
                                  surface_mass_properties, triangle_areas)

A, B, C = 0.060, 0.032, 0.055      # driver-like semi-axes, metres


def uniform_shell(vertices, triangles, mass):
    areas = triangle_areas(vertices, triangles)
    return surface_mass_properties(vertices, triangles, mass * areas / areas.sum())


def quadrature_shell(a, b, c, mass, z_max=None, order=160) -> MassProperties:
    """Independent oracle: Gauss-Legendre over the parametrised surface.

    Integrates the exact area element |dP/dth x dP/dph| with a high-order
    rule in both angles. Smooth integrand, so this converges spectrally and
    is accurate to ~1e-10 -- far beyond anything the tessellation reaches.
    Shares no code with the integrator beyond the parametrisation itself.
    """
    theta_start = 0.0 if z_max is None else math.acos(z_max / c)
    tn, tw = np.polynomial.legendre.leggauss(order)
    pn, pw = np.polynomial.legendre.leggauss(order)
    theta = 0.5 * (tn + 1) * (math.pi - theta_start) + theta_start
    tw = tw * 0.5 * (math.pi - theta_start)
    phi = 0.5 * (pn + 1) * 2 * math.pi
    pw = pw * math.pi

    th, ph = np.meshgrid(theta, phi, indexing="ij")
    w = np.outer(tw, pw)
    points = np.stack([a * np.sin(th) * np.cos(ph), b * np.sin(th) * np.sin(ph), c * np.cos(th)], -1)
    d_theta = np.stack([a * np.cos(th) * np.cos(ph), b * np.cos(th) * np.sin(ph), -c * np.sin(th)], -1)
    d_phi = np.stack([-a * np.sin(th) * np.sin(ph), b * np.sin(th) * np.cos(ph), np.zeros_like(th)], -1)
    area_element = np.linalg.norm(np.cross(d_theta, d_phi), axis=-1) * w

    area = area_element.sum()
    sigma = mass / area
    first = sigma * np.einsum("ij,ijk->k", area_element, points)
    second = sigma * np.einsum("ij,ijk,ijl->kl", area_element, points, points)
    cg = first / mass
    return MassProperties(mass, cg, inertia_from_second_moment(second - mass * np.outer(cg, cg)))


# ---------------------------------------------------------------------------
# SURFACE MODE
# ---------------------------------------------------------------------------

def test_a_thin_spherical_shell_gives_two_thirds_m_r_squared():
    """Proves the lamina machinery against the one curved closed form there
    is: a thin spherical shell has I = (2/3) m R^2 about every axis.
    """
    radius, mass = 0.021, 0.05
    vertices, triangles, _ = ellipsoid_surface_mesh(radius, radius, radius, 180, 360)
    result = uniform_shell(vertices, triangles, mass)

    expected = 2.0 / 3.0 * mass * radius ** 2
    assert np.allclose(np.diag(result.inertia_about_cg), expected, rtol=1e-3)
    assert np.allclose(result.cg_m, 0.0, atol=1e-12)
    assert result.mass_kg == pytest.approx(mass, rel=1e-12)


def test_a_flat_rectangular_plate_is_exact_with_two_triangles():
    """Proves the per-lamina formula is exact, not merely convergent: a
    rectangle split into two triangles must give the thin-plate result
    m b^2/12, m a^2/12, m(a^2+b^2)/12 to machine precision.
    """
    a, b, mass = 0.10, 0.06, 0.03
    vertices = np.array([[-a / 2, -b / 2, 0], [a / 2, -b / 2, 0], [a / 2, b / 2, 0], [-a / 2, b / 2, 0]])
    triangles = np.array([[0, 1, 2], [0, 2, 3]])
    result = uniform_shell(vertices, triangles, mass)

    expected = mass / 12.0 * np.array([b * b, a * a, a * a + b * b])
    assert np.allclose(np.diag(result.inertia_about_cg), expected, rtol=1e-12)
    assert np.allclose(result.inertia_about_cg - np.diag(np.diag(result.inertia_about_cg)), 0.0, atol=1e-18)


def test_an_ellipsoidal_shell_matches_independent_quadrature():
    """Proves the integrator on the actual shape. A uniform-density
    ellipsoidal shell has NO elementary closed form (its area involves
    elliptic integrals), so the oracle is Gauss-Legendre quadrature on the
    exact surface -- an independent method, accurate to ~1e-10.
    """
    mass = 0.150
    vertices, triangles, _ = ellipsoid_surface_mesh(A, B, C, 180, 360)
    result = uniform_shell(vertices, triangles, mass)
    oracle = quadrature_shell(A, B, C, mass)

    assert np.allclose(result.inertia_about_cg, oracle.inertia_about_cg, rtol=1e-3, atol=1e-9)
    assert np.allclose(result.cg_m, oracle.cg_m, atol=1e-9)


def test_a_clipped_shell_matches_quadrature_over_the_same_range():
    """Proves the truncation. Clipping at the face plane is exact in the
    parametrisation, so the clipped mesh must agree with quadrature over the
    identical theta range -- CG now off-centre and all.
    """
    z_max = C * math.sqrt(1 - (0.050 / A) ** 2)      # face 100 mm wide
    mass = 0.130
    vertices, triangles, _ = ellipsoid_surface_mesh(A, B, C, 180, 360, z_max=z_max)
    result = uniform_shell(vertices, triangles, mass)
    oracle = quadrature_shell(A, B, C, mass, z_max=z_max)

    assert np.all(vertices[:, 2] <= z_max + 1e-12)
    assert result.cg_m[2] < -0.001                    # pulled toward the back
    assert np.allclose(result.cg_m, oracle.cg_m, atol=1e-6)
    assert np.allclose(result.inertia_about_cg, oracle.inertia_about_cg, rtol=1e-3, atol=1e-9)


def test_the_cap_in_front_of_the_face_plane_is_a_large_share_of_the_shell():
    """Proves the brief's claim that truncation is not optional: for driver
    proportions with a 100 mm face, the surface in front of the face plane
    is about 21% of the whole shell (20.7% by exact quadrature).

    The concept brief originally said 29%. That came from a Monte Carlo
    pre-check that applied the sin(theta) area factor twice; this test and
    the quadrature oracle agree on the corrected figure, and the documents
    were corrected to match. A fifth of the shell is still far too much to
    double-count, so the conclusion is unchanged.
    """
    z_max = C * math.sqrt(1 - (0.050 / A) ** 2)
    whole = triangle_areas(*ellipsoid_surface_mesh(A, B, C, 180, 360)[:2]).sum()
    kept = triangle_areas(*ellipsoid_surface_mesh(A, B, C, 180, 360, z_max=z_max)[:2]).sum()

    cap_share = 1.0 - kept / whole
    assert cap_share == pytest.approx(0.2067, abs=0.003)


def test_refining_the_mesh_converges():
    """Proves the number belongs to the shape, not to the tessellation: the
    change from doubling the resolution must be far smaller than the change
    from halving it, and the default resolution must sit within 1e-4 of the
    quadrature oracle.
    """
    mass = 0.150
    oracle = quadrature_shell(A, B, C, mass).inertia_about_cg
    errors = []
    for n_theta, n_phi in ((45, 90), (90, 180), (180, 360)):
        vertices, triangles, _ = ellipsoid_surface_mesh(A, B, C, n_theta, n_phi)
        result = uniform_shell(vertices, triangles, mass).inertia_about_cg
        errors.append(np.max(np.abs(result - oracle)) / np.max(np.abs(oracle)))

    assert errors[0] > errors[1] > errors[2]
    assert errors[1] / errors[2] > 3.0                # second-order convergence
    assert errors[2] < 1e-4


def test_the_crown_sole_split_is_exact():
    """Proves the y = 0 plane is made of mesh edges: no triangle has vertices
    on both sides of it, so region masses can be assigned without error.
    """
    vertices, triangles, region = ellipsoid_surface_mesh(A, B, C, 60, 120)
    y = vertices[triangles][:, :, 1]

    assert np.all((y >= -1e-15).all(axis=1) | (y <= 1e-15).all(axis=1))
    assert np.count_nonzero(region == CROWN) == np.count_nonzero(region == SOLE)


def test_region_masses_land_where_they_are_sent():
    """Proves a heavier sole lowers the CG, which is the whole point of
    carrying two shell masses. Crown 40 g, sole 100 g: CG below centre.
    """
    vertices, triangles, region = ellipsoid_surface_mesh(A, B, C, 90, 180)
    areas = triangle_areas(vertices, triangles)
    masses = np.where(region == CROWN, 0.040 * areas / areas[region == CROWN].sum(),
                      0.100 * areas / areas[region == SOLE].sum())
    result = surface_mass_properties(vertices, triangles, masses)

    assert result.mass_kg == pytest.approx(0.140, rel=1e-12)
    assert result.cg_m[1] < -0.003
    assert abs(result.cg_m[0]) < 1e-9 and abs(result.cg_m[2]) < 1e-9


# ---------------------------------------------------------------------------
# SOLID MODE  (the future STL importer)
# ---------------------------------------------------------------------------

def unit_cube_mesh(side: float):
    s = side / 2
    v = np.array([[-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],
                  [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]])
    t = np.array([[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
                  [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]])
    return v, t


def test_a_solid_cube_is_exact_with_twelve_triangles():
    """Proves the tetrahedron machinery is exact for flat-faced solids: a
    cube gives m s^2 / 6 about each axis to machine precision, and its
    volume is s^3.
    """
    side, mass = 0.04, 0.2
    vertices, triangles = unit_cube_mesh(side)
    result = solid_mass_properties(vertices, triangles, mass_kg=mass)

    assert np.allclose(np.diag(result.inertia_about_cg), mass * side ** 2 / 6.0, rtol=1e-12)
    assert np.allclose(result.cg_m, 0.0, atol=1e-15)
    assert enclosed_volume(vertices, triangles) == pytest.approx(side ** 3, rel=1e-12)


def test_a_solid_ellipsoid_gives_m_over_five_times_b_squared_plus_c_squared():
    """Proves solid mode on a curved body: I_xx = m (b^2 + c^2) / 5 and
    cyclically, with volume (4/3) pi a b c, from the closed tessellation.
    """
    mass = 0.2
    vertices, triangles, _ = ellipsoid_surface_mesh(A, B, C, 180, 360)
    result = solid_mass_properties(vertices, triangles, mass_kg=mass)

    expected = mass / 5.0 * np.array([B * B + C * C, A * A + C * C, A * A + B * B])
    assert np.allclose(np.diag(result.inertia_about_cg), expected, rtol=1e-3)
    assert enclosed_volume(vertices, triangles) == pytest.approx(4 / 3 * math.pi * A * B * C, rel=1e-3)


def test_density_and_mass_are_two_ways_of_saying_the_same_thing():
    """Proves the scale is all a density adds: giving the density that
    reproduces the mass gives the identical tensor.
    """
    vertices, triangles = unit_cube_mesh(0.04)
    by_mass = solid_mass_properties(vertices, triangles, mass_kg=0.2)
    by_density = solid_mass_properties(vertices, triangles, density_kg_m3=0.2 / 0.04 ** 3)

    assert np.allclose(by_mass.inertia_about_cg, by_density.inertia_about_cg, rtol=1e-12)
    with pytest.raises(ValueError, match="exactly one"):
        solid_mass_properties(vertices, triangles, mass_kg=0.2, density_kg_m3=1.0)


def test_an_open_mesh_is_refused_by_solid_mode():
    """Proves the guard the STL route will rely on: a clipped shell does not
    enclose a volume, and solid mode must say so rather than return a
    plausible number.
    """
    vertices, triangles, _ = ellipsoid_surface_mesh(A, B, C, 30, 60, z_max=0.02)
    with pytest.raises(ValueError, match="not closed"):
        assert_watertight(vertices, triangles)
    with pytest.raises(ValueError, match="not closed"):
        solid_mass_properties(vertices, triangles, mass_kg=0.2)


def test_an_inconsistently_wound_mesh_is_refused():
    """Proves orientation errors are caught, since a single flipped triangle
    would silently subtract its tetrahedron instead of adding it.
    """
    vertices, triangles = unit_cube_mesh(0.04)
    triangles = triangles.copy()
    triangles[0] = triangles[0][::-1]
    with pytest.raises(ValueError, match="not consistently oriented"):
        assert_watertight(vertices, triangles)


def test_a_closed_ellipsoid_mesh_is_watertight_even_at_the_poles():
    """Proves the pole handling: the fan of triangles at each pole shares one
    vertex, so the full mesh passes the topological closure check.
    """
    vertices, triangles, _ = ellipsoid_surface_mesh(A, B, C, 20, 40)
    assert_watertight(vertices, triangles)


# ---------------------------------------------------------------------------
# INPUT VALIDATION
# ---------------------------------------------------------------------------

def test_bad_meshes_and_parameters_fail_loudly():
    with pytest.raises(ValueError, match="even n_phi"):
        ellipsoid_surface_mesh(A, B, C, 10, 21)
    with pytest.raises(ValueError, match="z_max"):
        ellipsoid_surface_mesh(A, B, C, 10, 20, z_max=C)
    with pytest.raises(ValueError, match="must be positive"):
        ellipsoid_surface_mesh(-A, B, C, 10, 20)
    vertices, triangles, _ = ellipsoid_surface_mesh(A, B, C, 10, 20)
    with pytest.raises(ValueError, match="one mass per triangle"):
        surface_mass_properties(vertices, triangles, np.ones(3))
    with pytest.raises(ValueError, match="non-negative"):
        surface_mass_properties(vertices, triangles, -np.ones(len(triangles)))
