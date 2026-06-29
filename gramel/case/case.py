"""
Clamshell print-in-place case geometry.

Case frame (case lying flat on a bench):
  CX: long axis. Aligns with the tool's Z (shank length).
       CX=0 sits at the bottom of the shank; the depth-lock knob extends
       to CX < 0; the shank top is at CX = shank.length.
  CY: short horizontal axis. Aligns with the tool's X (shaft direction).
       CY=0 sits at the shaft centre.
  CZ: vertical, short. Aligns with the tool's Y (tool depth).
       Split plane at CZ = 0 — base at CZ < 0, lid at CZ > 0.

Hinge: two clusters along the +CY back edge. Each cluster has a teardrop
pin (round bottom + 45° point) integral to the lid, protruding into a
matching teardrop bore in the base. Pin axis runs along CY.

Magnets: two pairs along the −CY front edge, blind pockets opening onto
the CZ=0 mating face.
"""

import math
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    Circle,
    Compound,
    Cylinder,
    FontStyle,
    Part,
    Plane,
    Polygon,
    Pos,
    Rot,
    Text,
    extrude,
)

from gramel.case.parameters import CaseParams
from gramel.parameters import PurflingCutterParams

# Font file shipped alongside this module; matches the Chelli Strings
# branding used by pzfreo/pegturner.
_LOGO_FONT_PATH = str(Path(__file__).parent / "MrsSaintDelafield-Regular.ttf")

# Cascading V-taper angles for the engraved letters — steepest first so
# the recess is self-supporting when the lid prints face-down. Falls
# back to gentler angles, then a straight extrude as last resort, if a
# particular glyph's thin strokes can't survive the chosen taper.
_ENGRAVE_TAPER_ANGLES = (45, 30, 20, 10)


# ---------------------------------------------------------------------------
# Coordinate transform: tool frame → case frame
# ---------------------------------------------------------------------------


def _tool_to_case(part: Part) -> Part:
    """Rotate a tool-frame Part into case frame.

    Mapping:
      tool_X (shaft) → case_Y
      tool_Y (depth) → case_Z
      tool_Z (shank long axis) → case_X

    Achieved by two 90° rotations: rotate +90° about world Z then +90° about
    world X. Equivalent single rotation handled by build123d Rot composition.
    """
    return Rot(90, 0, 90) * part


# ---------------------------------------------------------------------------
# Tool pocket (the negative carved out of the case interior), in CASE FRAME
# ---------------------------------------------------------------------------


def cutter_travel_offsets(cutter: PurflingCutterParams) -> tuple[float, float]:
    """Shaft X-travel limits (tool frame) as signed offsets from the centred
    (build_assembly default) position:

      retract_off ≤ 0 — shaft pulled back until the blade slot's inboard edge
        reaches the shank working face (blades/bones can't enter the crossbore).
      insert_off  ≥ 0 — shaft pushed in until the drive-screw thread is fully
        engaged (its root reaches the shank back face).

    These are the real, asymmetric end-stops of the edge-margin adjustment, so
    the case sizes the cutter trough + blade well to them rather than to a
    symmetric ±guess.
    """
    from gramel.parts.shank import build_shank

    sb = build_shank(cutter).bounding_box()
    working_face, back_face = sb.max.X, sb.min.X
    sp = cutter.shaft
    slot_inboard = -sp.length / 2 + sp.length - sp.end_to_slot_distance - sp.blade_slot_width
    thread_root = (
        -sp.length / 2
        + cutter.thumbwheel.boss_length
        + cutter.thumbwheel.thickness
        + cutter.drive_screw.unthreaded_length
    )
    return (working_face - slot_inboard, back_face - thread_root)


def _tool_pocket(cutter: PurflingCutterParams, case: CaseParams) -> Part:
    """Build the union of all clearance volumes the tool needs inside the case.

    All boxes are constructed directly in CASE FRAME so we don't have to
    rotate compound geometry. The shapes are simple boxes / cylinders sized
    from the tool's parameters with the necessary clearance margins.
    """
    sk = cutter.shank
    tc = case.tool_clearance
    # Real asymmetric shaft travel + a small safety margin (case.cutter_x_travel)
    retract_off, insert_off = cutter_travel_offsets(cutter)
    margin = case.cutter_x_travel

    # Crossbore Z in tool frame = case X of the shaft centre
    crossbore_cx = sk.length - sk.crossbore_position_from_top  # 66 default
    tapped_cx = sk.length - cutter.tapped_bore_position_from_top  # 75.5 default

    pocket = Part()

    # Assembled tool, used below for (a) the cutter trough's case-Y extent and
    # (b) the depth-lock knob pocket depth. The bolt knob hangs below the shank
    # by an amount that depends on the push-rod length (the bolt sits as low as
    # the rod allows at lock), so take the tool's real lowest point rather than
    # assuming the knob bottoms on the shank.
    from gramel.assembly import build_assembly

    centred_bb = build_assembly(cutter).bounding_box()

    # --- Shank pocket ----------------------------------------------------
    # Case X: 0..shank.length (= along shank long axis)
    # Case Y: ±shank.width/2 (shank's X = shaft direction = case Y)
    # Case Z: ±shank.depth/2 (shank's Y = depth = case Z, vertical)
    shank_cx_extent = sk.length + 2 * tc
    shank_cy_extent = sk.width + 2 * tc
    shank_cz_extent = sk.depth + 2 * tc
    shank_cx_centre = sk.length / 2
    pocket += Pos(shank_cx_centre, 0, 0) * Box(
        shank_cx_extent, shank_cy_extent, shank_cz_extent
    )

    # --- Depth-lock knob pocket -----------------------------------------
    # The knob, plus the bolt collar/thread below it, hang below the shank down
    # to the tool's lowest point (centred_bb.min.Z in tool Z = case X). Reach
    # the pocket down to there with clearance, rather than assuming the knob
    # bottoms on the shank (which the push-rod preload margin prevents).
    knob = cutter.depth_lock
    knob_r = knob.knob_diameter / 2 + tc
    knob_cx_min = centred_bb.min.Z - tc
    knob_cx_max = 0.0  # up to the shank bottom
    knob_cx_extent = knob_cx_max - knob_cx_min
    knob_cx_centre = (knob_cx_min + knob_cx_max) / 2
    # Cylinder along CX → axis must be along X. Build with Rot(0, 90, 0) of a Z-axis cylinder.
    pocket += Pos(knob_cx_centre, 0, 0) * Rot(0, 90, 0) * Cylinder(
        radius=knob_r, height=knob_cx_extent
    )

    # --- Cutter trough --------------------------------------------------
    # The whole cutter assembly (shaft + drive plate + thumbwheel) is a long
    # horizontal feature at the crossbore-Z level (= case X around 66).
    # In tool frame the centred bbox X extent is ~[-22, +22]; that becomes
    # case Y. Travel adds ±cutter_x_travel to that range.
    # In tool frame the cutter Z (vertical) spans from below-shaft to above-
    # thumbwheel-disc; that becomes case X extent for the cutter trough.
    # tool X bounds → case Y bounds, ± travel + clearance
    cutter_cy_min = centred_bb.min.X + retract_off - margin - tc
    cutter_cy_max = centred_bb.max.X + insert_off + margin + tc
    cutter_cy_extent = cutter_cy_max - cutter_cy_min
    cutter_cy_centre = (cutter_cy_min + cutter_cy_max) / 2

    # tool Z extent of cutter region: from below shaft to thumbwheel top
    cutter_cx_min = crossbore_cx - cutter.shaft_outer_diameter / 2 - tc
    cutter_cx_max = tapped_cx + cutter.thumbwheel.diameter / 2 + tc
    cutter_cx_extent = cutter_cx_max - cutter_cx_min
    cutter_cx_centre = (cutter_cx_min + cutter_cx_max) / 2

    # Case Z extent = tool Y extent = tool depth + clearance
    cutter_cz_extent = sk.depth + 2 * tc

    pocket += Pos(cutter_cx_centre, cutter_cy_centre, 0) * Box(
        cutter_cx_extent, cutter_cy_extent, cutter_cz_extent
    )

    # --- Blade well (deep channel below the shank for blade tip drop) ----
    # In tool frame: blade Z range = 39..79 (from max drop tip to min drop top).
    # That becomes case X = 39..79 (along shank length).
    # In tool frame: blade is at slot X (≈ +7..+13.5 centred) ± travel.
    # That becomes case Y range.
    # In tool frame: blade Y extent ≈ ±blade.width/2; becomes case Z = ±half-width + bc.
    bc = case.blade_clearance

    # Blade tip Z (tool frame) at max drop
    retainer_bottom_tool_z = crossbore_cx - cutter.blade_retainer.length / 2
    blade_tip_at_max_drop = retainer_bottom_tool_z - case.blade_drop_max
    # Blade top at min drop
    blade_top_at_min_drop = retainer_bottom_tool_z - case.blade_drop_min + cutter.blade.length
    # Cover both extremes plus retainer top so the slot region is open
    retainer_top_tool_z = crossbore_cx + cutter.blade_retainer.length / 2
    blade_cx_min = blade_tip_at_max_drop - bc
    blade_cx_max = max(retainer_top_tool_z, blade_top_at_min_drop) + bc
    blade_cx_extent = blade_cx_max - blade_cx_min
    blade_cx_centre = (blade_cx_max + blade_cx_min) / 2

    # Blade CY range (= tool X = slot X position ± travel)
    slot_x_min_centred = -cutter.shaft.length / 2 + cutter.shaft.length - cutter.shaft.end_to_slot_distance - cutter.shaft.blade_slot_width
    slot_x_max_centred = slot_x_min_centred + cutter.shaft.blade_slot_width
    blade_cy_min = slot_x_min_centred + retract_off - margin - bc
    blade_cy_max = slot_x_max_centred + insert_off + margin + bc
    blade_cy_extent = blade_cy_max - blade_cy_min
    blade_cy_centre = (blade_cy_max + blade_cy_min) / 2

    # Blade CZ range (= tool Y = blade width + clearance)
    blade_cz_extent = cutter.blade.width + 2 * bc

    pocket += Pos(blade_cx_centre, blade_cy_centre, 0) * Box(
        blade_cx_extent, blade_cy_extent, blade_cz_extent
    )

    return pocket


# ---------------------------------------------------------------------------
# Case bounds and outer shell
# ---------------------------------------------------------------------------


def _case_bounds(cutter: PurflingCutterParams, case: CaseParams) -> dict[str, float]:
    """Compute the case interior + exterior bounds based on the pocket envelope."""
    pocket = _tool_pocket(cutter, case)
    bb = pocket.bounding_box()
    w = case.wall_thickness

    int_cx_min, int_cx_max = bb.min.X, bb.max.X
    int_cy_min, int_cy_max = bb.min.Y, bb.max.Y
    int_cz_min, int_cz_max = bb.min.Z, bb.max.Z

    ext_cx_min = int_cx_min - w
    ext_cx_max = int_cx_max + w
    ext_cy_min = int_cy_min - w
    ext_cy_max = int_cy_max + w
    ext_cz_min = int_cz_min - w
    ext_cz_max = int_cz_max + w

    # Hinge cluster CY centre: at the +CY edge wall midplane
    hinge_cy = ext_cy_max - w / 2

    # Magnet pocket CY centre: at the -CY edge wall, magnet pocket centre
    magnet_cy = ext_cy_min + w + case.magnet_back_wall + case.magnet_thickness / 2

    return {
        "int_cx_min": int_cx_min,
        "int_cx_max": int_cx_max,
        "int_cy_min": int_cy_min,
        "int_cy_max": int_cy_max,
        "int_cz_min": int_cz_min,
        "int_cz_max": int_cz_max,
        "ext_cx_min": ext_cx_min,
        "ext_cx_max": ext_cx_max,
        "ext_cy_min": ext_cy_min,
        "ext_cy_max": ext_cy_max,
        "ext_cz_min": ext_cz_min,
        "ext_cz_max": ext_cz_max,
        "hinge_cy": hinge_cy,
        "magnet_cy": magnet_cy,
    }


def _build_outer_shell(bounds: dict[str, float], case: CaseParams) -> Part:
    """Solid rounded brick covering the closed case envelope."""
    cx_size = bounds["ext_cx_max"] - bounds["ext_cx_min"]
    cy_size = bounds["ext_cy_max"] - bounds["ext_cy_min"]
    cz_size = bounds["ext_cz_max"] - bounds["ext_cz_min"]
    cx_c = (bounds["ext_cx_max"] + bounds["ext_cx_min"]) / 2
    cy_c = (bounds["ext_cy_max"] + bounds["ext_cy_min"]) / 2
    cz_c = (bounds["ext_cz_max"] + bounds["ext_cz_min"]) / 2

    shell: Part = Part() + Pos(cx_c, cy_c, cz_c) * Box(cx_size, cy_size, cz_size)
    r = case.corner_radius
    if r > 0:
        # Fillet vertical edges (along CZ) only — those are the four corners
        # of the closed brick. Top/bottom edges stay sharp to keep boolean
        # geometry tractable.
        vertical_edges = shell.edges().filter_by(Axis.Z)
        if len(vertical_edges) >= 4:
            shell = shell.fillet(r, vertical_edges)
    return shell


# ---------------------------------------------------------------------------
# Teardrop hinge primitives
# ---------------------------------------------------------------------------


def _teardrop_cross_section_box(
    diameter: float, angle_deg: float, length_along_axis: float, axis_centre: tuple[float, float, float]
) -> Part:
    """Build a teardrop cylinder along the CY axis.

    Teardrop cross-section (in CX-CZ plane):
      - Round bottom: circle of given diameter centred at (cx, cz) = axis_centre's (X, Z)
      - Pointed top: triangular cap rising above the circle. The point angle
        is 2 × angle_deg (measured at the apex). Apex apex sits at
        Z = axis_z + diameter/2 + apex_height where apex_height = (radius)/tan(angle_deg).
        With angle_deg = 45°, apex_height = radius so the apex is at
        Z = axis_z + 2 × radius.

    The whole shape extends along CY for length_along_axis, centred on
    axis_centre's CY component.
    """
    radius = diameter / 2
    cx, cy, cz = axis_centre
    angle_rad = math.radians(angle_deg)
    apex_height = radius / math.tan(angle_rad)

    # Build the 2D teardrop on Plane.XZ centred on the origin: a Circle of
    # given radius + a Triangle on top whose apex sits at (0, radius+apex_height).
    circle = Circle(radius=radius)
    triangle = Polygon(
        (-radius, 0),
        (+radius, 0),
        (0, radius + apex_height),
        align=None,
    )
    teardrop_2d = circle + triangle

    # Extrude along Plane.XZ's normal (+Y direction).
    teardrop_extruded = extrude(Plane.XZ * teardrop_2d, amount=length_along_axis)

    # The extrusion starts at Y=0 and extends to Y=length. Shift so it's
    # centred on axis_centre.
    return Pos(cx, cy - length_along_axis / 2, cz) * teardrop_extruded


def _teardrop_cylinder_along_cx(
    diameter: float,
    angle_deg: float,
    length_along_cx: float,
    axis_centre: tuple[float, float, float],
    apex_direction: int = +1,
) -> Part:
    """Build a teardrop cylinder along the CX axis (hinge axis).

    Cross-section (in CY-CZ plane):
      Round bottom (centred at axis_centre's CY/CZ) + triangular apex.
      apex_direction = +1 → apex in +CZ direction (printable for the base
        half — apex points away from bed in print orientation).
      apex_direction = -1 → apex in -CZ direction (printable for the lid
        half — after 180° rotation about CX axis to flat-print orientation,
        apex points away from bed).

    Extruded along CX for `length_along_cx`, centred on axis_centre's CX.
    """
    radius = diameter / 2
    cx, cy, cz = axis_centre
    angle_rad = math.radians(angle_deg)
    apex_height = radius / math.tan(angle_rad)

    # 2D teardrop in Plane.YZ (sketch X = CY, sketch Y = CZ) centred at origin
    circle = Circle(radius=radius)
    if apex_direction >= 0:
        triangle = Polygon(
            (-radius, 0),
            (+radius, 0),
            (0, radius + apex_height),
            align=None,
        )
    else:
        triangle = Polygon(
            (-radius, 0),
            (+radius, 0),
            (0, -(radius + apex_height)),
            align=None,
        )
    teardrop_2d = circle + triangle

    # Extrude along Plane.YZ normal (+X direction)
    teardrop_extruded = extrude(Plane.YZ * teardrop_2d, amount=length_along_cx)

    return Pos(cx - length_along_cx / 2, cy, cz) * teardrop_extruded


def _build_hinge_features(
    bounds: dict[str, float], case: CaseParams
) -> tuple[Part, Part, Part, Part]:
    """Return (lid_add, base_add, lid_cavities, base_cavities).

    Hinge design (matched to the Oral-B reference case):
      - Two clusters at the CX ends of the back edge
      - Each cluster has alternating knuckles along CX: L, B (2 knuckles)
      - Each knuckle is a TEARDROP cylinder along the CX axis, integral
        with its owning half's wall (the wall locally thickens into the
        teardrop)
      - The opposing half has a matching teardrop CAVITY (slightly larger
        for clearance)
      - LID teardrops: apex in -CZ direction (case frame). After 180°
        rotation to flat-print orientation, apex points UP in print.
      - BASE teardrops: apex in +CZ direction (case frame), already UP in
        print orientation for the un-rotated base.

    lid_add, base_add: solid teardrops to UNION with each half's body
    lid_cavities, base_cavities: cavities to SUBTRACT from each half's body
    """
    # Teardrop round body diameter (reference ≈ 5.7 mm — matched by default
    # hinge_pin_round_diameter = 2.85 so teardrop_d = 5.7).
    teardrop_d = case.hinge_pin_round_diameter * 2
    angle_deg = case.hinge_teardrop_angle_deg
    # Cavity must accommodate the teardrop pin's full rotational sweep about
    # the hinge axis. The teardrop's apex extends (r + apex_height) from the
    # axis. With 45° angle apex_height = r so max sweep radius = 2r.
    # Cavity is a CIRCULAR bore (cylinder) sized to clear the sweep at any
    # rotation angle.
    teardrop_r = teardrop_d / 2
    apex_height = teardrop_r / math.tan(math.radians(angle_deg))
    max_sweep_radius = teardrop_r + apex_height
    cavity_d = 2 * max_sweep_radius + 2 * case.hinge_bore_radial_clearance
    kl = case.hinge_knuckle_length
    gap = case.hinge_axial_clearance
    n_per_cluster = case.hinge_knuckles_per_cluster

    # Hinge axis at the MATING FACE level (CZ=0). This is where the two
    # halves meet when closed. A 180° rotation about this axis correctly
    # maps the lid from its closed position (above base) to print-flat
    # position (next to base on the bed). The bind at intermediate angles
    # is unavoidable for clamshell hinges (the reference has it too) — the
    # PETG flexes through it during first-time closing.
    teardrop_r = case.hinge_pin_round_diameter
    hinge_cy_axis = bounds["ext_cy_max"] + teardrop_r - case.hinge_axis_offset
    hinge_cz_axis = 0.0

    # Cluster CX positions
    n_clusters = case.hinge_cluster_count
    cluster_total_len = n_per_cluster * kl + (n_per_cluster - 1) * gap
    cx_min_centre = bounds["ext_cx_min"] + case.hinge_cluster_end_margin + cluster_total_len / 2
    cx_max_centre = bounds["ext_cx_max"] - case.hinge_cluster_end_margin - cluster_total_len / 2
    if n_clusters == 1:
        cluster_cx_centres = [(cx_min_centre + cx_max_centre) / 2]
    else:
        cluster_cx_centres = [
            cx_min_centre + (cx_max_centre - cx_min_centre) * i / (n_clusters - 1)
            for i in range(n_clusters)
        ]

    lid_add = Part()
    base_add = Part()
    lid_cavities = Part()
    base_cavities = Part()

    cavity_length = kl + 2 * gap

    # ASYMMETRIC design matching the reference: ALL knuckles are teardrop
    # pins on the LID (with apex extending in -CZ → +CZ in print orientation).
    # The BASE has matching ROUND bores (no apex). This allows the lid's
    # teardrop pins to rotate freely inside the round bores at any angle,
    # eliminating the intermediate-angle bind.
    for cluster_cx in cluster_cx_centres:
        cluster_cx_min = cluster_cx - cluster_total_len / 2
        for i in range(n_per_cluster):
            knuckle_cx_centre = cluster_cx_min + i * (kl + gap) + kl / 2

            # LID teardrop pin (apex in -CZ direction → UP in print after rotation)
            teardrop = _teardrop_cylinder_along_cx(
                diameter=teardrop_d,
                angle_deg=angle_deg,
                length_along_cx=kl,
                axis_centre=(knuckle_cx_centre, hinge_cy_axis, hinge_cz_axis),
                apex_direction=-1,
            )
            lid_add += teardrop

            # BASE round bore (cylinder along CX) sized for teardrop sweep
            cavity = Pos(knuckle_cx_centre, hinge_cy_axis, hinge_cz_axis) * Rot(0, 90, 0) * Cylinder(
                radius=cavity_d / 2, height=cavity_length
            )
            base_cavities += cavity

    return lid_add, base_add, lid_cavities, base_cavities


# ---------------------------------------------------------------------------
# Magnet pockets
# ---------------------------------------------------------------------------


def _magnet_cx_positions(
    bounds: dict[str, float], case: CaseParams, cutter: PurflingCutterParams
) -> list[float]:
    """Pick CX positions for the magnet pairs along the -CY front edge.

    The +CX end of the case overlaps with the cutter trough (drive train
    region), so magnets can't go there — they'd cut into the tool clearance
    area. Restrict magnet CX positions to the SHANK region (CX < cutter
    trough's CX min) so they always sit in solid wall material.
    """
    n = case.magnet_pairs
    cx_min = bounds["ext_cx_min"]
    sk = cutter.shank
    crossbore_cx = sk.length - sk.crossbore_position_from_top
    # Stay below the cutter trough's CX min (= crossbore - shaft_OD/2 - tc).
    # Use a conservative limit a bit further from the trough.
    cutter_trough_cx_min = crossbore_cx - cutter.shaft_outer_diameter / 2 - case.tool_clearance
    cx_max_usable = cutter_trough_cx_min - case.magnet_diameter / 2 - 1.0

    margin = case.corner_radius + case.magnet_diameter / 2 + 2.0
    if n == 1:
        return [(cx_min + margin + cx_max_usable) / 2]
    if n == 2:
        return [cx_min + margin, cx_max_usable]
    return [
        cx_min + margin + (cx_max_usable - cx_min - margin) * i / (n - 1)
        for i in range(n)
    ]


def _build_magnet_pockets(
    bounds: dict[str, float], case: CaseParams, cutter: PurflingCutterParams, half: str
) -> Part:
    """Cylindrical pockets opening onto the CZ=0 mating face for one half."""
    pockets = Part()
    d = case.magnet_diameter + 2 * case.magnet_pocket_clearance
    h = case.magnet_thickness + case.magnet_pocket_clearance
    # Pocket axis along CZ. Lid (CZ>0) has pocket opening at CZ=0, extending +CZ.
    # Base (CZ<0) has pocket opening at CZ=0, extending -CZ.
    sign = +1 if half == "lid" else -1
    for cx in _magnet_cx_positions(bounds, case, cutter):
        pocket = Pos(cx, bounds["magnet_cy"], sign * h / 2) * Cylinder(
            radius=d / 2, height=h
        )
        pockets += pocket
    return pockets


# ---------------------------------------------------------------------------
# Top-level build
# ---------------------------------------------------------------------------


def _engrave_lid_logo(lid: Part, bounds: dict[str, float], case: CaseParams) -> Part:
    """Recess the configured logo text into the lid's outer-top face.

    Each line is extruded *down* from CZ=ext_cz_max into the lid with a
    V-taper (steepest first, fallback chain) so the cavity is self-
    supporting when the lid prints face-down in the flat-open print
    orientation (the lid's outer-top sits on the bed).

    The text block is built at the origin (lines stacked along ±Y),
    then rotated about the lid-top normal by ``case.logo_rotation``
    (degrees CCW), then translated to the lid centre.

    Returns the lid unchanged if logo_text is empty.
    """
    if not case.logo_text:
        return lid

    cx_c = (bounds["ext_cx_max"] + bounds["ext_cx_min"]) / 2
    cy_c = (bounds["ext_cy_max"] + bounds["ext_cy_min"]) / 2
    cz_top = bounds["ext_cz_max"]

    text_lines = case.logo_text.split("\n")
    line_spacing = case.logo_size
    total_text_height = (len(text_lines) - 1) * line_spacing

    # Build the text block at the origin, with lines stacked along Y.
    text_solid = None
    for i, line in enumerate(text_lines):
        if not line.strip():
            continue
        y_offset = total_text_height / 2 - i * line_spacing
        line_sketch = Pos(0, y_offset) * Text(
            line,
            font_size=case.logo_size,
            font_path=_LOGO_FONT_PATH,
            font_style=FontStyle.BOLD,
            align=(Align.CENTER, Align.CENTER),
        )

        line_solid = None
        for taper in _ENGRAVE_TAPER_ANGLES:
            try:
                line_solid = Pos(0, 0, cz_top) * extrude(line_sketch, -case.logo_depth, taper=taper)
                break
            except Exception:
                continue
        if line_solid is None:
            line_solid = Pos(0, 0, cz_top) * extrude(line_sketch, -case.logo_depth)

        text_solid = line_solid if text_solid is None else text_solid + line_solid

    if text_solid is not None:
        text_solid = Pos(cx_c, cy_c, 0) * Rot(0, 0, case.logo_rotation) * text_solid
        lid = lid - text_solid
    return lid


def _half(
    half: str,
    cutter: PurflingCutterParams,
    case: CaseParams,
    bounds: dict[str, float],
    pocket: Part,
    lid_add: Part,
    base_add: Part,
    lid_cavities: Part,
    base_cavities: Part,
) -> Part:
    """Build one case half. half='lid' (CZ>0) or 'base' (CZ<0).

    Build order:
      1. Outer shell, clipped to the half-space
      2. Add this half's hinge teardrops (integral with the wall)
      3. Subtract the opposing half's hinge cavities (clearance for the
         other half's teardrops to enter when closed)
      4. Carve pocket (the tool clearance volume) — done AFTER hinge so
         the pocket can also cut through the teardrop overhangs that stick
         into the interior
      5. Carve magnet pockets
    """
    shell = _build_outer_shell(bounds, case)

    # Clip the shell to the CZ half-space at the split plane (CZ=0)
    cz_clip_size = (bounds["ext_cz_max"] - bounds["ext_cz_min"]) * 2 + 20
    cx_size = (bounds["ext_cx_max"] - bounds["ext_cx_min"]) + 20
    cy_size = (bounds["ext_cy_max"] - bounds["ext_cy_min"]) + 20
    cx_c = (bounds["ext_cx_max"] + bounds["ext_cx_min"]) / 2
    cy_c = (bounds["ext_cy_max"] + bounds["ext_cy_min"]) / 2
    if half == "lid":
        clip = Pos(cx_c, cy_c, cz_clip_size / 4) * Box(cx_size, cy_size, cz_clip_size / 2)
        my_add = lid_add
        my_cavities = lid_cavities
    else:
        clip = Pos(cx_c, cy_c, -cz_clip_size / 4) * Box(cx_size, cy_size, cz_clip_size / 2)
        my_add = base_add
        my_cavities = base_cavities

    body = shell & clip
    # Add this half's teardrop knuckles WITHOUT clipping — the teardrop apex
    # naturally extends into the opposing half's region (which has a matching
    # cavity to receive it). Clipping would chop off the apex.
    body = body + my_add
    # Subtract the cavities in this half (where the opposing half's teardrops
    # will sit when closed).
    body = body - my_cavities
    body = body - pocket
    body = body - _build_magnet_pockets(bounds, case, cutter, half)

    if half == "lid":
        body = _engrave_lid_logo(body, bounds, case)

    return body


def build_case(cutter: PurflingCutterParams, case: CaseParams, include_hinge: bool = True) -> Compound:
    """Build the clamshell case. Returns Compound of (base, lid).

    include_hinge=False omits all hinge geometry — useful when the final
    hinge will be added externally (e.g. by merging a third-party hinge STL
    via trimesh).
    """
    bounds = _case_bounds(cutter, case)
    pocket = _tool_pocket(cutter, case)
    if include_hinge:
        lid_add, base_add, lid_cavities, base_cavities = _build_hinge_features(bounds, case)
    else:
        lid_add = Part()
        base_add = Part()
        lid_cavities = Part()
        base_cavities = Part()

    base = _half("base", cutter, case, bounds, pocket, lid_add, base_add, lid_cavities, base_cavities)
    lid = _half("lid", cutter, case, bounds, pocket, lid_add, base_add, lid_cavities, base_cavities)

    return Compound(children=[base, lid])


def main() -> None:
    """CLI: build the case and export STEP."""
    from build123d import export_step

    cutter = PurflingCutterParams().model_copy(
        update={"process": PurflingCutterParams().process.model_copy(update={"prototype": False})}
    )
    case = CaseParams()
    c = build_case(cutter, case)
    export_step(c, "/tmp/case_clamshell.step")
    print(f"Exported /tmp/case_clamshell.step (volume = {c.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
