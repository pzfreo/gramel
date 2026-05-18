"""
Depth-lock push rod — steel rod in the upper (smooth) section of the
depth-lock blind bore. The M6 bolt's tip pushes the rod up; the rod's
top face bears on the underside of the shaft (on its machined flat).

Local frame:
  Z: along the rod axis. Z = 0 = bottom face, +Z = top.
  Y, X: rod cross-section (cylindrical).
"""

from build123d import Cylinder, Part, Pos

from gramel.parameters import PurflingCutterParams


def build_push_rod(params: PurflingCutterParams) -> Part:
    """Build the depth-lock push rod."""
    dl = params.depth_lock
    body: Part = Pos(0, 0, dl.push_rod_length / 2) * Cylinder(
        radius=dl.push_rod_diameter / 2, height=dl.push_rod_length
    )
    return body


def main() -> None:
    from build123d import export_step

    params = PurflingCutterParams()
    rod = build_push_rod(params)
    export_step(rod, "/tmp/push_rod.step")
    print(f"Exported /tmp/push_rod.step  (volume = {rod.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
