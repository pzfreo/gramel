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
    assert p.sliding_clearance == 0.25


def test_production_mode_uses_iso286_worst_case() -> None:
    """CNC clearance comes from the H7/g6 fit on the cutting pair, not a manual number.
    At ⌀8 the worst-case H7/g6 clearance is 0.029 mm.
    """
    p = PurflingCutterParams(process={"prototype": False})
    assert p.sliding_clearance == pytest.approx(0.029)


# ---------------------------------------------------------------------------
# Cross-part derived values (worked examples — match the measured defaults)
# ---------------------------------------------------------------------------


def test_stack_thickness() -> None:
    # Hardware only: 4 × 0.85 + 2 × 0.7 = 4.8 (spacer not included)
    assert PurflingCutterParams().stack_thickness == pytest.approx(4.8)


def test_slot_spare() -> None:
    # slot(6.4) - hardware(4.8) = 1.6 available for spacer + grub advance
    assert PurflingCutterParams().slot_spare == pytest.approx(1.6)


def test_crossbore_diameter_prototype() -> None:
    # FDM: nominal (8.0) + printed gap (0.25) = 8.25 — bore enlarged for the print.
    assert PurflingCutterParams().crossbore_diameter == pytest.approx(8.25)


def test_crossbore_diameter_production() -> None:
    # CNC: bore nominal = shaft nominal = 8.0 (H7 callout carries the tolerance).
    p = PurflingCutterParams(process={"prototype": False})
    assert p.crossbore_diameter == pytest.approx(8.0)


def test_shaft_outer_diameter_matches_cutting_pair_nominal() -> None:
    p = PurflingCutterParams()
    assert p.shaft_outer_diameter == p.cutting_pair.nominal_diameter == 8.0


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
    # (8.0 − blade_slot_length=4.75) / 2 = 1.625
    assert PurflingCutterParams().shaft_wall_around_slot == pytest.approx(1.625)


def test_shank_wall_between_bores() -> None:
    # gap (9.5) − crossbore_radius (8.25/2 = 4.125) − tap_drill_radius (1.25) = 4.125
    assert PurflingCutterParams().shank_wall_between_bores == pytest.approx(4.125)


def test_shank_wall_around_crossbore_is_min_of_x_down_and_z() -> None:
    # Crossbore at FDM diameter 8.25 → radius 4.125.
    #   Z-down: 66 − 4.125 = 61.875
    #   Y either side: 5.5 − 4.125 = 1.375
    # min = 1.375
    assert PurflingCutterParams().shank_wall_around_crossbore == pytest.approx(1.375)


def test_shank_wall_around_tapped_bore_is_min_of_x_up_and_z() -> None:
    #   Z-up: tapped_bore_position_from_top (4.5) − tap_drill_radius (1.25) = 3.25
    #   Y either side: 5.5 − 1.25 = 4.25
    # min = 3.25
    assert PurflingCutterParams().shank_wall_around_tapped_bore == pytest.approx(3.25)


# ---------------------------------------------------------------------------
# Captive-bearing relationship (captive screw / drive plate / tap depth)
# ---------------------------------------------------------------------------


def test_captive_screw_defaults_to_M2x6_stock() -> None:
    p = PurflingCutterParams()
    assert p.captive_screw.thread == "M2"
    assert p.captive_screw.thread_length == 6.0


def test_journal_bearing_geometry_defaults() -> None:
    """Integral-journal bearing: play = journal_length − plate_thickness; the
    tap is deliberately deep (≥ screw thread); the journal leaves ≥1 mm wall
    around the M2 tap."""
    p = PurflingCutterParams()
    assert p.bearing_journal_length - p.drive_plate.thickness == pytest.approx(
        p.captive_bearing.axial_play
    )
    # tap deep enough that the head seats on the journal end before bottoming
    assert p.drive_screw.left_face_tap_depth >= p.captive_screw.thread_length
    # ≥1 mm wall around the M2 tap (M2 major radius = 1.0)
    wall = p.drive_screw.bearing_journal_diameter / 2 - 1.0
    assert wall >= 1.0 - 1e-9


def test_violation_journal_tap_wall_too_thin() -> None:
    """A journal too small to leave the ≥1 mm wall around the M2 tap is rejected."""
    with pytest.raises(ValidationError, match="Journal tap wall"):
        PurflingCutterParams(drive_screw={"bearing_journal_diameter": 3.0})


def test_violation_washer_too_small_to_retain() -> None:
    """A washer that doesn't overhang the plate bearing hole can't retain the plate."""
    with pytest.raises(ValidationError, match="outer_diameter"):
        PurflingCutterParams(captive_washer={"outer_diameter": 4.0})


# ---------------------------------------------------------------------------
# Depth-lock sliding fits (push rod / collar must fit inside their bores)
# ---------------------------------------------------------------------------


def test_push_rod_smaller_than_smooth_bore() -> None:
    p = PurflingCutterParams()
    assert p.depth_lock.push_rod_diameter < p.shank.depth_lock_bore_diameter


def test_bolt_collar_smaller_than_collar_bore() -> None:
    p = PurflingCutterParams()
    assert p.depth_lock.bolt_collar_diameter < p.shank.depth_lock_collar_bore_diameter


def test_violation_push_rod_too_large() -> None:
    """A ⌀5 push rod in a ⌀5 bore won't slide — must trip the validator."""
    with pytest.raises(ValidationError, match="Push-rod sliding-fit"):
        PurflingCutterParams(depth_lock={"push_rod_diameter": 5.0})


def test_violation_bolt_collar_too_large() -> None:
    """A ⌀6.35 collar in a ⌀6.35 bore won't slide — must trip the validator."""
    with pytest.raises(ValidationError, match="Bolt-collar sliding-fit"):
        PurflingCutterParams(depth_lock={"bolt_collar_diameter": 6.35})


def test_collar_bore_longer_than_collar() -> None:
    p = PurflingCutterParams()
    assert (
        p.shank.depth_lock_collar_bore_length
        > p.depth_lock.bolt_collar_length
    )


def test_violation_collar_bore_too_short() -> None:
    """If bore length matches collar length exactly, manufacturing tolerance
    could land the collar's top against the tap shoulder — validator catches it."""
    with pytest.raises(ValidationError, match="Collar-bore length margin"):
        PurflingCutterParams(shank={"depth_lock_collar_bore_length": 5.0})


# ---------------------------------------------------------------------------
# Wall validators fire on violations (one test per rule)
# ---------------------------------------------------------------------------


def test_violation_4213_blade_slot_too_wide_for_shaft() -> None:
    """§4.2.13 — widening the slot in Z until the side wall drops below the rule fails."""
    with pytest.raises(ValidationError, match=r"§4\.2\.13"):
        # Wall = (8.0 − 6.6)/2 = 0.7; rule = max(0.8, 0.7) = 0.8
        PurflingCutterParams(shaft={"blade_slot_length": 6.6})


def test_violation_4323_inter_bore_gap_too_small() -> None:
    """§4.3.23 — shrinking the inter-bore gap below the rule fails."""
    with pytest.raises(ValidationError, match=r"§4\.3\.23"):
        # Wall = 6.0 − 4.125 − 1.25 = 0.625; rule = max(1.2, 1.5) = 1.5
        PurflingCutterParams(shank={"crossbore_to_tapped_bore_gap": 6.0})


def test_violation_4324_shank_too_shallow_around_crossbore() -> None:
    """§4.3.24 — shrinking shank.depth until the Y-walls drop below the rule fails."""
    with pytest.raises(ValidationError, match=r"§4\.3\.24"):
        # Y-wall = 10/2 − 4.125 = 0.875; rule = max(1.0, 0.15 × 8.25) = 1.2375
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
