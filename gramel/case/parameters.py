"""
Parameters for the print-in-place clamshell case.

Defaults are tuned for PETG on a 0.4 mm nozzle. All overhangs are designed
to be ≤45° so the case prints supportless straight from the bed.

Case frame (case lying flat):
  CX: long axis, horizontal. Aligns with the tool's Z (shank length).
  CY: short horizontal axis. Aligns with the tool's X (shaft direction).
  CZ: vertical (short). Aligns with the tool's Y (depth direction).
       Split plane at CZ = 0 — base below, lid above.

Hinge: two clusters along the +CY back edge. Each cluster has a teardrop
pin integral to the lid and a matching teardrop bore in the base.

Magnets: two pairs along the −CY front edge.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _meta(units: str = "mm") -> dict[str, Any]:
    return {"units": units}


class CaseParams(BaseModel):
    """Parameters for the print-in-place clamshell case."""

    model_config = ConfigDict(validate_assignment=True)

    # --- Walls and clearances ------------------------------------------------

    wall_thickness: float = Field(
        default=2.0,
        gt=0,
        description="Outer wall thickness. 2 mm is the PETG sweet spot.",
        json_schema_extra=_meta(),
    )
    tool_clearance: float = Field(
        default=0.5,
        ge=0,
        description="Clearance between tool and pocket walls (all axes).",
        json_schema_extra=_meta(),
    )
    blade_clearance: float = Field(
        default=1.5,
        gt=0,
        description="Extra clearance around blade cutting edges. Case never touches the blades.",
        json_schema_extra=_meta(),
    )

    # --- Cutter extension and blade drop ranges ------------------------------

    cutter_x_travel: float = Field(
        default=5.0,
        ge=0,
        description="Half-range of shaft X travel from centred (in tool frame). ±5 mm covers the drive-screw thread travel.",
        json_schema_extra=_meta(),
    )
    blade_drop_min: float = Field(
        default=5.0,
        ge=0,
        description="Minimum protrusion of blade tip below the retainer bottoms.",
        json_schema_extra=_meta(),
    )
    blade_drop_max: float = Field(
        default=22.0,
        gt=0,
        description="Maximum protrusion. Leaves ~1 mm of blade still in the slot.",
        json_schema_extra=_meta(),
    )

    # --- Hinge --------------------------------------------------------------
    # Two end clusters along the +CY back edge. Each cluster = one teardrop
    # pin (on lid) + one teardrop bore (in base). The pin axis is along CY.
    # All features have 45° tops so they print supportless.

    hinge_cluster_count: int = Field(
        default=2,
        ge=1,
        description="Number of hinge clusters along the back edge. 2 = one at each end (recommended).",
        json_schema_extra=_meta(units=""),
    )
    hinge_cluster_end_margin: float = Field(
        default=8.0,
        gt=0,
        description="Distance from the case's CX end to the centre of the nearest hinge cluster.",
        json_schema_extra=_meta(),
    )
    hinge_knuckle_length: float = Field(
        default=5.0,
        gt=0,
        description="Length of each knuckle along the hinge axis. Reference has ~5 mm knuckles, 3 per cluster, totalling ~15.8 mm cluster length.",
        json_schema_extra=_meta(),
    )
    hinge_knuckles_per_cluster: int = Field(
        default=3,
        ge=2,
        description="Number of alternating knuckles per cluster (LRL pattern with 3). Reference uses 3.",
        json_schema_extra=_meta(units=""),
    )
    hinge_pin_round_diameter: float = Field(
        default=2.85,
        gt=0,
        description="Radius of the teardrop's round body × 2. Reference round body diameter is ~5.7 mm, so this defaults to 2.85 mm so teardrop_d = 2 × this = 5.7 mm.",
        json_schema_extra=_meta(),
    )
    hinge_pin_protrusion: float = Field(
        default=4.0,
        gt=0,
        description="How far the pin protrudes from the lid's knuckle face into the base's bore.",
        json_schema_extra=_meta(),
    )
    hinge_bore_radial_clearance: float = Field(
        default=0.2,
        gt=0,
        description="Radial clearance between pin round-body and bore round-bottom. 0.2 mm is the print-in-place sweet spot for PETG.",
        json_schema_extra=_meta(),
    )
    hinge_axial_clearance: float = Field(
        default=0.4,
        gt=0,
        description="Axial gap between the lid knuckle face and the base knuckle face (≥ one nozzle width).",
        json_schema_extra=_meta(),
    )
    hinge_teardrop_angle_deg: float = Field(
        default=45.0,
        gt=0,
        lt=90,
        description="Half-angle of the pointed top of the teardrop, measured from vertical. 45° is the FDM self-supporting limit.",
        json_schema_extra=_meta(units="deg"),
    )
    hinge_axis_offset: float = Field(
        default=0.5,
        ge=0,
        description="Distance the hinge pin axis is pushed OUTWARD past the back wall, beyond the teardrop's round-body radius. With offset = 0, knuckle's -CY edge is flush with the wall; with offset > 0, there's a small overlap so the knuckle anchors into the wall material by `offset` mm. Smaller offset = more bulge-out, more clearance for case halves to open.",
        json_schema_extra=_meta(),
    )

    # --- Magnets ------------------------------------------------------------

    magnet_diameter: float = Field(
        default=6.0,
        gt=0,
        description="Magnet OD. 6 × 3 mm N52 disc magnets.",
        json_schema_extra=_meta(),
    )
    magnet_thickness: float = Field(
        default=3.0,
        gt=0,
        description="Magnet thickness (along its magnetic axis).",
        json_schema_extra=_meta(),
    )
    magnet_pocket_clearance: float = Field(
        default=0.1,
        gt=0,
        description="Slip-fit clearance for glue. CA glue or epoxy will fill this.",
        json_schema_extra=_meta(),
    )
    magnet_back_wall: float = Field(
        default=1.0,
        gt=0,
        description="Thickness of material behind the magnet pocket.",
        json_schema_extra=_meta(),
    )
    magnet_pairs: int = Field(
        default=2,
        ge=1,
        description="Number of magnet pairs along the −CY front edge.",
        json_schema_extra=_meta(units=""),
    )

    # --- Outer cosmetic ------------------------------------------------------

    corner_radius: float = Field(
        default=4.0,
        ge=0,
        description="Outer corner fillet radius on vertical CZ edges.",
        json_schema_extra=_meta(),
    )

    # --- Logo engraving on the lid top --------------------------------------

    logo_text: str = Field(
        default="Chelli\nStrings",
        description="Engraved text on the lid's outer-top face. Use \\n for line breaks. Empty string disables.",
        json_schema_extra=_meta(units=""),
    )
    logo_size: float = Field(
        default=14.0,
        gt=0,
        description="Font size of the engraved logo (mm). Drives line spacing too.",
        json_schema_extra=_meta(),
    )
    logo_depth: float = Field(
        default=0.8,
        gt=0,
        description="Depth of the engraved recess into the lid top (mm). V-tapered at 45° (or shallower fallback) for self-supporting first-layer print.",
        json_schema_extra=_meta(),
    )
    logo_rotation: float = Field(
        default=-90.0,
        description="Rotation of the engraved logo about the lid-top normal (degrees, CCW positive). Default -90° rotates the text 90° clockwise as viewed from above the closed case — so the case reads naturally when held with its long edge upright.",
        json_schema_extra=_meta(),
    )


__all__ = ["CaseParams"]
