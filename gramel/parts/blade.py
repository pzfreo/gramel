"""
Blade — one of the two flat tool-steel cutters in the shaft's blade slot.

Local frame (the natural blade frame):
  X: thickness direction (0.7 mm). Wide flat face is perpendicular to X.
     The grub screw pushes against this face.
  Y: width direction (4 mm). The blade's "narrow" face.
  Z: length direction (23 mm). +Z = top (where the blade drops into the
     slot from), −Z = tip (cuts the violin).

The blade is rectangular for most of its length and rounded at the tip
end (semicircular, radius = width/2). Bevel sharpening is done by the
luthier and not modelled.
"""

from build123d import (
    Box,
    Cylinder,
    Part,
    Pos,
    Rot,
)

from gramel.parameters import PurflingCutterParams


def build_blade(params: PurflingCutterParams) -> Part:
    """Build a single blade."""
    blade = params.blade
    t = blade.thickness
    w = blade.width
    L = blade.length

    # Rectangular section for the upper portion of the blade.
    # Tip end gets replaced by a semicircular cap (radius = w/2).
    box_len_z = L - w / 2
    box = Pos(0, 0, w / 4) * Box(t, w, box_len_z)

    # Semicircular tip cap — cylinder along X with radius = w/2.
    tip = (
        Pos(0, 0, -L / 2 + w / 2) * Rot(0, 90, 0) * Cylinder(radius=w / 2, height=t)
    )

    body = box + tip
    return body  # type: ignore[return-value]


def main() -> None:
    """CLI: export blade to /tmp/blade.step."""
    from build123d import export_step

    params = PurflingCutterParams()
    blade = build_blade(params)
    export_step(blade, "/tmp/blade.step")
    print(f"Exported /tmp/blade.step  (volume = {blade.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
