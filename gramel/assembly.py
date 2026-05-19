"""
Full purfling-cutter assembly.

Positions every part in the shank's frame so the STEP exports as a
single complete cutter. Joint-based kinematic assembly (proper
build123d Joints) is a future refinement; this draft uses plain
transforms with parts in a static "as-clamped" position:

  - Shaft centred through the crossbore at a nominal edge-margin.
  - Blade stack inside the slot, grub screw clamped against the stack.
  - Drive plate mounted on the shaft's −X end face.
  - Silver-screw + thumbwheel/drive screw forming the captive bearing
    at the shank's tapped-bore level.
  - Depth-lock bolt fully advanced, push rod pressing up on the
    shaft's −Z flat.

Coordinate frame is the shank's frame:
  X = along the shaft (perpendicular to working face)
  Y = perpendicular (tool-travel direction)
  Z = along the shank, vertical (+Z = top)
"""

from build123d import Compound, Pos

from gramel.parameters import PurflingCutterParams
from gramel.parts.blade import build_blade
from gramel.parts.blade_retainer import build_blade_retainer
from gramel.parts.channel_spacer import build_channel_spacer
from gramel.parts.depth_lock_bolt import build_depth_lock_bolt
from gramel.parts.drive_plate import build_drive_plate
from gramel.parts.grub_screw import build_grub_screw
from gramel.parts.push_rod import build_push_rod
from gramel.parts.shaft import build_shaft
from gramel.parts.shank import build_shank
from gramel.parts.silver_screw import build_silver_screw
from gramel.parts.thumbwheel_drive_screw import build_thumbwheel_drive_screw


def build_assembly(params: PurflingCutterParams) -> Compound:
    """Compose the full assembly as a single Compound."""
    sp = params.shank
    crossbore_z = sp.length - sp.crossbore_position_from_top
    tapped_z = sp.length - params.tapped_bore_position_from_top

    shank = build_shank(params)

    # --- Shaft: centred through the crossbore ---------------------------
    shaft_local = build_shaft(params)
    shaft_len = params.shaft.length
    shaft_x_off = -shaft_len / 2
    shaft = Pos(shaft_x_off, 0, crossbore_z) * shaft_local

    # --- Blade slot stack (along the slot's X direction) ----------------
    slot_x_min = shaft_x_off + shaft_len - params.shaft.end_to_slot_distance - params.shaft.blade_slot_width
    blade_t = params.blade.thickness
    spacer_t = params.spacer.thickness
    ret_t = params.blade_retainer.thickness

    # Blade Z position: tip extends below the slot, top extends above
    blade_z = crossbore_z - 2.5

    retainer_local = build_blade_retainer(params)
    blade_local = build_blade(params)

    stack: list[Compound] = []
    x_c = slot_x_min
    for _ in range(2):
        stack.append(Pos(x_c + ret_t / 2, 0, crossbore_z) * retainer_local)
        x_c += ret_t
    stack.append(Pos(x_c + blade_t / 2, 0, blade_z) * blade_local)
    x_c += blade_t
    if spacer_t > 0:
        spacer_local = build_channel_spacer(params)
        stack.append(Pos(x_c + spacer_t / 2, 0, blade_z) * spacer_local)
        x_c += spacer_t
    stack.append(Pos(x_c + blade_t / 2, 0, blade_z) * blade_local)
    x_c += blade_t
    for _ in range(2):
        stack.append(Pos(x_c + ret_t / 2, 0, crossbore_z) * retainer_local)
        x_c += ret_t

    # --- Grub screw: tip touching the outboard end of the stack ---------
    grub_local = build_grub_screw(params)
    grub = Pos(x_c, 0, crossbore_z) * grub_local

    # --- Drive plate: back face at shaft's −X end -----------------------
    plate_local = build_drive_plate(params)
    plate_thick = params.drive_plate.thickness
    plate_x = shaft_x_off - plate_thick / 2
    plate = Pos(plate_x, 0, crossbore_z) * plate_local

    # --- Silver screw + thumbwheel/drive screw: captive bearing ---------
    silver_local = build_silver_screw(params)
    head_t = params.silver_screw.head_thickness
    silver_x = plate_x - plate_thick / 2 - head_t  # local X=0 (head −X face)
    silver = Pos(silver_x, 0, tapped_z) * silver_local

    tw_local = build_thumbwheel_drive_screw(params)
    # Silver boss −X face sits axial_play inboard of the plate's back face
    tw_x = shaft_x_off + params.captive_bearing.axial_play
    tw = Pos(tw_x, 0, tapped_z) * tw_local

    # --- Depth-lock bolt + push rod (fully advanced) --------------------
    rod_local = build_push_rod(params)
    bolt_local = build_depth_lock_bolt(params)

    # Push rod top bears on the shaft's −Z flat
    rod_top_z = crossbore_z - params.shaft_outer_diameter / 2 + params.shaft.flat_depth
    rod_bottom_z = rod_top_z - params.depth_lock.push_rod_length
    rod = Pos(0, 0, rod_bottom_z) * rod_local

    # Bolt tip at rod bottom; bolt's local Z=knob+thread is at the tip
    bolt_tip_local_z = params.depth_lock.knob_thickness + params.depth_lock.bolt_thread_length
    bolt = Pos(0, 0, rod_bottom_z - bolt_tip_local_z) * bolt_local

    return Compound(
        children=[
            shank,
            shaft,
            *stack,
            grub,
            plate,
            silver,
            tw,
            bolt,
            rod,
        ]
    )


def main() -> None:
    """CLI: build the assembly and export STEP to /tmp/assembly.step."""
    from build123d import export_step

    params = PurflingCutterParams()
    assembly = build_assembly(params)
    export_step(assembly, "/tmp/assembly.step")
    print(f"Exported /tmp/assembly.step  (volume = {assembly.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
