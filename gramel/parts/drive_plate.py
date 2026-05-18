"""
Drive plate — small brass plate that stands vertically up from the shaft's
outboard end, transmits drive screw translation to the shaft via the
captive silver-screw bearing at its thumb end.

Coordinate convention (plate's local frame):
  X: plate normal — thickness direction. +X = "back" (faces the shaft),
     −X = "front" (faces outboard, where the silver-screw head sits).
  Y: horizontal across the plate.
  Z: vertical. Origin (Z = 0) is the shaft-end boss centre; the thumb-end
     boss centre sits at Z = crossbore_to_tapped_bore_gap.

Outline: **egg shape** — larger circle (shaft_end_radius) at Z = 0,
smaller circle (thumb_end_radius) at Z = gap, connected by external
tangent lines.

Holes:
  - Central mount-screw clearance hole at the shaft end (Z = 0).
  - Silver-screw clearance hole at the thumb end (Z = gap).

Anti-rotation: rectangular slot milled into the back face (+X face) at
Z = 0, sized to receive the matching tenon on the shaft's −X end. The
slot + tenon pair prevents the plate from rotating around the mount-
screw axis; the screw itself holds the parts axially.
"""

import math

from build123d import (
    Box,
    BuildLine,
    BuildSketch,
    Cylinder,
    Line,
    Part,
    Plane,
    Pos,
    Rot,
    extrude,
    make_face,
)

from gramel.parameters import PurflingCutterParams


def build_drive_plate(params: PurflingCutterParams) -> Part:
    """Build the drive plate as a build123d Part."""
    dp = params.drive_plate
    sp = params.shaft
    r_big = dp.shaft_end_radius
    r_small = dp.thumb_end_radius
    gap = params.shank.crossbore_to_tapped_bore_gap
    thickness = dp.thickness

    # --- Egg outline ------------------------------------------------------
    # External tangent lines between two circles of different radii at a
    # given centre-to-centre distance. The tangent contact angle on the
    # large circle (measured from the line joining the centres) is:
    #     alpha = acos((r_big − r_small) / gap)
    alpha = math.acos((r_big - r_small) / gap)
    sin_a, cos_a = math.sin(alpha), math.cos(alpha)

    # Tangent points in the YZ sketch plane (local x = world Y, local y = world Z).
    p1_r = (r_big * sin_a, r_big * cos_a)  # right tangent on big circle
    p1_l = (-r_big * sin_a, r_big * cos_a)
    p2_r = (r_small * sin_a, gap + r_small * cos_a)  # right tangent on small
    p2_l = (-r_small * sin_a, gap + r_small * cos_a)

    # Two cylinders form the round ends; a quadrilateral filler with tangent
    # edges joins them smoothly.
    big = Pos(0, 0, 0) * Rot(0, 90, 0) * Cylinder(radius=r_big, height=thickness)
    small = Pos(0, 0, gap) * Rot(0, 90, 0) * Cylinder(radius=r_small, height=thickness)

    with BuildSketch(Plane.YZ) as quad_sketch:
        with BuildLine():
            Line(p1_l, p1_r)
            Line(p1_r, p2_r)
            Line(p2_r, p2_l)
            Line(p2_l, p1_l)
        make_face()
    quad = extrude(quad_sketch.sketch, amount=thickness / 2, both=True)

    plate = big + small + quad

    # --- Holes ------------------------------------------------------------
    # Mount hole at shaft end: standard M2 clearance (~0.2 mm radial).
    # Silver hole at thumb end: deliberately sloppy (~0.3 mm radial) so the
    # captive bearing doesn't bind.
    mount_r = dp.mount_hole_diameter / 2
    silver_r = dp.silver_clearance_hole_diameter / 2
    mount_hole = (
        Pos(0, 0, 0) * Rot(0, 90, 0) * Cylinder(radius=mount_r, height=thickness * 3)
    )
    silver_hole = (
        Pos(0, 0, gap) * Rot(0, 90, 0) * Cylinder(radius=silver_r, height=thickness * 3)
    )
    plate = plate - mount_hole - silver_hole

    # --- Anti-rotation slot in the back face (+X face) --------------------
    # *Horizontal slot across the full plate width* at Z = 0. The shaft's
    # tenon plugs into the middle part of this slot. Simpler to mill than a
    # small precise rectangle: one mill pass with no precise centring.
    overshoot = 0.5  # opens the slot cleanly through the plate edges
    slot_x_max = thickness / 2 + overshoot
    slot_x_min = thickness / 2 - sp.tenon_depth
    slot_x_size = slot_x_max - slot_x_min
    slot_x_centre = (slot_x_min + slot_x_max) / 2
    slot_y_extent = 2 * (r_big + overshoot)  # full plate Y at Z = 0 + margin
    slot = Pos(slot_x_centre, 0, 0) * Box(slot_x_size, slot_y_extent, sp.tenon_height)
    plate = plate - slot

    return plate  # type: ignore[return-value]


def main() -> None:
    """CLI: build the drive plate and export STEP to /tmp/drive_plate.step."""
    from build123d import export_step

    params = PurflingCutterParams()
    plate = build_drive_plate(params)
    export_step(plate, "/tmp/drive_plate.step")
    print(f"Exported /tmp/drive_plate.step  (volume = {plate.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
