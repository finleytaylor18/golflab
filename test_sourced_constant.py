"""Tests for the provenance wrapper.

Standing rule 3 says no constant may exist without a value, a unit and a
citation. These tests check that the rule is enforced by the type rather than
by anyone remembering it.
"""

import pytest

from sourced_constant import SourcedConstant


def test_a_sourced_constant_behaves_as_a_plain_float():
    """Proves provenance costs nothing at the point of use: the physics code
    can multiply and divide these directly, with no unwrapping, so the
    equations stay readable against the derivations in the docs.
    """
    mass = SourcedConstant(0.04593, "kg", "Equipment Rules Part 4 section 2, p.69")

    assert mass == 0.04593
    assert mass * 2 == pytest.approx(0.09186)
    assert float(mass) == 0.04593
    assert isinstance(mass, float)


def test_a_constant_without_a_citation_is_refused():
    """Proves an unsourced number cannot enter the model at all. This is the
    structural half of standing rule 3 -- it fails at construction, not at
    review time.
    """
    with pytest.raises(ValueError, match="citation"):
        SourcedConstant(0.83, "dimensionless", "")


def test_a_constant_without_a_unit_is_refused():
    """Proves a bare number is refused too. A value of 45.93 means nothing
    until it says grams, and the g/kg confusion is exactly the class of error
    this project cannot afford.
    """
    with pytest.raises(ValueError, match="unit"):
        SourcedConstant(45.93, "", "Equipment Rules Part 4 section 2, p.69")


def test_an_estimate_announces_itself():
    """Proves estimates are visibly distinct from measurements wherever they
    are printed. The ball's moment of inertia is currently the only one, and
    a reader must never mistake it for a sourced value.
    """
    estimate = SourcedConstant(0.4, "dimensionless", "ESTIMATE -- uniform sphere",
                               is_estimate=True)
    measured = SourcedConstant(0.78, "dimensionless", "Penner 2003, p.144")

    assert estimate.is_estimate and not measured.is_estimate
    assert "ESTIMATE" in estimate.provenance()
    assert "ESTIMATE" in repr(estimate)
    assert "ESTIMATE" not in measured.provenance()


def test_provenance_reports_value_unit_and_source_together():
    """Proves the question "where did this number come from?" is answerable
    from the number itself, without a lookup table that can drift out of date.
    """
    cor = SourcedConstant(0.78, "dimensionless", "Penner 2003, p.144 (Chou et al 1994)",
                          note="measured at 45 m/s")
    line = cor.provenance()

    assert "0.78" in line and "dimensionless" in line
    assert "Penner 2003, p.144" in line and "45 m/s" in line
