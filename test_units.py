"""Tests for the SI unit boundary.

Unit conversions look too trivial to test until you remember that a g*cm^2
value used as kg*m^2 is wrong by a factor of ten million and produces a
completely plausible-looking clubhead. These tests exist for that one error.
"""

import math

import pytest

import units


ROUND_TRIPS = [
    (units.grams_to_kg, units.kg_to_grams, 200.0),
    (units.mm_to_m, units.m_to_mm, 42.67),
    (units.g_cm2_to_kg_m2, units.kg_m2_to_g_cm2, 5900.0),
    (units.mph_to_mps, units.mps_to_mph, 112.5),
    (units.degrees_to_radians, units.radians_to_degrees, 10.5),
    (units.rpm_to_rad_s, units.rad_s_to_rpm, 2700.0),
]


@pytest.mark.parametrize("forward,back,value", ROUND_TRIPS)
def test_every_conversion_round_trips(forward, back, value):
    """Proves each pair is a true inverse, so a value can cross the boundary
    into the physics core and back out to a display without drifting.
    """
    assert back(forward(value)) == pytest.approx(value, rel=1e-12)


def test_the_inertia_conversion_is_ten_million():
    """Proves the single most dangerous factor in the project is right.

    g*cm^2 -> kg*m^2 is (1e-3 kg)(1e-2 m)^2 = 1e-7. Get it wrong and the head
    is either a feather or a boulder, yet the inertia tensor still passes
    symmetry, positive-definiteness and the triangle inequality untouched --
    it is only the conformance check that would catch it.
    """
    assert units.g_cm2_to_kg_m2(1.0) == 1.0e-7
    assert units.g_cm2_to_kg_m2(5900.0) == pytest.approx(5.9e-4, rel=1e-15)
    assert units.kg_m2_to_g_cm2(4.5e-4) == pytest.approx(4500.0, rel=1e-12)


def test_known_conversions_hit_their_published_values():
    """Proves the constants themselves, against values that can be checked
    against a reference rather than against our own arithmetic.
    """
    assert units.grams_to_kg(45.93) == pytest.approx(0.04593, rel=1e-15)
    assert units.mm_to_m(42.67) == pytest.approx(0.04267, rel=1e-15)
    # 1 mile = 1609.344 m exactly, so 1 mph = 0.44704 m/s exactly.
    assert units.mph_to_mps(1.0) == 0.44704
    # The COR protocol's 133 ft/s test speed, p.4.
    assert units.mph_to_mps(133.0 * 3600.0 / 5280.0) == pytest.approx(40.538, abs=1e-3)
    assert units.degrees_to_radians(180.0) == pytest.approx(math.pi, rel=1e-15)
    assert units.rpm_to_rad_s(60.0) == pytest.approx(2.0 * math.pi, rel=1e-15)


def test_conversions_preserve_sign_and_zero():
    """Proves nothing quietly takes an absolute value. Negative coordinates
    are ordinary here -- the CG depth is a negative z, and a toe strike is a
    negative x.
    """
    for forward, _, _ in ROUND_TRIPS:
        assert forward(0.0) == 0.0
        assert forward(-3.0) < 0.0
