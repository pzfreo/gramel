"""
Shaft — brass bar passing horizontally through the shank's crossbore,
carrying the blades at its outboard end.

Coordinate convention (matches the shank — Z-up):
  X: along the shaft. +X = right end (carries the blade slot, near
     the workpiece). −X = left end (outboard, drive-plate end).
  Y: perpendicular to shaft, horizontal (tool-travel direction).
  Z: vertical (depth-of-cut direction). Blades drop down in −Z.

Features:
  - Round cross-section of diameter ``shaft.outer_diameter``.
  - Flat machined on the underside (−Z) over a central X span — the
    depth-lock push rod registers against this flat.
  - Blade slot near the +X end: open through Z, with X extent =
    blade_slot_width and Y extent = blade_slot_length.
  - Grub-screw end tap (smooth bore at tap-drill diameter for now)
    in the +X end face, along X.
  - Two tapped holes in the −X end face (for the drive plate),
    spaced in Z, along X.

Threads on the grub-screw tap and the drive-plate mount holes come
later — this draft just leaves smooth bores at tap-drill diameter.
"""

from build123d import (
    Box,
    Cylinder,
    Part,
    Pos,
    Rot,
)

from gramel.parameters import _TAP_DRILL_DIAMETER, PurflingCutterParams


def build_shaft(params: PurflingCutterParams) -> Part:
    """Build the shaft as a build123d Part."""
    shaft = params.shaft
    length = shaft.length
    radius = shaft.outer_diameter / 2

    # --- Main cylinder along X --------------------------------------------
    # Default Cylinder is along Z; Rot(0, 90, 0) rotates Z → X.
    body: Part = Pos(length / 2, 0, 0) * Rot(0, 90, 0) * Cylinder(radius=radius, height=length)

    # --- Flat on the −Z underside, full length ----------------------------
    # Subtract a slab that covers the lower portion of the cylinder along the
    # full shaft length. The slab's +Z face sits at Z = −radius + flat_depth,
    # so the resulting flat surface is that height above the cylinder's bottom.
    flat_z_high = -radius + shaft.flat_depth
    flat_slab_height = radius * 3 + shaft.flat_depth
    flat_z_centre = flat_z_high - flat_slab_height / 2
    flat_x_extent = length + 4  # overshoot the ends so the cut goes fully through
    flat = Pos(length / 2, 0, flat_z_centre) * Box(
        flat_x_extent,
        radius * 4,
        flat_slab_height,
    )
    body = body - flat

    # --- Blade slot at the +X end -----------------------------------------
    # Slot's right wall (+X side) sits `end_to_slot_distance` from the +X end
    # face; slot extends inward (−X) for `blade_slot_width`. Open through Z
    # so blades drop in from the top and project out the bottom.
    slot_x_max = length - shaft.end_to_slot_distance
    slot_x_min = slot_x_max - shaft.blade_slot_width
    slot_x_centre = (slot_x_min + slot_x_max) / 2
    slot = Pos(slot_x_centre, 0, 0) * Box(
        shaft.blade_slot_width,
        shaft.blade_slot_length,
        radius * 4,  # through Z, generously beyond the shaft's vertical extent
    )
    body = body - slot

    # --- Grub-screw end tap (smooth bore) in the +X end face --------------
    grub_thread = params.grub_screw.thread
    grub_drill_radius = _TAP_DRILL_DIAMETER[grub_thread] / 2
    end_tap = (
        Pos(length - shaft.end_tap_depth / 2, 0, 0)
        * Rot(0, 90, 0)
        * Cylinder(radius=grub_drill_radius, height=shaft.end_tap_depth)
    )
    body = body - end_tap

    # --- Drive-plate mount holes in the −X end face -----------------------
    # Two holes, spaced in Z (vertically), centred on Y = 0. The drive plate
    # mounts to this face with screws through these holes.
    mount_thread = shaft.drive_plate_mount_thread
    mount_drill_radius = _TAP_DRILL_DIAMETER[mount_thread] / 2
    mount_depth = shaft.drive_plate_mount_depth
    for z_offset in (-shaft.drive_plate_mount_spacing / 2, +shaft.drive_plate_mount_spacing / 2):
        mount_hole = (
            Pos(mount_depth / 2, 0, z_offset)
            * Rot(0, 90, 0)
            * Cylinder(radius=mount_drill_radius, height=mount_depth)
        )
        body = body - mount_hole

    return body


def main() -> None:
    """CLI: build the shaft with default params and export STEP to /tmp/shaft.step."""
    from build123d import export_step

    params = PurflingCutterParams()
    shaft = build_shaft(params)
    export_step(shaft, "/tmp/shaft.step")
    print(f"Exported /tmp/shaft.step  (volume = {shaft.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
