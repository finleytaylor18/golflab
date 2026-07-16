import pytest
from club_specification import (
    ClubSpecification,
    ClubType,
    CLUB_LENGTH_RANGES,
    LOFT_RANGES,
    CLUB_TYPE_LABELS,
    CLUB_TYPE_CATEGORIES,
)


def test_valid_club_specification_is_created_successfully():
    club = ClubSpecification(
        club_type=ClubType.DRIVER,
        head_mass=200,
        shaft_mass=65,
        shaft_length=45.5,
        grip_mass=50,
        club_length=45.5,
        loft=10.5,
        lie_angle=58.0,
    )
    assert club.head_mass == 200


def test_club_length_out_of_range_raises_value_error():
    with pytest.raises(ValueError):
        ClubSpecification(
            club_type=ClubType.DRIVER,
            head_mass=200,
            shaft_mass=65,
            shaft_length=45.5,
            grip_mass=50,
            club_length=3443,
            loft=10.5,
            lie_angle=58.0,
        )


def test_head_mass_out_of_range_raises_value_error():
    with pytest.raises(ValueError):
        ClubSpecification(
            club_type=ClubType.DRIVER,
            head_mass=5555,
            shaft_mass=65,
            shaft_length=45.5,
            grip_mass=50,
            club_length=45.5,
            loft=10.5,
            lie_angle=58.0,
        )


def test_valid_specific_iron_is_created_successfully():
    club = ClubSpecification(
        club_type=ClubType.IRON_7,
        head_mass=260,
        shaft_mass=110,
        shaft_length=36.5,
        grip_mass=50,
        club_length=36.5,
        loft=38.0,
        lie_angle=62.0,
    )
    assert club.club_type == ClubType.IRON_7


def test_another_irons_length_raises_value_error_for_this_iron():
    # 39.0 inches is a valid 2-iron length, but well outside 7-iron's range --
    # confirms each iron number is validated against its own slice, not the
    # old shared "iron" bucket.
    with pytest.raises(ValueError):
        ClubSpecification(
            club_type=ClubType.IRON_7,
            head_mass=260,
            shaft_mass=110,
            shaft_length=39.0,
            grip_mass=50,
            club_length=39.0,
            loft=38.0,
            lie_angle=62.0,
        )


def test_valid_wedge_by_specific_loft_is_created_successfully():
    club = ClubSpecification(
        club_type=ClubType.WEDGE_54,
        head_mass=295,
        shaft_mass=115,
        shaft_length=35.5,
        grip_mass=50,
        club_length=35.5,
        loft=54.0,
        lie_angle=64.0,
    )
    assert club.club_type == ClubType.WEDGE_54


def test_wrong_wedge_loft_raises_value_error():
    # 46 degrees is a valid loft for WEDGE_46, but WEDGE_54 should reject it --
    # wedges are identified by their specific loft, not a shared "wedge" range.
    with pytest.raises(ValueError):
        ClubSpecification(
            club_type=ClubType.WEDGE_54,
            head_mass=295,
            shaft_mass=115,
            shaft_length=35.5,
            grip_mass=50,
            club_length=35.5,
            loft=46.0,
            lie_angle=64.0,
        )


def test_every_club_type_has_a_length_range_a_loft_range_and_a_label():
    for club_type in ClubType:
        assert club_type in CLUB_LENGTH_RANGES
        assert club_type in LOFT_RANGES
        assert club_type in CLUB_TYPE_LABELS


def test_club_type_categories_cover_every_club_type_exactly_once():
    categorized = [club_type for members in CLUB_TYPE_CATEGORIES.values() for club_type in members]
    assert sorted(categorized, key=lambda t: t.value) == sorted(ClubType, key=lambda t: t.value)