"""
Thumbwheel + drive screw — integral piece on the −X (outboard) side of the
shank. Spec §4.4 says these are turned from one piece.

Layout along X (from the −X outboard face at X = 0, inboard toward +X):

  silver boss | thumbwheel disc | unthreaded collar | M3 drive-screw thread

  X = 0                          (silver-screw tap entry; outboard −X face)
       silver_boss_length
            + thumbwheel.thickness
                 + drive_screw.unthreaded_length
                      + drive_screw.length        (total = thread inboard end)

Bores:
  - Silver-screw tap from the −X face inward by left_face_tap_depth. With
    default values (boss 0.5, disc 2, unthreaded collar 3, tap depth 3) the
    tap bottoms 0.5 mm into the unthreaded collar — well before the M3
    thread root, so the silver-screw tap can never compromise the drive-
    screw thread.

The threaded portion is modelled as a smooth cylinder at the thread's
major diameter for now; real IsoThread geometry comes later.
"""

from build123d import (
    Cylinder,
    Part,
    Pos,
    Rot,
)

from gramel import threads
from gramel.parameters import PurflingCutterParams
from gramel.parts._threads import external_thread_section


def build_thumbwheel_drive_screw(params: PurflingCutterParams) -> Part:
    """Build the integral thumbwheel + drive screw."""
    tw = params.thumbwheel
    ds = params.drive_screw

    # Section lengths along X
    boss_len = tw.silver_boss_length
    disc_thick = tw.thickness
    unth_len = ds.unthreaded_length
    thread_len = ds.length

    # Radii
    boss_r = tw.silver_boss_diameter / 2
    disc_r = tw.diameter / 2
    unth_r = ds.unthreaded_diameter / 2
    thread_r = threads.major_radius(ds.thread)

    # X centres for each section, stacked along +X
    x_boss = boss_len / 2
    x_disc = boss_len + disc_thick / 2
    x_unth = boss_len + disc_thick + unth_len / 2
    x_thread = boss_len + disc_thick + unth_len + thread_len / 2

    # Default Cylinder is along Z; Rot(0, 90, 0) rotates Z → X.
    silver_boss = (
        Pos(x_boss, 0, 0) * Rot(0, 90, 0) * Cylinder(radius=boss_r, height=boss_len)
    )
    disc = Pos(x_disc, 0, 0) * Rot(0, 90, 0) * Cylinder(radius=disc_r, height=disc_thick)
    unthreaded = (
        Pos(x_unth, 0, 0) * Rot(0, 90, 0) * Cylinder(radius=unth_r, height=unth_len)
    )

    # Drive-screw thread: real ISO helix on the FDM prototype path; plain
    # major-diameter cylinder on the CNC path (the shop reads the thread
    # callout off the drawing, not the geometry — see _threads.py docstring).
    thread_start_x = boss_len + disc_thick + unth_len
    if params.process.prototype:
        thread = Pos(thread_start_x, 0, 0) * Rot(0, 90, 0) * external_thread_section(
            ds.thread, thread_len
        )
    else:
        thread = (
            Pos(x_thread, 0, 0) * Rot(0, 90, 0) * Cylinder(radius=thread_r, height=thread_len)
        )

    body = silver_boss + disc + unthreaded + thread

    # --- Silver-screw tap from the −X face inward -------------------------
    tap_drill_r = threads.tap_drill_radius(ds.left_face_tap)
    tap_depth = ds.left_face_tap_depth
    tap = (
        Pos(tap_depth / 2, 0, 0) * Rot(0, 90, 0) * Cylinder(radius=tap_drill_r, height=tap_depth)
    )
    body = body - tap

    return body  # type: ignore[return-value]


def main() -> None:
    """CLI: build and export STEP to /tmp/thumbwheel_drive_screw.step."""
    from build123d import export_step

    params = PurflingCutterParams()
    part = build_thumbwheel_drive_screw(params)
    export_step(part, "/tmp/thumbwheel_drive_screw.step")
    print(f"Exported /tmp/thumbwheel_drive_screw.step  (volume = {part.volume:.1f} mm^3)")


if __name__ == "__main__":
    main()
