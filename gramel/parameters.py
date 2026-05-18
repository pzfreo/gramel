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

# ---------------------------------------------------------------------------
# Metadata helper
# ---------------------------------------------------------------------------

Status = Literal["ESTIMATE", "MEASURED", "DERIVED"]


def _spec(ref: str, status: Status = "ESTIMATE", units: str = "mm") -> dict[str, Any]:
    """Build the json_schema_extra payload tying a field to its spec entry."""
    return {"spec_ref": ref, "status": status, "units": units}


# Approximate thread-major radii (mm) — used by wall-thickness validators.
# bd_warehouse holds the authoritative table; this is a local shortcut so the
# param model can validate without spinning up build123d.
_THREAD_MAJOR_RADIUS: dict[str, float] = {
    "M2": 1.0,
    "M2.5": 1.25,
    "M3": 1.5,
    "M4": 2.0,
    "M5": 2.5,
    "M6": 3.0,
}

# Approximate tap-drill diameters (mm) for internal threads — used to compute
# the actual drilled hole diameter that the tap cuts. Conservative (coarse).
_TAP_DRILL_DIAMETER: dict[str, float] = {
    "M2": 1.6,
    "M2.5": 2.05,
    "M3": 2.5,
    "M4": 3.3,
    "M5": 4.2,
    "M6": 5.0,
}


def _thread_major_radius(thread: str) -> float:
    if thread not in _THREAD_MAJOR_RADIUS:
        raise ValueError(f"Unknown thread spec {thread!r}; extend _THREAD_MAJOR_RADIUS.")
    return _THREAD_MAJOR_RADIUS[thread]


def _tap_drill_radius(thread: str) -> float:
    if thread not in _TAP_DRILL_DIAMETER:
        raise ValueError(f"Unknown thread spec {thread!r}; extend _TAP_DRILL_DIAMETER.")
    return _TAP_DRILL_DIAMETER[thread] / 2


# ---------------------------------------------------------------------------
# Process configuration — prototype vs production fits
# ---------------------------------------------------------------------------


class ProcessConfig(BaseModel):
    """Manufacturing-process flags. Owns prototype/production fit clearances."""

    model_config = ConfigDict(validate_assignment=True)

    prototype: bool = Field(
        default=True,
        description="True for FDM 3D-print prototype. False for machined brass production.",
    )

    fdm_sliding_clearance: float = Field(
        default=0.25,
        gt=0,
        description="Radial sliding-fit clearance for FDM print. Used in place of H7/g6.",
        json_schema_extra=_spec("§8 — Critical fits (prototype override)"),
    )
    cnc_sliding_clearance: float = Field(
        default=0.03,
        gt=0,
        description="H7/g6 sliding-fit clearance for machined brass production.",
        json_schema_extra=_spec("§8 — Critical fits"),
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sliding_clearance(self) -> float:
        """Active sliding-fit clearance for the current process."""
        return self.fdm_sliding_clearance if self.prototype else self.cnc_sliding_clearance


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
        default=1.5,
        gt=0,
        description="X dimension of the user-supplied shim between blades. Sets the purfling channel width. ESTIMATE — user choice.",
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
        default="M3",
        description="Grub-screw thread designation.",
        json_schema_extra=_spec("§4.2.15", units=""),
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
    outer_diameter: float = Field(
        default=7.9,
        gt=0,
        description="Shaft OD (measured on the original tool).",
        json_schema_extra=_spec("§4.2.12", status="MEASURED"),
    )
    blade_slot_width: float = Field(
        default=6.0,
        gt=0,
        description="X dimension of blade slot (along the shaft). Fits 4 retainers + 2 blades + channel spacer + ~1.6 mm grub-screw advance.",
        json_schema_extra=_spec("§4.2.8", status="MEASURED"),
    )
    blade_slot_length: float = Field(
        default=5.0,
        gt=0,
        description="Y dimension of blade slot (across the shaft). The 5 mm direction; fits blade.width (4 mm) plus clearance. Z is the open through direction (blades drop through).",
        json_schema_extra=_spec("§4.2.9", status="MEASURED"),
    )
    end_to_slot_distance: float = Field(
        default=8.0,
        gt=0,
        description="Distance from shaft right end face to right wall of blade slot.",
        json_schema_extra=_spec("§4.2.17"),
    )
    end_tap_depth: float = Field(
        default=5.0,
        gt=0,
        description="Depth of grub-screw tap from the right end face. Sets §4.2.14 wall.",
        json_schema_extra=_spec("§4.2.14 (related)"),
    )
    length: float = Field(
        default=100.0,
        gt=0,
        description="Total shaft length. Slot + travel + drive-plate clearance.",
        json_schema_extra=_spec("§4.2.18"),
    )
    drive_plate_mount_thread: str = Field(
        default="M2",
        description="Thread for the two screws mounting the drive plate to the shaft's outboard end face.",
        json_schema_extra=_spec("§4.2.19", units=""),
    )
    drive_plate_mount_spacing: float = Field(
        default=4.0,
        gt=0,
        description="Centre-to-centre spacing between the two drive-plate mount screws.",
        json_schema_extra=_spec("§4.2.19"),
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
        default=8.11,
        gt=0,
        description="Radius of the spherical dome at the +Z end of the shank (next to the drive screw). Rounded in *both* X and Y directions — i.e. a sphere, not a single-axis cylinder like the working face. Similar radius to working_face_radius per the original. Bottom (−Z) face is flat.",
        json_schema_extra=_spec("§4.3 (top dome — not in spec)", status="MEASURED"),
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
        json_schema_extra=_spec("§4.4.38"),
    )
    length: float = Field(
        default=25.0,
        gt=0,
        description="Threaded length. Must support full X travel + engagement.",
        json_schema_extra=_spec("§4.4.39"),
    )
    left_face_tap: str = Field(
        default="M2",
        description="Thread of the tap on the thumbwheel's left end face (for silver screw).",
        json_schema_extra=_spec("§4.4.40", units=""),
    )
    left_face_tap_depth: float = Field(
        default=4.0,
        gt=0,
        description="Depth of the tap. Silver screw bottoms on this — sets bearing geometry.",
        json_schema_extra=_spec("§4.4.40"),
    )


class ThumbwheelParams(BaseModel):
    """§4.4 items 41–43 — thumbwheel (integral with drive screw)."""

    diameter: float = Field(
        default=18.0,
        gt=0,
        description="Thumbwheel knurled disc OD.",
        json_schema_extra=_spec("§4.4.41"),
    )
    thickness: float = Field(
        default=5.0,
        gt=0,
        description="Thumbwheel thickness (X dimension).",
        json_schema_extra=_spec("§4.4.42"),
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
    """§4.5 items 45–49 — drive plate that lets the drive screw pull the shaft."""

    height: float = Field(
        default=12.0,
        gt=0,
        description="Plate height above shaft. Must reach drive-screw axis.",
        json_schema_extra=_spec("§4.5.45"),
    )
    width: float = Field(
        default=8.0,
        gt=0,
        description="Plate Z dimension.",
        json_schema_extra=_spec("§4.5.46"),
    )
    thickness: float = Field(
        default=2.0,
        gt=0,
        description="Plate X dimension (1.5–2.5 mm typical).",
        json_schema_extra=_spec("§4.5.47"),
    )
    clearance_hole_diameter: float = Field(
        default=2.4,
        gt=0,
        description="Clearance hole the silver screw passes through (loose fit).",
        json_schema_extra=_spec("§4.5.48"),
    )


class SilverScrewParams(BaseModel):
    """§4.5 items 50, 52 — silver screw. Its length is owned by captive_bearing (§4.5.51)."""

    thread: str = Field(
        default="M2",
        description="Silver-screw thread. Matches drive_screw.left_face_tap (§4.4.40).",
        json_schema_extra=_spec("§4.5.50", units=""),
    )
    head_diameter: float = Field(
        default=4.0,
        gt=0,
        description="Head diameter. Must exceed drive_plate.clearance_hole_diameter.",
        json_schema_extra=_spec("§4.5.52"),
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
        description="Designed axial bearing clearance (0.1–0.3 mm). The non-binding gap.",
        json_schema_extra=_spec("§4.5.53"),
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

    # --- Cross-part derived values (§4 derivations) -------------------------

    @computed_field  # type: ignore[prop-decorator]
    @property
    def stack_thickness(self) -> float:
        """
        §4.1.7 — total clamped stack thickness in X direction (along shaft).

        Layout in the slot's X direction: retainer | retainer | blade |
        channel-spacer | blade | retainer | retainer | grub-screw slack.
        4 × retainer.thickness + 2 × blade.thickness + spacer.thickness.

        The original spec defined this as just 2 × blade + spacer; the real
        tool's 4 retainers also stack in this direction. With the default
        1.5 mm channel spacer this gives 5.9 mm, leaving only 0.1 mm of
        grub-screw advance in a 6 mm slot — measured "spare at the end"
        is 1.6 mm with no channel spacer, dropping as the user adds one.
        """
        return (
            4 * self.blade_retainer.thickness
            + 2 * self.blade.thickness
            + self.spacer.thickness
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def crossbore_diameter(self) -> float:
        """§4.3.20 — shaft OD plus process-appropriate sliding clearance."""
        return self.shaft.outer_diameter + self.process.sliding_clearance

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tapped_bore_drill_diameter(self) -> float:
        """Drill diameter for the shank tapped bore — derived from drive-screw thread."""
        return _TAP_DRILL_DIAMETER[self.drive_screw.thread]

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
        (shaft.outer_diameter − blade_slot_length) / 2 (where
        blade_slot_length is the slot's Y cross-section dim).
        """
        return (self.shaft.outer_diameter - self.shaft.blade_slot_length) / 2

    @computed_field  # type: ignore[prop-decorator]
    @property
    def shaft_wall_around_end_tap(self) -> float:
        """§4.2.14 — wall between bottom of grub-screw tap and far wall of slot."""
        return self.shaft.end_to_slot_distance - self.shaft.end_tap_depth

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

        # §4.2.14 — wall around shaft end tap
        min_end_tap_wall = 1.0 * _thread_major_radius(self.grub_screw.thread)
        if self.shaft_wall_around_end_tap < min_end_tap_wall:
            raise ValueError(
                f"shaft_wall_around_end_tap ({self.shaft_wall_around_end_tap:.3f}) "
                f"< min {min_end_tap_wall:.3f} (§4.2.14)."
            )

        # §4.3.23 — wall between bores
        min_wall_bb = max(1.2, 1.0 * _thread_major_radius(self.drive_screw.thread))
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
        min_wall_tap = max(1.0, 1.0 * _thread_major_radius(self.drive_screw.thread))
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
