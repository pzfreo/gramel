"""
Shank — the square brass body that doubles as the fence.

Coordinate convention:
  X: along the shank, +X = top of shank (where the drive screw / thumbwheel sit).
  Y: along the shaft AND normal to the working face. +Y = working face,
     which is also the side the shaft exits toward the workpiece.
  Z: perpendicular to both. Blade-projection (depth-of-cut) direction in use.

The shaft cross-bore and the drive-screw tapped bore therefore both pass
*through* the working face — the user pressing the working face against the
violin edge has the shaft pointing into the work, with the blades at its far
end hanging down (-Z) into the violin top.

This first draft uses *smooth* bores (no thread geometry yet) and no
fillets.
"""

from build123d import (
    Align,
    Box,
    Cylinder,
    Part,
    Pos,
    Rot,
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
    # sits exactly at Y = width/2 (no material removed at centre); at Z = 0
    # and Z = depth it sits a fraction inboard, so the +Y corners of the box
    # are trimmed off and the face curves slightly away.
    radius = shank.working_face_radius
    convexity_cyl = (
        Pos(length / 2, width / 2 - radius, depth / 2)
        * Rot(0, 90, 0)
        * Cylinder(radius=radius, height=length + 20)
    )
    body = body & convexity_cyl

    # --- Relief slot in the working face -----------------------------------
    # Groove cut into the +Y face. Length: X (full shank). Width: Z (across
    # the working face). Depth: into -Y (away from the workpiece). The cut
    # box extends past +Y by slot_overdepth so it definitely cuts through
    # whatever convexity is left.
    slot_overdepth = 2.0
    slot_y_min = width / 2 - shank.relief_slot_depth
    slot_y_max = width / 2 + slot_overdepth
    slot = Pos(length / 2, (slot_y_min + slot_y_max) / 2, depth / 2) * Box(
        length + 20,
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
    # Threads come in a later iteration. The tap-drill diameter is what the
    # drill leaves behind before the tap is run.
    tapped_x = length - params.tapped_bore_position_from_top
    tapped_z = depth / 2
    tapped = (
        Pos(tapped_x, 0, tapped_z)
        * Rot(90, 0, 0)
        * Cylinder(radius=params.tapped_bore_drill_diameter / 2, height=width + 20)
    )
    body = body - tapped

    # --- Depth-lock blind bore (along X, from the bottom) ------------------
    # Bore depth runs from X=0 up to X=depth_lock_bore_depth. Cylinder axis
    # along X; the cylinder spans that range centred at half-depth.
    dl_depth = params.depth_lock_bore_depth
    dl_radius = shank.depth_lock_bore_diameter / 2
    depth_lock_bore = (
        Pos(dl_depth / 2, 0, depth / 2) * Rot(0, 90, 0) * Cylinder(radius=dl_radius, height=dl_depth)
    )
    body = body - depth_lock_bore

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
