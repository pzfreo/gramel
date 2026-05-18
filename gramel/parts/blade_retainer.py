"""
Bone-shaped copper retainer. Four per tool, sit in the blade slot to
hold the blade-spacer-blade stack in place along the slot's X direction.

Local frame:
  X: thickness (0.75 mm). Plate's normal direction.
  Y: width — varies along the bone profile: 5.5 mm at the ends, 4.5 mm
     in the middle.
  Z: long axis (10 mm). Bone profile is symmetric about Z = 0.

This draft uses a stacked-rectangles approximation of the bone outline:
two short wider end blocks + a longer narrower middle block. Real bone
profile (with rounded outer corners) would be a refinement.
"""

from build123d import Box, Part, Pos

from gramel.parameters import PurflingCutterParams


def build_blade_retainer(params: PurflingCutterParams) -> Part:
    """Build one bone-shaped retainer."""
    r = params.blade_retainer
    t = r.thickness
    end_w = r.end_width
    mid_w = r.middle_width
    L = r.length

    # Allocate Z extent: each end takes 20% (2 mm), middle takes 60% (6 mm)
    end_z = L * 0.2
    mid_z = L * 0.6

    top_end = Pos(0, 0, +(L / 2 - end_z / 2)) * Box(t, end_w, end_z)
    middle = Pos(0, 0, 0) * Box(t, mid_w, mid_z)
    bot_end = Pos(0, 0, -(L / 2 - end_z / 2)) * Box(t, end_w, end_z)

    body = top_end + middle + bot_end
    return body  # type: ignore[return-value]


def main() -> None:
    from build123d import export_step

    params = PurflingCutterParams()
    retainer = build_blade_retainer(params)
    export_step(retainer, "/tmp/blade_retainer.step")
    print(f"Exported /tmp/blade_retainer.step  (volume = {retainer.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
