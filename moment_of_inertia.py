from club_specification import ClubSpecification

GRIP_CENTER_FROM_BUTT = 5.0  # inches, assumed grip midpoint


def calculate_moi(club: ClubSpecification) -> float:
    head_distance = club.club_length
    shaft_distance = club.shaft_length / 2
    grip_distance = GRIP_CENTER_FROM_BUTT

    head_moi = club.head_mass * head_distance ** 2
    shaft_moi = club.shaft_mass * shaft_distance ** 2
    grip_moi = club.grip_mass * grip_distance ** 2

    total_moi = head_moi + shaft_moi + grip_moi
    return total_moi


if __name__ == "__main__":
    driver = ClubSpecification(
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
    )
    moi = calculate_moi(driver)
    print(f"Total MOI: {moi:.2f} gram-inches^2")