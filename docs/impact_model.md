# Impact Model v1 — Concept Brief

**Status:** Phase 1 (concept only). No code has been written against this yet.
**Scope:** clubhead mass properties + strike location → ball launch conditions.
**Out of scope for v1:** ball flight, face flexibility, bulge and roll, shaft dynamics,
face angle / club path (square face assumed), pre-impact head rotation, left-handed heads.

---

## 0. How to read the source labels

Every physical claim and constant below carries one of these:

| Label | Meaning |
|---|---|
| ✅ **Verified** | I fetched the source document and read the specific passage. Page number given. |
| 📐 **Derived** | Follows algebraically from verified inputs. Derivation shown in full. |
| ⚠️ **Estimate** | A defensible standard approximation, explicitly *not* a measured value. |
| ❓ **Blocked** | Needed, not yet sourced. **Not guessed.** — *no constant currently carries this label; two did before Finley supplied the Penner and Arakawa papers.* |

One constant remains ⚠️ **Estimate** — the ball's moment of inertia. COR and the ball–face
friction coefficient were sourced from the literature (§7.1) after Finley supplied the Penner
review and the Arakawa friction study.

Sources fetched and read for this brief:

- **Equipment Rules** (R&A / USGA, joint), 99 pp. — `Equipment Rules 2020 v2.pdf`
- **Protocol for Measuring the Coefficient of Restitution of a Clubhead Relative to a Baseline Plate** (R&A/USGA), 6 pp.
- **Protocol for Measuring the Moment of Inertia of Golf Clubheads** (R&A/USGA), 5 pp.
- **Golf Ball Weight and Size Test Protocol** (R&A/USGA), 4 pp.
- **Initial Velocity Test Protocol** (R&A/USGA), 4 pp.
- **Penner (2003)**, "The physics of golf", *Rep. Prog. Phys.* **66**, 131–171 — full text, 41 pp.
- **Arakawa et al. (2007)**, "Dynamic Contact Behavior of a Golf Ball during Oblique Impact:
  Effect of Friction between the Ball and Target", *Exp. Mech.* **47**, 277–282 — full text, 6 pp.

Citation metadata confirmed via Crossref/Open Library for Penner 2001a, Penner 2001b, Penner
2003, Stronge, and Jorgensen — see §10. The two 2001 Penner papers and Stronge remain unread,
so **nothing is cited from them anywhere in this document.**

---

## 1. Why the head can be treated as a free rigid body during impact

**The intuition.** Ball–club contact lasts on the order of a few hundred microseconds. Over
that window, the impulsive contact force is enormous compared with everything else acting on
the head — gravity, the shaft's bending stiffness, the golfer's grip. Those forces are
*finite*, so the impulse they deliver (force × time) over half a millisecond is negligible
against the contact impulse. The head therefore behaves, for the duration of the collision,
as if nothing were attached to it: a free rigid body with mass `M` and inertia tensor `I`.

This is the standard impulse–momentum idealisation for collisions: during contact, only
impulsive forces matter, and the configuration of the body does not measurably change.

**Timescale evidence.** ✅ Arakawa et al. measured golf-ball impact directly with a high-speed
camera at a 10 μs framing interval, and report contact developing over a few hundred
microseconds — maximum contact area at **t = 220 μs** for an inbound velocity of 31.5 m/s,
with contact time *decreasing* as inbound velocity rises (*Exp. Mech.* 47, pp. 279–281).
✅ Independently, the Equipment Rules govern face flexibility via a pendulum test whose result
is a *characteristic time* in microseconds — a used driver exceeding **257 μs** is deemed
non-conforming (Equipment Rules, p.11, ref. Part 2 §4c(i)). Both confirm the sub-millisecond
timescale this argument rests on.

Over ~0.3 ms, gravity changes the head's velocity by roughly `g·t ≈ 0.003 m/s` — against
impact-induced velocity changes of tens of m/s. The neglect is safe by four orders of magnitude.

> ⚠️ **To confirm:** the general principle (non-impulsive forces negligible during collision)
> is textbook impact mechanics, and Stronge, *Impact Mechanics* is the right citation for it,
> but I have not read the book — so no chapter or page is cited. See §9.

**Consequence for the model:** we solve the impact with impulse–momentum equations on a free
body. The shaft does not appear in v1 at all.

---

## 2. Effective mass at a strike point

This is the heart of why off-centre strikes lose ball speed, and it is worth deriving by hand.

### 2.1 The intuition

Hit the head exactly in line with its centre of gravity and the head can only translate — all
of its mass resists the ball. Hit it off to one side and the head *also* starts to rotate.
Energy and momentum that would have gone into driving the ball forward instead go into
spinning the head. The ball "feels" a lighter club. We capture this with a single number:
the **effective mass** at the strike point.

### 2.2 Planar derivation

Work in 2D. Let:

- `M` = head mass
- `I` = head moment of inertia about its CG, about the axis perpendicular to the plane
- `n̂` = unit normal to the face
- `P` = strike point on the face
- `b` = the **moment arm**: the perpendicular distance from the CG to the line of action of
  the impact impulse (i.e. from the CG to the line through `P` along `n̂`)
- `J` = magnitude of the normal impulse delivered to the head (the ball pushes back along `−n̂`)

Linear impulse–momentum on the head:

```
M Δv_cg = −J n̂            →      Δv_cg · n̂ = −J / M            (1)
```

Angular impulse–momentum about the CG. The impulse `J` acting at moment arm `b` delivers
angular impulse `J·b`:

```
I Δω = −J b               →      Δω = −J b / I                  (2)
```

Now the quantity that actually matters is the velocity of the **contact point**, not the CG —
the ball only ever touches `P`. For a rigid body:

```
v_P = v_cg + ω × r
```

so the change in the contact point's normal velocity picks up both terms:

```
Δv_P · n̂ = Δv_cg · n̂ + (Δω × r) · n̂
         = −J/M           +  (−J b / I)·b
         = −J ( 1/M + b²/I )                                     (3)
```

Define the effective mass `M_eff` as the mass that would produce the same contact-point
velocity change under the same impulse, i.e. `Δv_P · n̂ ≡ −J / M_eff`. Comparing with (3):

> ### 📐 **1 / M_eff = 1/M + b² / I**
>
> equivalently  **M_eff = M / (1 + M b² / I)**

**Read it back physically.** The two ways the contact point can retreat — the whole head
translating, and the head rotating about its CG — add *in series*, like compliances. At
`b = 0` the rotational term vanishes and `M_eff = M`: the full mass resists the ball. As `b`
grows, `M_eff` falls monotonically. And the rate at which it falls is set by `I`: a
high-MOI head keeps `M_eff` closer to `M` further from centre. **That single expression is
the mathematical definition of forgiveness**, and it is what the Phase 4 map visualises.

### 2.3 Ball speed from effective mass

With `M_eff` in hand, the normal-direction problem reduces to a 1D collision: effective mass
`M_eff` approaching at normal speed `u_n`, ball mass `m` at rest, coefficient of restitution `e`.

```
momentum:     M_eff u_n = M_eff v_head + m v_ball
restitution:  e = (v_ball − v_head) / u_n
```

Solving the pair:

> ### 📐 **v_ball = u_n · M_eff (1 + e) / (M_eff + m)**

At the sweet spot (`b = 0`, `M_eff = M`) and a square face at zero loft (`u_n = u`), this
collapses to the closed-form check Phase 3 will assert against:

> ### 📐 **smash factor = v_ball / u = M (1 + e) / (M + m)**

**Why ball speed falls off-centre:** `M_eff < M`, and `M_eff(1+e)/(M_eff+m)` is monotonically
increasing in `M_eff`. Both the numerator falls and the mass-ratio penalty worsens. Ball speed
retention is therefore highest exactly at the sweet spot and decreases in every direction —
which is what makes a "map" the natural way to present it.

---

## 3. Coefficient of restitution, and what a rigid face cannot capture

`e` lumps every energy loss in the collision into one number: hysteresis in the ball's core
and cover, and elastic energy stored and returned by the face.

✅ **How it is officially defined.** The R&A/USGA protocol fires a ball at a clubhead and
computes

```
e = [ (V_out / V_in)(m_C + m_b) + m_b ] / m_C
```

(Protocol for Measuring the COR of a Clubhead Relative to a Baseline Plate, p.4), with the
impact "centered at the projection of the clubhead Centre of Mass through the club face",
"within 2° of normal to the surface of the club face", at an **impact velocity of 133 ± 0.5
ft/s** (40.5 m/s) (same page). That last clause matters: **COR is only meaningful paired with
the speed it was measured at.**

✅ **Measured values, and their speed dependence.** Penner reviews Chou et al (1994), who found
COR for a one-piece solid ball fell from **≈ 0.85 at 20 m/s to ≈ 0.78 at 45 m/s**, noting that
"the coefficient of restitution will, therefore, normally decrease with impact speed as a
result of the greater deformation of the golf ball" (*Rep. Prog. Phys.* 66, p. 144). Gobush
(1990) measured **0.78** for both two-piece and three-piece balls at a 20° oblique impact at
29 m/s (ibid., p. 145).

**What a single rigid-face `e` cannot represent:**

1. **Spatial variation.** Real COR is highest near the centre of the face and falls toward the
   perimeter. v1 applies one `e` everywhere, so the forgiveness map will *understate* real
   ball-speed loss off-centre — the geometric `M_eff` effect is modelled, the face-stiffness
   effect is not.
2. **Speed dependence.** COR falls measurably with impact speed — roughly 0.85 → 0.78 across
   20 → 45 m/s (above). One constant cannot honestly span a 70 mph wedge and a 120 mph driver,
   so v1's `e` must be quoted *with* the speed it is meant for.
3. **The spring-like (trampoline) effect at all.** A rigid face cannot store and return energy.
   That the Equipment Rules need a dedicated pendulum/characteristic-time test (✅ p.11) is
   itself proof that real faces flex meaningfully — v1 simply does not model that mechanism.
4. **Face flexural modes and their coupling to spin.**

This is the single largest fidelity gap in v1, and it is the natural subject of a later step.

---

## 4. Gear effect

### 4.1 The intuition

Off-centre, the head rotates (from §2.2, `Δω = −Jb/I`). Because the face sits *in front of*
the CG, that rotation drags the face sideways across the ball while they are still in contact.
Friction couples them, and the ball spins the opposite way to the head — exactly like two
meshed gears. Hence the name.

### 4.2 Why it depends on CG depth

Let `d` be the **CG depth**: the perpendicular distance from the face plane back to the CG.
The head rotates about its CG at `Δω`. A point on the *face*, a distance `d` in front of that
axis, therefore acquires a tangential velocity of approximately

```
v_tangential ≈ Δω · d
```

That tangential face motion is what shears the ball and spins it. So:

- **`d → 0`** (CG in the plane of the face): rotation produces no tangential motion at the
  face, and **gear effect vanishes** — even though the head still rotates and still loses ball
  speed. This is the clean separation Phase 3 tests: shrink `d` with `I` held fixed, and the
  speed loss stays while the gear spin goes to zero.
- **Deeper CG** (driver, ~large `d`): strong gear effect. This is why drivers gear noticeably
  and thin blade irons, whose CG sits close to the face, barely do.

Combining with `Δω = −Jb/I`, gear-effect spin scales roughly as `J·b·d / I`: proportional to
strike offset, proportional to CG depth, inversely proportional to head MOI.

### 4.3 Both planes

| Strike offset | Head rotates about | Face moves | Ball gets |
|---|---|---|---|
| **Toe** (+ toe-heel) | vertical axis | toe-ward at contact | draw-direction sidespin |
| **Heel** (− toe-heel) | vertical axis | heel-ward at contact | fade-direction sidespin |
| **High** (above CG line) | horizontal toe-heel axis | upward at contact | **less** backspin, higher launch |
| **Low** | horizontal toe-heel axis | downward at contact | **more** backspin, lower launch |

The horizontal pair is the familiar one — a toe hit draws, a heel hit fades. The vertical pair
is why driver fitting cares about strike height: high strikes trade spin for launch, which on a
driver is usually a *gain* in carry, and low strikes do the reverse.

> ✅ Penner 2003 is confirmed to treat this territory: its abstract states that "the effects
> that the curvature of a clubface and the moments of inertia of the clubhead have on the
> launch parameters and trajectory of an off-centred impacted golf ball are examined."
> (Rep. Prog. Phys. 66, 131–171 — abstract read; full text paywalled, so no equation cited.)

---

## 5. Loft, backspin, and the tangential condition at separation

### 5.1 Where backspin comes from

Resolve the head's velocity `u` into components relative to the **face**, for a delivered
loft `θ`:

```
normal to face:      u_n = u cos θ
tangential to face:  u_t = u sin θ
```

The normal component drives the ball out (§2.3). The tangential component means the ball and
face are sliding relative to one another — the ball effectively rides *up* the face. Friction
opposes that sliding, acting down the face on the ball. Because that friction force acts at the
ball's *surface*, offset from its centre by the radius `R`, it applies a torque — and that
torque is backspin. **Loft creates spin by creating tangential sliding for friction to act on.**

### 5.2 The two regimes at separation

Whether the ball leaves sliding or gripping decides which physics sets the spin.

**Rolling (no-slip) at separation.** The tangential impulse `J_t` required to bring the
contact point's tangential relative velocity to zero. With ball inertia written generally as
`I_b = α m R²`:

```
tangential:  Δv_t = −J_t / m
spin:        Δω_b =  J_t R / I_b  =  J_t / (α m R)

contact point stops sliding when:   u_t − J_t/m − (J_t/(α m R))·R = 0
                                     u_t = J_t (1/m)(1 + 1/α)
```

> ### 📐 **J_t,roll = m u_t · α/(1+α)**, and the resulting spin **ω = u_t / ((1+α) R)**

⚠️ For a **uniform** sphere `α = 2/5`, giving the classic results `J_t = (2/7) m u_t` and
`ω = 5u_t / 7R`. *Real golf balls are layered, so `α` is an estimate until measured —
see §9.* Note the `2/7` and `5/7` are **not universal constants**; they are consequences of
`α = 2/5`.

**Gross sliding throughout.** If friction cannot supply `J_t,roll`, the ball slides the whole
way and Coulomb friction caps the tangential impulse:

```
J_t = μ · J_n
```

Here spin is set by `μ`, not by kinematics.

**The switch:**

> ### 📐 no-slip is achieved if and only if **m u_t · α/(1+α) ≤ μ J_n**

### 5.3 Why this matters practically

Substituting §2.3 into the §5.2 condition, the required friction ratio is

> ### 📐 **J_t / J_n = [α/(1+α)] · tan θ · (M + m) / (M (1 + e))**

which is worth noting is **independent of clubhead speed** — it depends only on loft, the two
masses, `e` and `α`. Evaluating at the two extremes:

- **Driver, θ ≈ 10.5°, M = 200 g:** required `J_t / J_n ≈ 0.036`. Any realistic `μ` grips
  easily — spin is kinematic, and essentially insensitive to friction.
- **Wedge, θ ≈ 56°, M = 300 g:** required `J_t / J_n ≈ 0.27`. Now the demand is the same order
  as real dry friction. Marginal.

> ⚠️ **These two ratios are illustrative.** Evaluated with `e = 0.83` and uniform-sphere
> `α = 2/5`. `e` now has sourced support (§3) but sits at the top of the measured range, and
> `α` is still an estimate (§9). The *shape* of the conclusion — driver comfortably gripping,
> wedge marginal — is robust, because `e` enters only through a mild `1/(1+e)` factor. The
> specific digits are not.

✅ **Experimental confirmation that sliding is real.** Arakawa et al. measured the rolling
ratio `Rω/v_t` directly (it equals **1 exactly at rolling**). On a smooth PMMA target it
**fell from 0.52 to 0.13 as inbound velocity rose from 15 to 61 m/s**, and was "almost zero"
on an oiled target; a rough steel target gave "much larger values", which they read as the
ball's "angular velocity … fully developed during impact" (*Exp. Mech.* 47, p. 281).

Two things follow, and both matter for v1:

1. **Sliding is not an edge case.** On smooth, low-friction surfaces the ball never reaches
   rolling, so spin is friction-limited, not kinematic. The model must genuinely implement
   *both* branches of §5.2 rather than assuming rolling.
2. **Surface roughness dominates.** A real clubface is grooved and roughened — nearer their
   steel target than their PMMA. But note their targets are *not* clubfaces, so these numbers
   characterise the **mechanism**, not a face-specific `μ`.

That single contrast explains a real phenomenon: **wedge spin collapses in wet grass or from
the rough while driver spin barely moves**, because only the wedge was relying on friction
near its limit. It is also precisely why Phase 4 must flag grid points where the no-slip
solution demands more friction than the sourced `μ` allows — in that region the model is
extrapolating past its own validity.

### 5.4 A useful consequence: launch angle is less than loft

The ball leaves with a large component along `n̂` (at angle `θ`) and a smaller one *down* the
face. The resultant therefore sits **below** the loft angle. The model predicts this from
first principles, rather than assuming it — worth noting because the existing `ball_flight.py`
hard-codes `launch ≈ 0.85 × dynamic loft` as a rule of thumb. For a 10.5° driver the
derivation above gives a ratio near 0.81 (⚠️ same placeholder `e` caveat as §5.3), i.e. the
empirical shortcut is roughly recovered as an *output* of the physics rather than asserted as
an input. Reproducing that relationship properly, with a sourced `e`, is a good Phase 5
validation target.

---

## 6. The sweet spot

> **Definition:** the point where the line through the CG, normal to the face, meets the face.

✅ This is not merely a convention — it is the definition the governing bodies test against.
The COR protocol requires impact "centered at the projection of the clubhead Centre of Mass
through the club face" (COR protocol, p.4).

It is the sweet spot because it is exactly the locus where the moment arm `b` of §2.2 is zero:
no rotation is induced, `M_eff = M`, ball speed is maximal, and gear-effect spin is zero.

**Note it is generally *not* the geometric centre of the face.** Phase 4 marks both, because
the offset between them is a real and interesting design output.

---

## 7. Constants and inputs

### 7.1 Constants

| Symbol | Quantity | Value | Unit | Status | Source |
|---|---|---|---|---|---|
| `m` | Ball mass | ≤ 45.93 (1.620 oz) | g | ✅ Verified | Equipment Rules **Part 4 §2**, p.69 — "must not be greater than"; rules state explicitly **there is no minimum** |
| `D` | Ball diameter | ≥ 42.67 (1.680 in) | mm | ✅ Verified | Equipment Rules **Part 4 §3**, p.69 — "must not be less than" |
| `R` | Ball radius | `D/2` ≥ 21.335 | mm | 📐 Derived | from `D` |
| `I_b` | Ball moment of inertia | `α m R²`, α ≈ 0.4 → ≈ 8.4×10⁻⁶ | kg·m² | ⚠️ **Estimate** | uniform-sphere assumption only; no measured value found in the sources read — §9 |
| `e` | Coefficient of restitution | 0.85 @ 20 m/s → 0.78 @ 45 m/s; 0.78 @ 29 m/s oblique | – | ✅ Verified | Penner p.144 (Chou et al 1994); p.145 (Gobush 1990). **Speed-dependent — quote with its speed** |
| `μ` | Ball–face friction coefficient | 3-piece soft cover: 0.38 → 0.29; 2-piece hard cover: 0.16 → 0.075 (as tangential speed rises 12.8 → ~26 m/s) | – | ✅ Verified | Penner p.149 (Gobush 1996a). **Varies ~5× by ball construction** |
| — | COR test impact speed | 133 ± 0.5 (40.5 m/s) | ft/s | ✅ Verified | COR protocol, p.4 |
| — | Ball IV test impact speed | 143.8 (43.83 m/s) | ft/s | ✅ Verified | Initial Velocity protocol, p.3 |
| — | Pendulum CT field limit | 257 | μs | ✅ Verified | Equipment Rules, p.11 |
| — | Clubhead MOI limit | 5900 (+100 tolerance) | g·cm² | ✅ Verified | Equipment Rules **Part 2 §4b(i)**, p.54; MOI protocol p.3 |
| `g` | Gravity | 9.81 | m/s² | — | not used during impact (non-impulsive) |

✅ **Reference-frame gift from the rules.** The MOI protocol specifies measurement "about the
vertical axis of the clubhead orientated at a **60° lie angle**", "about the **centre of mass**
of the clubhead" (MOI protocol, p.3). Phase 2 should adopt a frame compatible with this, so
that a Fusion-derived tensor and a conformance measurement mean the same thing. The 5900 g·cm²
ceiling also gives a sanity band for validating any fixture inertia tensor.

### 7.2 Inputs

| Input | Meaning | Unit (boundary) | Unit (core) |
|---|---|---|---|
| Head mass `M` | | g | kg |
| Head CG position | in the head frame, incl. **CG depth `d`** | mm | m |
| Head inertia tensor | full 3×3 about the CG | g·cm² | kg·m² |
| Face geometry | plane + outline, for the Phase 4 sweep | mm | m |
| Clubhead speed | **of which point?** — must be stated | mph | m/s |
| Delivered loft | v1: equals input loft | deg | rad |
| Strike location | on the face, in the head frame | mm | m |

⚠️ **"Clubhead speed" is ambiguous and must be pinned down in Phase 2.** The speed of the CG,
of the sweet spot, and of the strike point all differ once the head is rotating. v1 assumes no
pre-impact head rotation, which makes them equal — but the field must still say which one it
means, because that assumption is the first thing a later step will relax.

---

## 8. Assumptions (v1)

1. The head is a **free rigid body** during contact; the shaft applies no impulse.
2. The head has **no angular velocity** before impact.
3. The face is **rigid** and **flat** — no trampoline effect, no bulge or roll.
4. A **single COR** applies everywhere on the face and at all speeds.
5. The face is **square** to the path, and delivered loft equals the input loft.
6. **Coulomb friction** with a single `μ`, no velocity or pressure dependence.
7. The ball is a **rigid sphere** in the tangential problem, with uniform density for `I_b`.
8. Contact occurs at a **point**, not over a finite patch.
9. Impact is **instantaneous**; the head's orientation does not change during contact.
10. The ball is **at rest** before impact.
11. Right-handed head; left-handed is a mirror operation, deferred.
12. Gravity and air are ignored during the impact window (non-impulsive).

## 9. Known limitations, and remaining estimates

**Physical limitations of v1**

- No face flex → off-centre ball-speed loss is **underestimated** (§3).
- No bulge/roll → the real corrective curvature of a driver face is absent, so predicted
  dispersion from off-centre strikes will differ from a real driver.
- Point contact misses the finite contact patch that real gear effect partly depends on.
- Single `e`, single `μ` — no spatial or speed variation.
- Rigid ball: no compression-dependent behaviour, no ball-construction differences.

**⚠️ Still an estimate**

1. **Ball moment of inertia `I_b`.** Still the uniform-sphere value (`α = 2/5`). Neither Penner
   nor Arakawa states a measured figure, and real balls are layered with a denser or lighter
   core depending on construction, so `α` is not exactly 0.4. This directly scales the no-slip
   spin result (`ω = u_t/((1+α)R)`): a 10% error in `α` moves predicted spin by ~3%. Tolerable
   for v1, worth closing later. Note Penner *does* confirm ball MOI matters — he reports that
   dimple pattern and MOI measurably affect spin *retention* in flight (p.152).

**Decisions this hands to Phase 2, rather than blockers**

2. **Which `e`, and which `μ`?** Both are now sourced but neither is a single number:
   `e` falls with impact speed, and `μ` varies ~5× between two-piece and three-piece balls and
   also falls with tangential speed. v1 uses one of each, so the model must **state the ball
   construction and speed its constants describe**, and the docs must say the map is for *that*
   ball. This is a genuine modelling choice for Finley, not something to quietly hard-code.

3. **No COR ceiling exists to cite.** The Equipment Rules govern spring-like effect through the
   pendulum/characteristic-time test, not a published COR limit — I found no "0.830"-style
   figure anywhere in the current text, and will not assert one from memory. The COR values
   above are *measured ball properties* from the literature, which is what the model needs
   anyway.

**⚠️ To confirm** — cited in spirit above but not read, so no page numbers given:

- Stronge, *Impact Mechanics* — for the impulse–momentum treatment of rigid-body impact with
  friction, and for the rigorous justification of neglecting non-impulsive forces (§1).

---

## 10. Reference status

| Reference | Existence verified | Full text read? |
|---|---|---|
| Penner, "The physics of golf: The optimum loft of a driver", *Am. J. Phys.* **69**(5), 563–568 (2001), DOI 10.1119/1.1344164 | ✅ Crossref | ❌ paywalled — abstract only |
| Penner, "The physics of golf: The convex face of a driver", *Am. J. Phys.* **69**(10), 1073–1081 (2001), DOI 10.1119/1.1380380 | ✅ Crossref | ❌ paywalled — abstract only |
| Penner, "The physics of golf", *Rep. Prog. Phys.* **66**(2), 131–171 (2003), DOI 10.1088/0034-4885/66/2/202 | ✅ Crossref | ✅ **read** — pp. 144, 145, 148, 149, 152, 162 cited |
| Arakawa, Mada, Komatsu, Shimizu, Satou, Takehara, Etoh, "Dynamic Contact Behavior of a Golf Ball during Oblique Impact: Effect of Friction between the Ball and Target", *Exp. Mech.* **47**, 277–282 (2007), DOI 10.1007/s11340-006-9018-4 | ✅ Crossref | ✅ **read** — pp. 279–281 cited |
| Stronge, *Impact Mechanics*, Cambridge University Press (1st ed. 2000, ISBN 0521632862) | ✅ Open Library | ❌ not accessed |
| Jorgensen, *The Physics of Golf*, AIP Press (1994, ISBN 0883189550) | ✅ Open Library | ❌ not accessed |
| R&A/USGA **Equipment Rules** (2020 v2) | ✅ downloaded | ✅ **read** — pp. 11, 54, 69 cited |
| R&A/USGA **COR Protocol** | ✅ downloaded | ✅ **read** — p. 4 cited |
| R&A/USGA **MOI Protocol** | ✅ downloaded | ✅ **read** — p. 3 cited |
| R&A/USGA **Ball Weight & Size Protocol** | ✅ downloaded | ✅ **read** — p. 3 cited |
| R&A/USGA **Initial Velocity Protocol** | ✅ downloaded | ✅ **read** — p. 3 cited |

Primary studies reached **only through Penner's review**, not read directly. Where a number
above is attributed to one of these, it is quoted as Penner reports it, with Penner's page
given — not cited as if the original were read:

- **Gobush (1996a)** — the `μ` measurements (via Penner p.149).
- **Chou et al (1994)**, **Gobush (1990)** — the COR figures (via Penner pp.144–145).

Further literature located but not accessed (candidates if the estimates above need closing):

- "Ekstrom EA (1998) Experimental determination of golf ball coefficients of sliding friction",
  *Science and Golf III*, ch. 64, pp. 510–518 — cited by Arakawa; the dedicated clubface
  sliding-friction study, and the best candidate for a face-specific `μ`.
- "An analytical model for ball-barrier impact: Part 2: A model for oblique impact",
  *Science and Golf II*, DOI 10.4324/9780203474709-54.
- "Contact forces, coefficient of restitution, and spin rate of golf ball impact",
  *Science and Golf II*, DOI 10.4324/9780203474709-51.

---

## 11. A correction to an existing constant in this repo

✅ `ball_flight.py:9` currently reads:

```python
BALL_MASS = 0.0459        # kg, USGA/R&A minimum golf ball mass spec (45.93 g)
```

The **value is right but the descriptor is wrong**: 45.93 g is the **maximum** permitted mass.
The Equipment Rules state "The weight of the ball must not be greater than 1.620 ounces
avoirdupois (45.93 g)… **There is no minimum weight** thus a ball can be as light as the
manufacturer desires" (Part 4 §2, p.69). It is the *diameter* that is a minimum (Part 4 §3).

Per the standing rule not to modify existing modules without approval, `ball_flight.py` is
**left untouched**; this is logged for a later, separately-approved fix.
