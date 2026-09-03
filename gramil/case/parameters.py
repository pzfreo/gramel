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
        default=1.0,
        ge=0,
        description="Extra clearance margin (mm) added BEYOND the geometrically-derived shaft-travel stops (see case.cutter_travel_offsets), on each side of the cutter trough and blade well. The real travel is asymmetric and derived from the mechanism — retract bounded by the blade slot reaching the shank working face, insert by the drive-screw thread fully engaging — so this is just a small safety buffer, not the travel itself.",
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
        description="Magnet OD. 6 × 2.65 mm N52 disc magnets.",
        json_schema_extra=_meta(),
    )
    magnet_thickness: float = Field(
        default=2.65,
        gt=0,
        description="Magnet thickness (along its magnetic axis). Measured from the actual N52 discs in use.",
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


class SandwichCaseParams(BaseModel):
    """Parameters for the "Option B" sandwich case.

    A SECOND, independent case design, parallel to the carved-pocket
    `CaseParams` clamshell. Concept (ported from pzfreo/gibson-peg-turner
    tuner_case_v2):

      * SHELL  — two thin-walled clamshell leaves: a plain rectangular
                 protective box, no carved tool pocket. Reuses the validated
                 gramil teardrop print-in-place hinge and lid logo; magnets
                 sit in corner bosses (thin walls can't embed them in-wall).
      * INSERT — a separate flat tray that slides into the shell. It carries
                 a silhouette pocket for the ASSEMBLED tool (the validated
                 `_tool_pocket` cut, so part fit is identical to the existing
                 case) plus a spares bay (spare blades + a 2 mm hex Allen key).

    The shell's Z cavity = insert + `foam_thickness` of foam ABOVE and BELOW
    (a foam / insert / foam sandwich), so the tool — including the exposed
    blades — is cushioned top and bottom. Foam is supplied/cut by the user.
    """

    model_config = ConfigDict(validate_assignment=True)

    # Shell hinge / magnets / logo / wall / clearances are shared with the
    # carved-pocket case — reuse that parameter set wholesale rather than
    # duplicating ~20 fields. The sandwich-specific knobs are below.
    shell: CaseParams = Field(default_factory=CaseParams)

    # --- Sandwich Z stack ---------------------------------------------------

    foam_thickness: float = Field(
        default=5.0,
        gt=0,
        description="Foam thickness ABOVE and BELOW the insert (mm). The shell's Z cavity = insert thickness + 2 × this. Zero Z margin by design so the foam grips the tool top and bottom.",
        json_schema_extra=_meta(),
    )
    tool_proud: float = Field(
        default=0.5,
        ge=0,
        description="The insert is built this much THINNER (mm) in Z than the tool's actual height, so the tool stands proud of the insert faces (half of this per side, as the insert is centred on the seam) and the foam clamps it firmly — no Z jiggle.",
        json_schema_extra=_meta(),
    )
    cavity_z_clearance: float = Field(
        default=1.0,
        ge=0,
        description="Extra Z room in the closed cavity beyond insert + 2×foam (total; 0.5 mm per side). A build/closing allowance so the foam–insert–foam stack isn't jammed and the lid latches.",
        json_schema_extra=_meta(),
    )
    slide_clearance: float = Field(
        default=0.4,
        gt=0,
        description="X/Y slide-fit clearance between the insert and the shell bore.",
        json_schema_extra=_meta(),
    )
    insert_rim: float = Field(
        default=3.0,
        gt=0,
        description="Border of solid insert material around the tool-pocket footprint (mm). Gives the insert a frame and room for the spares bay.",
        json_schema_extra=_meta(),
    )
    min_insert_wall: float = Field(
        default=2.5,
        gt=0,
        description="Minimum insert material between the tool pocket, the spares bay, and the outer edges (mm). Drives how far the tool storage is moved inward and how much the case is expanded.",
        json_schema_extra=_meta(),
    )
    tool_inset: float = Field(
        default=12.0,
        ge=0,
        description="Distance the tool storage is moved inward (+CY, toward the hinge) to open a clean front band for the spares bay, expanding the case to suit.",
        json_schema_extra=_meta(),
    )
    front_relief: float = Field(
        default=1.5,
        gt=0,
        description="Depth (mm) the insert's front (−CY) top edge is relieved ABOVE the seam so the closing lid's tilting front wall doesn't pinch it (gibson tuner_case_v2 fix). Below the seam the insert stays full size and located.",
        json_schema_extra=_meta(),
    )

    # --- Spares bay ---------------------------------------------------------

    spare_blades: int = Field(
        default=2,
        ge=0,
        description="Number of spare-blade pockets in the spares bay.",
        json_schema_extra=_meta(units=""),
    )
    spare_clearance: float = Field(
        default=0.4,
        gt=0,
        description="Clearance added around the spares when sizing the single key+blades pocket.",
        json_schema_extra=_meta(),
    )
    spares_bay_length: float = Field(
        default=52.0,
        gt=0,
        description="CX length of the SINGLE spares pocket (along the shaft axis). Must be ≥ the Allen key long arm so the key lies in it.",
        json_schema_extra=_meta(),
    )
    spares_bay_depth: float = Field(
        default=20.0,
        gt=0,
        description="CY depth of the SINGLE spares pocket that holds the Allen key + spare blades together (mm).",
        json_schema_extra=_meta(),
    )

    # --- Allen key (2 mm hex L-key for the M4 grub screw) -------------------

    allen_key_af: float = Field(
        default=2.0,
        gt=0,
        description="Allen key across-flats size (mm). 2 mm hex drives the M4 grub screw that clamps the blade stack.",
        json_schema_extra=_meta(),
    )
    allen_key_long_arm: float = Field(
        default=50.0,
        gt=0,
        description="Length of the Allen key's long arm (mm). Runs along CX in the spares bay.",
        json_schema_extra=_meta(),
    )
    allen_key_short_arm: float = Field(
        default=18.0,
        gt=0,
        description="Length of the Allen key's short arm (mm). Bends across CY at the low-CX end of the bay.",
        json_schema_extra=_meta(),
    )
    allen_key_clearance: float = Field(
        default=0.6,
        gt=0,
        description="Clearance added to the Allen key across-flats when sizing its channel.",
        json_schema_extra=_meta(),
    )
    allen_channel_depth: float = Field(
        default=3.0,
        gt=0,
        description="Depth of the floored L-shaped Allen-key channel (mm).",
        json_schema_extra=_meta(),
    )

    # --- Magnet corner bosses (thin-wall shell) -----------------------------

    magnet_boss_radius: float = Field(
        default=4.5,
        gt=0,
        description="Radius of the cylindrical boss that hosts a magnet pocket on the thin shell wall (mm). Must clear magnet_diameter/2 + magnet_pocket_clearance with wall around it.",
        json_schema_extra=_meta(),
    )

    # --- Variant presets ----------------------------------------------------

    @classmethod
    def thin_foam(cls, **overrides: Any) -> "SandwichCaseParams":
        """Slim variant: 1 mm EVA foam instead of 5 mm, as a zero-slack fit.

        The Z stack is nominally exact everywhere -- no cavity slack, and no
        preload on the foam:

          cavity      = stack_h (11.0) + 2 x foam (1.0) + clearance (0.0)
                      = 13.0 mm
          over insert = 1.0 + 11.0 + 1.0 = 13.0 mm  -> exact, insert located
          over tool   = 1.0 + 11.0 + 1.0 = 13.0 mm  -> exact, foam kisses the
                        tool

        Both departures from the 5 mm defaults are forced by the foam:

        ``cavity_z_clearance`` -> 0. The default 1.0 mm build allowance is a
        rounding error inside a 10 mm foam stack, but at 1 mm it is half a
        foam layer and would leave the tool loose.

        ``tool_proud`` -> 0. The default 0.5 mm makes the tool stand proud so
        the foam clamps it, which works on soft open-cell PU. EVA is stiff
        closed-cell: the tool presents ~860 mm2 of flat shank face to the
        foam, so 0.25 mm/side (25% strain, ~40-80 kPa CFD) needs roughly
        34-69 N to close -- against the ~16-20 N two 6 x 2.65 mm N52 pairs
        can muster. The lid would not latch. With EVA the foam is a liner,
        not a spring: the tool is held laterally by its through-pocket in the
        insert and in Z by friction against the foam.

        Pass ``tool_proud=0.5`` back in if you switch to soft PU foam and
        want the clamping fit.

        Closed exterior: 108.3 x 67.4 x 17.0 mm, against 25.5 mm tall for the
        5 mm-foam default -- an 8.5 mm (33%) reduction in thickness. Footprint
        is unchanged; it is the Z stack alone that shrinks.
        """
        return cls(
            **{
                "foam_thickness": 1.0,
                "cavity_z_clearance": 0.0,
                "tool_proud": 0.0,
                **overrides,
            }
        )


__all__ = ["CaseParams", "SandwichCaseParams"]
