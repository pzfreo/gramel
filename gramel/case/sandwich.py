"""
"Option B" sandwich case — a SECOND, independent case design.

The carved-pocket clamshell in ``case.py`` is left untouched; this module
builds a different concept, ported from pzfreo/gibson-peg-turner
``tuner_case_v2``:

  * SHELL  — two thin-walled clamshell leaves: a plain protective box with a
             rectangular interior, NO carved tool pocket. Joined by the
             validated pip print-in-place hinge (the `pip-hinge` PyPI package,
             the same one gibson tuner_case_v2 prints with) fused in the flat
             print layout. Magnets sit in the front (−CY) corners, opposite the
             hinge (gibson corner-magnet placement), supplied with a boss since
             the thin box wall can't embed them.
  * INSERT — a separate flat tray that slides into the shell. It carries a
             silhouette pocket for the ASSEMBLED tool (the validated
             ``case._tool_pocket`` cut, so part fit is identical to the existing
             case) cut clean THROUGH so foam cushions the tool — and the exposed
             blades — top and bottom. A spares bay (inboard of the magnet band)
             holds spare blades + a 2 mm hex Allen key for the M4 grub screw,
             and the front-top edge is relieved so the closing lid can't pinch
             it (gibson tuner_case_v2 fix).

The shell's Z cavity = tool depth + ``foam_thickness`` of foam ABOVE and BELOW
the insert (a foam / insert / foam sandwich). Foam is supplied/cut by the user.

Case frame (shared with ``case.py``):
  CX: long axis  = tool Z (shank length); the hinge runs along the +CY edge.
  CY: short axis = tool X (shaft direction). Magnets on the −CY front edge.
  CZ: vertical   = tool Y (depth). Closed split plane at CZ = 0.

Outputs (gramel_sandwich_*):
  shell_print.{step,stl}  — both leaves flat on the bed, joined by the pip
                            hinge (lid unfolded 180° open); the print file
  insert.{step,stl}       — the slide-in insert tray
  assembly.step           — flat-open + populated (tool + spares), for fit viz
"""

import copy
import math

from build123d import (
    Align,
    Axis,
    Box,
    Compound,
    Cylinder,
    Part,
    Plane,
    Pos,
    Rot,
    export_step,
    export_stl,
    extrude,
)

# The validated print-in-place hinge is the `pip-hinge` PyPI package (the same
# one gibson-peg-turner tuner_case_v2 prints with) — NOT gramel's older vendored
# tools/pip_hinge.py copy. It's a project dependency; import it directly.
from pip_hinge import HingeParams, Knuckle, make_hinge

from gramel.assembly import build_assembly
from gramel.case.case import (
    _build_outer_shell,
    _engrave_lid_logo,
    _tool_pocket,
)
from gramel.case.parameters import SandwichCaseParams
from gramel.parameters import PurflingCutterParams
from gramel.parts.blade import build_blade

# Pip-hinge feel — values hard-won on real gibson tuner_case_v2 prints
# (pzfreo/gibson-peg-turner d1ef3da, fcc4f95). The library defaults print too
# stiff and crack the knuckles; these spin freely without going sloppy.
HINGE_PIVOT_CLEARANCE = 0.7   # radial pin/bore gap (mm)
HINGE_MOUNTING_FLAT = 1.0     # running gap between knuckle barrel and leaf wall
HINGE_CLASP_CLEARANCE = 0.6   # axial clasp gap (→ 0.3 mm between adjacent knuckles)
HINGE_STATIONS = 8            # even; clasp_width = hinge_length / stations
HINGE_END_MARGIN = 8.0        # CX gap at each end of the back-edge hinge


def _split_hinge_by_side(hinge: Compound) -> tuple[Compound, Compound]:
    """Sort the bare hinge's fragments into cs-side (+X) and ps-side (−X).

    At small mounting_flat the hinge comes back fragmented; classify each
    solid by its bbox X-centre and fuse each group into its leaf wall.
    (Same approach as gibson tuner_case._split_hinge_by_side.)
    """
    cs, ps = [], []
    for s in hinge.solids():
        bb = s.bounding_box()
        (cs if (bb.min.X + bb.max.X) >= 0 else ps).append(s)
    return Compound(cs), Compound(ps)

# ---------------------------------------------------------------------------
# Geometry: derive the insert footprint, shell cavity and shell envelope from
# the validated tool pocket bbox.
# ---------------------------------------------------------------------------


def _sandwich_geometry(
    cutter: PurflingCutterParams, params: SandwichCaseParams
) -> tuple[dict[str, float], Part, dict[str, float]]:
    """Return (bounds, tool_pocket, geom).

    ``bounds`` is the case-frame ext_*/int_* dict the reused ``case.py``
    helpers expect. ``tool_pocket`` is the validated clearance volume (also
    reused for the insert silhouette). ``geom`` carries insert/stack sizes.
    """
    case = params.shell
    sk = cutter.shank
    mw = params.min_insert_wall
    rim = params.insert_rim

    # Move the tool storage INWARD (+CY, toward the hinge) to open a clean band
    # along the front (−CY) edge for the spares bay, and expand the case to suit.
    pocket = _tool_pocket(cutter, case).translate((0, params.tool_inset, 0))
    bb = pocket.bounding_box()
    stack_h = bb.size.Z  # tool depth incl. clearance (~12 mm)

    # SINGLE spares pocket (Allen key + spare blades together), in the front
    # band below the shifted shank, clear of the corners and the cutter trough.
    shank_front = -(sk.width / 2 + case.tool_clearance) + params.tool_inset
    bay_cx_min = bb.min.X + params.tool_inset + 6.0   # under the shank, past the knob/corner
    bay_cx_max = bay_cx_min + params.spares_bay_length
    bay_cy_max = shank_front - mw                      # min wall below the tool
    bay_cy_min = bay_cy_max - params.spares_bay_depth

    # Insert footprint = bounding rect of (shifted tool ∪ spares bay) + rim.
    # The front (−CY) edge must also sit far enough below the deepest front tool
    # feature (the cutter trough, at bb.min.Y) for a front-corner magnet boss +
    # its insert notch to clear it with a real wall. Otherwise the notch eats
    # into the cutter and pinches the front rim off into a long unsupported wall.
    s = params.magnet_boss_radius / math.sqrt(2)
    mag_front_clear = s + params.magnet_boss_radius + mw
    ins_cx_min = min(bb.min.X, bay_cx_min) - rim
    ins_cx_max = max(bb.max.X, bay_cx_max) + rim
    ins_cy_min = min(bb.min.Y - rim, bay_cy_min - rim, bb.min.Y - mag_front_clear)
    ins_cy_max = max(bb.max.Y, bay_cy_max) + rim
    insert_cx = ins_cx_max - ins_cx_min
    insert_cy = ins_cy_max - ins_cy_min

    sc = params.slide_clearance
    int_cx_min, int_cx_max = ins_cx_min - sc, ins_cx_max + sc
    int_cy_min, int_cy_max = ins_cy_min - sc, ins_cy_max + sc
    cav_cz = stack_h + 2 * params.foam_thickness
    int_cz_min, int_cz_max = -cav_cz / 2, cav_cz / 2

    w = case.wall_thickness
    bounds = {
        "int_cx_min": int_cx_min,
        "int_cx_max": int_cx_max,
        "int_cy_min": int_cy_min,
        "int_cy_max": int_cy_max,
        "int_cz_min": int_cz_min,
        "int_cz_max": int_cz_max,
        "ext_cx_min": int_cx_min - w,
        "ext_cx_max": int_cx_max + w,
        "ext_cy_min": int_cy_min - w,
        "ext_cy_max": int_cy_max + w,
        "ext_cz_min": int_cz_min - w,
        "ext_cz_max": int_cz_max + w,
        # Hinge helper recomputes its own axis.
        "hinge_cy": int_cy_max + w / 2,
    }
    geom = {
        "stack_h": stack_h,
        "ins_cx_min": ins_cx_min,
        "ins_cx_max": ins_cx_max,
        "ins_cy_min": ins_cy_min,
        "ins_cy_max": ins_cy_max,
        "insert_cx": insert_cx,
        "insert_cy": insert_cy,
        "cav_cz": cav_cz,
        "bay_cx_min": bay_cx_min,
        "bay_cx_max": bay_cx_max,
        "bay_cy_min": bay_cy_min,
        "bay_cy_max": bay_cy_max,
    }
    return bounds, pocket, geom


# ---------------------------------------------------------------------------
# Magnet corner bosses (thin-wall shell)
# ---------------------------------------------------------------------------


def _corner_magnet_positions(
    bounds: dict[str, float], params: SandwichCaseParams
) -> list[tuple[float, float]]:
    """Boss centres at the two FRONT (−CY) corners, opposite the hinge — the
    gibson tuner_case_v2 corner-magnet placement. Each boss is inset diagonally
    from the inner corner by BOSS_R/√2 so it fillets the corner."""
    s = params.magnet_boss_radius / math.sqrt(2)
    cy = bounds["int_cy_min"] + s  # inset toward the interior (+CY)
    return [
        (bounds["int_cx_min"] + s, cy),  # −CX front corner
        (bounds["int_cx_max"] - s, cy),  # +CX front corner
    ]


def _apply_corner_magnets(
    body: Part,
    bounds: dict[str, float],
    params: SandwichCaseParams,
    half: str,
) -> Part:
    """Add a boss + magnet pocket at each front corner for one half.

    Boss axis is CZ; the pocket opens on the CZ=0 mating face so the closed
    leaves attract. (gibson tuner_case_v2 add_corner_magnet_pockets.)
    """
    case = params.shell
    boss_r = params.magnet_boss_radius
    pkt_r = case.magnet_diameter / 2 + case.magnet_pocket_clearance
    pkt_h = case.magnet_thickness + case.magnet_pocket_clearance
    leaf_h = bounds["ext_cz_max"] if half == "lid" else -bounds["ext_cz_min"]
    z_align = Align.MIN if half == "lid" else Align.MAX

    for cx, cy in _corner_magnet_positions(bounds, params):
        boss = Cylinder(
            boss_r, leaf_h, align=(Align.CENTER, Align.CENTER, Align.MIN)
        ).translate((cx, cy, 0 if half == "lid" else -leaf_h))
        body = body + boss
        pocket = Cylinder(
            pkt_r, pkt_h, align=(Align.CENTER, Align.CENTER, z_align)
        ).translate((cx, cy, 0))
        body = body - pocket
    return body


# ---------------------------------------------------------------------------
# Insert tray
# ---------------------------------------------------------------------------


def _spares_cut(geom: dict[str, float]) -> Part:
    """The SINGLE spares pocket (Allen key + spare blades together), cut clean
    THROUGH the insert. Contents are held in X/Y by the pocket and by the foam
    above and below."""
    cx0, cx1 = geom["bay_cx_min"], geom["bay_cx_max"]
    cy0, cy1 = geom["bay_cy_min"], geom["bay_cy_max"]
    thru = geom["stack_h"] + 2.0
    return Box(
        cx1 - cx0, cy1 - cy0, thru, align=(Align.MIN, Align.MIN, Align.CENTER)
    ).translate((cx0, cy0, 0))


def _corner_notches(
    bounds: dict[str, float], geom: dict[str, float], params: SandwichCaseParams
) -> Part:
    """Full-depth notches at the insert's front corners to clear the corner
    magnet bosses (keeps the insert a prism — constant cross-section)."""
    notches = Part()
    boss_r = params.magnet_boss_radius
    sc = params.slide_clearance
    thru = geom["stack_h"] + 2.0
    cy_in = geom["ins_cy_min"]
    for cx, cy in _corner_magnet_positions(bounds, params):
        # rectangle from the insert front corner inward to clear the boss circle
        if cx < (geom["ins_cx_min"] + geom["ins_cx_max"]) / 2:
            x0, x1 = geom["ins_cx_min"] - 1.0, cx + boss_r + sc
        else:
            x0, x1 = cx - boss_r - sc, geom["ins_cx_max"] + 1.0
        y0, y1 = cy_in - 1.0, cy + boss_r + sc
        notches += Box(
            x1 - x0, y1 - y0, thru, align=(Align.MIN, Align.MIN, Align.CENTER)
        ).translate((x0, y0, 0))
    return notches


def build_insert(
    cutter: PurflingCutterParams, params: SandwichCaseParams
) -> Part:
    """The slide-in tray. Every pocket is cut clean THROUGH the slab (constant
    cross-section); contents are held in X/Y by their slots and cushioned by the
    foam above and below. The one exception is the gibson front-edge relief
    below, which removes the front-top corner so the closing lid can't pinch it.
    """
    bounds, pocket, geom = _sandwich_geometry(cutter, params)
    cx_c = (geom["ins_cx_min"] + geom["ins_cx_max"]) / 2
    cy_c = (geom["ins_cy_min"] + geom["ins_cy_max"]) / 2
    slab = Pos(cx_c, cy_c, 0) * Box(geom["insert_cx"], geom["insert_cy"], geom["stack_h"])

    # Tool silhouette as a true through-cut: section the pocket at the CZ=0
    # mid-plane (every tool feature crosses it) and extrude that profile through
    # the full slab — so the cut is a constant cross-section, not the pocket's
    # varying-depth shape.
    silhouette = pocket.intersect(Plane.XY)
    tool_cut = extrude(silhouette, amount=geom["stack_h"] / 2.0 + 1.0, both=True)

    insert = slab - tool_cut
    insert = insert - _spares_cut(geom)
    insert = insert - _corner_notches(bounds, geom, params)

    # FRONT-EDGE RELIEF (gibson tuner_case_v2 d3494f6). The insert is centred on
    # the seam (CZ=0) and its top half protrudes into the lid; as the lid swings
    # the last few degrees shut, its front (−CY) wall tilts inward and would
    # pinch the insert's front-top edge. Remove that corner: relieve the front
    # (−CY) face ABOVE the seam by `front_relief`, full CX width. Below the seam
    # the insert stays full size and located.
    relief = params.front_relief
    seam_z = -1.0  # start just below the seam so there's no ledge at CZ=0
    insert = insert - Box(
        geom["insert_cx"] + 2.0,
        relief + 1.0,
        geom["stack_h"] / 2.0 - seam_z + 1.0,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    ).translate((cx_c, geom["ins_cy_min"] - 1.0, seam_z))
    return insert


# ---------------------------------------------------------------------------
# Shell leaves
# ---------------------------------------------------------------------------


def _shell_half(
    half: str,
    cutter: PurflingCutterParams,
    params: SandwichCaseParams,
    bounds: dict[str, float],
    geom: dict[str, float],
) -> Part:
    """Build one thin-wall clamshell leaf (a hollow rectangular tray), in the
    CLOSED orientation (base at CZ<0, lid at CZ>0). The hinge is fused later in
    the print layout — see ``_print_layout``."""
    case = params.shell
    brick = _build_outer_shell(bounds, case)

    cx_c = (bounds["ext_cx_max"] + bounds["ext_cx_min"]) / 2
    cy_c = (bounds["ext_cy_max"] + bounds["ext_cy_min"]) / 2
    cx_size = (bounds["ext_cx_max"] - bounds["ext_cx_min"]) + 20
    cy_size = (bounds["ext_cy_max"] - bounds["ext_cy_min"]) + 20
    cz_clip = (bounds["ext_cz_max"] - bounds["ext_cz_min"]) * 2 + 20

    if half == "lid":
        clip = Pos(cx_c, cy_c, cz_clip / 4) * Box(cx_size, cy_size, cz_clip / 2)
    else:
        clip = Pos(cx_c, cy_c, -cz_clip / 4) * Box(cx_size, cy_size, cz_clip / 2)

    # Rectangular interior cavity (full interior height; clipping leaves a wall
    # floor on each half at its outer face).
    int_cx = bounds["int_cx_max"] - bounds["int_cx_min"]
    int_cy = bounds["int_cy_max"] - bounds["int_cy_min"]
    cavity = Pos(cx_c, cy_c, 0) * Box(int_cx, int_cy, geom["cav_cz"])

    body = brick & clip
    body = body - cavity          # hollow out the interior
    body = _apply_corner_magnets(body, bounds, params, half)

    if half == "lid":
        body = _engrave_lid_logo(body, bounds, case)
    return body


def build_shell(
    cutter: PurflingCutterParams, params: SandwichCaseParams
) -> Compound:
    """The two clamshell leaves in CLOSED orientation, no hinge (base, lid)."""
    bounds, _pocket, geom = _sandwich_geometry(cutter, params)
    base = _shell_half("base", cutter, params, bounds, geom)
    lid = _shell_half("lid", cutter, params, bounds, geom)
    return Compound(children=[base, lid])


# ---------------------------------------------------------------------------
# Print-in-place hinge: fuse the pip hinge and unfold to the flat print layout
# ---------------------------------------------------------------------------


def _hinge_params(bounds: dict[str, float]) -> HingeParams:
    """Pip-hinge inputs derived from the shell envelope. The hinge runs along
    CX (the long edge) at the +CY back wall."""
    case_h = -bounds["ext_cz_min"]                       # leaf height = half closed exterior
    hinge_length = (bounds["ext_cx_max"] - bounds["ext_cx_min"]) - 2 * HINGE_END_MARGIN
    return HingeParams(
        case_h=case_h,
        hinge_length=hinge_length,
        stations=HINGE_STATIONS,
        knuckle=Knuckle.SMALL,
        pivot_clearance=HINGE_PIVOT_CLEARANCE,
        mounting_flat=HINGE_MOUNTING_FLAT,
        clasp_clearance=HINGE_CLASP_CLEARANCE,
    )


def _print_layout(
    base: Part, lid: Part, bounds: dict[str, float]
) -> tuple[Part, Part, float]:
    """Lift the closed base/lid onto the bed, unfold the lid 180° about the
    back-edge hinge axis, and fuse the pip hinge. Returns (base_print,
    lid_print, hinge_axis_cy) — the flat, print-ready leaves with the hinge.

    Transform sequence copied from gramel tools/assemble_case_with_pip_hinge.py
    (the validated integration), with a single continuous hinge along CX.
    """
    hp = _hinge_params(bounds)
    res = hp._resolve()
    case_h = -bounds["ext_cz_min"]
    W = res["W"]
    hinge_axis_cy = bounds["ext_cy_max"] + W             # leaf outer face on wall inner face
    pz = hp.pivot_z_offset

    # Lift the lid by 2·pz so that after rotating about the lifted axis it lands
    # flat on the bed; the 2·pz gap shows up at the closed seam (intentional).
    lid_lifted = Pos(0, 0, 2 * pz) * lid
    lid_open = (
        Pos(0, hinge_axis_cy, pz)
        * Rot(180, 0, 0)
        * Pos(0, -hinge_axis_cy, -pz)
        * lid_lifted
    )
    base_print = Part() + Pos(0, 0, case_h) * base
    lid_print = Part() + Pos(0, 0, case_h) * lid_open

    # Single continuous hinge centred on the CX edge. Pip-hinge local frame:
    # axis along Y, cs leaf +X, ps leaf −X, leaves Z∈[−case_h,0], knuckle +Z.
    # Rot(0,0,−90): local +Y → print +X (axis along CX); local +X → print −Y.
    cluster_cx = (bounds["ext_cx_min"] + bounds["ext_cx_max"]) / 2
    cs, ps = _split_hinge_by_side(make_hinge(hp))
    cs_placed = Pos(cluster_cx, hinge_axis_cy, case_h) * (Rot(0, 0, -90) * cs)
    ps_placed = Pos(cluster_cx, hinge_axis_cy, case_h) * (Rot(0, 0, -90) * ps)
    base_print = base_print + cs_placed
    lid_print = lid_print + ps_placed
    return base_print, lid_print, hinge_axis_cy


def build_print_shell(
    cutter: PurflingCutterParams, params: SandwichCaseParams
) -> Compound:
    """The print deliverable: both leaves flat on the bed, joined by the
    print-in-place pip hinge (lid unfolded 180° open)."""
    bounds, _pocket, _geom = _sandwich_geometry(cutter, params)
    base, lid = build_shell(cutter, params).children
    base_print, lid_print, _axis = _print_layout(base, lid, bounds)
    return Compound(children=[base_print, lid_print])


# ---------------------------------------------------------------------------
# Populated contents (for the open assembly visualisation)
# ---------------------------------------------------------------------------


def _assembled_tool(cutter: PurflingCutterParams) -> Part:
    """The assembled cutter, tool frame → case frame, overlaying the pocket.

    A 120° rotation about (1,1,1) cyclically permutes the axes so tool Z
    (length) → case X, tool X (shaft) → case Y, tool Y (depth) → case Z —
    the same mapping ``_tool_pocket`` is built with, so the tool lands flat
    in its silhouette pocket.
    """
    return build_assembly(cutter).rotate(Axis((0, 0, 0), (1, 1, 1)), 120)


def _spare_parts(
    geom: dict[str, float],
    params: SandwichCaseParams,
    cutter: PurflingCutterParams,
) -> list[Part]:
    """The placed spare blades + a simple 2 mm Allen-key L, lying together in
    the single spares pocket (for the populated viz)."""
    bottom_z = -geom["stack_h"] / 2.0  # spares rest at the insert bottom (on the foam)
    af = params.allen_key_af
    parts: list[Part] = []

    # Allen key (two square rods in an L), long arm along CX near the bay's
    # +CY edge so the blades sit alongside it toward −CY.
    key_z = bottom_z + af / 2
    long_cy = geom["bay_cy_max"] - af / 2 - 1.0
    long_cx0 = geom["bay_cx_min"] + 1.0
    long_seg = Box(params.allen_key_long_arm, af, af).translate(
        (long_cx0 + params.allen_key_long_arm / 2, long_cy, key_z)
    )
    short_len = min(params.allen_key_short_arm, (long_cy - geom["bay_cy_min"]) - 1.0)
    short_seg = Box(af, short_len, af).translate(
        (long_cx0 + af / 2, long_cy - short_len / 2, key_z)
    )
    parts.append(long_seg + short_seg)

    # Spare blades, lying flat (length → CX, width → CY, thickness → CZ),
    # toward the −CY side of the bay, clear of the key long arm.
    blade = Rot(0, 90, 0) * build_blade(cutter)
    bl = blade.bounding_box()
    blade_z = bottom_z + bl.size.Z / 2
    blade_cx = geom["bay_cx_min"] + bl.size.X / 2 + 2.0
    cy0 = long_cy - af / 2 - 1.0  # just −CY of the key long arm
    for i in range(params.spare_blades):
        cy_c = cy0 - (i + 0.5) * (bl.size.Y + 1.0)
        parts.append(copy.copy(blade).translate((blade_cx, cy_c, blade_z)))

    return parts


# ---------------------------------------------------------------------------
# Assembly + CLI
# ---------------------------------------------------------------------------


def build_open_assembly(
    cutter: PurflingCutterParams,
    params: SandwichCaseParams,
    populate: bool = True,
) -> Compound:
    """The case flat-open (the print layout — lid unfolded 180° beside the base
    on the pip hinge), with the insert seated in the base and, when
    ``populate``, the assembled tool + spares dropped in.
    """
    bounds, _pocket, geom = _sandwich_geometry(cutter, params)
    base, lid = build_shell(cutter, params).children
    base_print, lid_print, _axis = _print_layout(base, lid, bounds)
    case_h = -bounds["ext_cz_min"]  # contents are built on the seam (CZ=0); base lifts by case_h

    children: list[Part] = [base_print, lid_print]
    if populate:
        insert = build_insert(cutter, params)
        children.append(copy.copy(insert).translate((0, 0, case_h)))
        # The tool is moved inward (+CY by tool_inset) to match its shifted pocket.
        children.append(_assembled_tool(cutter).translate((0, params.tool_inset, case_h)))
        children += [p.translate((0, 0, case_h)) for p in _spare_parts(geom, params, cutter)]

    return Compound(children=children)


def build_all(
    cutter: PurflingCutterParams, params: SandwichCaseParams
) -> tuple[Compound, Part, Compound, dict[str, float]]:
    """Return (shell_print, insert, open_populated_assembly, geom)."""
    _bounds, _pocket, geom = _sandwich_geometry(cutter, params)
    shell_print = build_print_shell(cutter, params)
    insert = build_insert(cutter, params)
    assembly = build_open_assembly(cutter, params)
    return shell_print, insert, assembly, geom


def main() -> None:
    cutter = PurflingCutterParams()
    cutter = cutter.model_copy(
        update={"process": cutter.process.model_copy(update={"prototype": False})}
    )
    params = SandwichCaseParams()
    shell_print, insert, assembly, geom = build_all(cutter, params)
    print(
        f"Sandwich case: insert {geom['insert_cx']:.1f} × {geom['insert_cy']:.1f} mm, "
        f"stack {geom['stack_h']:.1f} mm, cavity Z {geom['cav_cz']:.1f} mm"
    )
    export_step(shell_print, "/tmp/gramel_sandwich_shell_print.step")
    export_stl(shell_print, "/tmp/gramel_sandwich_shell_print.stl")
    export_step(insert, "/tmp/gramel_sandwich_insert.step")
    export_stl(insert, "/tmp/gramel_sandwich_insert.stl")
    export_step(assembly, "/tmp/gramel_sandwich_assembly.step")
    print("Exported /tmp/gramel_sandwich_{shell_print,insert}.{step,stl} + open populated assembly.step")


if __name__ == "__main__":
    main()
