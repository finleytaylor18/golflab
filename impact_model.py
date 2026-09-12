"""Rigid-body impulse-momentum solution of a single golf impact.

WHAT THIS DOES, IN PLAIN TERMS
------------------------------
Contact lasts under half a millisecond. Over that window the impulsive contact
force dwarfs gravity, aerodynamics and anything the shaft can transmit, so the
head is treated as a free rigid body and the whole problem becomes: find the
one impulse vector J that the face delivers to the ball. Everything the
launch monitor would report -- ball speed, launch angle, backspin, sidespin --
falls out of that single vector.

Two equations pin J down:

  Normal direction   Newton's restitution: the ball and face separate at e
                     times the speed they approached at.
  Tangential plane   Coulomb friction: the face grips the ball and stops it
                     sliding (STICK), or it cannot and slides at the friction
                     limit (SLIP).

We solve the stick case first, then check whether the friction it needed was
actually available. That ordering matters: it is the only way to find out
which regime you are in without assuming the answer.

THE K MATRIX
------------
The link between "impulse applied" and "relative velocity changed at the
contact point" is a 3x3 matrix, and it is the whole of the mechanics:

    delta_u_rel = K J,   K = (1/m + 1/M) 1
                           - [r_ball]x I_ball^-1 [r_ball]x
                           - [r_head]x I_head^-1 [r_head]x

Read it as three compliances in series: the ball's mass, the head's mass, and
the rotational give of each body about the contact point. An off-centre strike
enters only through r_head, and that single term produces both the ball speed
loss and the gear-effect spin. They are not two effects -- they are one.

FRAME
-----
All the mechanics happens in the head frame (x heel, y crown, z outward face
normal; see head_mass_properties for why x points at the HEEL, and note that
docs/impact_architecture.md section 1.1 originally had it pointing at the toe,
which is a left-handed triad). That frame is used because it is the one the
inertia tensor and the strike point are given in, and in it the face normal is
simply z-hat. Results are rotated to the lab frame at the end:

    X down the target line, Y to the golfer's LEFT, Z up.

Lab +Y being "left" is not a choice, it is forced: with X forward and Z up, a
right-handed frame puts Y on the left. Golfers talk in lefts and rights, so
every reported direction flips that sign back at the output boundary, and
each one says so where it is defined.

v1 assumes a square face and no club path, so head frame and lab frame differ
by the loft angle alone.
"""

import math
from dataclasses import dataclass

import numpy as np

from ball_properties import BallProperties
from head_mass_properties import HeadMassProperties
from units import mps_to_mph, rad_s_to_rpm, radians_to_degrees

# Below this, two floats are the same number as far as the physics is
# concerned. Used for "is the tangential velocity zero?" style questions,
# where the alternative is dividing by noise.
_NEGLIGIBLE = 1e-12


def skew(v: np.ndarray) -> np.ndarray:
    """Cross-product matrix: skew(a) @ b == np.cross(a, b)."""
    x, y, z = v
    return np.array([[0.0, -z, y],
                     [z, 0.0, -x],
                     [-y, x, 0.0]])


def head_to_lab_rotation(loft_rad: float) -> np.ndarray:
    """Rotation taking a head-frame vector to lab-frame components.

    Columns are the lab-frame images of the head axes. Tilting the face back
    by the loft puts the face normal above the target line, and the head's
    crown axis leaning back by the same angle.

    Sanity check that this is the right matrix: a head travelling with its
    face square must move horizontally down the target line, and
    solve_impact() relies on exactly that (see the test suite).
    """
    s, c = math.sin(loft_rad), math.cos(loft_rad)
    return np.array([[0.0, -s, c],
                     [1.0, 0.0, 0.0],
                     [0.0, c, s]])


@dataclass(frozen=True)
class SwingConditions:
    """How the head arrives. v1: square face, no path, no head rotation.

    head_speed_mps is the speed OF THE HEAD CENTRE OF GRAVITY. With no
    pre-impact head rotation (assumption 2) every point on the head shares
    that velocity, so the distinction is currently moot -- but it is named
    explicitly because relaxing assumption 2 is the first thing a later
    version will do, and then it stops being moot.
    """

    head_speed_mps: float
    loft_rad: float

    def __post_init__(self):
        if not math.isfinite(self.head_speed_mps) or self.head_speed_mps <= 0:
            raise ValueError(
                f"head_speed_mps must be positive and finite (got {self.head_speed_mps})"
            )
        if not math.isfinite(self.loft_rad) or not 0.0 <= self.loft_rad < math.pi / 2:
            raise ValueError(
                f"loft_rad must lie in [0, pi/2) radians (got {self.loft_rad})"
            )


@dataclass(frozen=True)
class ImpactResult:
    """Everything the impact produced, in SI, plus the diagnostics.

    The diagnostics are not decoration. `is_rolling` and `required_friction`
    tell you whether the spin number came from a grip or from a slide, and a
    slide means the answer depends entirely on a friction coefficient that is
    itself speed-dependent and single-valued only by assumption.
    """

    ball_velocity_lab_mps: np.ndarray
    ball_spin_lab_rad_s: np.ndarray
    head_velocity_after_lab_mps: np.ndarray
    head_spin_after_lab_rad_s: np.ndarray
    impulse_head_frame_ns: np.ndarray
    effective_mass_kg: float
    is_rolling: bool
    required_friction: float
    energy_before_j: float
    energy_after_j: float

    @property
    def ball_speed_mps(self) -> float:
        return float(np.linalg.norm(self.ball_velocity_lab_mps))

    @property
    def launch_angle_rad(self) -> float:
        """Vertical launch, positive upwards."""
        vx, vy, vz = self.ball_velocity_lab_mps
        return math.atan2(vz, math.hypot(vx, vy))

    @property
    def horizontal_launch_rad(self) -> float:
        """Starting direction, positive to the RIGHT of the target line.

        Lab +Y is the golfer's left, hence the sign flip: a right-handed
        golfer talks about pushes and pulls, not about +Y.
        """
        vx, vy, _ = self.ball_velocity_lab_mps
        return math.atan2(-vy, vx)

    @property
    def backspin_rad_s(self) -> float:
        """Positive means genuine backspin (the lift-producing direction)."""
        return -float(self.ball_spin_lab_rad_s[1])

    @property
    def sidespin_rad_s(self) -> float:
        """Positive means the ball curves to the RIGHT (a fade for a righty)."""
        return -float(self.ball_spin_lab_rad_s[2])

    @property
    def energy_lost_j(self) -> float:
        return self.energy_before_j - self.energy_after_j

    def to_display(self, head_speed_mps: float) -> dict:
        """Convert to the units a golfer or a launch monitor uses."""
        return {
            "ball_speed_mph": mps_to_mph(self.ball_speed_mps),
            "launch_angle_deg": radians_to_degrees(self.launch_angle_rad),
            "horizontal_launch_deg": radians_to_degrees(self.horizontal_launch_rad),
            "backspin_rpm": rad_s_to_rpm(self.backspin_rad_s),
            "sidespin_rpm": rad_s_to_rpm(self.sidespin_rad_s),
            "smash_factor": self.ball_speed_mps / head_speed_mps,
            "effective_mass_g": self.effective_mass_kg * 1000.0,
            "contact": "rolling (face gripped)" if self.is_rolling else "sliding",
            "required_friction": self.required_friction,
            "energy_lost_j": self.energy_lost_j,
        }


def collision_matrix(head: HeadMassProperties, ball: BallProperties,
                     strike_m: np.ndarray) -> np.ndarray:
    """The K matrix in head-frame coordinates, for a strike at `strike_m`.

    K maps an impulse at the contact point to the change in relative velocity
    there. It is symmetric and positive-definite for any real pair of bodies,
    which is why it can always be inverted for the stick solution.
    """
    strike = np.asarray(strike_m, dtype=float)
    contact = np.array([strike[0], strike[1], 0.0])   # on the face plane

    r_head = contact - head.cg_m                       # CG -> contact
    r_ball = np.array([0.0, 0.0, -ball.radius_m])      # ball centre -> contact

    inv_head = np.linalg.inv(head.inertia_about_cg)
    inv_ball = np.eye(3) / ball.inertia_kg_m2          # sphere: isotropic

    s_head, s_ball = skew(r_head), skew(r_ball)

    return ((1.0 / ball.mass_kg + 1.0 / head.mass_kg) * np.eye(3)
            - s_ball @ inv_ball @ s_ball
            - s_head @ inv_head @ s_head)


def effective_mass(head: HeadMassProperties, strike_m: np.ndarray) -> float:
    """Mass the ball 'feels' from the head alone, along the face normal.

    1 / M_eff = n_hat^T K_head n_hat, where K_head is the head's share of the
    collision matrix. Equals the full head mass exactly at the sweet spot and
    falls off everywhere else -- that fall-off IS the forgiveness map.
    """
    strike = np.asarray(strike_m, dtype=float)
    contact = np.array([strike[0], strike[1], 0.0])
    r_head = contact - head.cg_m

    inv_head = np.linalg.inv(head.inertia_about_cg)
    s_head = skew(r_head)
    k_head = (1.0 / head.mass_kg) * np.eye(3) - s_head @ inv_head @ s_head

    normal = np.array([0.0, 0.0, 1.0])
    return 1.0 / float(normal @ k_head @ normal)


def solve_impact(head: HeadMassProperties, ball: BallProperties,
                 conditions: SwingConditions,
                 strike_m: np.ndarray) -> ImpactResult:
    """Solve one impact and return the ball's launch conditions.

    Pure: no I/O, no mutation of its arguments, same inputs -> same outputs.
    """
    strike = np.asarray(strike_m, dtype=float)
    if strike.shape not in {(2,), (3,)}:
        raise ValueError(f"strike_m must be a 2- or 3-vector on the face (got {strike.shape})")
    contact = np.array([strike[0], strike[1], 0.0])

    m, M = ball.mass_kg, head.mass_kg
    e, mu = ball.cor, ball.friction_coefficient
    normal = np.array([0.0, 0.0, 1.0])

    r_head = contact - head.cg_m
    r_ball = np.array([0.0, 0.0, -ball.radius_m])

    inv_head = np.linalg.inv(head.inertia_about_cg)
    inv_ball = np.eye(3) / ball.inertia_kg_m2

    # Head velocity in the head frame. The head travels horizontally down the
    # target line; seen from the lofted head, that motion is partly along the
    # face normal (which compresses the ball) and partly down the face (which
    # is what generates backspin).
    u = conditions.head_speed_mps
    theta = conditions.loft_rad
    v_head = u * np.array([0.0, -math.sin(theta), math.cos(theta)])
    w_head = np.zeros(3)                   # assumption 2: no pre-impact rotation

    v_ball = np.zeros(3)                   # assumption 10: ball at rest
    w_ball = np.zeros(3)

    # Relative velocity of the ball's contact point with respect to the head's.
    u_rel = ((v_ball + np.cross(w_ball, r_ball))
             - (v_head + np.cross(w_head, r_head)))
    u_n = float(u_rel @ normal)
    if u_n >= 0.0:
        raise ValueError(
            f"the head is not approaching the ball along the face normal "
            f"(closing speed {u_n:+.3f} m/s); check the loft and speed"
        )

    k = collision_matrix(head, ball, strike)

    # --- STICK trial ------------------------------------------------------
    # Ask for the impulse that both satisfies restitution normally AND kills
    # all tangential sliding. Whether friction can actually deliver it is the
    # next question, not this one.
    target = np.array([-u_rel[0], -u_rel[1], -(1.0 + e) * u_n])
    impulse = np.linalg.solve(k, target)

    normal_impulse = float(impulse[2])
    tangential_impulse = float(math.hypot(impulse[0], impulse[1]))
    required_friction = tangential_impulse / normal_impulse
    is_rolling = required_friction <= mu

    # --- SLIP branch ------------------------------------------------------
    if not is_rolling:
        # Friction runs out. The face slides under the ball, and the
        # tangential impulse saturates at mu * J_n, directed against the
        # sliding. v1 holds that sliding direction fixed through contact --
        # a standard approximation, exact in the planar case and very close
        # in 3D unless the slide direction swings hard mid-contact.
        u_t = np.array([u_rel[0], u_rel[1], 0.0])
        speed_t = float(np.linalg.norm(u_t))
        if speed_t <= _NEGLIGIBLE:
            raise ValueError("sliding branch reached with no tangential motion")
        slide_dir = u_t / speed_t

        direction = normal - mu * slide_dir
        denominator = float(normal @ k @ direction)
        normal_impulse = -(1.0 + e) * u_n / denominator
        impulse = normal_impulse * direction

    # --- Apply the impulse ------------------------------------------------
    # The ball takes +J, the head takes -J. That is Newton's third law, and it
    # is also what makes momentum conservation a real test rather than a
    # tautology: nothing here imposes conservation, it emerges.
    v_ball_after = v_ball + impulse / m
    w_ball_after = w_ball + inv_ball @ np.cross(r_ball, impulse)
    v_head_after = v_head - impulse / M
    w_head_after = w_head - inv_head @ np.cross(r_head, impulse)

    def kinetic_energy(vb, wb, vh, wh):
        return (0.5 * m * float(vb @ vb)
                + 0.5 * ball.inertia_kg_m2 * float(wb @ wb)
                + 0.5 * M * float(vh @ vh)
                + 0.5 * float(wh @ head.inertia_about_cg @ wh))

    energy_before = kinetic_energy(v_ball, w_ball, v_head, w_head)
    energy_after = kinetic_energy(v_ball_after, w_ball_after, v_head_after, w_head_after)

    rotation = head_to_lab_rotation(theta)

    return ImpactResult(
        ball_velocity_lab_mps=rotation @ v_ball_after,
        ball_spin_lab_rad_s=rotation @ w_ball_after,
        head_velocity_after_lab_mps=rotation @ v_head_after,
        head_spin_after_lab_rad_s=rotation @ w_head_after,
        impulse_head_frame_ns=impulse,
        effective_mass_kg=effective_mass(head, strike),
        is_rolling=is_rolling,
        required_friction=required_friction,
        energy_before_j=energy_before,
        energy_after_j=energy_after,
    )
