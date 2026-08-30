"""
ISO 286 limits-and-fits — IT grade values + fundamental deviations.

Used to compute the actual upper/lower deviations of toleranced
dimensions (e.g. ``⌀8.0 H7``, ``⌀8.0 g6``) so the model can quote
worst-case clearance numbers, generate dim callouts, and validate
that bore/shaft pairs actually clear.

Scoped to what this project needs: nominal diameters from 1 mm to 30 mm,
hole grades ``H7`` and ``H8``, shaft grade ``g6``. Extend the tables
below as new fits appear.

Reference: ISO 286-1:2010 tables.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# IT grade values (µm) per nominal-diameter range, ISO 286-1 Table 1.
# ---------------------------------------------------------------------------

# Each entry: (max_nominal_mm, {grade: tolerance_µm}).
# Use the FIRST entry whose max is strictly greater than the nominal.
_IT_TABLE: list[tuple[float, dict[str, int]]] = [
    # ≤3 mm
    (3.0, {"IT6": 6, "IT7": 10, "IT8": 14}),
    # 3 < nominal ≤ 6
    (6.0, {"IT6": 8, "IT7": 12, "IT8": 18}),
    # 6 < nominal ≤ 10
    (10.0, {"IT6": 9, "IT7": 15, "IT8": 22}),
    # 10 < nominal ≤ 18
    (18.0, {"IT6": 11, "IT7": 18, "IT8": 27}),
    # 18 < nominal ≤ 30
    (30.0, {"IT6": 13, "IT7": 21, "IT8": 33}),
]


def it_tolerance_um(nominal_mm: float, grade: str) -> int:
    """Return the IT grade tolerance in micrometres for a given nominal diameter.

    Raises ValueError for nominal diameters outside the supported range or
    for grades not in the table.
    """
    for upper_bound, grades in _IT_TABLE:
        if nominal_mm <= upper_bound:
            if grade not in grades:
                raise ValueError(
                    f"Unsupported IT grade {grade!r}. Known: {sorted(grades)}."
                )
            return grades[grade]
    raise ValueError(
        f"Nominal diameter {nominal_mm} mm outside the supported range (≤30 mm). "
        "Extend gramil.tolerances._IT_TABLE."
    )


# ---------------------------------------------------------------------------
# Fundamental deviations (µm) per ISO 286-1 Table 4 (shafts) and Table 5 (holes).
# ---------------------------------------------------------------------------

# Shaft fundamental deviation es (upper limit) for position 'g'.
# Tabulated by nominal-diameter range, ISO 286-1 Table 4.
_SHAFT_G_ES_UM: list[tuple[float, int]] = [
    (3.0, -2),   # ≤3
    (6.0, -4),   # 3<≤6
    (10.0, -5),  # 6<≤10
    (18.0, -6),  # 10<≤18
    (30.0, -7),  # 18<≤30
]

# Hole fundamental deviation EI (lower limit) for position 'H' is always 0.
_HOLE_H_EI_UM = 0


@dataclass(frozen=True)
class FitLimits:
    """The two deviations of a toleranced feature (in mm)."""

    upper: float  # signed upper deviation, mm (e.g. +0.015 for H7 bore)
    lower: float  # signed lower deviation, mm (e.g. 0 for H7 bore)

    def min(self, nominal: float) -> float:
        return nominal + self.lower

    def max(self, nominal: float) -> float:
        return nominal + self.upper


def _shaft_g_es(nominal_mm: float) -> int:
    for upper_bound, es in _SHAFT_G_ES_UM:
        if nominal_mm <= upper_bound:
            return es
    raise ValueError(
        f"Nominal diameter {nominal_mm} mm outside supported g-shaft range."
    )


def limits(nominal_mm: float, fit_class: str) -> FitLimits:
    """Return the upper/lower deviations (in mm) of an ISO 286 fit class
    at a given nominal diameter.

    Supports ``H7``, ``H8`` (holes) and ``g6`` (shafts). Extend as needed.
    """
    grade = "IT" + fit_class[1:]  # 'H7' → 'IT7', 'g6' → 'IT6'
    it_um = it_tolerance_um(nominal_mm, grade)

    if fit_class[0] == "H":
        # Hole, lower deviation = 0, upper = +IT
        return FitLimits(upper=it_um / 1000, lower=_HOLE_H_EI_UM / 1000)
    if fit_class[0] == "g":
        # Shaft 'g', upper deviation es is negative, lower = es - IT
        es_um = _shaft_g_es(nominal_mm)
        return FitLimits(upper=es_um / 1000, lower=(es_um - it_um) / 1000)
    raise ValueError(
        f"Unsupported fit class {fit_class!r}. Known: H7, H8, g6 (extend tolerances.limits)."
    )


def worst_case_clearance(
    nominal_mm: float, *, hole_fit: str, shaft_fit: str
) -> float:
    """Maximum clearance between a hole and a shaft of given fit classes.

    = max(hole) − min(shaft). Both expressed at the same nominal diameter.
    """
    hole = limits(nominal_mm, hole_fit)
    shaft = limits(nominal_mm, shaft_fit)
    return hole.max(nominal_mm) - shaft.min(nominal_mm)


def best_case_clearance(
    nominal_mm: float, *, hole_fit: str, shaft_fit: str
) -> float:
    """Minimum clearance between a hole and a shaft of given fit classes.

    = min(hole) − max(shaft). Negative implies interference.
    """
    hole = limits(nominal_mm, hole_fit)
    shaft = limits(nominal_mm, shaft_fit)
    return hole.min(nominal_mm) - shaft.max(nominal_mm)


__all__ = [
    "FitLimits",
    "best_case_clearance",
    "it_tolerance_um",
    "limits",
    "worst_case_clearance",
]
