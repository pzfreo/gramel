"""
Shank — the square brass body that doubles as the fence.

Coordinate convention (Z-up, intuitive for holding the tool):
  Z: along the shank, +Z = top (drive screw / thumbwheel end).
     Bottom of shank (depth-lock knob) at Z = 0.
  X: along the shaft AND normal to the working face. +X = working face
     direction. The shaft passes through the working face out toward the
     workpiece. Edge-margin adjustment translates the shaft in X.
  Y: perpendicular to both. Tool-travel direction (along the violin edge).

Blades cut downward in −Z when the tool is in use.

This draft uses *smooth* bores (no thread geometry yet) and a single
fillet radius applied to all external edges as the finishing layer.
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
    length = shank.length  # Z extent
    width = shank.width  # X extent (perpendicular to working face)
    depth = shank.depth  # Y extent (tool-travel direction)

    # Box: X width centered, Y depth centered, Z length from 0 (bottom) to length (top).
    # Working face is +X face at X = +width/2.
    body: Part = Box(width, depth, length, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # --- Convex working face (+X face) ------------------------------------
    # The +X face is curved so the centre of Y bulges out in +X. Intersect
    # the box with a cylinder whose axis runs along Z at (width/2 − R, 0).
    # At Y = 0 the cylinder surface sits at X = width/2 (the peak); at
    # Y = ±depth/2 it sits inboard, trimming the +X corners.
    radius = shank.working_face_radius
    convexity_cyl = (
        Pos(width / 2 - radius, 0, length / 2) * Cylinder(radius=radius, height=length + 20)
    )
    body = body & convexity_cyl

    # --- Spherical dome at the top (+Z end) -------------------------------
    # The +Z face of the shank is a sphere section, rounded in both X and Y.
    # Surface tangents the original top face at the centre (X = 0, Y = 0,
    # Z = length); at off-centre X or Y, the sphere dips below Z = length,
    # trimming the box's top corners.
    dome_r = shank.top_dome_radius
    top_sphere = Pos(0, 0, length - dome_r) * Sphere(radius=dome_r)
    big = max(length, width, depth) * 4
    lower_zone = Pos(0, 0, (length - dome_r) / 2) * Box(big, big, length - dome_r)
    body = body & (lower_zone + top_sphere)

    # --- Relief slot in the working face ----------------------------------
    # Length along Z (shank long axis), width across Y, depth into −X.
    # Cut box extends past +X by slot_overdepth so it cuts through whatever
    # convexity is left at the bottom of the slot.
    slot_overdepth = 2.0
    slot_x_min = width / 2 - shank.relief_slot_depth
    slot_x_max = width / 2 + slot_overdepth
    slot_x_extent = slot_x_max - slot_x_min
    slot_x_centre = (slot_x_min + slot_x_max) / 2
    slot_length = params.relief_slot_length
    slot = Pos(slot_x_centre, 0, slot_length / 2) * Box(
        slot_x_extent,
        shank.relief_slot_width,
        slot_length,
    )
    body = body - slot

    # --- Crossbore (along X — the shaft direction) ------------------------
    crossbore_z = length - shank.crossbore_position_from_top
    crossbore = (
        Pos(0, 0, crossbore_z)
        * Rot(0, 90, 0)
        * Cylinder(radius=params.crossbore_diameter / 2, height=width + 20)
    )
    body = body - crossbore

    # --- Shank tapped bore (along X) — smooth bore at tap-drill diameter --
    tapped_z = length - params.tapped_bore_position_from_top
    tapped = (
        Pos(0, 0, tapped_z)
        * Rot(0, 90, 0)
        * Cylinder(radius=params.tapped_bore_drill_diameter / 2, height=width + 20)
    )
    body = body - tapped

    # --- Depth-lock blind bore (along Z, from Z = 0 up) -------------------
    # Bore extends from the bottom face up to the crossbore (no clearance —
    # push rod must reach the crossbore to bear on the shaft).
    dl_depth = params.depth_lock_bore_depth
    dl_radius = shank.depth_lock_bore_diameter / 2
    depth_lock_bore = Pos(0, 0, dl_depth / 2) * Cylinder(radius=dl_radius, height=dl_depth)
    body = body - depth_lock_bore

    # --- Edge fillets (ergonomic finishing) -------------------------------
    fillet_r = shank.edge_fillet_radius
    if fillet_r > 0:
        try:
            body = body.fillet(fillet_r, body.edges())
        except Exception:
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
