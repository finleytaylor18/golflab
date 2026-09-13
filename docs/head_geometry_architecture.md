# Parametric Head Geometry v1 — Architecture Proposal

**Status:** Step 2, Phase 2 (proposal only). **No code has been written.** Every code block is
an illustrative sketch of a proposed interface, not an implementation.

Physics and the reasons behind the modelling choices live in [`head_geometry.md`](head_geometry.md).
This document covers *how it is built*: frame, parameter schema, the integrator, assembly,
outputs, persistence, wiring, and the one change to an existing module that needs approval.

**Decisions carried in from the brief (approved):** crown/sole split in v1; masses not
thicknesses; weights as a list of point masses; numerical integration with closed-form
oracles; the integrator built with a solid mode for a later STL import.

---

## 1. One frame for everything

All designer-specified positions, and all outputs, are in the **head frame** of
`impact_architecture.md` §1.1: origin at the geometric face centre, `+x` toward the **heel**,
`+y` toward the crown, `+z` along the outward face normal.

The ellipsoid is *not* centred at the origin. Its centre sits behind the face at
`(0, 0, −z_f)`, where `z_f` is derived from the face width (§2.2). That is a derived quantity
the designer never types.

```
   PLAN — looking down from the crown

        back                           face plane  z = 0
   ╭──────────────╮                    ┊
  ╱   ●W      W●   ╲                   ┊
 │       ◇ ellipsoid centre (0,0,−z_f) ┊        +z  →  outward normal
 │  H                │                 ⊕ origin = face centre
  ╲                 ╱                  ┊
   ╰───────╌╌╌╌╌╌╌╌╯╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┊  ← shell clipped here; face plate fills the opening
        │◄─── z_f ───►│
        +x  →  heel   (toe is −x)
```

**Sign helper, as in Step 1.** Nobody should type a sign. A designer says "14 mm toward the
toe, 6 mm below centre, 42 mm back", and one function turns that into head-frame metres:

```python
def position_from_toe_crown_back_mm(toe_mm, crown_mm, back_mm) -> np.ndarray:
    # +x is the heel, so toe carries a sign flip; +z is outward, so "back" does too.
    return np.array([mm_to_m(-toe_mm), mm_to_m(crown_mm), mm_to_m(-back_mm)])
```

It lives next to `strike_from_toe_crown_mm` and is the *only* place those two flips exist.

---

## 2. The parameter schema

### 2.1 `HeadDesign`

Industry units at the boundary (mm, g), exactly like `HeadMassProperties.from_industry_units`;
SI inside. Sketch:

```python
@dataclass
class PointMass:
    name: str
    mass_g: float
    toe_mm: float          # + toward the toe
    crown_mm: float        # + toward the crown
    back_mm: float         # + deeper into the head

@dataclass
class HeadDesign:
    name: str                       # a DESIGN name, e.g. "design_v1"; never a product name
    half_width_mm: float            # a  — ellipsoid semi-axis, heel–toe
    half_height_mm: float           # b  — sole–crown
    half_depth_mm: float            # c  — face–back
    face_width_mm: float            # sets z_f; must be < 2a
    crown_mass_g: float             # shell above the y = 0 plane
    sole_mass_g: float              # shell below it
    face_mass_g: float
    hosel: PointMass
    weights: list[PointMass] = field(default_factory=list)
    mesh: MeshResolution = MeshResolution()   # a numerical setting, defaulted
```

Seven dimensions/masses, one hosel, and a list of weights. That is the whole design.

### 2.2 Derived, never typed

| Quantity | From | Formula |
|---|---|---|
| Face-plane offset `z_f` | face width `w`, `a`, `c` | `z_f = c √(1 − (w/2a)²)` |
| Face outline semi-axes | `z_f` | `a_f = a √(1 − (z_f/c)²) = w/2`, `b_f = b √(1 − (z_f/c)²)` |
| Ellipsoid centre | `z_f` | `(0, 0, −z_f)` in the head frame |
| Total mass | all parts | `Σ m` — reported, and compared to what a driver head weighs |

The face outline is therefore fully determined by the design, which is why §6 proposes an
`outline_source` of `"design"`.

### 2.3 Validation at the boundary (`__post_init__`, `ValueError`, matching the repo)

| Rule | Why it is an error rather than a warning |
|---|---|
| `a, b, c` positive and finite | not a shape otherwise |
| `0 < face_width < 2a` | the face plane must cut the ellipsoid; equal to `2a` is a tangent line, not a face |
| every mass `≥ 0`, total `> 0` | negative mass is not a design choice |
| every point-mass position finite and inside the bounding box `[−a, a] × [−b, b] × [−z_f − c, 0]` | a weight outside the head's box is a typo, not a design |
| `name` non-empty | outputs are labelled with it |

**Reported, not rejected** (a `warnings` list on the result): a point mass outside the
*ellipsoid surface* but inside the box (a hosel legitimately does this); total mass outside
150–250 g; any of the Rules limits in §5 exceeded.

### 2.4 `MeshResolution`

```python
@dataclass(frozen=True)
class MeshResolution:
    n_theta: int = 180      # polar divisions, face-plane to back
    n_phi: int = 360        # azimuthal divisions around the axis; must be even
```

Defaults give ~130 k triangles, which numpy integrates in milliseconds. `n_phi` must be even
so that `φ = 0` and `φ = π` are grid lines — that is what makes the crown/sole split exact
(§3.3). A convergence test (§8) fixes the defaults rather than a guess.

---

## 3. `mesh_mass_properties.py` — the integrator

One module, no knowledge of clubheads. It takes triangles and returns mass properties. It has
two modes because it will have two callers.

### 3.1 The common return type

```python
@dataclass(frozen=True)
class MassProperties:
    mass_kg: float
    cg_m: np.ndarray               # (3,) about the caller's origin
    inertia_about_cg: np.ndarray   # (3, 3) kg·m², about cg_m, caller's axes
```

SI, always. Conversion happens in the callers, at their boundaries.

### 3.2 Surface mode — thin shells

```python
def surface_mass_properties(vertices, triangles, triangle_masses) -> MassProperties
```

Each triangle is a flat lamina of known mass. For a lamina with vertices `p₁, p₂, p₃` and
mass `m`, the second-moment matrix about the origin is

> 📐 `S = (m/12) · [ p₁p₁ᵀ + p₂p₂ᵀ + p₃p₃ᵀ + (p₁+p₂+p₃)(p₁+p₂+p₃)ᵀ ]`

and the inertia tensor is `I = tr(S)·𝟙 − S`. Summing `S` over triangles, along with mass and
first moments, gives the shell's properties about the origin; the parallel-axis shift to the
CG is one subtraction. This is *exact per lamina*, so the only error is the tessellation's
approximation of the curved surface, and that converges as the mesh refines.

**Why not point masses at centroids?** They also converge, but slower (the lamina's own spread
is dropped). The exact lamina formula costs nothing extra and makes the convergence test
sharper.

### 3.3 The ellipsoid mesh, clipped and split exactly

```python
def ellipsoid_surface_mesh(a, b, c, resolution, z_min) -> (vertices, triangles, region)
```

Parametrise `x = a sinθ cosφ, y = b sinθ sinφ, z = c cosθ`. Two things fall out of choosing
this parametrisation and this grid:

- **Clipping is exact.** The face plane `z = z_f` (ellipsoid coordinates) is the level set
  `θ = θ_f = arccos(z_f / c)`. Restrict the grid to `θ ∈ [θ_f, π]` and no triangle straddles
  the plane — the truncation introduces no error of its own.
- **The crown/sole split is exact.** `y = 0` is `φ ∈ {0, π}`; with `n_phi` even both are grid
  lines, so every triangle lies wholly on one side. `region[k] ∈ {crown, sole}` by the sign of
  the centroid's `y`.

Each region's triangles get `σ = m_region / A_region` (area from the same triangles), so
`triangle_masses = σ_region · Aₖ`. The face plate is **not** meshed — it is closed form (§4.2).

### 3.4 Solid mode — closed meshes (the future STL importer)

```python
def solid_mass_properties(vertices, triangles, mass_kg=None, density_kg_m3=None) -> MassProperties
def assert_watertight(vertices, triangles) -> None
```

For a closed, consistently oriented mesh, the divergence theorem turns the volume integrals
into a sum over signed tetrahedra (each triangle with the origin). Volume, first moments and
second moments all come from the same loop. **Not built in this step beyond the interface and
its oracle tests** (§8) — but designing the surface mode without it would mean two
integrators later. `assert_watertight` (every edge shared by exactly two triangles with
opposite orientation) is the guard the STL route will need, and it is cheap to write now.

Given either a total mass or a density: mass fixes the scale; density is only ever
*caller-supplied with a citation*, per rule 3.

---

## 4. `head_geometry.py` — assembly

### 4.1 The function

```python
def design_mass_properties(design: HeadDesign) -> DesignResult
```

Pure. Steps: mesh the shell (§3.3) → surface properties per region → face plate closed form →
hosel and weights as point masses → superpose about a common origin → shift to the CG →
build `HeadMassProperties` (which re-validates the tensor: triangle inequality,
positive-definiteness, CG behind the face) → breakdown → conformance trio.

### 4.2 Face plate, closed form, about the origin

Thin elliptical plate, semi-axes `a_f, b_f`, mass `m_f`, centroid **at the origin**:

> 📐 `Iₓₓ = m_f b_f²/4`, `I_yy = m_f a_f²/4`, `I_zz = m_f (a_f² + b_f²)/4`

Its centroid being the origin is what makes the frame clean: the face plate needs no
parallel-axis shift until the final move to the assembled CG.

### 4.3 `DesignResult`

```python
@dataclass
class DesignResult:
    head: HeadMassProperties          # the thing the impact model consumes
    breakdown: list[PartContribution] # one row per part
    conformance: dict                 # volume, dimensions, MOI — see §5
    warnings: list[str]
    design: HeadDesign
```

`PartContribution` carries, per part: mass and its share; the part's pull on the CG (its
`mᵢ (rᵢ − r_cg) / M`, which sums to zero — a useful check); and its share of `Iₓₓ` and `I_yy`
about the assembled CG (the part's own tensor plus its parallel-axis term, which is exactly
the quantity that sums to the total). "The two 14 g weights are 31 % of `I_yy`" comes from
here.

### 4.4 Face outline

A `FaceGeometry(a_f, b_f, shape="ellipse", outline_source="design")` — see §6 for the field.

---

## 5. Conformance trio

`conformance_report()` on `HeadMassProperties` already covers MOI. The design adds volume and
dimensions, all ✅ from the Equipment Rules Part 2 §4b(i) (page numbers are the PDF's):

| Check | Computed as | Limit | Page |
|---|---|---|---|
| Heel–toe length | `2a` | ≤ 127 mm | 51 |
| Sole–crown height | `2b` | ≤ 71.12 mm | 51 |
| Proportion | `2a > z_f + c` | heel–toe must exceed face–back | 51 |
| Volume | `(4/3)π a b c − V_cap` | ≤ 460 + 10 cm³ | 52 |
| MOI | existing report | ≤ 5900 + 100 g·cm² | 54 |

The cap volume in front of the face plane, for the plane at `z_f` (ellipsoid coordinates):

> 📐 `V_cap = π a b ( 2c/3 − z_f + z_f³ / (3c²) )`
>
> Derived by integrating the cross-section area `π a b (1 − z²/c²)` from `z_f` to `c`.
> Verified during this proposal against Monte Carlo to 0.02 %, and exact at both endpoints
> (`z_f = −c` gives the whole ellipsoid, `z_f = c` gives zero). For the brief's proportions
> the cap is 12.8 % of the volume — against 20.7 % of the surface area (corrected in Phase 3
> from a mis-weighted 29 %; see the brief §3), which is why the truncation matters more for
> the tensor than for the volume.

All five are **reported, never enforced** — the same decision as Step 1's MOI report.

> 🔧 **Corrected in Phase 3.** The proportion row originally read `a > c`. The Rules compare
> heel-to-toe with *face-to-back*, and for a truncated head face-to-back is the face plane to
> the back pole, `z_f + c` — not the ellipsoid's full depth `2c`. The code uses `z_f + c` and
> a test pins it.

**As derived for `design_v1` (Phase 3, default mesh):** 200 g; CG 37.2 mm deep, 3.0 mm below
centre and 2.7 mm toward the heel (the hosel); `I = diag(2134, 3868, 3113) g·cm²` with
products of order 100; Rules-frame MOI **3543 g·cm²**; 385.9 cc; conforming on all five; no
warnings. Placeholder numbers from a placeholder design — but the right order of magnitude
without any tuning, which is the point of §7 in the brief.

---

## 6. One change to an existing module — needs approval (rule 7)

`FaceGeometry.outline_is_measured` is a boolean, and a designed outline is neither *assumed*
nor *measured*. Proposal, backward compatible:

```python
@dataclass
class FaceGeometry:
    half_width_m: float
    half_height_m: float
    outline_source: str = "assumed"      # "assumed" | "design" | "measured"
    shape: str = "ellipse"

    @property
    def outline_is_measured(self) -> bool:   # kept, so nothing that reads it changes
        return self.outline_source == "measured"
```

Touches: `head_mass_properties.py` (the field and `describe()`), `head_repository.py` (store
`face_outline_source`, and still *load* the old `face_outline_is_measured` key so an existing
`heads.json` keeps working), `api_schemas.py` and the frontend types/form (a three-way select
replacing the checkbox), and the tests that set the flag. The map's label becomes
`assumed (not measured)` / `from design` / `measured`.

It is small, it is the honest thing, and it is the only Step 1 module this step modifies.
**I will not make it without an explicit yes at this gate.** The fallback if refused: designs
carry `outline_is_measured=False` and the map says "assumed", which is wrong but harmless.

---

## 7. Persistence and the default design

`head_design_repository.py` mirrors `head_repository.py` exactly: module-level functions,
`designs.json`, industry units in the file, injected `data_file` for `tmp_path` tests. A design
can also be **exported** as a plain head via the existing `save_head`, so every current map
flow works on a designed head with no changes.

**`design_v1`** ships as the default the CLI and web form open on: the brief's §7 dimensions
(120 × 64 × 110 mm, face 100 mm wide) with a mass budget summing to 200 g — face 30, crown
50, sole 80, hosel 12, two rear-corner weights of 14 each. It is a **placeholder design to
edit**, labelled so in its name and in every output, and it is not a product. Its role is the
same as `fixture_symmetric_head`'s was: something real enough that the tool opens on a map.

---

## 8. Tests (Phase 3), mapped to files

| File | Test | Proves |
|---|---|---|
| `test_mesh_mass_properties.py` | sphere shell → `(2/3) m R²` to < 0.1 % | surface-mode machinery is right |
| | thin ellipsoidal shell (outer − inner oracle) to < 0.1 % | …and on the actual shape |
| | solid cube and solid ellipsoid oracles (solid mode) | the future importer's machinery is right |
| | `assert_watertight` rejects an open mesh | the STL guard works |
| | halving both resolutions changes the tensor by < 1e-4 relative | the number belongs to the shape |
| | clipped mesh has no vertex beyond `z_f`; split regions have no crossing triangle | exactness claims of §3.3 |
| `test_head_geometry.py` | assembling about two reference points → identical result | parallel-axis bookkeeping |
| | symmetric design → CG on the centreline, zero products, sweet spot at the face centre | no hidden asymmetry |
| | truncated vs untruncated shell differ by the cap share (≈ 21 % of area for §7 proportions) | clipping does what the brief says |
| | rear weight → deeper CG and larger `Iₓₓ`, `I_yy`; heel/toe pair → `I_yy` rises more than `Iₓₓ`; lighter crown → lower CG | the design levers move the right way |
| | breakdown shares sum to the totals; CG pulls sum to zero | the breakdown is a partition, not a story |
| | output passes `HeadMassProperties` validation | the derived tensor is physically possible |
| | a uniform 200 g shell lands within ±30 % of the brief's closed-form pre-check (3630 g·cm²) | the two methods agree to the order they should — the pre-check was an untruncated, non-uniform-thickness shell, so a band, not a number |
| | cap volume vs the closed form; conformance trio against the cited limits | §5 |
| | boundary validation rejects each rule in §2.3 | bad designs fail at the edge |
| `test_head_design_repository.py` | round trip, industry units on disk, old-key compatibility, `tmp_path` isolation | persistence |

---

## 9. Wiring (Phase 4)

- **CLI:** option 8, "Design a clubhead parametrically" — enter or load a design, print the
  breakdown and conformance trio, save it, and optionally export it as a head and run the
  existing forgiveness map on it.
- **API:** `POST /calculations/head-design` → the head payload (as `/heads/{name}` returns it)
  plus breakdown and conformance; `/designs` save/list/load mirroring `/heads`.
- **Web:** a `HeadDesignForm` (dimensions, mass budget, hosel, weights) beside the existing
  raw-tensor `HeadPropertiesForm`, with a toggle — *design it* or *type it in*. The
  forgiveness panel consumes the resulting head exactly as now. The breakdown renders as a
  small table under the form, because "which part owns the MOI" is the insight the designer
  is there for.

Nothing in the impact model, the map, or their tests changes.

---

## 10. Open questions for Phase 3

1. **Hosel default position** for `design_v1`. Something like 10 mm inside the heel edge, 20 mm
   above centre, 15 mm back is plausible for the placeholder — but it is a placeholder, and
   the number will be labelled as one.
2. **Report thickness?** If a designer supplies a density *with a citation*, the model could
   print the implied shell thickness as a sanity figure. Cheap; not needed for v1; suggest
   deferring.
3. **Warnings vs errors for a point mass outside the ellipsoid** — §2.3 proposes a warning
   because a hosel legitimately protrudes. Confirm.

The rest is decided above. Approve, and Phase 3 writes the integrator first — with its oracle
tests before anything that depends on it.
