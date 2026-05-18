"""
Tests for gramel.parameters.

Covers:
  - Default parameter set validates cleanly.
  - Prototype/production sliding-clearance switch.
  - Every cross-part derived value computes to a known number.
  - Every wall-thickness rule (§4.2.13, §4.2.14, §4.3.23, §4.3.24, §4.3.25)
    fires when its derivation drops below the spec minimum.
  - Field metadata (spec_ref, status, units, description) survives on
    representative fields.
"""

import pytest
from pydantic import ValidationError

from gramel.parameters import BladeParams, PurflingCutterParams

# ---------------------------------------------------------------------------
# Defaults and process configuration
# ---------------------------------------------------------------------------


def test_defaults_validate() -> None:
    """Default values must satisfy every spec rule — instantiation cannot fail."""
    PurflingCutterParams()


def test_prototype_flag_default_is_true() -> None:
    p = PurflingCutterParams()
    assert p.process.prototype is True


def test_prototype_sliding_clearance_is_fdm_value() -> None:
    p = PurflingCutterParams()
    assert p.process.sliding_clearance == 0.25


def test_production_mode_swaps_to_cnc_clearance() -> None:
    p = PurflingCutterParams(process={"prototype": False})
    assert p.process.sliding_clearance == 0.03


# ---------------------------------------------------------------------------
# Cross-part derived values (worked examples)
# ---------------------------------------------------------------------------


def test_stack_thickness() -> None:
    # 2 × blade.thickness (0.8) + spacer.thickness (1.5) = 3.1
    assert PurflingCutterParams().stack_thickness == pytest.approx(3.1)


def test_crossbore_diameter_prototype() -> None:
    # shaft.outer_diameter (10.0) + sliding_clearance (0.25) = 10.25
    assert PurflingCutterParams().crossbore_diameter == pytest.approx(10.25)


def test_crossbore_diameter_production() -> None:
    # 10.0 + 0.03 = 10.03
    p = PurflingCutterParams(process={"prototype": False})
    assert p.crossbore_diameter == pytest.approx(10.03)


def test_tapped_bore_drill_diameter() -> None:
    # M4 tap drill ≈ 3.3 mm
    assert PurflingCutterParams().tapped_bore_drill_diameter == pytest.approx(3.3)


def test_tapped_bore_position_from_top() -> None:
    # crossbore at 16 from top; gap 10 → tapped bore at 6 from top (closer to top)
    assert PurflingCutterParams().tapped_bore_position_from_top == pytest.approx(6.0)


def test_depth_lock_bore_depth() -> None:
    # shank.length (100) − crossbore_position_from_top (16) − small_clearance (1) = 83
    assert PurflingCutterParams().depth_lock_bore_depth == pytest.approx(83.0)


def test_contact_corner_width() -> None:
    # Slot width is in Z (across working face); corner width is in Z too.
    # (shank.depth (28) − relief_slot_width (6)) / 2 = 11.0
    assert PurflingCutterParams().contact_corner_width == pytest.approx(11.0)


# ---------------------------------------------------------------------------
# Derived wall thicknesses
# ---------------------------------------------------------------------------


def test_shaft_wall_around_slot_is_min_of_y_and_z() -> None:
    # Y: (10.0 − 4.5) / 2 = 2.75
    # Z: (10.0 − 5.5) / 2 = 2.25
    # min = 2.25
    assert PurflingCutterParams().shaft_wall_around_slot == pytest.approx(2.25)


def test_shaft_wall_around_end_tap() -> None:
    # 8.0 − 5.0 = 3.0
    assert PurflingCutterParams().shaft_wall_around_end_tap == pytest.approx(3.0)


def test_shank_wall_between_bores() -> None:
    # gap (10) − crossbore_radius (10.25/2) − tap_drill_radius (3.3/2) = 3.225
    assert PurflingCutterParams().shank_wall_between_bores == pytest.approx(3.225)


def test_shank_wall_around_crossbore_is_min_of_x_down_and_z() -> None:
    # Bore axis is along Y. Walls perpendicular to Y, excluding +X (toward tapped bore):
    #   X-down: crossbore_x (84) − crossbore_radius (5.125) = 78.875
    #   Z: depth/2 (14) − crossbore_radius (5.125) = 8.875
    # min = 8.875
    assert PurflingCutterParams().shank_wall_around_crossbore == pytest.approx(8.875)


def test_shank_wall_around_tapped_bore_is_min_of_x_up_and_z() -> None:
    # Walls perpendicular to Y, excluding −X (toward crossbore):
    #   X-up: tapped_bore_position_from_top (6) − tap_drill_radius (1.65) = 4.35
    #   Z: depth/2 (14) − tap_drill_radius (1.65) = 12.35
    # min = 4.35
    assert PurflingCutterParams().shank_wall_around_tapped_bore == pytest.approx(4.35)


# ---------------------------------------------------------------------------
# Wall validators fire on violations (one test per rule)
# ---------------------------------------------------------------------------


def test_violation_4213_blade_slot_too_wide_for_shaft() -> None:
    """§4.2.13 — widening the blade slot until shaft wall falls below 2 mm fails."""
    with pytest.raises(ValidationError, match=r"§4\.2\.13"):
        # Y-wall becomes (10 − 8) / 2 = 1.0 < 2.0 minimum
        PurflingCutterParams(shaft={"blade_slot_width": 8.0})


def test_violation_4214_tap_too_deep_for_end_to_slot() -> None:
    """§4.2.14 — making the grub-screw tap deep enough to thin the slot wall fails."""
    with pytest.raises(ValidationError, match=r"§4\.2\.14"):
        # Wall becomes 8.0 − 7.0 = 1.0; min for M3 = 1.5 × 1.5 = 2.25
        PurflingCutterParams(shaft={"end_tap_depth": 7.0})


def test_violation_4323_inter_bore_gap_too_small() -> None:
    """§4.3.23 — shrinking the inter-bore gap below the spec minimum fails."""
    with pytest.raises(ValidationError, match=r"§4\.3\.23"):
        # Wall = 7 − 5.125 − 1.65 = 0.225; min for M4 = max(2.0, 3.0) = 3.0
        PurflingCutterParams(shank={"crossbore_to_tapped_bore_gap": 7.0})


def test_violation_4324_shank_too_shallow_around_crossbore() -> None:
    """§4.3.24 — shrinking shank.depth (Z) until the Z-walls drop below the rule fails."""
    with pytest.raises(ValidationError, match=r"§4\.3\.24"):
        # Z-wall = 22/2 − 5.125 = 5.875; min = max(3.0, 0.6 × 10.25) = 6.15
        PurflingCutterParams(shank={"depth": 22.0})


def test_violation_4325_tapped_bore_too_close_to_top() -> None:
    """§4.3.25 — placing tapped bore too close to top of shank fails."""
    with pytest.raises(ValidationError, match=r"§4\.3\.25"):
        # crossbore at 12, gap 10 → tapped at 2; Z-above = 2 − 1.65 = 0.35
        # min for M4 = max(3.0, 3.0) = 3.0
        PurflingCutterParams(shank={"crossbore_position_from_top": 12.0})


# ---------------------------------------------------------------------------
# Field metadata preservation
# ---------------------------------------------------------------------------


def test_blade_thickness_carries_spec_metadata() -> None:
    field = BladeParams.model_fields["thickness"]
    extra = field.json_schema_extra
    assert isinstance(extra, dict)
    assert extra["spec_ref"] == "§4.1.1"
    assert extra["status"] == "ESTIMATE"
    assert extra["units"] == "mm"
    assert field.description == "Across the wide flat. Face the grub screw pushes against."


def test_every_numeric_field_has_status_tag() -> None:
    """Every numeric field across all sub-models should carry a status tag."""
    p = PurflingCutterParams()
    missing: list[str] = []
    for submodel_name in type(p).model_fields:
        submodel = getattr(p, submodel_name)
        for field_name, field_info in type(submodel).model_fields.items():
            if field_info.annotation not in (float, int):
                continue
            extra = field_info.json_schema_extra
            if not (isinstance(extra, dict) and extra.get("status")):
                missing.append(f"{submodel_name}.{field_name}")
    assert not missing, f"Numeric fields without status tag: {missing}"
