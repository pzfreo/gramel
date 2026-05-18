"""
Shank — the square brass body that doubles as the fence.

Coordinate convention:
  X: along the shank, +X = top of shank (where the drive screw / thumbwheel sit).
  Y: along the shaft AND normal to the working face. +Y = working face,
     which is also the side the shaft exits toward the workpiece.
  Z: perpendicular to both. Blade-projection (depth-of-cut) direction in use.

The shaft cross-bore and the drive-screw tapped bore both pass *through* the
working face — the user pressing the working face against the violin edge
has the shaft pointing into the work, with the blades at its far end hanging
down (-Z) into the violin top.

This draft uses *smooth* bores (no thread geometry yet) and a single fillet
radius applied to all external edges as the finishing layer (per
`code-spec.md` §8).
"""

from build123d import (
    Align,
    Box,
    Cylinder,
    Part,
    Pos,
    Rot,
    Sphere,
)

from gramel.parameters import PurflingCutterParams


def build_shank(params: PurflingCutterParams) -> Part:
    """Build the shank as a build123d Part, using `params` as single source of truth."""
    shank = params.shank
    length = shank.length
    width = shank.width
    depth = shank.depth

    # Origin convention: X starts at 0 (bottom), Y centred so the working face
    # is at +Y = +width/2, Z starts at 0.
    body: Part = Box(length, width, depth, align=(Align.MIN, Align.CENTER, Align.MIN))

    # --- Convex working face (+Y face) -------------------------------------
    # The +Y face is curved so the centre of Z bulges out in +Y. Achieved by
    # intersecting the box with a large cylinder whose axis runs along X at
    # (anywhere, width/2 − R, depth/2). At Z = depth/2 the cylinder surface
    # sits at Y = width/2 (the peak); at Z = 0 and Z = depth it sits inboard,
    # so the +Y corners of the box are trimmed off and the face curves away.
    radius = shank.working_face_radius
    convexity_cyl = (
        Pos(length / 2, width / 2 - radius, depth / 2)
        * Rot(0, 90, 0)
        * Cylinder(radius=radius, height=length + 20)
    )
    body = body & convexity_cyl

    # --- Spherical dome at the top (+X end) --------------------------------
    # The top face of the shank is rounded in BOTH Y and Z. Modelled as a
    # sphere section whose surface tangents the original top face at the
    # centre point (Y=0, Z=depth/2, X=length). At off-centre Y or Z, the
    # sphere dips below X=length, trimming the box's top corners.
    dome_r = shank.top_dome_radius
    top_sphere = Pos(length - dome_r, 0, depth / 2) * Sphere(radius=dome_r)
    # `top_keep_zone` = "everything below dome line, AS-IS" ∪ "the dome region".
    big = max(length, width, depth) * 4
    lower_zone = Pos((length - dome_r) / 2, 0, depth / 2) * Box(
        length - dome_r,
        big,
        big,
    )
    body = body & (lower_zone + top_sphere)

    # --- Relief slot in the working face -----------------------------------
    # Slot is bounded — runs along X from the bottom up to the shaft level
    # only; doesn't continue above the crossbore. Z width = relief_slot_width,
    # Y depth = relief_slot_depth into -Y. Cut box extends past +Y by
    # slot_overdepth so it cuts through whatever convexity is left at the
    # bottom of the slot.
    slot_overdepth = 2.0
    slot_y_min = width / 2 - shank.relief_slot_depth
    slot_y_max = width / 2 + slot_overdepth
    slot_length = params.relief_slot_length
    slot = Pos(slot_length / 2, (slot_y_min + slot_y_max) / 2, depth / 2) * Box(
        slot_length,
        slot_y_max - slot_y_min,
        shank.relief_slot_width,
    )
    body = body - slot

    # --- Crossbore (along Y) -----------------------------------------------
    crossbore_x = length - shank.crossbore_position_from_top
    crossbore_z = depth / 2  # centred in Z for now (open question worth revisiting)
    crossbore = (
        Pos(crossbore_x, 0, crossbore_z)
        * Rot(90, 0, 0)
        * Cylinder(radius=params.crossbore_diameter / 2, height=width + 20)
    )
    body = body - crossbore

    # --- Shank tapped bore (along Y) — smooth bore at tap-drill diameter ---
    tapped_x = length - params.tapped_bore_position_from_top
    tapped_z = depth / 2
    tapped = (
        Pos(tapped_x, 0, tapped_z)
        * Rot(90, 0, 0)
        * Cylinder(radius=params.tapped_bore_drill_diameter / 2, height=width + 20)
    )
    body = body - tapped

    # --- Depth-lock blind bore (along X, from the bottom) ------------------
    # Bore extends from X=0 up to the crossbore (no clearance — push rod must
    # reach the crossbore region to bear on the shaft).
    dl_depth = params.depth_lock_bore_depth
    dl_radius = shank.depth_lock_bore_diameter / 2
    depth_lock_bore = (
        Pos(dl_depth / 2, 0, depth / 2) * Rot(0, 90, 0) * Cylinder(radius=dl_radius, height=dl_depth)
    )
    body = body - depth_lock_bore

    # --- Edge fillets (ergonomic finishing) --------------------------------
    # 0.5 mm fillet on every external edge. Applied last so cuts don't
    # destroy the fillets. May be skipped if it fails to apply cleanly on
    # complex edges (e.g. where the slot meets the convex face).
    fillet_r = shank.edge_fillet_radius
    if fillet_r > 0:
        try:
            body = body.fillet(fillet_r, body.edges())
        except Exception:
            # If filleting all edges fails, leave them sharp — flag to the user.
            print(f"WARN: failed to fillet all edges at r={fillet_r}; leaving sharp.")

    return body


def main() -> None:
    """CLI: build the shank with default params and export STEP to /tmp/shank.step."""
    from build123d import export_step

    params = PurflingCutterParams()
    shank = build_shank(params)
    export_step(shank, "/tmp/shank.step")
    print(f"Exported /tmp/shank.step  (volume = {shank.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
