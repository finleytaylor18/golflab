# Impact Model v1 — Architecture Proposal

**Status:** Phase 2 (proposal only). **No code has been written.** Every code block below is an
illustrative sketch of a proposed interface, not an implementation.

Physics, derivations and sourced constants live in [`impact_model.md`](impact_model.md).
This document covers only *how the thing is built*: frame, data model, validation,
formulation, provenance and file layout.

**Ball choice (decided):** three-piece tour ball. This fixes `μ` and `e` — see §5.2.

---

## 1. Coordinate frame

### 1.1 Recommendation

One head-fixed, right-handed frame. **Origin at the geometric centre of the face.**

| Axis | Direction | Positive toward |
|---|---|---|
| `x̂` | across the face | **heel** (toe → heel) |
| `ŷ` | up the face | **crown** (sole → crown) |
| `ẑ` | face normal | **outward**, away from the face (toward ball / target) |

✅ Verified right-handed: `x̂ × ŷ = ẑ`.

> 🔧 **Corrected in Phase 3.** This table originally read `x̂ → toe`, and claimed
> right-handedness on the strength of the abstract identity `x̂ × ŷ = ẑ`. That identity is
> true of *any* right-handed frame by definition, so it proved nothing about whether these
> three **physical** directions form one. They do not. For a right-handed club, with the
> crown up and the face normal down the target line, the toe lies on the opposite side from
> the golfer, and `toe × crown = −outward`: the triad **(toe, crown, outward) is
> left-handed**. Cross products, inertia-tensor rotations and angular momentum all assume a
> right-handed frame, so exactly one axis had to flip.
>
> `x̂` is the one to flip, for two reasons. First, it is the only flip that leaves the **face
> normal** and the **vertical axis** alone — every equation in `impact_model.md` is written
> around those two, and the sole–crown axis carries the strongest physical intuition
> (launch angle, backspin). Second, it is the better choice for **plotting**: drawn with
> `+x` rightward and `+y` upward, a forgiveness map becomes a true face-on view of the club,
> toe on the left — which is how a driver face is photographed and how a launch monitor
> draws its impact pattern.
>
> **Consequence:** a toe strike is `x < 0`, a heel strike `x > 0`. Nothing else in this
> document changes; `d = −cg_z` and the sweet spot `(cg_x, cg_y, 0)` are unaffected.

All conventions are for a **right-handed head**. A left-handed head is the mirror image
(`x̂ → −x̂`), deferred per the Phase 1 scope.

### 1.2 Why origin at the face centre, not the CG

The obvious alternative is to put the origin at the CG, since that is where the inertia
tensor is defined. I recommend against it:

| | Origin at face centre **(recommended)** | Origin at CG |
|---|---|---|
| Strike locations | Natural — a strike *is* an `(x, y)` on the face, `z = 0` | Needs an offset every time |
| CG depth `d` | Falls out directly as `−cg_z` | Must be derived from face-plane position |
| Sweet spot | `(cg_x, cg_y, 0)` — a projection, computed not stored | Also easy |
| Moment arm `b` | `(x − cg_x, y − cg_y, 0)` — a subtraction | Also easy |
| `HeadMassProperties.cg` | Meaningful data | Trivially `(0,0,0)`, so the field is pointless |
| Inertia tensor | Must be labelled "about the CG" explicitly | Implicit |

The deciding argument is the last-but-one row: the brief asks `HeadMassProperties` to carry a
CG position, and that field only carries information if the origin is somewhere else. Face
centre is the most useful "somewhere else", because it makes the two quantities that drive the
whole model — **CG depth** (gear effect) and **moment arm** (effective mass) — direct readouts
of the frame rather than derived quantities.

**Trade-off accepted:** the inertia tensor's reference point (CG) differs from the frame origin
(face centre). That is normal and unambiguous — a tensor is always "about a point, expressed in
some axes" — but it must be named explicitly, so the field is called `inertia_about_cg` and never
just `inertia`. Getting this wrong is a silent, plausible-looking error, so §3 validates it.

### 1.3 Diagram

```
   FACE-ON  —  looking at the face from in front (along −ẑ; ẑ comes out of the page).
                This is the view a launch monitor draws: toe on the left, heel on the right.

                               ŷ  crown
                               ▲
        ╔══════════════════════╪══════════════════════╗
        ║                      │                      ║
        ║          ★ S         │                      ║     ⊕  origin = face centre
        ║           ╲          │                      ║     ★  S = sweet spot
        ║            ╲  b      │                      ║     ●  P = strike point
        ║             ● P      │                      ║     b  = P − S  (moment arm)
    toe ║                      ⊕──────────────────────╫──▶  x̂  heel
        ║                                             ║
        ║                                             ║
        ╚═════════════════════════════════════════════╝
                               sole

        S = (cg_x, cg_y, 0)          the CG projected forward onto the face
        P = (x, y, 0)                any strike location
        b = P − S                    zero only at the sweet spot


   PLAN  —  looking down from above (along −ŷ; ŷ comes out of the page)

         x̂ heel
            ▲
            │
    ┌───────┴────────┐▐
    │                │▐
    │      ◆ CG      │▐ ← face plane, z = 0
    │                │▐
    └────────────────┘▐
                      ⊕─────────────────▶  ẑ   outward face normal
            │         │                        (toward ball / target)
            │←─── d ──┤
                 origin = face centre

        ◆ CG at z = −d          d = CG depth = −cg_z > 0
        Gear effect scales with d; it vanishes as d → 0 (see impact_model.md §4.2)
```

### 1.4 Relationship to the Equipment Rules frame

⚠️ **These are not the same axis, and the difference is easy to miss.** The Rules measure MOI
"about the **vertical** axis of the clubhead orientated at a **60° lie angle**, about the centre
of mass" (MOI protocol, p.3, limit 5900 g·cm²). Our `ŷ` is a *head-fixed* axis; at 60° lie it
sits 30° from the lab vertical.

So the conformance number is **not** `I_yy`. To compare, rotate the head-frame tensor into the
60°-lie orientation and take the component about the lab vertical:

```
I_rules = v̂ᵀ · R I_about_cg Rᵀ · v̂        where v̂ is the lab vertical at 60° lie
```

I propose a small helper for exactly this, because it is the single best sanity check on a
Fusion-exported tensor: it produces a number directly comparable to a published conformance
figure. It is a **check**, not a constraint — see §3.3.

### 1.5 Fusion 360

Fusion's model frame will not match this one. The transform is deliberately **not** built now
(per scope). The contract is simply: *whatever* produces a `HeadMassProperties` must express it
in the frame above, and every position field states its frame in the docstring.

---

## 2. Data model

Following existing repo convention: `@dataclass`, validation in `__post_init__` raising
`ValueError` with a descriptive message, SI internally.

### 2.1 `FaceGeometry`

```python
@dataclass(frozen=True)
class FaceGeometry:
    """Face plane is z = 0 in the head frame; v1 assumes it is flat (no bulge/roll)."""
    half_width_m:  float   # x half-extent, heel↔toe
    half_height_m: float   # y half-extent, sole↔crown
    outline_is_measured: bool = False   # False ⇒ label plots "approximate outline"
```

**Trade-off.** The brief lists face geometry as a field of `HeadMassProperties`. I propose it
as its **own type, composed into** `HeadMassProperties` — same field, separate validation.
A rectangle is deliberately crude; it is enough to bound the Phase 4 sweep, and Phase 4 must
label the outline "approximate" unless `outline_is_measured` is set. A richer outline
(polygon) can replace this without touching the physics, because the solver never looks at the
outline — only the sweep does.

### 2.2 `HeadMassProperties`

```python
@dataclass(frozen=True)
class HeadMassProperties:
    mass_kg:          float
    cg_m:             np.ndarray   # (3,) position of CG, head frame, origin = face centre
    inertia_about_cg: np.ndarray   # (3,3) kg·m², about the CG, in head-frame AXES
    face:             FaceGeometry

    @property
    def cg_depth_m(self) -> float:      # = -cg_m[2], positive
    @property
    def sweet_spot_m(self) -> np.ndarray:   # = (cg_x, cg_y, 0)
```

Per the brief, the **full 3×3 tensor is stored even though v1 uses only part of it**. Real heads
have non-zero products of inertia (principal axes are not aligned with the face), and storing
the full tensor means a later step needs no migration.

### 2.3 `BallProperties`

```python
@dataclass(frozen=True)
class BallProperties:
    mass_kg:      SourcedConstant
    radius_m:     SourcedConstant
    inertia_kg_m2: SourcedConstant   # ⚠️ uniform-sphere estimate, α = 2/5
    cor:          SourcedConstant    # paired with the speed it was measured at
    friction:     SourcedConstant    # paired with ball construction + tangential speed
```

Constants carry their own provenance (§5), so a later feature can display "where did 0.38 come
from?" without a lookup table.

### 2.4 `ImpactConditions`

```python
@dataclass(frozen=True)
class ImpactConditions:
    cg_speed_mps:       float   # ← see below: velocity OF THE CG
    delivered_loft_rad: float
    strike_m:           np.ndarray   # (2,) (x, y) on the face plane, head frame
```

⚠️ **"Clubhead speed" is ambiguous, so the field is not called that.** The speed of the CG, of
the sweet spot, and of the strike point all differ the moment the head has any angular velocity.
I recommend **the velocity of the CG**, because:

1. It is what the linear-momentum equation consumes directly (`M v_cg`), with no conversion.
2. It stays well-defined when pre-impact rotation is added later; a face-point velocity does not,
   without also specifying *which* point.

**Trade-off / caveat to document:** a launch monitor's reported "clubhead speed" is a tracked
point near the face centre, not the CG. In v1 these coincide exactly (zero pre-impact head
rotation, assumption 2 in `impact_model.md` §8). The moment that assumption is relaxed they
diverge, and the field name will already be honest about which one we mean.

v1 takes the CG velocity as **horizontal** (zero attack angle) with `delivered_loft` giving the
face orientation relative to it. Adding attack angle later is a rotation of the velocity vector
in the vertical plane and touches nothing else.

### 2.5 `ImpactResult`

```python
@dataclass(frozen=True)
class ImpactResult:
    ball_speed_mps:        float
    smash_factor:          float
    launch_vertical_rad:   float
    launch_horizontal_rad: float
    backspin_rad_s:        float
    sidespin_rad_s:        float
    spin_axis_tilt_rad:    float
    head_velocity_after:   np.ndarray   # (3,)
    head_omega_after:      np.ndarray   # (3,)
    required_friction:     float        # |J_t| / J_n the no-slip solution demanded
    slip_regime:           str          # "rolling" | "sliding"
```

`required_friction` and `slip_regime` are the important pair. They are what lets Phase 4 flag
grid points where the no-slip solution needed more friction than the sourced `μ` allows — i.e.
where the model is extrapolating past its own validity. Reporting the *demand* rather than only
the outcome means the map can show **how far** past the limit a region is, not just that it is.

Returning post-impact head velocity and angular velocity costs nothing and makes the momentum-
and energy-conservation tests in Phase 3 possible at all.

---

## 3. Boundary validation

Validation lives in `__post_init__`, consistent with `ClubSpecification` and `SwingProfile`.

### 3.1 Required (raise `ValueError`)

| Check | Why |
|---|---|
| `mass_kg > 0` | trivially unphysical otherwise |
| `radius_m > 0`, `0 ≤ cor ≤ 1`, `friction ≥ 0` | ditto |
| Inertia tensor is **symmetric** (within tolerance) | a real inertia tensor always is; asymmetry means a transcription or transpose error |
| Inertia tensor is **positive-definite** | all eigenvalues > 0; catches sign errors and garbage |
| Principal moments satisfy the **triangle inequality** `I₁ + I₂ ≥ I₃` | the brief's key catch — see below |
| `cg_z < 0` | the CG must lie *behind* the face plane. A positive value means a sign convention was mixed up |
| Face half-extents > 0 | degenerate outline breaks the sweep |

**The triangle inequality is the valuable one.** For any real rigid body the principal moments
obey `I₁ + I₂ ≥ I₃` (each is an integral of mass × squared distance, so no one moment can exceed
the sum of the other two). A tensor can be symmetric *and* positive-definite and still be
physically impossible — which is exactly the failure mode of a mis-transcribed or wrongly-united
Fusion export. This check costs three eigenvalues and catches a class of error that would
otherwise produce plausible-looking but meaningless forgiveness maps.

**Tolerances.** Symmetry and the triangle inequality need a relative tolerance, not exact
equality — floating point and Fusion's own rounding both bite. Proposal: `rtol=1e-9` for
symmetry, and a small relative slack on the triangle inequality so a body that is legitimately
*on* the boundary (a flat plate, where `I₁ + I₂ = I₃`) is not rejected.

### 3.2 Units are the most likely real error

A `g·cm²` value passed where `kg·m²` is expected is wrong by **10⁷** and will pass every check
above. The mitigations are structural, not validation: SI-only field names carry their unit
(`inertia_about_cg` is documented kg·m²; the boundary converter in §6 is the only sanctioned way
in), plus the §3.3 warning below, which *would* catch a 10⁷ error immediately.

### 3.3 Warn, do not reject: conformance

The Rules' 5900 g·cm² MOI ceiling is **not** a validation error. This is a design and R&D tool —
modelling a non-conforming head is a legitimate thing to want to do, and refusing to is the tool
getting in the designer's way. Proposal: expose a `conformance_report()` returning the
rules-frame MOI (§1.4) alongside the limit, and let the caller decide. Phase 4 can annotate the
map. A value wildly outside the band is also the fastest way to notice a unit error.

---

## 4. Model formulation

### 4.1 Recommendation: implement in 3D, explain and test in 2D

I agree with the brief's recommendation, and I have already checked the load-bearing claim.

**Why 3D rather than two planar models.** A real strike is off-centre in *both* axes at once —
high-toe, low-heel. That is the entire subject of a forgiveness map. Two independent planar
models cannot represent it, because the two rotations couple through the inertia tensor's
off-diagonal terms. Since the map is the deliverable, the 3D model is not gold-plating; it is
the minimum that answers the question.

**Cost is genuinely low.** With numpy the 3D solution is a 3×3 solve. The formulation:

```
K = (1/M)·1 − [r]ₓ I⁻¹ [r]ₓ          "inverse inertia matrix" at the contact point
```

where `[r]ₓ` is the skew-symmetric cross-product matrix of the contact offset. `K` maps an
impulse at the contact point to the change in that point's velocity. The head and ball each
contribute one, and they add: `K_total = K_head + K_ball`. Then:

1. **Normal impulse** from the restitution condition along `n̂`.
2. **Tangential impulse**: first *assume sticking* and solve for the `J_t` that drives tangential
   contact velocity to zero. If `|J_t| ≤ μ J_n`, that is the answer (rolling). Otherwise the
   contact slides and `J_t = μ J_n` opposing the slip direction.
3. `required_friction = |J_t,stick| / J_n` is reported either way.

Step 2 is exactly the two-branch structure that `impact_model.md` §5.2 derives and that
Arakawa's data says is genuinely needed — the sliding branch is not an edge case.

**Effective mass falls out of the same `K`.** Along the normal:

```
1/M_eff = n̂ᵀ K_head n̂  =  1/M + n̂ · [ (I⁻¹(r × n̂)) × r ]
```

✅ **I verified numerically that this reduces exactly to the planar `1/M + b²/I`** for a
diagonal tensor and a pure toe-ward offset (agreement to machine precision). That is the
Phase 3 "reduction" test, and it already passes in prototype form — so the 3D route carries no
risk of failing to reproduce the hand-derived results.

### 4.2 Rejected alternative

*Implement planar only, add 3D later.* Rejected: it cannot produce a 2D forgiveness map, which
is the Phase 4 deliverable, so it would have to be replaced within the same step rather than
extended. The planar equations keep their role — as the **explanation** in the brief and as the
**test oracle** in Phase 3 — which is where they are most valuable.

---

## 5. Sourced constants

### 5.1 The type

```python
class SourcedConstant(float):
    """A float that remembers where it came from."""
    unit: str
    citation: str
    note: str = ""
```

**Recommendation: subclass `float`.** Then `ball.mass_kg * 2` just works, and no call site needs
`.value`. Arithmetic returns a plain `float`, which is the correct behaviour — the provenance of
`m·v²` is not the provenance of `m`, and silently pretending otherwise would be worse than
losing it.

**Trade-off considered.** A plain wrapper with `.value` forces conscious unwrapping, which is
arguably safer. I judge the ergonomic win larger: a wrapper means every formula in the physics
core is littered with `.value`, which hurts readability of exactly the code that most needs to be
readable against the derivations. The degradation-to-float behaviour is a feature, not a leak.

### 5.2 The v1 tour-ball values

Following Finley's decision. Each carries its citation; full context in `impact_model.md` §7.1.

| Constant | v1 value | Citation | Caveat carried in `note` |
|---|---|---|---|
| `mass_kg` | 0.04593 | Equipment Rules Part 4 §2, p.69 | **maximum** permitted, not minimum |
| `radius_m` | 0.021335 | Equipment Rules Part 4 §3, p.69 | minimum permitted diameter |
| `inertia_kg_m2` | ≈ 8.4×10⁻⁶ | ⚠️ uniform-sphere estimate, α = 2/5 | not measured; ±10% in α moves spin ≈3% |
| `cor` | **0.78 @ 29 m/s** | Penner p.145 (Gobush 1990) | measured against a **rigid barrier** |
| `friction` | **0.38 @ 12.8 m/s tangential** | Penner p.149 (Gobush 1996a) | three-piece soft cover; falls to 0.29 by 26.8 m/s |

Two notes on these choices:

- **The COR pairing is not arbitrary.** Gobush's 0.78 was measured ball-against-rigid-barrier.
  Our face is *rigid by assumption*, so a rigid-barrier COR is the physically consistent number
  to use — a driver-face COR would double-count face flex that our model does not have. This
  constant must be revisited if face flexibility is ever added.
- **μ = 0.38 is the low-tangential-speed datum**, which suits driver-like lofts (a 10.5° driver
  at 45 m/s has only ≈8 m/s of tangential speed). It is **optimistic for high-loft clubs**, where
  Gobush measured 0.29 and tangential speeds run far higher. The mitigation is structural rather
  than numerical: `required_friction` (§2.5) makes the model *report* where it is leaning on
  friction it may not have, instead of quietly overestimating wedge spin. Speed-dependent
  interpolation between the two sourced points is a clearly-labelled later option.

---

## 6. File layout

Flat, one concern per file, matching the existing repo. Five new modules:

| File | Responsibility |
|---|---|
| `sourced_constant.py` | the `SourcedConstant` type only |
| `units.py` | the **only** sanctioned boundary conversion: g↔kg, mm↔m, g·cm²↔kg·m², mph↔m/s, deg↔rad |
| `head_mass_properties.py` | `FaceGeometry`, `HeadMassProperties`, their validation, `conformance_report()` |
| `ball_properties.py` | `BallProperties` + the v1 tour-ball sourced constants |
| `impact_model.py` | `ImpactConditions`, `ImpactResult`, and the solver functions |

Tests mirror them: `test_head_mass_properties.py`, `test_ball_properties.py`, `test_impact_model.py`.

**Why `impact_model.py` holds three things.** It mirrors the existing `ball_flight.py`, which
holds `LaunchConditions`, `TrajectoryResult` and its solvers together. Consistency with the
established pattern beats a purer split here, and the conditions/result types are meaningless
apart from the solver that consumes and produces them.

Phase 4 adds `forgiveness_map.py` (computation) and `forgiveness_diagram.py` (matplotlib),
keeping the project's calculation/display separation.

**Nothing existing is modified.** `ball_flight.py` in particular stays untouched, as agreed —
including its mislabelled `BALL_MASS` comment, which is logged in `impact_model.md` §11 for a
separate approval.

---

## 7. Open questions for Phase 3

1. **Does `ImpactConditions` belong to a club?** Right now a `HeadMassProperties` is standalone
   and unconnected to `ClubSpecification`. I propose keeping them separate for v1 — the existing
   `ClubSpecification` has no CG, no tensor and no face, so joining them would mean changing a
   domain object used by six other modules for no v1 benefit. Worth a decision before Phase 4.
2. **Sweep resolution and the summary metric.** Phase 4's "face area retaining ≥ X% ball speed"
   needs `X` chosen and labelled as a setting. Suggest deciding it when we can see a real map.
3. **Fixture head data.** Phase 3 needs at least one `fixture_*` head. Phase 4 needs real data,
   which per Rule 4 must come from you, not from me.
