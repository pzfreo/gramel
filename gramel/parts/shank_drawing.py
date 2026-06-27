"""
A4 landscape technical drawing of the shank — CNC handoff package.

Drawing standard: ISO 5457 frame + centering marks, ISO 7200 title block,
ISO 128 line types, ISO 2768-mK general tolerances, ISO 286 fits,
ISO 6410 simplified thread representation.

Layout — left half holds the views, right half holds notes + title block:
  - Working-face view (camera at +X, looking at the +X face)
  - Side view         (camera at +Y, looking at the -Y face)
  - Bottom view       (camera at -Z, looking up at the bottom face)
  - Iso view          (camera in +X+Y+Z octant) — 1:1, same scale as the
                      orthographic views.

Shared page frame / title block / notes block / export pipeline live in
`gramel.parts._drawing`. Dim lines and leader callouts come from
`build123d_drafting` (`dim_linear`, `leader`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from build123d import Compound, Draft, Shape
from build123d_drafting import dim_linear, leader  # type: ignore[import-untyped]

from gramel.parameters import PurflingCutterParams
from gramel.parts._drawing import (
    dim_label,
    export_drawing,
    line_segment,
    notes_block_lines,
    notes_block_text,
    page_frame,
    placed_text,
    project_view,
    title_block_lines,
    title_block_text,
)
from gramel.parts.shank import build_shank


@dataclass
class ViewPlacement:
    """View centroids on the sheet (frame coords).

    Third-angle layout for the vertical shank: bottom view directly below
    the side view (same X centre) so the working-face direction (world X)
    reads off the same vertical line on the page. Face view sits to the
    left of the side view with a wide gap to host its RHS dim and the
    bore callouts.
    """

    face: tuple[float, float] = (-118.0, 0.0)
    side: tuple[float, float] = (-65.0, 0.0)
    bottom: tuple[float, float] = (-65.0, -65.0)
    iso: tuple[float, float] = (12.0, 48.0)


def build_shank_drawing(
    params: PurflingCutterParams,
) -> tuple[Compound, Compound, Compound, list[Shape[object]], Compound, Compound]:
    """Compose the shank drawing.

    Returns (parts_visible, parts_hidden, frame, dim_shapes, text, annotations).
    """
    # Force CNC representation: clean reference cylinders for threaded features.
    params = params.model_copy(update={"process": params.process.model_copy(update={"prototype": False})})

    shank = build_shank(params)
    sp = params.shank
    length, width, depth = sp.length, sp.width, sp.depth

    cb_d = params.crossbore_diameter
    cb_x_from_top = sp.crossbore_position_from_top
    tap_x_from_top = params.tapped_bore_position_from_top
    inter_gap = sp.crossbore_to_tapped_bore_gap
    dl_d = sp.depth_lock_bore_diameter
    dl_collar_d = sp.depth_lock_collar_bore_diameter
    dl_collar_len = sp.depth_lock_collar_bore_length
    dl_thread_len = sp.depth_lock_threaded_length
    dl_depth = params.depth_lock_bore_depth
    slot_w = sp.relief_slot_width
    slot_d = sp.relief_slot_depth
    ds_thread = params.drive_screw.thread
    ds_pitch = params.drive_screw.thread_pitch
    dl_thread = params.depth_lock.thread

    centroid = (0, 0, length / 2)
    far = 1000.0

    # --- Project the four views ----------------------------------------------
    face_v, face_h = project_view(shank, (far, 0, length / 2), (0, 0, 1), centroid)
    side_v, side_h = project_view(shank, (0, far, length / 2), (0, 0, 1), centroid)
    bottom_v, bottom_h = project_view(shank, (0, 0, -far), (0, 1, 0), (0, 0, 0))
    iso_v, _iso_h = project_view(shank, (far, far, far), (0, 0, 1), centroid)

    layout = ViewPlacement()

    def place(compound: Compound, pos: tuple[float, float]) -> Compound:
        return compound.translate((pos[0], pos[1], 0))

    parts_visible = Compound(
        children=[
            place(face_v, layout.face),
            place(side_v, layout.side),
            place(bottom_v, layout.bottom),
            place(iso_v, layout.iso),
        ]
    )
    parts_hidden = Compound(
        children=[
            place(face_h, layout.face),
            place(side_h, layout.side),
            place(bottom_h, layout.bottom),
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

    # Working-face view: page X = world Y (depth), page Y = world Z (length).
    fx, fy = layout.face
    f_left = fx - depth / 2
    f_right = fx + depth / 2
    f_bot = fy - length / 2
    f_top = fy + length / 2
    add_dim((f_left, f_bot), (f_left, f_top), "left", 9, dim_label(length, min_decimals=1))
    cb_face_y = f_top - cb_x_from_top
    add_dim((f_right, f_top), (f_right, cb_face_y), "right", 8, dim_label(cb_x_from_top, min_decimals=1))
    # Below the face view: feature dim (slot width) as a leader because
    # the slot is only ~5.5 mm wide — too short for an inline dim label.
    # Overall dim (depth) inline below.
    add_leader(
        (fx, f_bot),
        (fx + 14, f_bot - 8),
        f"slot {dim_label(slot_w)} wide",
    )
    add_dim((f_left, f_bot), (f_right, f_bot), "below", 14, dim_label(depth, min_decimals=1))

    # Bore callouts pointing RIGHT into the gap between face view and side view.
    sx_for_face = layout.side[0]
    s_left_for_face = sx_for_face - width / 2
    leader_label_x = (f_right + s_left_for_face) / 2
    tap_face_y = f_top - tap_x_from_top
    add_leader((fx, cb_face_y), (leader_label_x, cb_face_y - 4), f"Ø{dim_label(cb_d)} H7")
    add_leader((fx, tap_face_y), (leader_label_x, tap_face_y + 3), f"{ds_thread}×{ds_pitch} thru")

    # Side view: page X = world X (width), page Y = world Z (length).
    sx, sy = layout.side
    s_left = sx - width / 2
    s_right = sx + width / 2
    s_bot = sy - length / 2
    s_top = sy + length / 2
    add_dim((s_left, s_bot), (s_right, s_bot), "below", 6, dim_label(width, min_decimals=1))
    cb_side_y = s_top - cb_x_from_top
    tap_side_y = s_top - tap_x_from_top
    add_dim((s_right, cb_side_y), (s_right, tap_side_y), "right", 8, dim_label(inter_gap, min_decimals=1))
    s_collar_top = s_bot + dl_collar_len
    s_thread_top = s_collar_top + dl_thread_len
    # Collar + threaded + smooth section dims sit FURTHER OUT than the leader
    # callouts below — so the leader lines don't cross through the dim lines.
    # The collar segment is only ~5.5 mm so use a leader rather than an
    # inline dim (label wider than segment triggers a build123d edge case).
    add_leader(
        (s_right, (s_bot + s_collar_top) / 2),
        (s_right + 24, s_collar_top + 4),
        f"collar {dim_label(dl_collar_len)} long",
    )
    add_dim((s_right, s_collar_top), (s_right, s_thread_top), "right", 32, dim_label(dl_thread_len, min_decimals=1))
    add_dim((s_right, s_thread_top), (s_right, cb_side_y), "right", 38, dim_label(dl_depth - dl_collar_len - dl_thread_len, min_decimals=1))
    # Section-boundary indicator lines across the bore.
    bore_half = dl_d / 2
    collar_half = dl_collar_d / 2
    annotation_lines.append(line_segment(sx - collar_half, s_collar_top, sx + collar_half, s_collar_top))
    annotation_lines.append(line_segment(sx - bore_half, s_thread_top, sx + bore_half, s_thread_top))

    # Depth-lock bore-section callouts — leaders pointing RIGHT.
    side_label_x = s_right + 16
    add_leader((sx, (s_bot + s_collar_top) / 2), (side_label_x, (s_bot + s_collar_top) / 2), f"Ø{dim_label(dl_collar_d)}")
    add_leader((sx, (s_collar_top + s_thread_top) / 2), (side_label_x, (s_collar_top + s_thread_top) / 2), f"{dl_thread}×1")
    push_rod_mid_y = (s_thread_top + cb_side_y) / 2
    add_leader((sx, push_rod_mid_y), (side_label_x, push_rod_mid_y), f"Ø{dim_label(dl_d)} H8")

    # Relief slot depth callout — leader pointing LEFT from the slot's
    # inner edge in the side view to a label in the empty gap below the
    # face-view bore callouts.
    slot_inner_x = s_left + slot_d
    slot_mid_y = s_bot + (s_thread_top - s_bot) * 0.7
    # Label sits in the gap between the face view (to the left) and the side
    # view: -20 pushed its left end ~2 mm onto the face view outline; -10
    # centres the ~20 mm label in the ~40 mm gap, clearing both views.
    add_leader(
        (slot_inner_x, slot_mid_y),
        (s_left - 10, slot_mid_y),
        f"slot {dim_label(slot_d)} deep, flat floor",
    )

    # Bottom view: width (page X, working-face direction) × depth (page Y).
    bx, by = layout.bottom
    b_left = bx - width / 2
    b_right = bx + width / 2
    b_bot = by - depth / 2
    b_top = by + depth / 2
    add_dim((b_left, b_bot), (b_right, b_bot), "below", 6, dim_label(width, min_decimals=1))
    add_dim((b_right, b_bot), (b_right, b_top), "right", 6, dim_label(depth, min_decimals=1))

    # Iso view label.
    iso_label_y = layout.iso[1] - 40
    annotation_text.append(placed_text("ISO VIEW", 3.0, layout.iso[0], iso_label_y, left_align=False))

    # --- Frame, title block, notes ------------------------------------------
    frame = page_frame()
    title_lines = title_block_lines()
    title_text = title_block_text(
        part_name="SHANK",
        drawing_no="GRM-01",
        scale="1:1",
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
    parts_visible, parts_hidden, frame, dim_shapes, text, annotations = build_shank_drawing(params)
    export_drawing(
        svg_path="/tmp/shank_drawing.svg",
        pdf_path="/tmp/shank_drawing.pdf",
        parts_visible=parts_visible,
        parts_hidden=parts_hidden,
        frame=frame,
        dim_shapes=dim_shapes,
        text=text,
        annotations=annotations,
    )


if __name__ == "__main__":
    main()
