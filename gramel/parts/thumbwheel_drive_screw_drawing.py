"""
A4 landscape technical drawing of the integral thumbwheel + drive screw —
CNC handoff package.

The part is a turned stepped cylinder: boss (⌀6) + knurled disc
(⌀10) + unthreaded collar (⌀5) + M3 thread, all from one piece of
brass, plus an M2 tap from the −X face for the captive-screw captive
bearing.

Layout: side view of the X–Z profile across the top, left end view
showing the boss + M2 tap on the right, iso below. All views at 1:1.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from build123d import Compound, Draft, Shape
from build123d_drafting import dim_linear, leader  # type: ignore[import-untyped]

from gramel import threads
from gramel.parameters import PurflingCutterParams
from gramel.parts._drawing import (
    export_drawing,
    notes_block_lines,
    notes_block_text,
    page_frame,
    placed_text,
    project_view,
    title_block_lines,
    title_block_text,
)
from gramel.parts.thumbwheel_drive_screw import build_thumbwheel_drive_screw


SCALE = 2.0  # 2:1 drawing scale — part is small enough that 1:1 leaves leaders cramped


@dataclass
class ViewPlacement:
    """View centroids on the sheet (frame coords). Part rendered at 2:1.

    At 2:1 the part is 47 mm long × ⌀20 wide on the page. Front view takes
    the upper-left; left end view sits to its right; iso below.
    """

    front: tuple[float, float] = (-45.0, 25.0)
    left_end: tuple[float, float] = (25.0, 25.0)
    iso: tuple[float, float] = (-45.0, -45.0)


def build_thumbwheel_drawing(
    params: PurflingCutterParams,
) -> tuple[Compound, Compound, Compound, list[Shape[object]], Compound, Compound]:
    """Compose the thumbwheel + drive screw drawing.

    Returns (parts_visible, parts_hidden, frame, dim_shapes, text, annotations).
    """
    # Force CNC representation: smooth cylinders instead of helical threads.
    params = params.model_copy(update={"process": params.process.model_copy(update={"prototype": False})})

    part = build_thumbwheel_drive_screw(params)
    tw = params.thumbwheel
    ds = params.drive_screw

    boss_d = tw.boss_diameter
    boss_len = tw.boss_length
    disc_d = tw.diameter
    disc_t = tw.thickness
    collar_d = ds.unthreaded_diameter
    collar_len = ds.unthreaded_length
    thread_d = 2 * threads.major_radius(ds.thread)
    thread_len = ds.length
    overall_len = boss_len + disc_t + collar_len + thread_len  # 23.5

    tap_thread = ds.left_face_tap                          # M2
    tap_pitch = threads.pitch(tap_thread)
    tap_depth = ds.left_face_tap_depth                     # 2.8 mm

    # Step boundaries along the local +X axis (from −X end at X=0):
    x_boss_end = boss_len                # 0.5
    x_disc_end = boss_len + disc_t       # 2.5
    x_collar_end = x_disc_end + collar_len  # 5.5
    x_thread_end = overall_len           # 23.5

    centroid = (overall_len / 2, 0, 0)
    far = 1000.0

    # --- Project the views --------------------------------------------------
    # Front view: camera at -Y, up=+Z → world X = page X (+1), world Z = page Y (+1).
    front_v, front_h = project_view(part, (overall_len / 2, -far, 0), (0, 0, 1), centroid)
    # Left end view: camera at -X, up=+Z → world Y = page X (-1), world Z = page Y (+1).
    end_v, end_h = project_view(part, (-far, 0, 0), (0, 0, 1), (0, 0, 0))
    # Iso view.
    iso_v, _iso_h = project_view(part, (far, -far, far), (0, 0, 1), centroid)

    layout = ViewPlacement()

    def place(compound: Compound, pos: tuple[float, float]) -> Compound:
        return compound.translate((pos[0], pos[1], 0))

    # Scale every projected view to 2:1 before placing on the page
    parts_visible = Compound(
        children=[
            place(front_v.scale(SCALE), layout.front),
            place(end_v.scale(SCALE), layout.left_end),
            place(iso_v.scale(SCALE), layout.iso),
        ]
    )
    parts_hidden = Compound(
        children=[
            place(front_h.scale(SCALE), layout.front),
            place(end_h.scale(SCALE), layout.left_end),
        ]
    )

    # --- Dimensions ---------------------------------------------------------
    draft = Draft(font_size=2.0, decimal_precision=1, arrow_length=1.0, line_width=0.1)
    leader_draft = Draft(font_size=2.4, decimal_precision=1, arrow_length=1.0, line_width=0.1)

    dim_shapes: list[Shape[object]] = []
    annotation_lines: list[Shape[object]] = []
    annotation_text: list[Shape[object]] = []

    def add_dim(
        p1: tuple[float, float],
        p2: tuple[float, float],
        side: str,
        distance: float,
        label: str,
    ) -> None:
        result = dim_linear((p1[0], p1[1], 0), (p2[0], p2[1], 0), side, distance, draft, label=label)
        dim_shapes.append(result.shape)

    def add_leader(
        feature_xy: tuple[float, float],
        label_anchor_xy: tuple[float, float],
        label: str,
    ) -> None:
        result = leader(
            tip=(feature_xy[0], feature_xy[1], 0),
            elbow=(label_anchor_xy[0], label_anchor_xy[1], 0),
            label=label,
            draft=leader_draft,
        )
        annotation_lines.append(result.lines)
        annotation_text.append(result.text)

    # World X → page X = fx + SCALE*(worldX − overall_len/2)  (centred at fx)
    fx, fy = layout.front
    f_left = fx - SCALE * overall_len / 2                    # world X = 0 (−X face)
    f_right = fx + SCALE * overall_len / 2                   # world X = overall_len (+X face)
    f_disc_end = fx + SCALE * (x_disc_end - overall_len / 2)
    f_collar_end = fx + SCALE * (x_collar_end - overall_len / 2)
    f_top = fy + SCALE * disc_d / 2
    f_bot = fy - SCALE * disc_d / 2

    # Chained dims above the part: head section (5.5) + thread (18) = overall (23.5).
    # At SCALE 2 each dim path is wide enough for its label to fit inline.
    add_dim((f_left, f_top), (f_collar_end, f_top), "above", 5, f"{x_collar_end:.1f}")
    add_dim((f_collar_end, f_top), (f_right, f_top), "above", 5, f"{thread_len:.0f}")
    add_dim((f_left, f_top), (f_right, f_top), "above", 13, f"{overall_len:.1f}")

    # Disc diameter — Y dim on left side of the front view (path = 20 page units).
    add_dim((f_left - 2, f_bot), (f_left - 2, f_top), "left", 8, f"⌀{disc_d:.0f}")

    # Mid-X positions in PAGE coords (apply SCALE)
    x_boss_mid = fx + SCALE * (boss_len / 2 - overall_len / 2)
    x_disc_mid = fx + SCALE * ((boss_len + disc_t / 2) - overall_len / 2)
    x_collar_mid = fx + SCALE * ((x_disc_end + x_collar_end) / 2 - overall_len / 2)
    x_thread_mid = fx + SCALE * ((x_collar_end + x_thread_end) / 2 - overall_len / 2)

    # Leaders fan into clear zones: far-left (boss), below (3×), above (knurl + thread spec).

    # FAR LEFT: combined boss spec
    add_leader(
        (x_boss_mid, fy),
        (f_left - 18, fy - 14),
        f"⌀{boss_d:.0f} × {boss_len:.1f} boss",
    )

    # BELOW the part — three callouts spread along X
    add_leader(
        (x_disc_mid, f_bot),
        (x_disc_mid - 8, f_bot - 12),
        f"disc {disc_t:.0f} thick",
    )
    add_leader(
        (x_collar_mid, fy - SCALE * collar_d / 2),
        (x_collar_mid + 4, f_bot - 12),
        f"⌀{collar_d:.0f} collar",
    )
    add_leader(
        (x_thread_mid + 6, fy - SCALE * thread_d / 2),
        (x_thread_mid + 10, f_bot - 12),
        "Ra 1.6 on thread",
    )

    # ABOVE the dim stack — knurl over the disc, thread spec over the thread.
    add_leader(
        (x_disc_mid, f_top),
        (x_disc_mid - 12, f_top + 28),
        "straight knurl, 0.5 pitch",
    )
    add_leader(
        (x_thread_mid, fy + SCALE * thread_d / 2),
        (x_thread_mid + 12, f_top + 28),
        f"{ds.thread}×{ds.thread_pitch}",
    )

    # --- Left end view: boss + M2 tap visible -----------------------
    ex, ey = layout.left_end
    # Tap callout points up-left so the label sits between the front and end views,
    # well clear of the notes block (X ≥ 38.5).
    add_leader(
        (ex, ey),
        (ex - 14, ey + 14),
        f"{tap_thread}×{tap_pitch} × {tap_depth:.1f} deep",
    )

    # --- Iso view label -----------------------------------------------------
    annotation_text.append(placed_text("ISO VIEW", 3.0, layout.iso[0], layout.iso[1] - 18, left_align=False))

    # --- Frame, title block, notes ------------------------------------------
    frame = page_frame()
    title_lines = title_block_lines()
    title_text = title_block_text(
        part_name="THUMBWHEEL",
        drawing_no="GRM-03",
        scale="2:1",
        sheet="1/1",
        material="Brass (CuZn37 / C26800)",
        drawn_by="P. Fremantle",
        drawn_date=date.today().isoformat(),
    )
    nb_lines = notes_block_lines()
    nb_text = notes_block_text()
    frame_compound = Compound(children=[frame, title_lines, nb_lines])
    text_compound = Compound(children=[title_text, nb_text, *annotation_text])
    annotations_compound = Compound(children=annotation_lines)

    return parts_visible, parts_hidden, frame_compound, dim_shapes, text_compound, annotations_compound


def main() -> None:
    params = PurflingCutterParams()
    parts_visible, parts_hidden, frame, dim_shapes, text, annotations = build_thumbwheel_drawing(params)
    export_drawing(
        svg_path="/tmp/thumbwheel_drawing.svg",
        pdf_path="/tmp/thumbwheel_drawing.pdf",
        parts_visible=parts_visible,
        parts_hidden=parts_hidden,
        frame=frame,
        dim_shapes=dim_shapes,
        text=text,
        annotations=annotations,
    )


if __name__ == "__main__":
    main()
