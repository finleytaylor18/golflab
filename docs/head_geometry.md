# Parametric Head Geometry v1 — Concept Brief

**Status:** Step 2, Phase 1 (concept only). **No code has been written against this.**
**Scope:** a handful of design parameters → mass, centre of gravity and full inertia tensor of a
clubhead → `HeadMassProperties` → the impact model and forgiveness map, with no CAD required.
**Companions:** [`impact_model.md`](impact_model.md) (what consumes the output),
[`impact_architecture.md`](impact_architecture.md) §1 (the frame the output must be in).
**Out of scope for v1:** importing real CAD geometry (though §4 builds the tool that will do it),
non-uniform shell thickness beyond a crown/sole split, hosel geometry, internal ribs and
badges, face curvature (the impact model is flat-faced anyway), material databases.

Source labels as in `impact_model.md` §0: ✅ Verified · 📐 Derived · ⚠️ Estimate · 🧪 Tested.

---

## 1. The problem this solves

Step 1 built the engine of the design-to-outcome chain: mass properties in, launch conditions
and a forgiveness map out. Its input side is empty. There is no CAD model, `clubs.json` is
empty, and every figure so far is of `fixture_symmetric_head`, a synthetic head with invented
round numbers.

The engine needs three things about a head — mass, CG position, and the 3×3 inertia tensor
about the CG — and a tensor is an integral of mass × distance² over an actual shape. It cannot
be looked up, and under standing rule 4 it cannot be invented.

This step makes the shape a **design input**: a designer specifies an idealised head with a
few dimensions and a mass budget, and the tensor is *derived* from that. Nothing is invented;
what is estimated is the idealisation, and it is labelled as such. Later, real CAD geometry can
replace the idealised shape without changing anything downstream — and §4 builds the one piece
of machinery both need.

**Standing-rule framing.** A head defined by dimensions *you* choose is your design, named
`design_*`, and never presented as a product. Its mass properties are 📐 derived from stated
inputs; the shape itself is ⚠️ an estimate of a real driver's, and §8 says how good.

---

## 2. The one idea: superposition

**The intuition.** A clubhead is an assembly — a thin body shell, a thicker face, a hosel, a
couple of tungsten weights. Mass properties of an assembly are just the sum of the parts',
provided every part's tensor is expressed about the *same* point. Each part is simple enough
to handle on its own; the assembly is bookkeeping.

**The notation.** For parts with mass `mᵢ`, CG position `rᵢ`, and tensor `Iᵢ` about their own
CG:

```
M   = Σ mᵢ
r_cg = (Σ mᵢ rᵢ) / M                                         first moments add
I_cg = Σ [ Iᵢ + mᵢ ( |dᵢ|² 𝟙 − dᵢ dᵢᵀ ) ],   dᵢ = rᵢ − r_cg      parallel-axis theorem
```

> 📐 The parallel-axis term is the same `M·d²` that the Fusion checklist warned about
> ("at centre of mass", not "at origin") — here it is used deliberately, once per part, and
> it is what a test will check by assembling the same head about two different reference
> points and demanding the same answer.

That is the whole method. Everything else is deciding what the parts are and how to get each
one's own tensor.

---

## 3. The idealised head

```
   PLAN — looking down (crown toward you)                 FACE-ON — from the target

                    back                                        crown
            ╭───────────────╮                              ╭───────────╮
          ╱   ●W          W●  ╲   ← rear weights         ╱  ╭───────╮  ╲
         │         ◆ CG        │                        │   │ face  │   │  ← face plate:
   heel  │  H                  │  toe            heel   │   │ plate │   │    ellipse of
          ╲                   ╱                          ╲  ╰───────╯  ╱     intersection
     ╌╌╌╌╌╌╲╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╱╌╌╌╌╌  face plane z = z_f     ╰───────────╯
          ⊕ face centre = head-frame origin                     sole
                    ↓ +z (outward normal)

   ●W weight (point mass)   H hosel (point mass)   ◆ assembled CG   ⊕ origin
```

| Part | Idealised as | Tensor from | Designer specifies |
|---|---|---|---|
| **Body shell** | thin ellipsoidal shell, semi-axes `a` (heel–toe), `b` (sole–crown), `c` (face–back), **truncated** at the face plane | numerical surface integration (§4) | `a, b, c`, shell mass (or crown + sole masses), face-plane position |
| **Face plate** | thin flat elliptical plate filling the truncation opening | closed form (§4) | face mass (thickness optional) |
| **Hosel** | point mass | parallel axis only | mass, position |
| **Weights** | point masses (0 … n of them) | parallel axis only | mass, position each |

**Why an ellipsoid.** A driver is not one, but it is far closer to one than to a box, its
principal directions line up with the head frame by construction, its volume is closed-form,
and its face-plane intersection is an ellipse — which is exactly the outline `FaceGeometry`
already uses. The 27 % box-vs-ellipse area difference from Step 1 is the same argument again.

**Why the truncation is not optional.** The face is not a tangent point; it is a plane cutting
the ellipsoid where it is still wide. For driver-like proportions (120 × 64 × 110 mm, face
100 mm wide) the plane sits 30 mm in front of the centre, and the shell surface in front of it
— the part the face plate replaces — is **21 % of the total** (20.7 % by exact quadrature;
🧪 tested). Modelling "complete ellipsoid plus a plate" would double-count a fifth of the
body. So the shell must be clipped, and once clipped it has no closed-form tensor. That
decides §4.

> 🔧 **Corrected in Phase 3.** This brief originally said 29 %. The Monte Carlo pre-check it
> came from sampled θ with density ∝ sin θ and then divided by sin θ again, so it weighted the
> region near the front pole — the cap — too heavily. The integrator and an independent
> Gauss–Legendre quadrature agree on 20.7 %. The conclusion is unchanged; the number was not.

**Why masses, not thicknesses.** The designer states a mass budget per part (shell 140 g,
face 30 g, hosel 12 g, weights 2 × 9 g …) rather than thickness × density. Two reasons:
the total is then a directly checkable number against the ~200 g a driver head weighs; and it
needs **no material density constants**, which standing rule 3 would otherwise require to be
sourced. A thickness can be *reported* if the designer optionally supplies a density with a
citation, but it is never needed.

---

## 4. Computing each part

### 4.1 The shell — a mesh mass-property integrator

Parametrise the ellipsoid surface, tessellate it into triangles, discard triangles in front of
the face plane, and treat each remaining triangle as a flat lamina of area `Aₖ` carrying mass
`σ Aₖ`, where `σ = m_shell / A_total` is the uniform surface density. Then sum the lamina
contributions — mass, first moment, and second moment about the origin — and shift to the
assembly CG with the parallel-axis theorem.

This is not an approximation in the sense that matters: a thin shell *is* a surface with mass
per unit area, and the tessellation error falls as the mesh is refined. 🧪 Convergence is
testable, and so is exactness, because two limits **do** have closed forms:

> 📐 **Thin spherical shell**, radius `R`: `I = (2/3) m R²` about any axis.
> 📐 **Solid ellipsoid**, semi-axes `a, b, c`: `Iₓₓ = m (b² + c²)/5`, and cyclically.

> 🔧 **Corrected in Phase 3.** An earlier draft added that a thin ellipsoidal shell is
> "outer minus inner" concentric solid ellipsoids in the thin limit. It is not: that limit is
> a shell whose *thickness varies* around the surface, not one of uniform mass per unit area,
> and a uniform ellipsoidal shell has no elementary closed form at all (its area involves
> elliptic integrals). The oracle for the ellipsoid — clipped or not — is therefore an
> **independent Gauss–Legendre quadrature** of the exact surface, accurate to ~1e-10, against
> which the tessellation agrees to 1e-4. The sphere and the solid ellipsoid remain the exact
> closed-form checks.

The integrator must reproduce the closed forms to well under 0.1 % and the quadrature to
1e-3 on a moderate mesh before it is trusted on anything it cannot be checked against.

**The same integrator, run in "solid" mode, is a CAD importer.** For a closed triangle mesh
bounding a *volume* (an STL export from Fusion), the divergence theorem turns the volume
integrals for mass, CG and tensor into sums over the same triangles. So the tool built here is
the tool that reads a real head later — the parametric shell and the Fusion import share one
integrator with two modes, and the parametric head becomes the test fixture for the importer.
That is the strongest argument for doing this step numerically rather than hunting for
closed forms.

### 4.2 The face plate — closed form

A thin elliptical plate with semi-axes `a_f` (heel–toe) and `b_f` (sole–crown), mass `m_f`,
about its centroid:

> 📐 `Iₓₓ = m_f b_f²/4`, `I_yy = m_f a_f²/4`, `I_zz = m_f (a_f² + b_f²)/4`

The semi-axes are **derived, not specified**: the plane `z = z_f` cuts the ellipsoid in the
ellipse with `a_f = a √(1 − (z_f/c)²)` and `b_f = b √(1 − (z_f/c)²)`, centred on the axis. So
the designer can equivalently state the face *width* and the model solves for `z_f`. The face
plate's centroid is the head-frame origin, which is what makes the frame fall out cleanly
(§5).

### 4.3 Hosel and weights — point masses

No own tensor; parallel axis only. A hosel as a point mass is crude (§9), but its mass is
small and its position is what matters — it sits high on the heel and pulls the CG that way,
which is a real and visible effect on the sweet-spot position.

### 4.4 Crown/sole split (recommended for v1, as an option)

Real design leans hard on a light carbon crown and a heavy sole. The shell integrator handles
this for free: split the surface at `y = 0` and give the two halves different surface
densities from two stated masses. Nothing else changes. This is worth having from the start
because "lighten the crown" is the single most common modern design move, and its effect on
CG height and the vertical gear effect is exactly the kind of thing the map should show.

---

## 5. The frame, and what the output looks like

The ellipsoid is naturally described about its own centre, but the impact model wants the
**head frame**: origin at the geometric face centre, `x` toward the heel, `y` toward the
crown, `z` along the outward normal (`impact_architecture.md` §1.1, as corrected).

Because the face plane is perpendicular to `z` and its intersection ellipse is centred on the
axis, the head-frame origin is simply `(0, 0, z_f)` in ellipsoid coordinates and the axes are
already parallel. The transform is a translation by `z_f` and nothing else — no rotation, no
handedness question. The CG lands at negative `z` automatically, which `HeadMassProperties`
requires.

**Output:** a validated `HeadMassProperties` — so the triangle inequality, positive-definiteness
and CG-behind-face checks all apply to the *derived* tensor, which is a useful sanity net on
the integrator — plus:

- a **breakdown**: each part's share of `Iₓₓ`, `I_yy`, of the CG position, of the mass. This is
  the design insight the numbers alone hide ("the two 9 g weights are 31 % of `I_yy`").
- the **conformance trio** against the Equipment Rules (§6): volume, dimensions, MOI.
- the face outline as a `FaceGeometry` with its source marked. `outline_is_measured` is a
  boolean and this outline is neither *assumed* nor *measured* — it is *designed*. Phase 2
  should replace the flag with `outline_source: assumed | design | measured` so a map can say
  which.

---

## 6. Design bounds from the Equipment Rules

A parametric designer should know the box it is designing inside. ✅ All from Part 2 §4b(i),
which applies to woodheads; page numbers are the PDF's.

| Constraint | Limit | Where |
|---|---|---|
| Heel-to-toe length | ≤ 5 in (127 mm), measured at 60° lie | p.51 |
| Sole-to-crown height | ≤ 2.8 in (71.12 mm), including permitted features | p.51 |
| Proportion | heel-to-toe must exceed face-to-back | p.51 |
| Volume | ≤ 460 cm³ (28.06 in³), + 10 cm³ tolerance | p.52 |
| MOI about the vertical axis at 60° lie, about the CG | ≤ 5900 g·cm², + 100 tolerance | p.54; MOI protocol p.3 |

The model reports all five as a **report, not a rejection** — GolfLab is a design tool and
"how much would a non-conforming head gain?" is a legitimate question, exactly as Step 1
decided for MOI. The ellipsoid's bounding box is `2a × 2b × 2c` (so the proportion rule reads
`a > c`), and its volume is `(4/3) π a b c` minus the truncated cap, for which a closed form
exists and which the integrator also gives numerically — a small extra cross-check for free.

---

## 7. Pre-check: does the idealisation land in the right place?

Computed while writing this brief, with the closed-form untruncated shell (so *indicative*,
not the v1 method):

| Design | `Iₓₓ` | `I_yy` | `I_zz` | Rules-frame MOI | Volume |
|---|---|---|---|---|---|
| 120 × 64 × 110 mm shell, all 200 g in the shell, no weights | 2614 | 3968 | 2902 | **3629** | 442 cc |
| same, 160 g shell + 2 × 20 g weights at the rear heel/toe corners | 2941 | 4624 | 3001 | **4203** | 442 cc |

All in g·cm². Two things to take from it:

1. **The order of magnitude is right without tuning.** A plain shell at driver dimensions
   lands in the low thousands, under the 5900 ceiling — where a mid-forgiveness driver sits.
   Moving 40 g to the rear corners adds ~16 % to `I_yy` and pulls the CG 9 mm back, which is
   the size of effect real weight ports produce. If the idealisation were badly wrong, these
   numbers would be off by a factor, not a fraction.
2. **`I_yy > Iₓₓ`, as it should be** for a head wider than it is tall. The map's toe–heel
   fall-off will be gentler than its high–low fall-off, matching the Step 1 fixture's shape and
   the geometry of every real driver.

Neither table row is a design recommendation, and neither is a real product.

---

## 8. What is derived, what is estimated, and how good it is

**📐 Derived from stated inputs:** the tensor, CG, volume, face outline, breakdown. Given the
idealised shape, these are exact to mesh convergence, and the tests in §10 pin that.

**⚠️ Estimated — the shape.** A real driver is fuller behind the face, flatter on the sole,
and not symmetric about the heel–toe plane; its shell thickness varies; its hosel is a tube.
The ellipsoid gets the mass in roughly the right places, which is what the tensor is
sensitive to, but *how* good it is cannot be stated from this brief. Honest expectation:
**trends right, ratios close, absolute values within a band that only validation can
narrow.** Three cross-checks are available and Step 2 Phase 5 should use all it can:

- the Rules' MOI ceiling and the volume limit — a band, not a value, but a hard one;
- a **published MOI figure for a real driver**, cited, used purely as a comparison against a
  design set to that head's outer dimensions and mass — never as an input;
- a **measured head** via the bifilar-pendulum route, if one is available. This is the check
  that would actually put a number on the idealisation error.

**What the estimate does *not* affect:** the impact model's physics, which is unchanged; and
relative comparisons between two designs, where the idealisation error largely cancels — the
same argument as Step 1's validity table. A designer asking "does moving this weight help?"
gets a trustworthy answer sooner than one asking "what is my exact MOI?"

---

## 9. Limitations (v1)

1. **Ellipsoidal shell.** The shape is the estimate. See §8.
2. **Uniform thickness** within each shell region (whole, or crown/sole halves).
3. **Flat face plate**, which is also what the impact model assumes. Face curvature is a Step 3
   problem on both sides.
4. **Point-mass hosel.** Its inertia about its own axis is ignored; its position is kept.
5. **No internal structure** — ribs, sound plates, adhesive, paint. The mass budget absorbs
   them if the designer wants; the model does not place them.
6. **No density constants** unless the designer supplies one with a citation. This is a
   feature under rule 3, but it means "make the crown 0.6 mm carbon" cannot be expressed
   directly — it is expressed as a crown mass.

---

## 10. Validation plan

Each is a test in Phase 3, with the physical claim it proves.

| Test | Proves |
|---|---|
| Integrator vs `(2/3) m R²` on a sphere, and vs `m (b²+c²)/5` on a solid ellipsoid | the lamina/divergence machinery is right, to < 0.1 % |
| Refining the mesh converges monotonically | the number is a property of the shape, not of the tessellation |
| Assemble the same head about two different reference points → identical tensor | the parallel-axis bookkeeping is right |
| Symmetric design → CG on the centreline, zero products of inertia, sweet spot exactly at the face centre | no hidden asymmetry; connects to Step 1's symmetry test |
| Truncated vs untruncated shell differ by the cap's share (≈ 21 % of area for the §7 proportions) | the clipping is doing what §3 says it must |
| Rear weight → deeper CG, larger `Iₓₓ` and `I_yy`; heel/toe weights → `I_yy` rises more than `Iₓₓ`; lighter crown → lower CG | the design levers move the right way |
| Output passes `HeadMassProperties` validation | the derived tensor is physically possible, every time |
| Volume, dimensions and MOI conformance reported against the cited limits | the design box is visible |
| The §7 numbers are reproduced by the numerical method to within the cap correction | the closed-form pre-check and the integrator agree where they should |

---

## 11. Where it lands (sketch — Phase 2 decides)

Flat, one responsibility per file, matching the repo:

| File | Responsibility |
|---|---|
| `mesh_mass_properties.py` | the integrator: thin-surface mode (shells) and solid mode (closed meshes). **Reused by a later STL import.** |
| `head_geometry.py` | `HeadDesign` (the parameters) → `HeadMassProperties` + breakdown + conformance trio |
| `head_design_repository.py` | persistence, mirroring `head_repository.py` |
| tests for each | |

Then wire in: a CLI option ("design a head parametrically") feeding the existing forgiveness
map; a web panel with the design parameters replacing the raw tensor form, with the tensor
form kept for measured/CAD heads. The map is unchanged — it just finally has a real input.

---

## 12. Decisions for Finley before Phase 2

1. **Crown/sole split in v1?** Recommended yes (§4.4) — it is nearly free and it is the design
   lever people actually pull. Say no and v1 is a single shell mass.
2. **Default design dimensions.** The §7 numbers are round. A first `design_v1` wants real
   dimensions — a ruler on any driver gives length, height and depth in a minute, and those
   are dimensions, not product data. Or choose them as design intent.
3. **Weights.** How many, and roughly where — rear-corner ports, a sole slider, a single back
   weight? This shapes the parameter schema more than anything else.
4. **Mass budget or thickness?** This brief argues for masses (§3). If you would rather think
   in thicknesses, the densities need sourcing first, and that is a small research task.

---

## 13. Phases for Step 2

Mirroring Step 1: **1** this brief → **2** architecture (parameter schema, integrator
interface, the `outline_source` change) → **3** implement + tests → **4** wire into CLI, map
and web panel → **5** validate against the Rules band, a cited published MOI, and a measured
head if one exists. Gate at each.
