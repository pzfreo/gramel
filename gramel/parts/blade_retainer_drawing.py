"""
A4 landscape drawing of the bone-shaped copper blade retainer (GRM-06).

The retainer is a flat sheet-metal part — laser cut or stamped from
copper sheet stock. The drawing shows the 2D outline (the profile that
will be cut) and a thickness callout. No iso view: nothing useful to
see in 3D for a flat part.

Layout: face view (looking along X, the thickness direction) at upper
half, dim stack around it, notes + title block on the right.
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
    notes_block_lines,
    notes_block_text,
    page_frame,
    project_view,
    title_block_lines,
    title_block_text,
)
from gramel.parts.blade_retainer import build_blade_retainer

SCALE = 5.0  # 5:1 — the part is only 10 × 5.5 × 0.75 mm


@dataclass
class ViewPlacement:
    """View centroid on the sheet (frame coords). One face view at 5:1."""

    face: tuple[float, float] = (-60.0, 15.0)


def build_blade_retainer_drawing(
    params: PurflingCutterParams,
) -> tuple[Compound, Compound, Compound, list[Shape[object]], Compound, Compound]:
    """Compose the retainer drawing.

    Returns (parts_visible, parts_hidden, frame, dim_shapes, text, annotations).
    """
    retainer = build_blade_retainer(params)
    r = params.blade_retainer
    end_w = r.end_width
    mid_w = r.middle_width
    length = r.length
    mid_length = r.middle_length
    thick = r.thickness

    centroid = (0, 0, 0)
    far = 1000.0

    # Face view: camera at +X, up=+Z → world +Y → page -X, world +Z → page +Y.
    face_v, face_h = project_view(retainer, (far, 0, 0), (0, 0, 1), centroid)

    layout = ViewPlacement()

    def place(compound: Compound, pos: tuple[float, float]) -> Compound:
        return compound.translate((pos[0], pos[1], 0))

    parts_visible = Compound(children=[place(face_v.scale(SCALE), layout.face)])
    parts_hidden = Compound(children=[place(face_h.scale(SCALE), layout.face)])

    # --- Dimensions ---------------------------------------------------------
    draft = Draft(font_size=2.0, decimal_precision=1, arrow_length=1.0, line_width=0.1)
    leader_draft = Draft(font_size=2.4, decimal_precision=1, arrow_length=1.0, line_width=0.1)

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

    fx, fy = layout.face
    # World +Y → page -X. World +Z → page +Y. Scale 5:1.
    def face_xy(world_y: float, world_z: float) -> tuple[float, float]:
        return (fx - SCALE * world_y, fy + SCALE * world_z)

    # Outer extents
    end_z = (length - mid_length) / 2  # 1.5 mm — each end block
    f_top = face_xy(0, length / 2)
    f_bot = face_xy(0, -length / 2)
    f_end_right = face_xy(-end_w / 2, length / 2)   # +Y end is at -X on page
    f_end_left = face_xy(end_w / 2, length / 2)
    f_mid_right = face_xy(-mid_w / 2, 0)
    f_mid_left = face_xy(mid_w / 2, 0)

    # Overall length (Z) on the LEFT side of the part
    add_dim(
        (f_end_left[0], f_bot[1]),
        (f_end_left[0], f_top[1]),
        "left",
        10,
        dim_label(length, min_decimals=1),
    )
    # End width (Y) ABOVE the top end block
    add_dim(
        (f_end_left[0], f_top[1]),
        (f_end_right[0], f_top[1]),
        "above",
        6,
        dim_label(end_w, min_decimals=1),
    )
    # Middle width (Y) BELOW the middle block
    add_dim(
        (f_mid_left[0], face_xy(0, 0)[1]),
        (f_mid_right[0], face_xy(0, 0)[1]),
        "below",
        16,
        dim_label(mid_w, min_decimals=1),
    )
    # End-block Z length, on the right side
    add_dim(
        (f_end_right[0], face_xy(0, length / 2 - end_z)[1]),
        (f_end_right[0], f_top[1]),
        "right",
        6,
        dim_label(end_z, min_decimals=1),
    )
    # Waist Z length, on the right at further offset
    add_dim(
        (f_end_right[0], face_xy(0, -mid_length / 2)[1]),
        (f_end_right[0], face_xy(0, +mid_length / 2)[1]),
        "right",
        16,
        dim_label(mid_length, min_decimals=1),
    )

    # Thickness callout (X direction — out of page)
    add_leader(
        f_mid_right,
        (f_mid_right[0] + 22, f_mid_right[1] - 8),
        f"thickness {dim_label(thick)}",
    )

    # Process / finish callout
    add_leader(
        face_xy(0, length / 4),
        (fx + 30, fy + 15),
        "laser cut or stamped, deburred",
    )

    # --- Frame, title block, notes ------------------------------------------
    frame = page_frame()
    title_lines = title_block_lines()
    title_text = title_block_text(
        part_name="BLADE RETAINER",
        drawing_no="GRM-06",
        scale="5:1",
        sheet="1/1",
        material="Copper sheet, annealed (4× per tool)",
        drawn_by="P. Fremantle",
        drawn_date=date.today().isoformat(),
    )
    nb_lines = notes_block_lines()
    nb_text = notes_block_text(notes=(
        "NOTES:",
        "1. General tolerances per ISO 2768-mK",
        "2. Material: copper sheet, annealed",
        "3. Process: laser cut or stamped",
        "4. All dimensions in mm",
        "5. Outline ± 0.1 mm; thickness ± 0.05 mm",
        "6. Deburr edges; as-received sheet finish OK",
    ))
    frame_compound = Compound(children=[frame, title_lines, nb_lines])
    text_compound = Compound(children=[title_text, nb_text, *annotation_text])
    annotations_compound = Compound(children=annotation_lines)

    return parts_visible, parts_hidden, frame_compound, dim_shapes, text_compound, annotations_compound


def main() -> None:
    params = PurflingCutterParams()
    parts_visible, parts_hidden, frame, dim_shapes, text, annotations = build_blade_retainer_drawing(params)
    export_drawing(
        svg_path="/tmp/blade_retainer_drawing.svg",
        pdf_path="/tmp/blade_retainer_drawing.pdf",
        parts_visible=parts_visible,
        parts_hidden=parts_hidden,
        frame=frame,
        dim_shapes=dim_shapes,
        text=text,
        annotations=annotations,
    )


if __name__ == "__main__":
    main()
