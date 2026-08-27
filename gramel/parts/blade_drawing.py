"""
A4 landscape drawing of the violin purfling blade (GRM-07).

The blade is a small O1 tool-steel knife. The shop supplies it with a
single-bevel grind at the tip; the luthier finish-grinds and hones the
cutting edge after delivery.

Layout: face view (Z up, looking along X) on the left, side view to
its right at same scale. The bevel wedge is visible in the side view
at the tip.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from build123d import Compound, Draft, Shape

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
from gramel.parts._legacy_drafting import dim_linear, leader
from gramel.parts.blade import build_blade

SCALE = 5.0  # 5:1 — 23 × 3.6 mm blade


@dataclass
class ViewPlacement:
    """View centroids on the sheet (frame coords). Two views at 5:1."""

    face: tuple[float, float] = (-100.0, 0.0)
    side: tuple[float, float] = (-50.0, 0.0)


def build_blade_drawing(
    params: PurflingCutterParams,
) -> tuple[Compound, Compound, Compound, list[Shape[object]], Compound, Compound]:
    """Compose the blade drawing.

    Returns (parts_visible, parts_hidden, frame, dim_shapes, text, annotations).
    """
    blade_part = build_blade(params)
    b = params.blade
    width = b.width
    length = b.length
    thick = b.thickness
    bevel_angle = b.bevel_angle
    bevel_run = thick / math.tan(math.radians(bevel_angle))
    tip_radius = width / 2

    centroid = (0, 0, 0)
    far = 1000.0

    # Face view: camera at +X, up=+Z → world +Y → page −X, world +Z → page +Y.
    face_v, face_h = project_view(blade_part, (far, 0, 0), (0, 0, 1), centroid)
    # Side view: camera at +Y, up=+Z → world +X → page +X, world +Z → page +Y.
    side_v, side_h = project_view(blade_part, (0, far, 0), (0, 0, 1), centroid)

    layout = ViewPlacement()

    def place(compound: Compound, pos: tuple[float, float]) -> Compound:
        return compound.translate((pos[0], pos[1], 0))

    parts_visible = Compound(
        children=[
            place(face_v.scale(SCALE), layout.face),
            place(side_v.scale(SCALE), layout.side),
        ]
    )
    parts_hidden = Compound(
        children=[
            place(face_h.scale(SCALE), layout.face),
            place(side_h.scale(SCALE), layout.side),
        ]
    )

    # --- Dimensions ---------------------------------------------------------
    draft = Draft(font_size=2.0, decimal_precision=2, arrow_length=1.0, line_width=0.1)
    leader_draft = Draft(font_size=2.4, decimal_precision=2, arrow_length=1.0, line_width=0.1)

    dim_shapes: list[Shape[object]] = []
    annotation_lines: list[Shape[object]] = []
    annotation_text: list[Shape[object]] = []

    def add_dim(p1, p2, side, distance, label):  # type: ignore[no-untyped-def]
        result = dim_linear((p1[0], p1[1], 0), (p2[0], p2[1], 0), side, distance, draft, label=label)
        dim_shapes.append(result.shape)

    def add_leader(feature_xy, label_anchor_xy, label):  # type: ignore[no-untyped-def]
        result = leader(
            tip=(feature_xy[0], feature_xy[1], 0),
            elbow=(label_anchor_xy[0], label_anchor_xy[1], 0),
            label=label,
            draft=leader_draft,
        )
        annotation_lines.append(result.lines)
        annotation_text.append(result.text)

    # Face view coords: world +Y → page −X, world +Z → page +Y.
    fx, fy = layout.face

    def face_xy(world_y: float, world_z: float) -> tuple[float, float]:
        return (fx - SCALE * world_y, fy + SCALE * world_z)

    # Side view coords: world +X → page +X, world +Z → page +Y.
    sx, sy = layout.side

    def side_xy(world_x: float, world_z: float) -> tuple[float, float]:
        return (sx + SCALE * world_x, sy + SCALE * world_z)

    # --- Face view dims (long Z left side, width above the top) ---
    f_top_left = face_xy(+width / 2, length / 2)
    f_top_right = face_xy(-width / 2, length / 2)
    f_bot_left = face_xy(+width / 2, -length / 2)

    # Overall length on the LEFT
    add_dim(
        (f_bot_left[0], f_bot_left[1]),
        (f_top_left[0], f_top_left[1]),
        "left",
        10,
        dim_label(length, min_decimals=1),
    )
    # Width ABOVE the top edge
    add_dim(
        f_top_left,
        f_top_right,
        "above",
        6,
        dim_label(width, min_decimals=1),
    )
    # Tip radius callout
    tip_curve_xy = face_xy(width / 2.5, -length / 2 + tip_radius * 0.5)
    add_leader(
        tip_curve_xy,
        (tip_curve_xy[0] + 18, tip_curve_xy[1] - 10),
        f"R {dim_label(tip_radius)}",
    )

    # --- Side view dims (callouts only — the side view is only 3.5 mm wide at 5:1) ---
    # Thickness — leader from the side view's top edge
    s_top_mid = side_xy(0, length / 2)
    add_leader(
        s_top_mid,
        (s_top_mid[0] + 18, s_top_mid[1] + 6),
        f"thickness {dim_label(thick)}",
    )

    # Bevel-run dim on the RIGHT of the side view's tip (1.5 mm × 5 = 7.5 mm — fits)
    # bevel_run is derived from bevel_angle and thickness; show 1 decimal
    # (the shop grinds the bevel by angle, not by run length).
    s_bevel_tip = side_xy(+thick / 2, -length / 2)
    s_bevel_heel = side_xy(+thick / 2, -length / 2 + bevel_run)
    add_dim(
        s_bevel_tip,
        s_bevel_heel,
        "right",
        6,
        dim_label(bevel_run, min_decimals=1, max_decimals=1),
    )

    # Bevel angle leader to the bevel face midpoint
    bevel_face_mid = side_xy(0, -length / 2 + bevel_run / 2)
    add_leader(
        bevel_face_mid,
        (bevel_face_mid[0] + 22, bevel_face_mid[1] - 8),
        f"{dim_label(bevel_angle)}° single bevel",
    )

    # View labels above each view
    fv_label = placed_text("FACE", 3.5, fx, fy + SCALE * length / 2 + 15, left_align=False)
    sv_label = placed_text("SIDE", 3.5, sx, sy + SCALE * length / 2 + 15, left_align=False)

    # --- Frame, title block, notes ------------------------------------------
    frame = page_frame()
    title_lines = title_block_lines()
    title_text = title_block_text(
        part_name="BLADE",
        drawing_no="GRM-07",
        scale="5:1",
        sheet="1/1",
        material="O1 tool steel, hardened ~60 HRC",
        drawn_by="P. Fremantle",
        drawn_date=date.today().isoformat(),
    )
    nb_lines = notes_block_lines()
    nb_text = notes_block_text(notes=(
        "NOTES:",
        "1. Material: O1 tool steel, hardened & tempered ~60 HRC",
        "2. Outline ± 0.05; thickness ± 0.025",
        "3. Single bevel as shown — primary grind + hone by luthier",
        "4. Tip: rounded, polished",
        "5. Quantity: 2 per tool (see RFQ for batch quantities)",
        "6. All dimensions in mm",
    ))
    frame_compound = Compound(children=[frame, title_lines, nb_lines])
    text_compound = Compound(
        children=[title_text, nb_text, fv_label, sv_label, *annotation_text]
    )
    annotations_compound = Compound(children=annotation_lines)

    return parts_visible, parts_hidden, frame_compound, dim_shapes, text_compound, annotations_compound


def main() -> None:
    params = PurflingCutterParams()
    parts_visible, parts_hidden, frame, dim_shapes, text, annotations = build_blade_drawing(params)
    export_drawing(
        svg_path="/tmp/blade_drawing.svg",
        pdf_path="/tmp/blade_drawing.pdf",
        parts_visible=parts_visible,
        parts_hidden=parts_hidden,
        frame=frame,
        dim_shapes=dim_shapes,
        text=text,
        annotations=annotations,
    )


if __name__ == "__main__":
    main()
