from club_specification import ClubSpecification

FULCRUM_DISTANCE_FROM_BUTT = 14.0  # inches, industry standard
GRIP_CENTER_FROM_BUTT = 5.0        # inches, assumed grip midpoint

A0_REFERENCE_MOMENT = 3401.9   # gram-inches, calibrated from industry D0 reference example
POINTS_PER_INCREMENT = 49.61   # gram-inches per swing weight point (verified: 1.75 oz-in/point)


def calculate_moment(club: ClubSpecification) -> float:
    head_distance = club.club_length - FULCRUM_DISTANCE_FROM_BUTT
    shaft_distance = (club.shaft_length / 2) - FULCRUM_DISTANCE_FROM_BUTT
    grip_distance = GRIP_CENTER_FROM_BUTT - FULCRUM_DISTANCE_FROM_BUTT

    head_moment = club.head_mass * head_distance
    shaft_moment = club.shaft_mass * shaft_distance
    grip_moment = club.grip_mass * grip_distance

    total_moment = head_moment + shaft_moment + grip_moment
    return total_moment


def moment_to_swing_weight(moment: float) -> str:
    points_from_a0 = (moment - A0_REFERENCE_MOMENT) / POINTS_PER_INCREMENT

    letters = "ABCDEFGHIJ"
    letter_index = int(points_from_a0 // 10)
    number = int(points_from_a0 % 10)

    letter = letters[letter_index]
    return f"{letter}{number}"


if __name__ == "__main__":
    driver = ClubSpecification(
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )
    moment = calculate_moment(driver)
    swing_weight = moment_to_swing_weight(moment)
    print(f"Total moment: {moment:.2f} gram-inches")
    print(f"Swing weight: {swing_weight}")