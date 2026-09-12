"""A float that remembers where it came from.

Every physical constant in the impact model carries its unit and its citation
alongside its value, so a later provenance feature can answer "where did 0.38
come from?" without a separate lookup table.

Subclassing float is deliberate: `ball.mass_kg * 2` works with no `.value`
unwrapping, which keeps the physics code readable against the derivations in
docs/impact_model.md. Arithmetic returns a plain float, which is correct --
the provenance of `m * v**2` is not the provenance of `m`, and pretending
otherwise would be worse than losing it.
"""


class SourcedConstant(float):
    unit: str
    citation: str
    note: str
    is_estimate: bool

    def __new__(cls, value: float, unit: str, citation: str, note: str = "",
                is_estimate: bool = False):
        if not unit:
            raise ValueError("a sourced constant must state its unit")
        if not citation:
            raise ValueError(
                f"a sourced constant must state its citation (value={value} {unit}); "
                "unsourced numbers are not permitted in the impact model"
            )
        instance = super().__new__(cls, value)
        instance.unit = unit
        instance.citation = citation
        instance.note = note
        instance.is_estimate = is_estimate
        return instance

    def provenance(self) -> str:
        """One-line human-readable description, for docs and diagnostics."""
        prefix = "ESTIMATE " if self.is_estimate else ""
        line = f"{prefix}{float(self)} {self.unit} [{self.citation}]"
        return f"{line} -- {self.note}" if self.note else line

    def __repr__(self) -> str:
        kind = "ESTIMATE " if self.is_estimate else ""
        return f"SourcedConstant({kind}{float(self)}, {self.unit!r}, {self.citation!r})"
