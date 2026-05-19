"""
Depth-lock bolt + knurled knob — the M6 hand-clamp at the bottom of the
shank's depth-lock blind bore. The bolt's tip pushes the push rod up to
clamp the shaft against the underside of the cross-bore.

Local frame:
  Z: along the bolt axis. Z = 0 = bottom face of the knurled knob;
     +Z = upward (into the shank when assembled).

Stack from bottom (−Z) to top (+Z):
  Knob (knurled disc, knob_diameter × knob_thickness)
   → M6 threaded portion (thread major diameter × bolt_thread_length)

Knurl decoration not modelled.
"""

from build123d import Cylinder, Part, Pos

from gramel import threads
from gramel.parameters import PurflingCutterParams
from gramel.parts._threads import external_thread_section


def build_depth_lock_bolt(params: PurflingCutterParams) -> Part:
    """Build the depth-lock bolt + knurled knob as one piece."""
    dl = params.depth_lock
    knob_r = dl.knob_diameter / 2
    knob_t = dl.knob_thickness
    bolt_r = threads.major_radius(dl.thread)
    bolt_len = dl.bolt_thread_length

    # Knob from Z = 0 to Z = knob_t
    knob = Pos(0, 0, knob_t / 2) * Cylinder(radius=knob_r, height=knob_t)
    # Bolt from Z = knob_t to Z = knob_t + bolt_len. Real helix on the FDM
    # prototype path; plain major-diameter cylinder on the CNC path.
    if params.process.prototype:
        bolt = Pos(0, 0, knob_t) * external_thread_section(dl.thread, bolt_len)
    else:
        bolt = Pos(0, 0, knob_t + bolt_len / 2) * Cylinder(radius=bolt_r, height=bolt_len)
    body = knob + bolt
    return body  # type: ignore[return-value]


def main() -> None:
    from build123d import export_step

    params = PurflingCutterParams()
    part = build_depth_lock_bolt(params)
    export_step(part, "/tmp/depth_lock_bolt.step")
    print(f"Exported /tmp/depth_lock_bolt.step  (volume = {part.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
