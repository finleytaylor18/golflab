# Parametric Head Geometry v1 — Model Report

**Status:** Step 2, Phase 5 — implemented, tested, validated as far as the sources allow.
**Scope:** seven design numbers, a hosel and a list of weights → mass, centre of gravity and full
inertia tensor → `HeadMassProperties` → the impact model and forgiveness map. No CAD required.
**Companions:** [`head_geometry_architecture.md`](head_geometry_architecture.md) (how it is built),
[`impact_model.md`](impact_model.md) (what consumes the output). Tests:
`test_mesh_mass_properties.py`, `test_head_geometry.py`, `test_head_geometry_validation.py`.
**Out of scope for v1:** importing real CAD geometry (though the integrator's solid mode is
built for it), non-uniform shell thickness beyond the crown/sole split, hosel geometry,
internal structure, face curvature, material databases.

Source labels as in `impact_model.md` §0: ✅ Verified · 📐 Derived · ⚠️ Estimate · 🧪 Tested.

---

## 1. Why it exists

Step 1 built the engine of the design-to-outcome chain and left its input side empty: no CAD
model exists, and every figure was of a synthetic fixture with invented round numbers. The
engine needs a head's mass, CG and 3×3 inertia tensor, and a tensor is an integral over an
actual shape — it cannot be looked up, and under standing rule 4 it cannot be invented.

This step makes the shape a **design input**. A head defined by dimensions *you* choose is
your design, named `design_*`, never presented as a product; its mass properties are
📐 derived from the stated inputs; the idealised shape is ⚠️ an estimate of a real driver's,
and §4 puts a number on how much that estimate can matter.

---

## 2. The model

### 2.1 One idea: superposition

An assembly's mass properties are the sum of its parts', once every part's tensor is shifted
to a common point. For parts with mass `mᵢ`, CG `rᵢ` and tensor `Iᵢ` about their own CG:

```
M    = Σ mᵢ
r_cg = (Σ mᵢ rᵢ) / M
I_cg = Σ [ Iᵢ + mᵢ ( |dᵢ|² 𝟙 − dᵢ dᵢᵀ ) ],   dᵢ = rᵢ − r_cg        (parallel-axis theorem)
```

🧪 Translating every part by the same offset leaves `I_cg` unchanged to 1e-12. The per-part
terms are reported as a **breakdown**; they are a true partition (shares sum to one, CG pulls
sum to zero), 🧪 tested.

### 2.2 The parts

| Part | Idealised as | Tensor from | Designer states |
|---|---|---|---|
| Body shell | thin ellipsoidal shell, semi-axes `a` (heel–toe), `b` (sole–crown), `c` (face–back), **truncated** at the face plane, split into crown and sole halves | numerical surface integration (§2.3) | `a, b, c`, crown mass, sole mass, face width |
| Face plate | thin flat ellipse filling the truncation opening | 📐 `m/4 · (b_f², a_f², a_f² + b_f²)` | face mass |
| Hosel, weights | point masses | parallel axis only | mass and position, in the designer's words (toe / crown / back) |

**Masses, not thicknesses.** The total is checkable against the ~200 g a driver head weighs,
and no material density has to be sourced. **Everything in one frame** — the head frame of
`impact_architecture.md` §1.1 — with the ellipsoid centre a *derived* point `(0, 0, −z_f)`.

**Derived, never typed:** `z_f = c √(1 − (w/2a)²)`; face outline semi-axes
`a_f = w/2`, `b_f = b √(1 − (z_f/c)²)`; face-to-back `z_f + c`; truncated volume
`(4/3)π a b c − π a b (2c/3 − z_f + z_f³/3c²)` — 📐 the cap term verified against Monte Carlo
to 0.02 % and exact at both endpoints.

### 2.3 The shell — a mesh integrator with two modes

The ellipsoid is parametrised `x = a sinθ cosφ, y = b sinθ sinφ, z = c cosθ` and tessellated.
Two things are **exact by construction**: the face plane `z = z_f` is the grid line
`θ = arccos(z_f/c)`, so clipping introduces no error; and with an even `n_φ`, `y = 0` is a grid
line, so every triangle lies wholly in the crown or the sole. Each triangle is a flat lamina
with the exact second moment

> 📐 `S = (m/12) [ p₁p₁ᵀ + p₂p₂ᵀ + p₃p₃ᵀ + (p₁+p₂+p₃)(p₁+p₂+p₃)ᵀ ]`,  `I = tr(S)·𝟙 − S`

so the only approximation is the tessellation of a smooth surface, and 🧪 that converges at
second order. **Solid mode** (signed tetrahedra, divergence theorem) is built alongside with
its oracle tests and watertightness guard: it is the future STL importer, and the parametric
shell is its test fixture. One integrator, two callers.

**Why the truncation is mandatory.** For driver proportions with a 100 mm face, the shell
surface in front of the face plane is **20.7 %** of the whole (🧪 by exact quadrature). A
"complete ellipsoid plus a plate" would double-count a fifth of the body.

> 🔧 Two corrections made during implementation, recorded rather than edited away: the concept
> brief first said 29 % (a Monte Carlo pre-check applied `sin θ` twice), and claimed a uniform
> ellipsoidal shell is the thin limit of outer-minus-inner solid ellipsoids (that limit has
> non-uniform thickness). The oracle for the ellipsoid is therefore an independent
> Gauss–Legendre quadrature, not a closed form.

---

## 3. Sources and constants

The model needs **no physical constants**: masses are inputs, and the shape is geometry. The
Equipment Rules supply the design box, all ✅ from Part 2 §4b(i) (page numbers are the PDF's):

| Constraint | Limit | Page |
|---|---|---|
| Heel-to-toe length, at 60° lie | ≤ 5 in (127 mm) | 51 |
| Sole-to-crown height | ≤ 2.8 in (71.12 mm) | 51 |
| Proportion | heel-to-toe > face-to-back (`2a > z_f + c`) | 51 |
| Volume | ≤ 460 cm³ + 10 cm³ tolerance | 52 |
| MOI about the vertical at 60° lie, about the CG | ≤ 5900 + 100 g·cm² | 54; MOI protocol p.3 |

All five are **reported, never enforced** — a non-conforming design is a legitimate thing to
want to model. The volume the Rules measure is by water displacement (p.53); ours is the
geometric volume of the idealised shape, which is the same quantity for a closed shell.

---

## 4. Assumptions and validity range

**Assumptions (v1).** 1. Thin ellipsoidal body shell, truncated flat at the face. 2. Uniform
mass per unit area within each of the crown and sole halves. 3. Flat elliptical face plate.
4. Hosel and weights are point masses. 5. No internal structure; the mass budget absorbs it.
6. Everything is rigid and the frame is the head frame.

**How large is the shape assumption?** Nobody has measured a real head against this model
yet, so the honest way to bound the error is to bracket it: the same shell mass in the same
outer box as a **thin rectangular box** (closed form, six plates) is the opposite extreme — all
mass at the extremities — and a real driver lies between the two.

| | Ellipsoidal shell (ours) | Box shell | Ratio |
|---|---|---|---|
| Shell alone (130 g, 120 × 64 × 85 mm) `Iₓₓ, I_yy, I_zz` | 1308, 2314, 2114 | 2141, 3598, 3121 | **1.64, 1.55, 1.48** |
| Assembled head (200 g, all parts) | 2134, 3868, 3113 | 2967, 5152, 4121 | **1.39, 1.33, 1.32** |
| Rules-frame MOI, assembled | 3543 | ~4606 | 1.30 |

All g·cm², 🧪 tested. So: **the shape assumption is worth up to ~30 % on the assembled
tensor**, and less on ratios and trends. That is the validity statement.

| Trust it for | Do not trust it for |
|---|---|
| **Comparisons between designs** — move a weight, lighten the crown, widen the head: the idealisation error largely cancels | **absolute MOI to better than ~±30 %** until a measured or CAD head narrows the bracket |
| **Trends and their direction** (§5 F) — every lever moves the right way, 🧪 | the exact conformance margin of a real product — this is a design tool, not a conformance lab |
| **Order of magnitude** — a plain shell lands in the low thousands of g·cm² with no tuning | heads far from ellipsoidal (a square-back "triangular" driver sits nearer the box end) |
| **Which part owns the MOI** — the breakdown is a true partition | the hosel's own inertia (a point mass), or anything internal |

---

## 5. Validation results

Every number below is asserted in `test_head_geometry_validation.py`.

**What could not be validated, and why.** No source read for this project states a real
driver's absolute moment of inertia: Penner (2003) treats MOI qualitatively (p.166), the
Equipment Rules give only the ceiling, the MOI protocol gives no example values. Per standing
rule 3, **no published absolute MOI is cited or asserted**, and no marketing figure is
repeated from memory. The one check that would put a number on the idealisation error — a
measured head via the bifilar pendulum — has not been done, because no head is available.

| # | Check | Result | Verdict |
|---|---|---|---|
| A | Placeholder `design_v1` against all five Rules limits | conforms; Rules-frame MOI **3543 g·cm²**, 386 cc | in band, untuned |
| B | Idealisation bracket, ellipsoid vs box shell | ×1.5–1.65 on the shell, **×1.33** on the assembled `I_yy` | the error bar, stated |
| C | Iwatsubo et al (2000) via Penner p.166: +19 % vertical MOI → sidespin ratio **0.74** on a 10 mm toe strike | +19 % `I_yy` by growing the shell at 200 g → ratio **0.915** (Step 1's fixture: 0.845) | direction right; **further from 0.74 than the fixture** |
| D | Does the Rules' MOI ceiling bind? | growing the shell to 126 × 70 mm reaches ~4770 g·cm² — but 499 cc, **over the volume limit first** | reproduces the real squeeze |
| E | Step 1's engine on a designed head (hosel, offset CG, non-zero products) | linear momentum conserved to 1e-9; energy falls | the two steps agree |
| F | Sensitivity, +10 % per input | half-width → `I_yy` **+10.6 %**; height → +1 %; wider face → `I_yy` −3.6 %, `Iₓₓ` −7.7 %, CG **2.8 mm shallower** | levers ranked |

**On C, honestly.** Two things make the designed-head ratio weaker than the fixture's. Scaling
the fixture's tensor changed *only* the tensor; growing a real shell also moves the CG deeper —
the gear-effect lever arm — and hands back part of what the extra MOI took away. **MOI alone
does not set gear effect; CG depth rises with it.** And the +19 % head is 137 mm and ~500 cc,
non-conforming on both counts — it is a physics comparison, not a design. The remaining gap
to 0.74 is Step 1's flat face, exactly as `impact_model.md` §5 records.

**On D.** At 200 g, a designer cannot reach high MOI inside the Rules by making the head
bigger — volume runs out before MOI does. It has to come from **perimeter mass**, which is
precisely the modern driver recipe, and exactly why the Rules carry both limits.

**On F.** A designer who wants heel–toe forgiveness *widens the head*, not the face: a wider
face cuts more shell off the front and lowers every moment. Height barely touches `I_yy`.

---

## 6. Limitations

1. **The ellipsoid** — up to ~30 % on the assembled tensor (§4). The largest.
2. **Uniform thickness** within each shell half. A real crown thins toward the middle.
3. **Point-mass hosel.** Its position is right; its own inertia is dropped.
4. **Flat face plate**, consistent with Step 1's flat-face impact model — and the map now shows
   the consequence more clearly on a designed head than on the fixture: with a lower CG and a
   53 mm-tall face, the topspin region at the crown edge is larger. Real roll would prevent it.
   **Bulge and roll are the next physics to add, on both sides of the chain.**
5. **No densities** unless supplied with a citation — "0.6 mm carbon" is expressed as a crown
   mass.

**Logged for later:** a measured head (bifilar pendulum) is the only check that turns the
§4 bracket into a number; the integrator's solid mode is ready for an STL export the moment a
CAD head exists.

---

## 7. References

| Reference | Read? | Cited |
|---|---|---|
| R&A/USGA **Equipment Rules** (2020 v2), Part 2 §4b(i) | ✅ | pp. 51, 52, 53, 54 |
| R&A/USGA **MOI Protocol** | ✅ | p. 3 |
| Penner, "The physics of golf", *Rep. Prog. Phys.* **66**, 131–171 (2003) | ✅ | p. 166 (Iwatsubo et al 2000, as Penner reports it) |

Closed forms used as oracles — thin spherical shell `(2/3) m R²`, solid ellipsoid
`m (b² + c²)/5`, thin plate `m/12 (q², p², p² + q²)`, tetrahedron and triangle second-moment
formulas — are standard results of rigid-body mechanics, each 🧪 verified numerically in
`test_mesh_mass_properties.py` rather than cited from a text I have not read.
