from club_specification import ClubSpecification

GRIP_CENTER_FROM_BUTT = 5.0  # inches, assumed grip midpoint


def calculate_balance_point(club: ClubSpecification) -> float:
    head_distance = club.club_length
    shaft_distance = club.shaft_length / 2
    grip_distance = GRIP_CENTER_FROM_BUTT

    total_moment = (
        club.head_mass * head_distance
        + club.shaft_mass * shaft_distance
        + club.grip_mass * grip_distance
    )
    total_mass = club.head_mass + club.shaft_mass + club.grip_mass

    return total_moment / total_mass


if __name__ == "__main__":
    driver = ClubSpecification(
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )
    balance_point = calculate_balance_point(driver)
    print(f"Balance point: {balance_point:.2f} inches from butt end")