"""
Silver screw — the small fastener that captures the drive plate against
the thumbwheel's left face. The deliberately-over-length screw bottoms
on the thumbwheel tap *before* its head clamps the drive plate,
leaving the captive-bearing axial play.

Local frame:
  X: along the screw axis. X = 0 = head's outboard (−X) face;
     +X = inboard (toward the thumbwheel).

Length (head to tip) = drive_plate.thickness + captive_bearing.axial_play
                       + drive_screw.left_face_tap_depth.
"""

from build123d import (
    Cylinder,
    Part,
    Pos,
    Rot,
)

from gramel import threads
from gramel.parameters import PurflingCutterParams


def build_silver_screw(params: PurflingCutterParams) -> Part:
    """Build the silver screw."""
    ss = params.silver_screw
    dp = params.drive_plate
    ds = params.drive_screw
    cb = params.captive_bearing

    head_d = ss.head_diameter
    head_t = ss.head_thickness
    thread_r = threads.major_radius(ss.thread)
    thread_len = dp.thickness + cb.axial_play + ds.left_face_tap_depth

    # Head: cylinder along X at X = head_t / 2
    head = Pos(head_t / 2, 0, 0) * Rot(0, 90, 0) * Cylinder(radius=head_d / 2, height=head_t)
    # Thread: cylinder along X starting at X = head_t, extending to X = head_t + thread_len
    thread = (
        Pos(head_t + thread_len / 2, 0, 0)
        * Rot(0, 90, 0)
        * Cylinder(radius=thread_r, height=thread_len)
    )

    body = head + thread
    return body  # type: ignore[return-value]


def main() -> None:
    from build123d import export_step

    params = PurflingCutterParams()
    screw = build_silver_screw(params)
    export_step(screw, "/tmp/silver_screw.step")
    print(f"Exported /tmp/silver_screw.step  (volume = {screw.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
