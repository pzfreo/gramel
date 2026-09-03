"""
Tests for gramil.case.parameters.

Covers the sandwich case's Z-stack arithmetic, which is what the thin-foam
variant changes. Parameter-level only — no geometry is built, so these stay
fast.
"""

from gramil.case.parameters import SandwichCaseParams


def test_default_is_five_millimetre_foam() -> None:
    p = SandwichCaseParams()
    assert p.foam_thickness == 5.0
    assert p.cavity_z_clearance == 1.0


def test_thin_foam_preset_values() -> None:
    """1 mm foam, and the build allowance must go to zero with it — 1 mm of
    slack is half a foam layer at this thickness and would leave the tool
    loose."""
    p = SandwichCaseParams.thin_foam()
    assert p.foam_thickness == 1.0
    assert p.cavity_z_clearance == 0.0


def test_thin_foam_preset_accepts_overrides() -> None:
    p = SandwichCaseParams.thin_foam(spare_blades=4)
    assert p.spare_blades == 4
    assert p.foam_thickness == 1.0


def test_thin_foam_stack_is_zero_slack_over_the_insert() -> None:
    """foam + insert + foam must exactly fill the cavity away from the tool,
    so the insert is located rather than rattling."""
    p = SandwichCaseParams.thin_foam()
    stack_h = 10.5  # insert thickness for the default cutter (tool 11.0 − tool_proud 0.5)
    cavity = stack_h + 2 * p.foam_thickness + p.cavity_z_clearance
    assert cavity == stack_h + 2 * p.foam_thickness


def test_thin_foam_preloads_the_foam_over_the_tool() -> None:
    """Where the tool stands proud of the insert it must squeeze the foam —
    that squeeze is the whole point of ``tool_proud``."""
    p = SandwichCaseParams.thin_foam()
    stack_h = 10.5
    tool_z = stack_h + p.tool_proud
    cavity = stack_h + 2 * p.foam_thickness + p.cavity_z_clearance
    squeeze = (tool_z + 2 * p.foam_thickness) - cavity
    assert squeeze == p.tool_proud
    # Per side, as a fraction of one foam layer: firm, not crushed.
    assert 0.1 <= (squeeze / 2) / p.foam_thickness <= 0.35
