# Impact Model v1 — Model Report

**Status:** Phase 5 — implemented, tested, validated against published results.
**Scope:** clubhead mass properties + strike location → ball launch conditions, swept across
the face to produce a forgiveness map.
**Companions:** [`impact_architecture.md`](impact_architecture.md) — coordinate frame, data
model, validation, file layout. `test_impact_model.py`, `test_impact_validation.py` — every
claim below that can be tested is.
**Out of scope for v1:** ball flight, face flexibility, bulge and roll, shaft dynamics, face
angle / club path (square face assumed), pre-impact head rotation, left-handed heads.

---

## 0. How to read the source labels

| Label | Meaning |
|---|---|
| ✅ **Verified** | Source document fetched and the specific passage read. Page number given. |
| 📐 **Derived** | Follows algebraically from verified inputs. Derivation shown. |
| ⚠️ **Estimate** | A defensible standard approximation, explicitly *not* a measured value. |
| 🧪 **Tested** | Asserted by a test in this repo, to the stated tolerance. |

One constant remains ⚠️ **Estimate** — the ball's moment of inertia (§7, §11). Everything
else carries a value, a unit and a citation, enforced structurally: `SourcedConstant` refuses
to exist without them.

Sources read in full for this report: the R&A/USGA **Equipment Rules** (2020 v2, 99 pp.) and
four R&A/USGA test protocols (COR, MOI, ball weight & size, initial velocity); **Penner
(2003)**, "The physics of golf", *Rep. Prog. Phys.* **66**, 131–171; **Arakawa et al. (2007)**,
*Exp. Mech.* **47**, 277–282. Full list with page citations in §12.

---

## 1. The model

### 1.1 Why the head is a free rigid body during impact

Contact lasts a few hundred microseconds. Over that window the impulsive contact force
dwarfs every other force on the head — gravity, shaft stiffness, the golfer's grip — so the
impulse those finite forces deliver is negligible and the head behaves as a free rigid body
with mass `M` and inertia tensor `I`. The shaft does not appear in v1 at all.

✅ Arakawa et al. filmed impact at 10 μs intervals and report maximum contact area at
**t = 220 μs** for 31.5 m/s inbound (*Exp. Mech.* 47, pp. 279–281). ✅ The Equipment Rules'
pendulum test expresses face compliance as a *characteristic time* with a **257 μs** field
limit (p.11, Part 2 §4c(i)). Over 0.3 ms gravity changes the head's velocity by ~0.003 m/s
against impact-induced changes of tens of m/s: safe by four orders of magnitude.

### 1.2 Effective mass — the planar derivation

Hit the head in line with its CG and it can only translate; the ball feels all of `M`. Hit it
off-centre and the head also rotates; momentum that would have driven the ball goes into
spinning the head, and the ball feels a lighter club. That is captured by one number.

With `b` the moment arm from the CG to the impulse's line of action, `J` the normal impulse,
and `I` the head's moment about the axis perpendicular to the plane:

```
M Δv_cg = −J n̂                 →  Δv_cg · n̂ = −J / M                     (1)
I Δω    = −J b                  →  Δω = −J b / I                          (2)
Δv_P · n̂ = Δv_cg · n̂ + (Δω × r) · n̂ = −J (1/M + b²/I)                  (3)
```

Defining `Δv_P · n̂ ≡ −J / M_eff`:

> ### 📐 **1 / M_eff = 1/M + b² / I**

Translation and rotation add *in series*, like compliances. At `b = 0`, `M_eff = M`; as `b`
grows `M_eff` falls, and the rate is set by `I`. **That expression is the mathematical
definition of forgiveness.** The normal-direction problem is then a 1D collision:

> ### 📐 **v_ball = u_n · M_eff (1 + e) / (M_eff + m)**  and, at the sweet spot with zero loft,  **smash = M (1 + e) / (M + m)**

✅ This is exactly Penner's equation (6) (p.160). 🧪 The 3D solver reduces to it to 1e-14.

### 1.3 The 3D formulation actually implemented

The code solves the full problem with the **collision matrix** `K`, which maps an impulse at
the contact point to the change in relative velocity there:

```
Δu_rel = K J,   K = (1/m + 1/M) 𝟙 − [r_ball]ₓ I_ball⁻¹ [r_ball]ₓ − [r_head]ₓ I⁻¹ [r_head]ₓ
```

Three compliances in series — the ball's mass, the head's mass, and each body's rotational
give about the contact point. The off-centre strike enters only through `r_head`, and that one
term produces *both* the ball-speed loss and the gear-effect spin: they are one effect.

The normal effective mass in 3D is `1/M_eff = n̂ᵀ K_head n̂`. With `r_head = (bₓ, b_y, d)` and
a diagonal tensor this is `1/M + b_y²/Iₓₓ + bₓ²/I_yy` — 📐 exactly the planar result in each
plane, and **CG depth `d` drops out of the normal problem entirely**. 🧪 Tested to 1e-12.

The solution proceeds by solving the **stick** case first (`J = K⁻¹ Δu_target`, tangential
relative velocity driven to zero, normal to `−e` times its approach value), then checking
`|J_t| ≤ μ J_n`. If friction cannot deliver it, the **slip** branch applies Coulomb's limit
`J_t = μ J_n` against the sliding direction. That ordering is the only way to find the regime
without assuming it. v1 holds the sliding direction fixed through contact — exact in the
planar case, a standard approximation in 3D.

### 1.4 Gear effect

Off-centre, the head rotates (`Δω = −Jb/I`). Because the face sits a distance `d` **in front
of** the CG, that rotation drags the face sideways across the ball while they are in contact;
friction couples them and the ball spins the opposite way, like meshed gears. The tangential
face motion is `≈ Δω · d`, so gear spin scales as **`J · b · d / I`**: proportional to offset,
proportional to CG depth, inversely proportional to MOI. At `d → 0` it vanishes while the
speed loss remains. 🧪 Tested: linear in `d` to 0.1%, zero at the rigid limit.

In the corrected frame (`+x` toward the **heel** — see `impact_architecture.md` §1.1):

| Strike | Head rotates about | Ball gets |
|---|---|---|
| **Toe** (`x < 0`) | vertical axis, face opens | starts right, **draw** spin — the toe-hook |
| **Heel** (`x > 0`) | vertical axis, face closes | starts left, **fade** spin — the heel-slice |
| **High** (`y > 0`) | toe–heel axis | higher launch, **less** backspin |
| **Low** (`y < 0`) | toe–heel axis | lower launch, **more** backspin |

🧪 All four signs tested. One result found during implementation that the concept brief did
not anticipate: **CG depth lowers backspin even on a perfectly centred strike**, because
friction acts in the face plane while the CG sits `d` behind it, so the friction impulse
torques the head. Deeper CG → less tangential impulse needed to grip → less spin. On the
fixture head, 5 mm → 45 mm of depth moves centred-strike backspin from 2458 to 2272 rpm
with the normal impulse unchanged. That is the vertical gear effect with no off-centre strike
at all, and it is why "move the CG back to lower spin" works.

### 1.5 Loft, backspin, and the tangential condition

Resolve the head velocity `u` against a face at delivered loft `θ`: `u_n = u cos θ`,
`u_t = u sin θ`. The tangential part is sliding for friction to act on; friction at the ball's
surface applies a torque, and that torque is backspin. With `I_b = α m R²`:

> ### 📐 Rolling at separation: **J_t = m u_t · α/(1+α)**, **ω = u_t / ((1+α) R)**
> ### 📐 achieved iff **m u_t · α/(1+α) ≤ μ J_n**; otherwise **J_t = μ J_n** and `μ` sets the spin.

For a uniform sphere (`α = 2/5`) these are the classic `(2/7) m u_t` and `ω R = (5/7) u_t`.
🧪 Both reproduced to 1e-6 against an immovable head. Note the 2/7 and 5/7 are consequences of
`α`, not universal constants.

The required friction ratio is 📐 **speed-independent**:
`J_t/J_n = [α/(1+α)] tan θ (M+m) / (M(1+e))` for a point-mass head; the full model adds the
head's rotational compliance. With the sourced `e = 0.78`:

- **Driver, 10.5°, 200 g:** the model needs `J_t/J_n = 0.033` against an available `μ = 0.38`.
  About **9% of the grip available** — the driver is nowhere near sliding, and its spin is
  essentially insensitive to `μ`.
- **50° wedge, hard two-piece cover (`μ = 0.16`):** the model needs 0.21. **Slides.** The same
  wedge with a soft three-piece cover (`μ = 0.38`) still grips. 🧪 Both tested.

✅ Arakawa et al. confirm sliding is real: the rolling ratio `Rω/v_t` fell from 0.52 to 0.13
on smooth PMMA as inbound speed rose 15 → 61 m/s, and was "almost zero" on an oiled target
(p.281). It explains why wedge spin collapses in wet grass while driver spin barely moves.

📐 **Launch angle sits below loft**, because the ball leaves between the face normal and the
path. For the 10.5° driver the model gives **8.63°, a ratio of 0.822** — the `0.85 × loft`
rule of thumb hard-coded in `ball_flight.py` is recovered as an *output* of the physics, within
3%. 🧪 Tested.

### 1.6 The sweet spot

> The point where the line through the CG, normal to the face, meets the face.

✅ This is the governing bodies' definition: the COR protocol requires impact "centered at the
projection of the clubhead Centre of Mass through the club face" (p.4). It is where `b = 0`,
`M_eff = M`, ball speed is maximal and gear spin is zero — and it is generally **not** the
geometric face centre. The map marks both. 🧪 Symmetry is tested about the sweet spot of an
offset-CG head, not about the face centre.

---

## 2. Constants

| Symbol | Quantity | Value | Unit | Status | Source |
|---|---|---|---|---|---|
| `m` | Ball mass | ≤ 45.93 | g | ✅ | Equipment Rules Part 4 §2, p.69 — a **maximum**; "there is no minimum weight" |
| `D` | Ball diameter | ≥ 42.67 | mm | ✅ | Equipment Rules Part 4 §3, p.69 — a minimum |
| `α` | Ball inertia ratio `I_b/(mR²)` | 2/5 → `I_b ≈ 8.36×10⁻⁶ kg·m²` | – | ⚠️ **Estimate** | uniform sphere; no measured value in the sources read |
| `e` | Coefficient of restitution | **0.78 @ 45 m/s** (0.85 @ 20 m/s) | – | ✅ | Penner p.144 (Chou et al 1994); p.145 (Gobush 1990). Speed-dependent |
| `μ` | Ball–face friction | **0.38** three-piece (→0.29 by 26.8 m/s); 0.16 two-piece (→0.075) | – | ✅ | Penner p.149 (Gobush 1996a). Varies ~2.4× by cover |
| — | COR test speed | 133 ± 0.5 (40.5 m/s) | ft/s | ✅ | COR protocol p.4 |
| — | COR conformance | `e_C ≤ e_BP + 0.008` — relative to a **baseline plate**, not a fixed number | – | ✅ | COR protocol p.5 |
| — | Ball IV limit | 250.0 + 2 % | ft/s | ✅ | IV protocol p.4 |
| — | Pendulum CT field limit | 257 | μs | ✅ | Equipment Rules p.11 |
| — | Clubhead MOI limit | 5900 (+100 tolerance), about the lab vertical at 60° lie | g·cm² | ✅ | Equipment Rules Part 2 §4b(i), p.54; MOI protocol p.3 |

The v1 ball is a **conforming three-piece tour ball built to the Rules limits** — a generic
ball, not a commercial product. `e` is the 45 m/s value because that is where a driver lives;
it is the wrong constant for a wedge, and the code says so where it is defined.

**No COR ceiling exists to cite.** The protocol's conformance test is relative to a titanium
baseline plate (p.5); the widely quoted "0.830" appears nowhere in the documents read and is
not asserted here.

---

## 3. Assumptions (v1)

1. Free rigid head during contact; the shaft applies no impulse.
2. No pre-impact head rotation.
3. Rigid, **flat** face — no trampoline effect, no bulge or roll.
4. A single COR everywhere on the face and at all speeds.
5. Square face; delivered loft is an input. (The web app derives it as dynamic loft − attack
   angle, the angle between the face normal and the head's actual path.)
6. Coulomb friction with a single `μ`; sliding direction fixed through contact.
7. Rigid sphere ball, uniform density for `I_b`.
8. Point contact.
9. Instantaneous impact; head orientation unchanged during contact.
10. Ball at rest before impact.
11. Right-handed head.
12. Gravity and air ignored during the impact window.

---

## 4. Validity range

Where the model can be trusted, and where it is extrapolating. Each line is a consequence of
a specific assumption above.

| Trust it for | Because | Do not trust it for |
|---|---|---|
| **Centred and near-centre strikes** (within ~15–20 mm) | the K-matrix physics is exact for a rigid flat face | **the rim of the face** — bulge and roll exist precisely to counteract the gear effect this model computes, so curvature is **overstated** toward the edges; at the crown edge of the fixture the flat face drives backspin negative, which real roll would prevent |
| **Driver lofts (8–14°) with any ball** | required friction is ~9% of what is available, so results are insensitive to `μ` | **wedges with hard-cover balls** — sliding regime; spin is set by a `μ` that is speed-dependent and single-valued only by assumption |
| **Impact speeds 20–45 m/s** | `e` is sourced across that range | speeds outside it, and any claim to ±0.01 in `e` |
| **Relative comparisons between heads** (A − B) | systematic errors largely cancel | **absolute ball speed** — no face flex, so smash factor is ~5% low against a modern driver (see §5, Cochran) |
| Ball-speed loss trends | `M_eff` is geometric | absolute off-centre loss — a real face is stiffer at the perimeter, so real loss is **larger** than shown |
| Spin **trends** | gear effect is linear in `b` and `d`, inverse in `I` | spin to better than ~±3%, because `α` is an estimate |

The forgiveness map's area metric uses a **97% threshold that is a chosen setting**, not a
standard; no source read defines a "forgiveness area". The face outline is labelled
`ASSUMED` until it is measured, and the area is only as good as the outline.

---

## 5. Validation results

Every number here is produced by `test_impact_validation.py` and asserted there.
"Model" figures use the synthetic `fixture_symmetric_head` (200 g, CG 35 mm deep,
`I = diag(3000, 5000, 4000) g·cm²`) and the conforming three-piece ball, unless stated.

| # | Published result | Source | Model | Verdict |
|---|---|---|---|---|
| A | `Vb = (1+e)Vc / (1 + Mb/Mc)` — Penner's equation (6) | Penner p.160 | reproduced to **1e-14** across 170–215 g | 🧪 exact |
| B | `e = [(Vout/Vin)(m_C+m_b)+m_b]/m_C` — the COR protocol's own formula, ball fired at a free stationary head | COR protocol p.4 | Galilean shift of our solution returns `e` to **1e-16** | 🧪 exact |
| C | COR +12 % → "approximately 5 %" more launch speed (Cochran 1999) | Penner p.162 | **+5.25 %** | agrees |
| D | 191 g → 170 g head with +8.5 % head speed → "approximately 5.6 %" more launch speed (Reyes & Mittendorf 1999) | Penner p.160 | **+5.96 %** | 0.36 points high — **discrepancy** |
| E | Launch angle ≈ 0.85 × dynamic loft | `ball_flight.py` (empirical rule in this repo) | **0.822** | within 3 % |
| F | 10 mm toe strike: +19 % vertical MOI cuts sidespin 3.1 → 2.3 rps, ratio 0.74 (Iwatsubo et al 2000) | Penner p.166 | ratio **0.845**; absolute **9.8 rps** at 45 m/s | direction right, **magnitude wrong** |
| G | 4-iron at 40 m/s, centre strike: 54 m/s simulated, 56.9 m/s measured (Knowles et al 1998) | Penner p.166 | **55.1 m/s** (⚠️ 250 g and 24° assumed) | bracketed |

**Centre-strike smash factor.** The model gives **1.448** at zero loft and **1.424** at 10.5°
with `e = 0.78`. That is ~5 % below the figures launch-monitor vendors quote for modern
drivers — and result C says why: a compliant face raises the effective COR by up to 12 %,
worth ~5 % in ball speed, and v1's face is rigid. I have found no *primary* source stating a
driver smash factor and do not cite one; the Rules' own ceiling on the ball (250 ft/s initial
velocity, IV protocol p.4) governs a different quantity.

**On the discrepancies, honestly.**

- **D** cannot be closed by ball mass — a lighter ball moves the model *further* from 5.6 %.
  Penner does not state the COR behind his figure; the ratio depends on it weakly. Recorded,
  not tuned.
- **F** is the informative one. Three reasons the model overstates gear spin roughly threefold
  here: the flat face (§4 — this is the rim-overstatement in action), Iwatsubo's unstated
  clubhead speed, and Penner's own note that their heads "may" have differed in more than the
  one parameter. The magnitude gap is the size of the bulge-and-roll term v1 omits, which is
  useful to know.
- **G** is a bracket, not a match: the head mass is an assumption and the loft is the floor of
  this repo's 4-iron range. It is included because it is the only measured centre-strike ball
  speed found, not because it validates much.

**What could not be reproduced.** Penner's optimum dynamic lofts (13.1° for drive, 14.9° for
carry at 45 m/s and 200 g, p.161) and the off-centre carry losses (Winfield & Tan, p.165) all
require ball flight, which is out of scope. His optimum bulge radius of 21.5 cm (p.164)
requires the curved face v1 does not have.

---

## 6. Limitations and remaining estimates

**Physical limitations, in order of consequence**

1. **No bulge or roll.** The largest. Overstates curvature and gear spin toward the rim; the
   Iwatsubo comparison (§5 F) shows the size of it.
2. **No face flex.** Under-predicts absolute ball speed by ~5 % (Cochran) and under-predicts
   off-centre loss, because a real face is stiffer at the perimeter.
3. **Single `e`, single `μ`** — no spatial or speed variation.
4. **Rigid ball, point contact** — no compression, no construction differences, no finite
   contact patch.
5. **Sliding direction fixed** through contact in the slip branch (3D approximation).

**⚠️ Still an estimate:** the ball's inertia ratio `α = 2/5`. A 10 % error in `α` moves
predicted spin by ~3 %. Penner confirms ball MOI matters (p.152) but gives no figure.

**Two things logged for separate approval**

- `ball_flight.py:9` describes 45.93 g as the "minimum" ball mass. The value is right; the
  descriptor is wrong — it is the **maximum**, and the Rules say explicitly there is no minimum
  (Part 4 §2, p.69). Left untouched per the standing rule on existing modules.
- `clubhead_composition.py` uses `toe_heel` **positive toward the toe**; the impact model's
  frame is positive toward the heel (a left-handed triad otherwise — see
  `impact_architecture.md` §1.1). The two subsystems are unconnected today, so nothing is
  wrong, but joining them would be a silent sign flip.

---

## 7. References

| Reference | Read? | Pages cited |
|---|---|---|
| R&A/USGA **Equipment Rules** (2020 v2) | ✅ | 11, 54, 69 |
| R&A/USGA **COR Protocol** (relative to a baseline plate) | ✅ | 4, 5 |
| R&A/USGA **MOI Protocol** | ✅ | 3 |
| R&A/USGA **Ball Weight & Size Protocol** | ✅ | 3 |
| R&A/USGA **Initial Velocity Protocol** | ✅ | 3, 4 |
| Penner, "The physics of golf", *Rep. Prog. Phys.* **66**, 131–171 (2003), DOI 10.1088/0034-4885/66/2/202 | ✅ | 144, 145, 149, 152, 160, 161, 162, 164, 165, 166 |
| Arakawa et al., "Dynamic Contact Behavior of a Golf Ball during Oblique Impact", *Exp. Mech.* **47**, 277–282 (2007), DOI 10.1007/s11340-006-9018-4 | ✅ | 279–281 |
| Penner, *Am. J. Phys.* **69**(5), 563–568 (2001a) and **69**(10), 1073–1081 (2001b) | ❌ paywalled | cited only as Penner 2003 reports them |
| Stronge, *Impact Mechanics*, CUP (2000) | ❌ not accessed | none — the right citation for §1.1's principle, unread |

Primary studies reached **only through Penner's review**, quoted as he reports them with his
page given: Chou et al (1994), Gobush (1990, 1996a), Reyes & Mittendorf (1999), Cochran
(1999), Iwatsubo et al (2000), Knowles et al (1998), Winfield & Tan (1994, 1996).

Located but not accessed, if the estimate in §6 needs closing: Ekstrom (1998), "Experimental
determination of golf ball coefficients of sliding friction", *Science and Golf III*, ch. 64.
