"""
Tests for gramel.parameters.

Covers:
  - Default parameter set validates cleanly (after measurement-driven
    relaxation of the wall-thickness rules).
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
# Cross-part derived values (worked examples — match the measured defaults)
# ---------------------------------------------------------------------------


def test_stack_thickness() -> None:
    # Hardware only: 4 × 0.75 + 2 × 0.7 = 4.4 (spacer not included)
    assert PurflingCutterParams().stack_thickness == pytest.approx(4.4)


def test_slot_spare() -> None:
    # slot(6.0) - hardware(4.4) = 1.6 available for spacer + grub advance
    assert PurflingCutterParams().slot_spare == pytest.approx(1.6)


def test_crossbore_diameter_prototype() -> None:
    # shaft.outer_diameter (7.9) + sliding_clearance (0.25) = 8.15
    assert PurflingCutterParams().crossbore_diameter == pytest.approx(8.15)


def test_crossbore_diameter_production() -> None:
    # 7.9 + 0.03 = 7.93
    p = PurflingCutterParams(process={"prototype": False})
    assert p.crossbore_diameter == pytest.approx(7.93)


def test_tapped_bore_drill_diameter() -> None:
    # M3 tap drill = 2.5 mm
    assert PurflingCutterParams().tapped_bore_drill_diameter == pytest.approx(2.5)


def test_tapped_bore_position_from_top() -> None:
    # crossbore at 14 from top; gap 9.5 → tapped bore at 4.5 from top
    assert PurflingCutterParams().tapped_bore_position_from_top == pytest.approx(4.5)


def test_depth_lock_bore_depth() -> None:
    # Bore extends up to the crossbore axis (no clearance — push rod must reach
    # the crossbore to press on the shaft).
    # shank.length (80) − crossbore_position_from_top (14) = 66
    assert PurflingCutterParams().depth_lock_bore_depth == pytest.approx(66.0)


def test_relief_slot_length() -> None:
    # Slot stops at the shaft level, doesn't continue above; length = 80 - 14 = 66
    assert PurflingCutterParams().relief_slot_length == pytest.approx(66.0)


def test_contact_corner_width() -> None:
    # (shank.depth (11) − relief_slot_width (2)) / 2 = 4.5
    assert PurflingCutterParams().contact_corner_width == pytest.approx(4.5)


# ---------------------------------------------------------------------------
# Derived wall thicknesses
# ---------------------------------------------------------------------------


def test_shaft_wall_around_slot() -> None:
    # Only the X-direction wall matters (slot is open in Y, end walls are §4.2.14).
    # (7.9 − blade_slot_length=5) / 2 = 1.45
    assert PurflingCutterParams().shaft_wall_around_slot == pytest.approx(1.45)


def test_shank_wall_between_bores() -> None:
    # gap (9.5) − crossbore_radius (8.15/2) − tap_drill_radius (2.5/2) = 4.175
    assert PurflingCutterParams().shank_wall_between_bores == pytest.approx(4.175)


def test_shank_wall_around_crossbore_is_min_of_x_down_and_z() -> None:
    # Bore axis along X. Walls perpendicular to X, excluding +Z (toward tapped bore):
    #   X-down: crossbore_x (66) − crossbore_radius (4.075) = 61.925
    #   Y either side: depth/2 (5.5) − crossbore_radius (4.075) = 1.425
    # min = 1.425
    assert PurflingCutterParams().shank_wall_around_crossbore == pytest.approx(1.425)


def test_shank_wall_around_tapped_bore_is_min_of_x_up_and_z() -> None:
    #   X-up: tapped_bore_position_from_top (4.5) − tap_drill_radius (1.25) = 3.25
    #   Y either side: depth/2 (5.5) − tap_drill_radius (1.25) = 4.25
    # min = 3.25
    assert PurflingCutterParams().shank_wall_around_tapped_bore == pytest.approx(3.25)


# ---------------------------------------------------------------------------
# Wall validators fire on violations (one test per rule)
# ---------------------------------------------------------------------------


def test_violation_4213_blade_slot_too_wide_for_shaft() -> None:
    """§4.2.13 — widening the slot in Z until the side wall drops below the rule fails."""
    with pytest.raises(ValidationError, match=r"§4\.2\.13"):
        # Wall = (7.9 − 6.5)/2 = 0.7; rule = max(0.8, 0.7) = 0.8
        PurflingCutterParams(shaft={"blade_slot_length": 6.5})


def test_violation_4323_inter_bore_gap_too_small() -> None:
    """§4.3.23 — shrinking the inter-bore gap below the rule fails."""
    with pytest.raises(ValidationError, match=r"§4\.3\.23"):
        # Wall = 6.0 − 4.075 − 1.25 = 0.675; rule = max(1.2, 1.5) = 1.5
        PurflingCutterParams(shank={"crossbore_to_tapped_bore_gap": 6.0})


def test_violation_4324_shank_too_shallow_around_crossbore() -> None:
    """§4.3.24 — shrinking shank.depth until the Z-walls drop below the rule fails."""
    with pytest.raises(ValidationError, match=r"§4\.3\.24"):
        # Z-wall = 10/2 − 4.075 = 0.925; rule = max(1.0, 0.15 × 8.15) = 1.222
        PurflingCutterParams(shank={"depth": 10.0})


def test_violation_4325_tapped_bore_too_close_to_top() -> None:
    """§4.3.25 — placing tapped bore too close to top of shank fails."""
    with pytest.raises(ValidationError, match=r"§4\.3\.25"):
        # crossbore at 12, gap 9.5 → tapped at 2.5; X-up = 2.5 − 1.25 = 1.25
        # rule = max(1.0, 1.5) = 1.5
        PurflingCutterParams(shank={"crossbore_position_from_top": 12.0})


# ---------------------------------------------------------------------------
# Field metadata preservation
# ---------------------------------------------------------------------------


def test_blade_thickness_carries_spec_metadata() -> None:
    field = BladeParams.model_fields["thickness"]
    extra = field.json_schema_extra
    assert isinstance(extra, dict)
    assert extra["spec_ref"] == "§4.1.1"
    assert extra["status"] == "MEASURED"
    assert extra["units"] == "mm"
    assert field.description is not None
    assert "wide flat" in field.description
    assert "grub screw" in field.description


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
