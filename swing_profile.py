from dataclasses import dataclass

# Sign conventions below assume a right-handed golfer facing the target
# (mirror all signs for a left-handed golfer). These are the same conventions
# used by TrackMan/GC-style launch monitors, chosen so downstream ball_flight.py
# math lines up with commonly published launch-monitor data for sanity-checking.

MIN_CLUBHEAD_SPEED, MAX_CLUBHEAD_SPEED = 40.0, 150.0   # mph, junior through tour/long-drive
MIN_ATTACK_ANGLE, MAX_ATTACK_ANGLE = -15.0, 10.0        # degrees
MIN_SWING_PATH, MAX_SWING_PATH = -20.0, 20.0            # degrees
MIN_FACE_ANGLE, MAX_FACE_ANGLE = -20.0, 20.0            # degrees
MIN_DYNAMIC_LOFT, MAX_DYNAMIC_LOFT = 0.0, 70.0          # degrees
# These bounds are generous sanity limits meant to catch obviously invalid data
# entry (e.g. a typo), not tightly calibrated per-club-type ranges like
# club_specification.py's CLUB_LENGTH_RANGES/LOFT_RANGES.


@dataclass
class SwingProfile:
    clubhead_speed: float   # mph
    attack_angle: float     # degrees; negative = descending (ball struck on the downswing), positive = ascending
    swing_path: float       # degrees; positive = in-to-out (path right of target line), negative = out-to-in
    face_angle: float       # degrees relative to target line at impact; positive = open (right of target), negative = closed (left of target)
    dynamic_loft: float     # degrees; the club's effective loft at the moment of impact (accounts for shaft lean), distinct from the static club_type loft

    def __post_init__(self):
        for field_name, value, min_value, max_value, unit in [
            ("clubhead_speed", self.clubhead_speed, MIN_CLUBHEAD_SPEED, MAX_CLUBHEAD_SPEED, "mph"),
            ("attack_angle", self.attack_angle, MIN_ATTACK_ANGLE, MAX_ATTACK_ANGLE, "degrees"),
            ("swing_path", self.swing_path, MIN_SWING_PATH, MAX_SWING_PATH, "degrees"),
            ("face_angle", self.face_angle, MIN_FACE_ANGLE, MAX_FACE_ANGLE, "degrees"),
            ("dynamic_loft", self.dynamic_loft, MIN_DYNAMIC_LOFT, MAX_DYNAMIC_LOFT, "degrees"),
        ]:
            if not (min_value <= value <= max_value):
                raise ValueError(
                    f"{field_name} {value} is outside realistic range "
                    f"({min_value}-{max_value} {unit})"
                )
