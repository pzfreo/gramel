"""
Partial assembly of the purfling cutter.

Currently includes the shank and the shaft. Other parts (blades, spacer,
retainers, drive plate, thumbwheel + drive screw, fasteners) will be
added as they're built. Joint-based assembly with proper Joint objects
is task #8 — this draft just positions parts via plain transforms.

Coordinate frame is the shank's frame:
  X = along the shaft (perpendicular to working face)
  Y = perpendicular (tool-travel direction)
  Z = along the shank, vertical (+Z = top)
"""

from build123d import Compound, Pos

from gramel.parameters import PurflingCutterParams
from gramel.parts.shaft import build_shaft
from gramel.parts.shank import build_shank


def build_assembly(params: PurflingCutterParams) -> Compound:
    """Compose the shank + shaft into a single assembly Compound."""
    shank = build_shank(params)
    shaft_local = build_shaft(params)

    # Shaft was built in its own coords (cylinder axis at Y=0, Z=0, X from 0 to length).
    # Slide it into the shank's crossbore: axis at (Y=0, Z=shank_top − crossbore_position).
    # Centre the shaft's X mid-point on the shank's centre so it pokes out
    # roughly the same amount each side at nominal edge-margin.
    shaft_x_offset = -params.shaft.length / 2
    shaft_z_offset = params.shank.length - params.shank.crossbore_position_from_top
    shaft = Pos(shaft_x_offset, 0, shaft_z_offset) * shaft_local

    return Compound(children=[shank, shaft])


def main() -> None:
    """CLI: build the assembly and export STEP to /tmp/assembly.step."""
    from build123d import export_step

    params = PurflingCutterParams()
    assembly = build_assembly(params)
    export_step(assembly, "/tmp/assembly.step")
    print(f"Exported /tmp/assembly.step  (volume = {assembly.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
