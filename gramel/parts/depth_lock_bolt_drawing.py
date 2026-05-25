"""
A4 landscape technical drawing of the depth-lock bolt + knurled knob —
CNC handoff package.

Turned brass part: ⌀10 knurled knob → ⌀6.25 collar → M6 × 1 thread with a
45° lead-in chamfer at the tip. Single setup on a lathe. 2:1 scale (the
bolt is only 32 × ⌀10 mm — 1:1 would crowd the callouts).

Layout: front view (side profile of the bolt) at upper-left, end view
(circular cross-section looking down the bolt axis) to its right, iso
below.
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
from gramel.parts.depth_lock_bolt import build_depth_lock_bolt


SCALE = 2.0  # 2:1 — bolt is 32 mm tall × ⌀10


@dataclass
class ViewPlacement:
    """View centroids on the sheet (frame coords). Part rendered at 2:1.

    Bolt is drawn HORIZONTAL on the page (axial along page X) — same
    convention as the shaft drawing. Knob at the left, thread tip on
    the right.
    """

    front: tuple[float, float] = (-65.0, 35.0)
    end: tuple[float, float] = (-65.0, -15.0)
    iso: tuple[float, float] = (-65.0, -60.0)


def build_depth_lock_bolt_drawing(
    params: PurflingCutterParams,
) -> tuple[Compound, Compound, Compound, list[Shape[object]], Compound, Compound]:
    """Compose the depth-lock bolt drawing.

    Returns (parts_visible, parts_hidden, frame, dim_shapes, text, annotations).
    """
    params = params.model_copy(update={"process": params.process.model_copy(update={"prototype": False})})

    bolt = build_depth_lock_bolt(params)
    dl = params.depth_lock

    knob_d = dl.knob_diameter            # 10
    knob_t = dl.knob_thickness           # 14
    collar_d = dl.bolt_collar_diameter   # 6.25
    collar_len = dl.bolt_collar_length   # 5
    thread = dl.thread                    # "M6"
    thread_d = 2 * threads.major_radius(thread)
    thread_pitch = threads.pitch(thread)
    thread_len = dl.bolt_thread_length   # 13
    chamfer = dl.bolt_tip_chamfer        # 1.0 (one full thread pitch for M6)
    knob_chamfer = dl.knob_bottom_chamfer  # 1.5
    overall_len = knob_t + collar_len + thread_len   # 32

    # Step boundaries along the bolt's local +Z axis (Z=0 at knob bottom)
    z_knob_end = knob_t
    z_collar_end = knob_t + collar_len
    z_thread_end = overall_len

    # Centroid for projection — middle of the bolt
    centroid = (0, 0, overall_len / 2)
    far = 1000.0

    # --- Project the views --------------------------------------------------
    # Bolt is drawn HORIZONTAL on the page: bolt's +Z axis → page +X.
    # Front view: camera at -Y, up=+Z → world +Z = page +Y. Then we rotate the
    # projection 90° CW so the +Z axis runs along page +X (knob on the left).
    # Simpler: use camera at (0, -far, ...) up=(1, 0, 0) — that's "camera
    # in front, with the bolt's +Z axis pointing RIGHT on the page".
    front_v, front_h = project_view(bolt, (0, -far, overall_len / 2), (-1, 0, 0), centroid)
    # End view: camera at -Z, up=+X → looking up the bolt's axis from the
    # knob end. World +X → page +X, world +Y → page +Y.
    end_v, end_h = project_view(bolt, (0, 0, -far), (1, 0, 0), (0, 0, 0))
    # Iso view from the +X+Y+Z octant.
    iso_v, _iso_h = project_view(bolt, (far, far, far), (0, 0, 1), centroid)

    layout = ViewPlacement()

    def place(compound: Compound, pos: tuple[float, float]) -> Compound:
        return compound.translate((pos[0], pos[1], 0))

    parts_visible = Compound(
        children=[
            place(front_v.scale(SCALE), layout.front),
            place(end_v.scale(SCALE), layout.end),
            place(iso_v.scale(SCALE), layout.iso),
        ]
    )
    parts_hidden = Compound(
        children=[
            place(front_h.scale(SCALE), layout.front),
            place(end_h.scale(SCALE), layout.end),
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

    # Front view: bolt's local Z → page X. World Z=0 (knob bottom) maps to
    # page X = fx − SCALE * overall_len/2 (left end). Knob is on the LEFT.
    fx, fy = layout.front
    f_left = fx - SCALE * overall_len / 2          # knob bottom (Z = 0)
    f_right = fx + SCALE * overall_len / 2         # thread tip (Z = overall_len)
    f_knob_end = fx + SCALE * (z_knob_end - overall_len / 2)
    f_collar_end = fx + SCALE * (z_collar_end - overall_len / 2)
    f_top = fy + SCALE * knob_d / 2                # top edge of knob in page Y
    f_bot = fy - SCALE * knob_d / 2

    # Chained dim stack above the bolt: knob + collar + thread = overall
    add_dim((f_left, f_top), (f_knob_end, f_top), "above", 5, dim_label(knob_t, min_decimals=1))
    add_dim((f_knob_end, f_top), (f_collar_end, f_top), "above", 5, dim_label(collar_len, min_decimals=1))
    add_dim((f_collar_end, f_top), (f_right, f_top), "above", 5, dim_label(thread_len, min_decimals=1))
    add_dim((f_left, f_top), (f_right, f_top), "above", 13, dim_label(overall_len, min_decimals=1))

    # Knob diameter dim on the left side of the front view
    add_dim((f_left, f_bot), (f_left, f_top), "left", 8, f"⌀{dim_label(knob_d)}")

    # Mid-X positions for leader callouts
    x_knob_mid = fx + SCALE * (knob_t / 2 - overall_len / 2)
    x_collar_mid = fx + SCALE * ((knob_t + collar_len / 2) - overall_len / 2)
    x_thread_mid = fx + SCALE * ((knob_t + collar_len + thread_len / 2) - overall_len / 2)

    # Knurl callout — leader from the top of the knob
    add_leader(
        (x_knob_mid, f_top),
        (x_knob_mid - 6, f_top + 24),
        "straight knurl, 0.5 pitch",
    )
    # Knob bottom chamfer — leader pointing at the −X (knob) end face
    add_leader(
        (f_left, f_bot),
        (f_left - 12, f_bot - 12),
        f"{dim_label(knob_chamfer)} × 45° chamfer",
    )
    # Collar diameter (⌀6.25)
    add_leader(
        (x_collar_mid, fy + SCALE * collar_d / 2),
        (x_collar_mid + 4, f_top + 24),
        f"⌀{dim_label(collar_d)} collar",
    )
    # M6 thread spec
    add_leader(
        (x_thread_mid, fy + SCALE * thread_d / 2),
        (x_thread_mid + 8, f_top + 24),
        f"{thread}×{thread_pitch:g}",
    )
    # Tip chamfer
    add_leader(
        (f_right, fy),
        (f_right + 12, f_bot - 10),
        f"{dim_label(chamfer)} × 45° chamfer",
    )
    # Ra 1.6 on the thread (mating surface)
    add_leader(
        (x_thread_mid, fy - SCALE * thread_d / 2),
        (x_thread_mid + 4, f_bot - 10),
        "Ra 1.6 on thread",
    )

    # --- End view label -----------------------------------------------------
    # End view shows the knob's circular cross-section (looking up the axis
    # from the knob end). Add a label so it's clear which end we're seeing.
    ex, ey = layout.end
    annotation_text.append(placed_text("END VIEW (knob)", 3.0, ex, ey - SCALE * knob_d / 2 - 6, left_align=False))

    # --- Iso view label -----------------------------------------------------
    annotation_text.append(placed_text("ISO VIEW", 3.0, layout.iso[0], layout.iso[1] - 18, left_align=False))

    # --- Frame, title block, notes ------------------------------------------
    frame = page_frame()
    title_lines = title_block_lines()
    title_text = title_block_text(
        part_name="DEPTH-LOCK BOLT",
        drawing_no="GRM-05",
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
    parts_visible, parts_hidden, frame, dim_shapes, text, annotations = build_depth_lock_bolt_drawing(params)
    export_drawing(
        svg_path="/tmp/depth_lock_bolt_drawing.svg",
        pdf_path="/tmp/depth_lock_bolt_drawing.pdf",
        parts_visible=parts_visible,
        parts_hidden=parts_hidden,
        frame=frame,
        dim_shapes=dim_shapes,
        text=text,
        annotations=annotations,
    )


if __name__ == "__main__":
    main()
