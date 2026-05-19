"""
Purfling cutter — parametric model.

Single source of truth for every dimension that crosses a part boundary.
Each numeric field carries spec_ref, status (ESTIMATE | MEASURED | DERIVED),
and units in json_schema_extra.

Wall thicknesses around the four critical bore / slot features (§4.2.13,
§4.2.14, §4.3.23, §4.3.24, §4.3.25) are **derived** from the surrounding
geometry, exposed as computed properties on PurflingCutterParams, and
validated against the spec's minimum-thickness rules. A caller cannot claim a
wall thickness inconsistent with the geometry.

See:
    specification.md   — canonical CAD spec (intent + dimensions)
    code-spec.md       — implementation approach for this build
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from gramel import threads

# ---------------------------------------------------------------------------
# Metadata helper
# ---------------------------------------------------------------------------

Status = Literal["ESTIMATE", "MEASURED", "DERIVED"]


def _spec(ref: str, status: Status = "ESTIMATE", units: str = "mm") -> dict[str, Any]:
    """Build the json_schema_extra payload tying a field to its spec entry."""
    return {"spec_ref": ref, "status": status, "units": units}


# ---------------------------------------------------------------------------
# Process configuration — prototype vs production fits
# ---------------------------------------------------------------------------


class ProcessConfig(BaseModel):
    """Manufacturing-process flags. Owns the FDM printed-gap clearance.

    The CNC sliding clearance is NOT a parameter here — it falls out of the
    ISO 286 fit classes (bore_fit + shaft_fit on CuttingPairParams). For a
    given nominal diameter the worst-case clearance is computed by
    `gramel.tolerances.worst_case_clearance(...)`.
    """

    model_config = ConfigDict(validate_assignment=True)

    prototype: bool = Field(
        default=True,
        description="True for FDM 3D-print prototype. False for machined brass production.",
    )

    fdm_sliding_clearance: float = Field(
        default=0.25,
        gt=0,
        description="Radial sliding-fit clearance for FDM print. Real printed gap — bore is enlarged by this much over the shaft nominal so the print mates.",
        json_schema_extra=_spec("§8 — Critical fits (prototype override)"),
    )


class CuttingPairParams(BaseModel):
    """The shaft + crossbore mating pair — single nominal diameter with
    ISO 286 fit classes on each side.

    On the CNC path, both shaft and crossbore are nominally the same
    diameter; the bore is reamed at `bore_fit` (typically H7) and the
    shaft is lathed at `shaft_fit` (typically g6), and the clearance
    falls out of the standard tolerance bands.

    On the FDM path, the bore is enlarged by `process.fdm_sliding_clearance`
    to leave room for the printed surfaces; the shaft stays at nominal.
    """

    nominal_diameter: float = Field(
        default=8.0,
        gt=0,
        description="Nominal diameter of the shaft and the crossbore. Picked to match a standard H7 reamer size (8 mm here); the original tool measured 7.9 mm but was rounded up for production simplicity.",
        json_schema_extra=_spec("§4.2.12", status="DERIVED"),
    )
    bore_fit: str = Field(
        default="H7",
        description="ISO 286 fit class for the shank crossbore. H7 = standard reamed-hole sliding fit.",
        json_schema_extra=_spec("§8 — Critical fits", units=""),
    )
    shaft_fit: str = Field(
        default="g6",
        description="ISO 286 fit class for the shaft OD. g6 mates with an H7 hole to give a clearance running fit.",
        json_schema_extra=_spec("§8 — Critical fits", units=""),
    )


# ---------------------------------------------------------------------------
# Tier 1 — Blades and spacer (specification §4.1)
# ---------------------------------------------------------------------------


class BladeParams(BaseModel):
    """§4.1 items 1–4 — blade dimensions."""

    thickness: float = Field(
        default=0.7,
        gt=0,
        description="X dimension when seated in the slot — along the shaft, the direction the grub screw pushes. Across the wide flat of the blade.",
        json_schema_extra=_spec("§4.1.1", status="MEASURED"),
    )
    width: float = Field(
        default=4.0,
        gt=0,
        description="Y dimension when seated — perpendicular to the shaft, fits in the slot's 5 mm Y dim with clearance.",
        json_schema_extra=_spec("§4.1.2", status="MEASURED"),
    )
    length: float = Field(
        default=23.0,
        gt=0,
        description="Z dimension when seated — vertical in use, longer than the slot's Z extent so blades drop through and project below for cutting.",
        json_schema_extra=_spec("§4.1.3", status="MEASURED"),
    )
    bevel_angle: float = Field(
        default=25.0,
        gt=0,
        lt=90,
        description="Single bevel — confirmed on the original. Angle still estimate.",
        json_schema_extra=_spec("§4.1.4", units="deg"),
    )
    tip_shape: Literal["round", "straight", "angled"] = Field(
        default="round",
        description="Geometry of the blade tip. The original tool's blades have rounded ends.",
        json_schema_extra=_spec("§4.1 (M1.5)", status="MEASURED", units=""),
    )


class SpacerParams(BaseModel):
    """
    §4.1 items 5–6 — channel-width spacer.

    USER-SUPPLIED: the original tool ships with 4 bone-shaped copper
    *retainers* (see BladeRetainerParams) that are NOT the channel-width
    setter. The actual channel width is set by an additional shim that
    the luthier places between the two blades, and is the user's choice
    of thickness. We model it here so the parameter chain still has a
    single source of truth for the channel.
    """

    thickness: float = Field(
        default=0.0,
        ge=0,
        description="X dimension of the user-supplied shim between blades. Sets the purfling channel width. Default 0 = no spacer installed (bare tool state).",
        json_schema_extra=_spec("§4.1.5"),
    )


class BladeRetainerParams(BaseModel):
    """
    Bone-shaped copper retainer.

    *Missing from the original spec.* Four of these per tool, all identical.

    Layout in the slot's X direction (along the shaft, 6 mm slot dim): two
    retainers on each side of the blade-spacer-blade stack —
        retainer | retainer | blade | spacer | blade | retainer | retainer
        | grub-screw slack
    Total X stack ≈ 4 × 0.75 + 2 × 0.7 + spacer = 4.4 mm + spacer, leaving
    the remainder of the 6 mm slot for grub-screw advance.

    The bone shape locks each retainer in place against the slot's open
    Z direction: the narrow Y middle (4.5 mm) fits inside the slot's 5 mm
    Y opening, the wider Y ends (5.5 mm) sit above and below the slot's
    +Z and −Z openings so the retainer can't slide through.
    """

    length: float = Field(
        default=10.0,
        gt=0,
        description="Z length of the retainer (long axis = slot's open Z direction). Wider Y ends stick out at the top and bottom of the slot.",
        json_schema_extra=_spec("§4.1 (retainer — missing from spec)", status="MEASURED"),
    )
    end_width: float = Field(
        default=5.5,
        gt=0,
        description="Y width at the bone-shaped ends (at +Z and −Z extremes of the retainer). > slot's 5 mm Y so the ends lock against the shaft's +Z and −Z faces.",
        json_schema_extra=_spec("§4.1 (retainer — missing from spec)", status="MEASURED"),
    )
    middle_width: float = Field(
        default=4.5,
        gt=0,
        description="Y width through the retainer's middle. < slot's 5 mm Y so this section fits inside the slot.",
        json_schema_extra=_spec("§4.1 (retainer — missing from spec)", status="MEASURED"),
    )
    thickness: float = Field(
        default=0.75,
        gt=0,
        description="X dimension of the flat copper shim — stacks alongside the blades along the shaft.",
        json_schema_extra=_spec("§4.1 (retainer — missing from spec)", status="MEASURED"),
    )


# ---------------------------------------------------------------------------
# Tier 2 — Shaft (specification §4.2)
# ---------------------------------------------------------------------------


class GrubScrewParams(BaseModel):
    """§4.2 items 15–16 — blade-clamp grub screw."""

    thread: str = Field(
        default="M4",
        description="Grub-screw thread. Original tool has a non-standard 4.4 mm diameter — we substitute M4 (4 mm) as the closest convenient standard size.",
        json_schema_extra=_spec("§4.2.15", status="MEASURED", units=""),
    )
    length: float = Field(
        default=10.0,
        gt=0,
        description="Total threaded length of the grub screw. M4 × 10 mm.",
        json_schema_extra=_spec("§4.2 (grub screw length — not numbered)", status="MEASURED"),
    )
    max_nose_advance: float = Field(
        default=3.0,
        gt=0,
        description="Max distance the nose extends past the right wall of the blade slot.",
        json_schema_extra=_spec("§4.2.16"),
    )


class ShaftParams(BaseModel):
    """§4.2 items 8–19 — shaft dimensions."""

    cross_section: Literal["round", "round_with_flat"] = Field(
        default="round_with_flat",
        description="Shaft cross-section profile. Measured: the original has a flat machined on the underside that registers against the depth-lock push rod — answers spec §5 open question Q3. Flat-on-flat contact gives a more positive lock AND prevents shaft rotation.",
        json_schema_extra=_spec("§4.2.11", status="MEASURED", units=""),
    )
    flat_depth: float = Field(
        default=0.6,
        gt=0,
        description="Depth of the flat machined on the −Z underside of the shaft — the sagitta of the cylinder segment removed from the bottom. Flat extends the full shaft.length.",
        json_schema_extra=_spec("§4.2.11 (flat — not in spec items)", status="MEASURED"),
    )
    drive_plate_mount_depth: float = Field(
        default=5.0,
        gt=0,
        description="Depth of the tapped holes on the shaft's outboard end face (for the drive-plate screws). ESTIMATE.",
        json_schema_extra=_spec("§4.2.19 (mount depth — not numbered)"),
    )
    tenon_height: float = Field(
        default=2.0,
        gt=0,
        description="Z dimension of the anti-rotation tenon — a horizontal rib across the shaft's −X end face. The tenon's Y extent is the full shaft diameter (one mill pass instead of a small rectangle).",
        json_schema_extra=_spec("§4.2.19 (tenon — design addition)"),
    )
    tenon_depth: float = Field(
        default=1.0,
        gt=0,
        description="X projection of the tenon outboard from the shaft's −X end face.",
        json_schema_extra=_spec("§4.2.19 (tenon — design addition)"),
    )
    # Note: shaft OD is no longer a field on ShaftParams — it now derives
    # from PurflingCutterParams.cutting_pair.nominal_diameter. The shaft's
    # OD is one half of a mating pair and must stay in lockstep with the
    # crossbore. Access via params.shaft_outer_diameter at the top level.

    blade_slot_width: float = Field(
        default=6.0,
        gt=0,
        description="X dimension of blade slot (along the shaft). Hardware stack (4 retainers + 2 blades) = ~4.4 mm; remaining ~1.6 mm is shared between the channel spacer and grub-screw advance.",
        json_schema_extra=_spec("§4.2.8", status="MEASURED"),
    )
    blade_slot_length: float = Field(
        default=5.0,
        gt=0,
        description="Y dimension of blade slot (across the shaft). The 5 mm direction; fits blade.width (4 mm) plus clearance. Z is the open through direction (blades drop through).",
        json_schema_extra=_spec("§4.2.9", status="MEASURED"),
    )
    end_to_slot_distance: float = Field(
        default=4.0,
        gt=0,
        description="Distance from shaft right end face to right wall of blade slot. The grub-screw end tap fills this entire distance — there is *no* wall between the tap and the slot, so the grub screw's tip directly contacts the blade stack. (Spec §4.2.14 wall rule does not apply to this tool's design.)",
        json_schema_extra=_spec("§4.2.17", status="MEASURED"),
    )
    length: float = Field(
        default=45.0,
        gt=0,
        description="Total shaft length (measured on the original).",
        json_schema_extra=_spec("§4.2.18", status="MEASURED"),
    )
    drive_plate_mount_thread: str = Field(
        default="M2",
        description="Thread for the single central screw mounting the drive plate to the shaft's outboard end face. Spec called for two screws; this scale (~7.9 mm shaft) doesn't fit two M2 screws, so we go with one + use the shaft's existing −Z flat as the anti-rotation feature (the drive plate has a matching D-shaped hole that mates with the shaft cross-section).",
        json_schema_extra=_spec("§4.2.19", units=""),
    )


# ---------------------------------------------------------------------------
# Tier 3 — Shank (specification §4.3)
# ---------------------------------------------------------------------------


class DepthLockParams(BaseModel):
    """
    §4.3 item 32 — depth-lock bolt, thumbwheel, and push rod.

    Mechanism (corrected from spec): the bolt's tip does NOT bear on the shaft
    directly. Instead, the depth-lock bore is tapped for only the lower portion;
    above the threaded section sits a free-sliding steel push rod. Tightening
    the thumbwheel advances the bolt, which pushes the rod up against the
    underside of the shaft. The spec's `Depth-lock bolt — its upper end bears
    directly on the underside of the shaft` is incorrect; the push rod is the
    intermediary.
    """

    thread: str = Field(
        default="M6",
        description="Depth-lock bolt thread (measured OD = 6 mm → M6).",
        json_schema_extra=_spec("§4.3.32", status="MEASURED", units=""),
    )
    bolt_thread_length: float = Field(
        default=18.0,
        gt=0,
        description="Length of threaded portion of the depth-lock bolt.",
        json_schema_extra=_spec("§4.3 (bolt — not numbered)", status="MEASURED"),
    )
    knob_diameter: float = Field(
        default=10.0,
        gt=0,
        description="Thumbwheel OD at the bottom of the shank.",
        json_schema_extra=_spec("§4.3 (knob — not numbered)", status="MEASURED"),
    )
    knob_thickness: float = Field(
        default=14.0,
        gt=0,
        description="Thumbwheel length along the bolt axis (Z).",
        json_schema_extra=_spec("§4.3 (knob — not numbered)", status="MEASURED"),
    )
    push_rod_diameter: float = Field(
        default=5.0,
        gt=0,
        description="Steel push-rod diameter. Slides freely in the upper (untapped) section of the depth-lock bore.",
        json_schema_extra=_spec("§4.3 (push rod — missing from spec)", status="MEASURED"),
    )
    push_rod_length: float = Field(
        default=45.5,
        gt=0,
        description="Steel push-rod length. Sits above the bolt; pushed up against the shaft to lock.",
        json_schema_extra=_spec("§4.3 (push rod — missing from spec)", status="MEASURED"),
    )


class ShankParams(BaseModel):
    """§4.3 items 20–36 — shank dimensions (user-set; walls are derived on the top-level model)."""

    width: float = Field(
        default=13.55,
        gt=0,
        description="Shank cross-section X dimension (from back of shank to peak of convex working face, includes sagitta).",
        json_schema_extra=_spec("§4.3.26", status="MEASURED"),
    )
    depth: float = Field(
        default=11.0,
        gt=0,
        description="Shank cross-section Y dimension (across the working face).",
        json_schema_extra=_spec("§4.3.26", status="MEASURED"),
    )
    length: float = Field(
        default=80.0,
        gt=0,
        description="Shank length along Z. Affects balance, reach, depth-lock bore length.",
        json_schema_extra=_spec("§4.3.27", status="MEASURED"),
    )
    crossbore_position_from_top: float = Field(
        default=14.0,
        gt=0,
        description="Distance from the top of the shank to the shaft cross-bore axis.",
        json_schema_extra=_spec("§4.3.28", status="MEASURED"),
    )
    crossbore_to_tapped_bore_gap: float = Field(
        default=9.5,
        gt=0,
        description="Centre-to-centre distance between shaft cross-bore and shank tapped bore. Derived from measured crossbore_position_from_top (14) − tapped-bore-position-from-top (4.5).",
        json_schema_extra=_spec("§4.3.22", status="DERIVED"),
    )
    depth_lock_bore_diameter: float = Field(
        default=5.0,
        gt=0,
        description="Depth-lock blind bore diameter. M6 tap drill is 5.0 mm; same diameter also accepts the 5 mm push rod (sliding fit in the untapped upper section).",
        json_schema_extra=_spec("§4.3.30", status="DERIVED"),
    )
    depth_lock_threaded_length: float = Field(
        default=12.0,
        gt=0,
        description="Length of the M6-tapped section at the BOTTOM of the depth-lock bore. The remainder of the bore (up to the crossbore) is a smooth sliding fit for the push rod. ESTIMATE: bolt thread length is 18 mm, so 12 mm of tapped engagement is sufficient and leaves the rest as push-rod travel.",
        json_schema_extra=_spec("§4.3 (threading depth — not in spec)"),
    )
    relief_slot_width: float = Field(
        default=2.0,
        gt=0,
        description="Relief slot Y width — central groove down the working face.",
        json_schema_extra=_spec("§4.3.33", status="MEASURED"),
    )
    relief_slot_depth: float = Field(
        default=1.0,
        gt=0,
        description="Relief slot X depth — into body from working face. 1 mm at deepest (centre); slightly less at slot edges where the convex face is lower.",
        json_schema_extra=_spec("§4.3.34", status="MEASURED"),
    )
    working_face_radius: float = Field(
        default=8.11,
        gt=0,
        description="Convexity radius of working face. Derived from measured sagitta 2.15 mm over chord depth 11 mm: R = (c² + 4s²)/(8s).",
        json_schema_extra=_spec("§4.3.35", status="DERIVED"),
    )
    top_dome_radius: float = Field(
        default=30.0,
        gt=0,
        description="Radius of the spherical dome at the +Z end of the shank. Rounded in *both* X and Y directions (sphere, not a single-axis cylinder). Must be large enough that the dome's lowest point (at the +X +Y corner) sits above the top of the tapped bore — empirically requires R ≥ ~15 mm for the current shank/bore proportions. R = 30 mm gives a ~1.5 mm wall above the bore.",
        json_schema_extra=_spec("§4.3 (top dome — not in spec)"),
    )
    edge_fillet_radius: float = Field(
        default=0.5,
        ge=0,
        description="Radius of fillet applied to every external edge of the shank.",
        json_schema_extra=_spec("§8 (finishing — not in §4)", status="MEASURED"),
    )


# ---------------------------------------------------------------------------
# Tier 4 — Drive train (specification §4.4)
# ---------------------------------------------------------------------------


class DriveScrewParams(BaseModel):
    """§4.4 items 37–40, 44 — drive screw (integral with thumbwheel)."""

    thread: str = Field(
        default="M3",
        description="Drive-screw thread (measured OD = 3 mm → M3). Matches shank tapped bore (§4.3.21), which is fully threaded along its full X length (= shank.width).",
        json_schema_extra=_spec("§4.4.37", status="MEASURED", units=""),
    )
    thread_pitch: float = Field(
        default=0.5,
        gt=0,
        description="Drive-screw thread pitch. Fine pitch for adjustment resolution.",
        json_schema_extra=_spec("§4.4.38", status="MEASURED"),
    )
    length: float = Field(
        default=18.0,
        gt=0,
        description="Threaded length of the drive screw — supports full X travel + engagement.",
        json_schema_extra=_spec("§4.4.39", status="MEASURED"),
    )
    left_face_tap: str = Field(
        default="M2",
        description="Thread of the tap on the thumbwheel's left end face (for silver screw).",
        json_schema_extra=_spec("§4.4.40", status="MEASURED", units=""),
    )
    left_face_tap_depth: float = Field(
        default=3.0,
        gt=0,
        description="Depth of the tap for the silver screw, into the −X face of the silver boss / thumbwheel. Was 4 mm originally; reduced to 3 mm so the tap bottoms a safe distance before reaching the drive screw's M3 thread (preserves ≥1.5 mm of solid material in the unthreaded section).",
        json_schema_extra=_spec("§4.4.40", status="MEASURED"),
    )
    unthreaded_length: float = Field(
        default=3.0,
        gt=0,
        description="Length of the unthreaded section between the thumbwheel disc and the start of the M3 threaded portion of the drive screw. Provides solid material around the silver-screw tap bottom so it doesn't eat into the M3 thread.",
        json_schema_extra=_spec("§4.4 (unthreaded section — design addition)", status="MEASURED"),
    )
    unthreaded_diameter: float = Field(
        default=5.0,
        gt=0,
        description="Outer diameter of the unthreaded section. Larger than M3 major (3 mm) so it provides a positive shoulder against the inboard face of the shank tapped bore at maximum-margin.",
        json_schema_extra=_spec("§4.4 (unthreaded section — design addition)", status="MEASURED"),
    )


class ThumbwheelParams(BaseModel):
    """§4.4 items 41–43 — thumbwheel (integral with drive screw)."""

    diameter: float = Field(
        default=10.0,
        gt=0,
        description="Thumbwheel knurled disc OD. Original measured at 9.5 mm; rounded to 10 mm for the prototype (interchangeable with 9 mm by user choice).",
        json_schema_extra=_spec("§4.4.41", status="MEASURED"),
    )
    thickness: float = Field(
        default=2.0,
        gt=0,
        description="Thumbwheel thickness (X dimension — along the drive-screw axis).",
        json_schema_extra=_spec("§4.4.42", status="MEASURED"),
    )
    silver_boss_diameter: float = Field(
        default=6.0,
        gt=0,
        description="Diameter of the small boss on the outboard (−X, drive-plate side) face of the thumbwheel. The silver-screw tap enters through this boss, giving extra material around the tap so it doesn't eat into the thumbwheel's knurled edge.",
        json_schema_extra=_spec("§4.4 (silver boss — design addition)", status="MEASURED"),
    )
    silver_boss_length: float = Field(
        default=0.5,
        gt=0,
        description="X length of the silver boss. Short — just enough to give a positive seat for the silver-screw tap.",
        json_schema_extra=_spec("§4.4 (silver boss — design addition)", status="MEASURED"),
    )
    knurl: Literal["straight", "diamond"] = Field(
        default="straight",
        description="Knurl pattern style.",
        json_schema_extra=_spec("§4.4.43", units=""),
    )


# ---------------------------------------------------------------------------
# Tier 5 — Drive plate and captive bearing (specification §4.5)
# ---------------------------------------------------------------------------


class DrivePlateParams(BaseModel):
    """
    §4.5 items 45–49 — drive plate that lets the drive screw pull the shaft.

    The real plate is **egg-shaped** (NOT the rectangle the spec drafted):
    two circular bosses, the larger one at the shaft end (10 mm radius)
    and the smaller one at the thumbwheel end (5 mm radius), connected
    by a smooth tangent boundary. The plate's plane is YZ (normal = X),
    standing vertically up from the shaft's outboard −X end face.

    The vertical distance between the two bosses' centres equals the
    shank's `crossbore_to_tapped_bore_gap` so the plate spans from the
    shaft axis up to the drive-screw axis.
    """

    shaft_end_radius: float = Field(
        default=4.5,
        gt=0,
        description="Radius of the larger boss at the shaft end of the plate (9 mm diameter).",
        json_schema_extra=_spec("§4.5.45 (egg shape — not in spec)", status="MEASURED"),
    )
    thumb_end_radius: float = Field(
        default=3.0,
        gt=0,
        description="Radius of the smaller boss at the thumbwheel end (6 mm diameter), around the silver-screw clearance hole.",
        json_schema_extra=_spec("§4.5.45 (egg shape — not in spec)", status="MEASURED"),
    )
    thickness: float = Field(
        default=3.0,
        gt=0,
        description="Plate thickness (X dimension — the plate's normal direction). 3 mm = 1 mm anti-rotation slot + 2 mm wall on the front face.",
        json_schema_extra=_spec("§4.5.47", status="MEASURED"),
    )
    silver_clearance_hole_diameter: float = Field(
        default=2.4,
        gt=0,
        description="Hole the SILVER screw passes through. 0.2 mm radial clearance on M2 — sufficient for the captive bearing to spin freely without binding.",
        json_schema_extra=_spec("§4.5.48"),
    )
    mount_hole_diameter: float = Field(
        default=2.4,
        gt=0,
        description="Hole the MOUNT screw passes through (shaft end of plate). Standard M2 clearance fit (~0.2 mm radial). Doesn't need the sloppy captive-bearing tolerance.",
        json_schema_extra=_spec("§4.5 (mount hole — distinct from silver hole)"),
    )


class SilverScrewParams(BaseModel):
    """§4.5 items 50, 52 — silver screw. Its length is owned by captive_bearing (§4.5.51)."""

    thread: str = Field(
        default="M2",
        description="Silver-screw thread. Matches drive_screw.left_face_tap (§4.4.40).",
        json_schema_extra=_spec("§4.5.50", status="MEASURED", units=""),
    )
    head_diameter: float = Field(
        default=4.0,
        gt=0,
        description="Head diameter (measured). Must exceed drive_plate.clearance_hole_diameter.",
        json_schema_extra=_spec("§4.5.52", status="MEASURED"),
    )
    head_thickness: float = Field(
        default=1.5,
        gt=0,
        description="Head thickness.",
        json_schema_extra=_spec("§4.5.52"),
    )


class CaptiveBearingParams(BaseModel):
    """
    §4.5 item 53 — the signature mechanism of this tool.

    The silver screw is deliberately over-length. It bottoms on the thumbwheel's
    left-face tap *before* its head clamps the drive plate, leaving the plate
    captive in axial play between the silver-screw head (outboard) and the
    thumbwheel left face (inboard). The mate class `CaptiveBearing` (Layer 2,
    see code-spec §6) consumes this together with drive_plate.thickness and
    drive_screw.left_face_tap_depth to emit the required silver-screw length.
    """

    axial_play: float = Field(
        default=0.2,
        gt=0,
        le=0.5,
        description="Designed axial bearing clearance. Measured 0.2 mm — the non-binding gap that lets the drive plate float between the silver-screw head and the thumbwheel's left face while the drive screw rotates freely.",
        json_schema_extra=_spec("§4.5.53", status="MEASURED"),
    )


# ---------------------------------------------------------------------------
# Top-level model — composes sub-models, owns cross-part derivations
# ---------------------------------------------------------------------------


class PurflingCutterParams(BaseModel):
    """
    Top-level parameter set for the purfling cutter.

    Cross-part derived values (stack thickness, bore diameter, wall thicknesses)
    are exposed as computed properties. Wall-thickness rules from §4 of
    specification.md are enforced as a model validator: invalid geometry raises
    ValidationError.
    """

    process: ProcessConfig = Field(default_factory=ProcessConfig)
    cutting_pair: CuttingPairParams = Field(default_factory=CuttingPairParams)
    blade: BladeParams = Field(default_factory=BladeParams)
    spacer: SpacerParams = Field(default_factory=SpacerParams)
    blade_retainer: BladeRetainerParams = Field(default_factory=BladeRetainerParams)
    grub_screw: GrubScrewParams = Field(default_factory=GrubScrewParams)
    shaft: ShaftParams = Field(default_factory=ShaftParams)
    shank: ShankParams = Field(default_factory=ShankParams)
    depth_lock: DepthLockParams = Field(default_factory=DepthLockParams)
    drive_screw: DriveScrewParams = Field(default_factory=DriveScrewParams)
    thumbwheel: ThumbwheelParams = Field(default_factory=ThumbwheelParams)
    drive_plate: DrivePlateParams = Field(default_factory=DrivePlateParams)
    silver_screw: SilverScrewParams = Field(default_factory=SilverScrewParams)
    captive_bearing: CaptiveBearingParams = Field(default_factory=CaptiveBearingParams)

    # --- Mating-pair derivations (cutting_pair + process) ------------------

    @computed_field  # type: ignore[prop-decorator]
    @property
    def shaft_outer_diameter(self) -> float:
        """Nominal shaft OD — the cutting-pair nominal. Tolerance class
        (e.g. g6) lives on cutting_pair.shaft_fit and is rendered on the
        drawing, not numerically expanded here."""
        return self.cutting_pair.nominal_diameter

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sliding_clearance(self) -> float:
        """Active sliding-fit clearance for the current process.

        FDM: a real printed gap (process.fdm_sliding_clearance).
        CNC: the ISO 286 worst-case clearance for the bore/shaft fit pair.
        """
        if self.process.prototype:
            return self.process.fdm_sliding_clearance
        from gramel import tolerances

        return tolerances.worst_case_clearance(
            self.cutting_pair.nominal_diameter,
            hole_fit=self.cutting_pair.bore_fit,
            shaft_fit=self.cutting_pair.shaft_fit,
        )

    # --- Cross-part derived values (§4 derivations) -------------------------

    @computed_field  # type: ignore[prop-decorator]
    @property
    def stack_thickness(self) -> float:
        """
        §4.1.7 — permanent hardware stack in X direction (along shaft).

        Layout: retainer | retainer | blade | blade | retainer | retainer.
        The channel spacer sits in the remaining spare space between the two
        blades; it is NOT part of this fixed stack. Spare space for spacer +
        grub-screw advance = blade_slot_width − stack_thickness (~1.6 mm with
        defaults).
        """
        return 4 * self.blade_retainer.thickness + 2 * self.blade.thickness

    @computed_field  # type: ignore[prop-decorator]
    @property
    def slot_spare(self) -> float:
        """X space available for channel spacer + grub-screw advance (hardware stack only)."""
        return self.shaft.blade_slot_width - self.stack_thickness

    @computed_field  # type: ignore[prop-decorator]
    @property
    def crossbore_diameter(self) -> float:
        """§4.3.20 — modelled crossbore diameter for boolean geometry.

        FDM: shaft nominal + printed gap (the geometry literally needs the
        bore enlarged so the printed shaft will fit).
        CNC: the same nominal as the shaft — the fit class on the drawing
        (e.g. H7) carries the tolerance, not the modelled geometry.
        """
        if self.process.prototype:
            return self.cutting_pair.nominal_diameter + self.process.fdm_sliding_clearance
        return self.cutting_pair.nominal_diameter

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tapped_bore_drill_diameter(self) -> float:
        """Drill diameter for the shank tapped bore — derived from drive-screw thread."""
        return threads.tap_drill_diameter(self.drive_screw.thread)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tapped_bore_position_from_top(self) -> float:
        """§4.3.29 — tapped bore sits above the crossbore, so closer to the top."""
        return self.shank.crossbore_position_from_top - self.shank.crossbore_to_tapped_bore_gap

    @computed_field  # type: ignore[prop-decorator]
    @property
    def depth_lock_bore_depth(self) -> float:
        """
        §4.3.31 — bore extends from the bottom face up to the crossbore axis.

        Originally the spec called for a `small_clearance` so the bore stopped
        just below the crossbore. Measurement showed the bore actually meets
        the crossbore (it has to — the push rod's upper end sits in the
        crossbore region so it can press on the shaft). So no clearance term.
        """
        return self.shank.length - self.shank.crossbore_position_from_top

    @computed_field  # type: ignore[prop-decorator]
    @property
    def relief_slot_length(self) -> float:
        """
        Slot runs along Z from the bottom of the shank up to (but not past)
        the shaft cross-bore. Measured against the original tool: slot stops
        at the shaft level, doesn't extend above. So length = length − crossbore_position_from_top.
        """
        return self.shank.length - self.shank.crossbore_position_from_top

    @computed_field  # type: ignore[prop-decorator]
    @property
    def contact_corner_width(self) -> float:
        """§4.3.36 — contact corner is in Y direction (across the working face).

        Slot length is along Z (shank long axis); slot width is across the working
        face in Z; contact corners sit either side of the slot, also in Y. The
        symmetric corner width is (shank.depth − relief_slot_width) / 2.
        """
        return (self.shank.depth - self.shank.relief_slot_width) / 2

    # --- Derived wall thicknesses (§4 critical constraints) ----------------

    @computed_field  # type: ignore[prop-decorator]
    @property
    def shaft_wall_around_slot(self) -> float:
        """
        §4.2.13 — wall thickness between the slot's Y edge and the shaft's
        outer surface, measured at the slot's mid-Z plane.

        The slot is open in Z (top and bottom of the shaft — blades drop
        through). The slot extends along X inside the shaft body, with
        end walls handled separately by §4.2.14 (`shaft_wall_around_end_tap`).
        The remaining relevant wall is in the Y direction, taking
        (shaft_outer_diameter − blade_slot_length) / 2 (where
        blade_slot_length is the slot's Y cross-section dim).
        """
        return (self.shaft_outer_diameter - self.shaft.blade_slot_length) / 2

    @computed_field  # type: ignore[prop-decorator]
    @property
    def shank_wall_between_bores(self) -> float:
        """§4.3.23 — wall between crossbore and tapped bore in shank."""
        crossbore_radius = self.crossbore_diameter / 2
        tapped_radius = self.tapped_bore_drill_diameter / 2
        return self.shank.crossbore_to_tapped_bore_gap - crossbore_radius - tapped_radius

    @computed_field  # type: ignore[prop-decorator]
    @property
    def shank_wall_around_crossbore(self) -> float:
        """
        §4.3.24 — min wall around the crossbore in directions perpendicular to bore axis.

        Bore axis is X (along the shaft, normal to working face). Excludes the wall
        toward the tapped bore (+Z direction — that's §4.3.23). Considers:
          - Z down (toward bottom of shank): crossbore_z − crossbore_radius
          - Y either side (assumes bore centred in Y): depth/2 − crossbore_radius
        """
        crossbore_radius = self.crossbore_diameter / 2
        crossbore_z = self.shank.length - self.shank.crossbore_position_from_top
        wall_z_down = crossbore_z - crossbore_radius
        wall_y = self.shank.depth / 2 - crossbore_radius
        return min(wall_z_down, wall_y)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def shank_wall_around_tapped_bore(self) -> float:
        """
        §4.3.25 — min wall around the tapped bore in directions perpendicular to bore axis.

        Excludes the wall toward the crossbore (−Z — that's §4.3.23). Considers:
          - Z up (toward top of shank): tapped_bore_position_from_top − tapped_radius
          - Y either side (assumes bore centred in Y): depth/2 − tapped_radius
        """
        tapped_radius = self.tapped_bore_drill_diameter / 2
        wall_z_up = self.tapped_bore_position_from_top - tapped_radius
        wall_y = self.shank.depth / 2 - tapped_radius
        return min(wall_z_up, wall_y)

    # --- Wall-thickness validators ------------------------------------------

    @model_validator(mode="after")
    def _validate_walls(self) -> "PurflingCutterParams":
        """
        Wall-thickness rules.

        Rules relaxed from the original spec after measuring the real tool —
        the original ≥3 mm / ≥0.6 × D constants were conservative CAD-shop
        guesses; the working brass tool sits closer to 1× thread radius and
        ~0.15 × bore diameter. New rules are: ≥1 mm floor, plus a ratio
        appropriate to the feature.
        """
        # §4.2.13 — wall around blade slot
        min_slot_wall = max(0.8, 1.0 * self.blade.thickness)
        if self.shaft_wall_around_slot < min_slot_wall:
            raise ValueError(
                f"shaft_wall_around_slot ({self.shaft_wall_around_slot:.3f}) "
                f"< min {min_slot_wall:.3f} (§4.2.13)."
            )

        # §4.2.14 wall rule removed: in this tool, the grub-screw end tap
        # opens directly into the slot (no wall). Spec was wrong for this
        # design.

        # §4.3.23 — wall between bores
        min_wall_bb = max(1.2, 1.0 * threads.major_radius(self.drive_screw.thread))
        if self.shank_wall_between_bores < min_wall_bb:
            raise ValueError(
                f"shank_wall_between_bores ({self.shank_wall_between_bores:.3f}) "
                f"< min {min_wall_bb:.3f} (§4.3.23)."
            )

        # §4.3.24 — wall around cross-bore (perpendicular to bore axis)
        min_wall_xb = max(1.0, 0.15 * self.crossbore_diameter)
        if self.shank_wall_around_crossbore < min_wall_xb:
            raise ValueError(
                f"shank_wall_around_crossbore ({self.shank_wall_around_crossbore:.3f}) "
                f"< min {min_wall_xb:.3f} (§4.3.24)."
            )

        # §4.3.25 — wall around tapped bore (perpendicular to bore axis)
        min_wall_tap = max(1.0, 1.0 * threads.major_radius(self.drive_screw.thread))
        if self.shank_wall_around_tapped_bore < min_wall_tap:
            raise ValueError(
                f"shank_wall_around_tapped_bore ({self.shank_wall_around_tapped_bore:.3f}) "
                f"< min {min_wall_tap:.3f} (§4.3.25)."
            )

        return self


__all__ = [
    "BladeParams",
    "CaptiveBearingParams",
    "DepthLockParams",
    "DrivePlateParams",
    "DriveScrewParams",
    "GrubScrewParams",
    "ProcessConfig",
    "PurflingCutterParams",
    "ShaftParams",
    "ShankParams",
    "SilverScrewParams",
    "SpacerParams",
    "Status",
    "ThumbwheelParams",
]
