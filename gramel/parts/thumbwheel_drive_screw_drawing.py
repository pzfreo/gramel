"""
A4 landscape technical drawing of the integral thumbwheel + drive screw —
CNC handoff package.

The part is a turned stepped cylinder: integral journal (Ø4, bearing) +
boss (Ø6, thrust face) + knurled disc (Ø10) + unthreaded collar (Ø5) +
M3 thread, all from one piece of brass, plus a deep M2 tap down the
journal centre. The drive plate rides on the journal; a retaining washer
+ M2 screw cap the journal end face (the screw head seats there, so the
bearing float is set by the journal length, not the tap depth).

Layout: side view of the X–Z profile across the top, left end view
showing the journal end + M2 tap on the right, iso below.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from build123d import Compound, Draft, Shape
from build123d_drafting import dim_linear, leader  # type: ignore[import-untyped]

from gramel import threads
from gramel.parameters import PurflingCutterParams
from gramel.parts._drawing import (
    dim_label,
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

    At 2:1 the part is 47 mm long × Ø20 wide on the page. Front view takes
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
    journal_d = ds.bearing_journal_diameter               # Ø4 — plate bearing journal
    journal_len = params.bearing_journal_length            # 3.2 (= plate thickness + 0.2 float)
    plus_x_len = boss_len + disc_t + collar_len + thread_len  # 23.5 (boss face → thread tip)
    total_len = journal_len + plus_x_len                   # 28.7 (journal end → thread tip)

    tap_thread = ds.left_face_tap                          # M2
    tap_pitch = threads.pitch(tap_thread)
    tap_depth = ds.left_face_tap_depth                     # 7 mm — deep; head seats on journal end
    chip_relief = ds.left_face_tap_chip_relief             # extra drilled depth for chip relief

    # Step boundaries along local +X (boss −X face at X=0; journal projects −X):
    x_jstart = -journal_len                  # −3.2 journal end face (−X-most)
    x_boss_face = 0.0                         # journal base = boss −X face = thrust shoulder
    x_disc_end = boss_len + disc_t            # 2.5
    x_collar_end = x_disc_end + collar_len    # 5.5
    x_thread_end = x_collar_end + thread_len  # 23.5 (+X face / thread tip)
    center_x = (x_jstart + x_thread_end) / 2

    centroid = (center_x, 0, 0)
    far = 1000.0

    # --- Project the views --------------------------------------------------
    # Front view: camera at -Y, up=+Z → world X = page X (+1), world Z = page Y (+1).
    front_v, front_h = project_view(part, (center_x, -far, 0), (0, 0, 1), centroid)
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

    # World X → page X = fx + SCALE*(worldX − center_x)  (centred at fx)
    fx, fy = layout.front
    f_jstart = fx + SCALE * (x_jstart - center_x)           # journal end (−X-most)
    f_boss_face = fx + SCALE * (x_boss_face - center_x)     # journal base / boss −X face
    f_collar_end = fx + SCALE * (x_collar_end - center_x)
    f_right = fx + SCALE * (x_thread_end - center_x)        # thread tip (+X face)
    f_top = fy + SCALE * disc_d / 2
    f_bot = fy - SCALE * disc_d / 2

    # Chained dims above: head (5.5) | thread (20); total (28.7) above. The
    # journal length is too short for an inline dim — it's on its leader below.
    add_dim((f_boss_face, f_top), (f_collar_end, f_top), "above", 5, dim_label(x_collar_end, min_decimals=1))
    add_dim((f_collar_end, f_top), (f_right, f_top), "above", 5, dim_label(thread_len, min_decimals=1))
    add_dim((f_jstart, f_top), (f_right, f_top), "above", 13, dim_label(total_len, min_decimals=1))

    # Disc diameter — Y dim on the far left of the front view.
    add_dim((f_jstart - 2, f_bot), (f_jstart - 2, f_top), "left", 8, f"Ø{dim_label(disc_d)}")

    # Mid-X positions in PAGE coords (apply SCALE)
    x_journal_mid = fx + SCALE * (-journal_len / 2 - center_x)
    x_boss_mid = fx + SCALE * (boss_len / 2 - center_x)
    x_disc_mid = fx + SCALE * ((boss_len + disc_t / 2) - center_x)
    x_collar_mid = fx + SCALE * ((x_disc_end + x_collar_end) / 2 - center_x)
    x_thread_mid = fx + SCALE * ((x_collar_end + x_thread_end) / 2 - center_x)

    # Journal — the new bearing feature — leader up-left.
    add_leader(
        (x_journal_mid, fy + SCALE * journal_d / 2),
        (f_jstart - 6, f_top + 18),
        f"Ø{dim_label(journal_d)} × {dim_label(journal_len)} journal (bearing dia)",
    )

    # FAR LEFT-BELOW: boss spec (the thrust shoulder)
    add_leader(
        (x_boss_mid, fy),
        (f_jstart - 6, fy - 16),
        f"Ø{dim_label(boss_d)} × {dim_label(boss_len)} boss (thrust face)",
    )

    # BELOW the part — disc / collar / thread callouts staggered along Y.
    add_leader(
        (x_disc_mid, f_bot),
        (x_disc_mid - 8, f_bot - 8),
        f"disc {dim_label(disc_t)} thick",
    )
    add_leader(
        (x_collar_mid, fy - SCALE * collar_d / 2),
        (x_collar_mid + 4, f_bot - 14),
        f"Ø{dim_label(collar_d)} collar",
    )
    add_leader(
        (x_thread_mid + 6, fy - SCALE * thread_d / 2),
        (x_thread_mid + 10, f_bot - 20),
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

    # Drive-screw tip chamfer (lead-in for the shank tap)
    add_leader(
        (f_right, fy),
        (f_right + 10, f_bot - 12),
        f"{dim_label(ds.tip_chamfer)} × 45° chamfer",
    )

    # --- Left end view: journal end face + deep M2 tap ----------------
    ex, ey = layout.left_end
    # Callouts to the UPPER-RIGHT of the end view, clear of the front-view
    # dim chain and the notes block (X ≤ 38.5).
    add_leader(
        (ex, ey),
        (ex + 4, ey + 18),
        f"Ø{dim_label(journal_d)} journal",
    )
    add_leader(
        (ex, ey),
        (ex + 4, ey + 13),
        f"{tap_thread}×{tap_pitch} × {dim_label(tap_depth)} deep tap",
    )
    add_leader(
        (ex, ey),
        (ex + 4, ey + 8),
        f"drill {dim_label(tap_depth + chip_relief)}; head seats on journal end",
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
