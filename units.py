"""The unit boundary for the impact model.

The impact core is SI throughout: kg, m, kg*m^2, m/s, rad, rad/s. Industry
units (g, mm, g*cm^2, mph, degrees, rpm) belong at the input and display
edges only, and this module is the only sanctioned way to cross between them.

The conversion that matters most is inertia: a g*cm^2 value passed where
kg*m^2 is expected is wrong by a factor of 10^7 and looks entirely plausible,
so it will pass symmetry, positive-definiteness and triangle-inequality
checks untouched. head_mass_properties.conformance_report() is the backstop
for that specific mistake.
"""

import math

# Exact by definition
_GRAMS_PER_KG = 1000.0
_MM_PER_M = 1000.0
_MPH_TO_MPS = 0.44704          # 1 mile = 1609.344 m exactly, / 3600 s
_G_CM2_TO_KG_M2 = 1.0e-7       # (1e-3 kg) * (1e-2 m)^2
_SECONDS_PER_MINUTE = 60.0


# -- mass ---------------------------------------------------------------
def grams_to_kg(grams: float) -> float:
    return grams / _GRAMS_PER_KG


def kg_to_grams(kg: float) -> float:
    return kg * _GRAMS_PER_KG


# -- length -------------------------------------------------------------
def mm_to_m(mm: float) -> float:
    return mm / _MM_PER_M


def m_to_mm(metres: float) -> float:
    return metres * _MM_PER_M


# -- moment of inertia --------------------------------------------------
def g_cm2_to_kg_m2(g_cm2: float) -> float:
    return g_cm2 * _G_CM2_TO_KG_M2


def kg_m2_to_g_cm2(kg_m2: float) -> float:
    return kg_m2 / _G_CM2_TO_KG_M2


# -- speed --------------------------------------------------------------
def mph_to_mps(mph: float) -> float:
    return mph * _MPH_TO_MPS


def mps_to_mph(mps: float) -> float:
    return mps / _MPH_TO_MPS


# -- angle --------------------------------------------------------------
def degrees_to_radians(degrees: float) -> float:
    return math.radians(degrees)


def radians_to_degrees(radians: float) -> float:
    return math.degrees(radians)


# -- angular velocity ---------------------------------------------------
def rpm_to_rad_s(rpm: float) -> float:
    return rpm * 2.0 * math.pi / _SECONDS_PER_MINUTE


def rad_s_to_rpm(rad_s: float) -> float:
    return rad_s * _SECONDS_PER_MINUTE / (2.0 * math.pi)
