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
    """1 mm EVA foam. The build allowance and the tool preload must BOTH go to
    zero with it — 1 mm of slack is half a foam layer, and EVA is far too stiff
    to be squeezed by the closure magnets."""
    p = SandwichCaseParams.thin_foam()
    assert p.foam_thickness == 1.0
    assert p.cavity_z_clearance == 0.0
    assert p.tool_proud == 0.0


def test_thin_foam_preset_accepts_overrides() -> None:
    """Notably tool_proud, for anyone swapping EVA for soft PU foam."""
    p = SandwichCaseParams.thin_foam(tool_proud=0.5)
    assert p.tool_proud == 0.5
    assert p.foam_thickness == 1.0


def test_thin_foam_stack_is_exact_over_insert_and_tool() -> None:
    """foam + insert + foam must exactly fill the cavity both away from the
    tool (so the insert is located, not rattling) and over it (so the lid
    latches against stiff EVA rather than fighting it)."""
    p = SandwichCaseParams.thin_foam()
    tool_z = 11.0  # the cutter's Z envelope in case frame, set by shank.depth
    stack_h = tool_z - p.tool_proud
    cavity = stack_h + 2 * p.foam_thickness + p.cavity_z_clearance
    assert cavity == stack_h + 2 * p.foam_thickness
    assert cavity == tool_z + 2 * p.foam_thickness


def test_thin_foam_is_thinner_than_the_default_stack() -> None:
    default, thin = SandwichCaseParams(), SandwichCaseParams.thin_foam()
    tool_z = 11.0

    def closed_height(p: SandwichCaseParams) -> float:
        stack_h = tool_z - p.tool_proud
        cavity = stack_h + 2 * p.foam_thickness + p.cavity_z_clearance
        return cavity + 2 * p.shell.wall_thickness

    assert closed_height(default) == 25.5
    assert closed_height(thin) == 17.0
