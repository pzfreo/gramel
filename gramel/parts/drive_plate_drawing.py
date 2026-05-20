"""
A4 landscape technical drawing of the drive plate — CNC handoff package.

The plate is a small egg-shaped brass disk that stands vertically up from
the shaft's outboard end, with two through-holes (mount + captive screw)
and an anti-rotation slot milled across the back face at the shaft end.

Layout: face view (camera at +X, showing the back face with the slot
solid) at upper-left, side edge view to its right, iso below. 3:1 scale —
the plate is only 9 × 17 × 3 mm so 1:1 would crowd the dim and leader
callouts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from build123d import Compound, Draft, Shape
from build123d_drafting import dim_linear, leader  # type: ignore[import-untyped]

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
from gramel.parts.drive_plate import build_drive_plate


SCALE = 3.0  # 3:1 — the plate is small (9 × 17 mm face)


@dataclass
class ViewPlacement:
    """View centroids on the sheet (frame coords). Part rendered at 3:1.

    Face view (back face, slot visible) upper-left; side edge view to its
    right; iso below.
    """

    face: tuple[float, float] = (-95.0, 20.0)
    side: tuple[float, float] = (-30.0, 20.0)
    iso: tuple[float, float] = (-50.0, -55.0)


def build_drive_plate_drawing(
    params: PurflingCutterParams,
) -> tuple[Compound, Compound, Compound, list[Shape[object]], Compound, Compound]:
    """Compose the drive plate drawing.

    Returns (parts_visible, parts_hidden, frame, dim_shapes, text, annotations).
    """
    params = params.model_copy(update={"process": params.process.model_copy(update={"prototype": False})})

    plate = build_drive_plate(params)
    dp = params.drive_plate

    r_big = dp.shaft_end_radius          # 4.5 → ⌀9
    r_small = dp.thumb_end_radius        # 3.0 → ⌀6
    thickness = dp.thickness             # 3.0
    gap = params.shank.crossbore_to_tapped_bore_gap  # 9.5
    mount_d = dp.mount_hole_diameter     # 2.4
    captive_d = dp.captive_clearance_hole_diameter  # 2.6
    tenon_depth = dp.tenon_depth         # 1.5 — tenon X projection from back face
    tenon_height = dp.tenon_height       # 3.0 — tenon Z extent
    tenon_width = dp.tenon_width         # 6.0 — tenon Y extent

    # World Z extent of the plate: −r_big to +r_small + gap
    z_min = -r_big
    z_max = gap + r_small
    z_centre = (z_min + z_max) / 2

    far = 1000.0
    centroid = (0, 0, z_centre)

    # --- Project the views --------------------------------------------------
    # Face view: camera at +X, up=+Z. world +Y → page -X; world +Z → page +Y.
    face_v, face_h = project_view(plate, (far, 0, z_centre), (0, 0, 1), centroid)
    # Side view: camera at +Y, up=+Z. world +X → page +X; world +Z → page +Y.
    side_v, side_h = project_view(plate, (0, far, z_centre), (0, 0, 1), centroid)
    # Iso view.
    iso_v, _iso_h = project_view(plate, (far, far, far), (0, 0, 1), centroid)

    layout = ViewPlacement()

    def place(compound: Compound, pos: tuple[float, float]) -> Compound:
        return compound.translate((pos[0], pos[1], 0))

    parts_visible = Compound(
        children=[
            place(face_v.scale(SCALE), layout.face),
            place(side_v.scale(SCALE), layout.side),
            place(iso_v.scale(SCALE), layout.iso),
        ]
    )
    parts_hidden = Compound(
        children=[
            place(face_h.scale(SCALE), layout.face),
            place(side_h.scale(SCALE), layout.side),
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

    # --- Face view page coords (centred at fx, fy) -------------------------
    # World +Y → page -X (sign flip): page X = fx − SCALE * worldY
    # World +Z → page +Y:             page Y = fy + SCALE * (worldZ − z_centre)
    fx, fy = layout.face

    def face_xy(world_y: float, world_z: float) -> tuple[float, float]:
        return (fx - SCALE * world_y, fy + SCALE * (world_z - z_centre))

    # Big boss outline (centre at (Y=0, Z=0)), small boss (Y=0, Z=gap)
    f_big_centre = face_xy(0, 0)
    f_small_centre = face_xy(0, gap)
    f_big_bot = face_xy(0, z_min)
    f_big_top = face_xy(0, 0 + r_big)      # top of big circle (Z = r_big)
    f_small_top = face_xy(0, z_max)
    f_big_left = face_xy(r_big, 0)         # world Y=+4.5 → page -X side
    f_big_right = face_xy(-r_big, 0)

    # Centre-to-centre vertical distance (9.5) — dim on the LEFT side,
    # past the big boss outline (half-width = 13.5 page units at 3:1).
    add_dim(f_big_centre, f_small_centre, "left", 20, f"{gap:.1f}")
    # Big boss diameter via leader
    add_leader(
        f_big_left,
        (f_big_left[0] - 14, f_big_left[1] - 6),
        f"⌀{2 * r_big:.0f}",
    )
    # Small boss diameter via leader
    add_leader(
        face_xy(r_small, gap),
        (face_xy(r_small, gap)[0] - 12, face_xy(r_small, gap)[1] + 6),
        f"⌀{2 * r_small:.0f}",
    )

    # Mount hole (big boss, Z=0) — leader to the right
    add_leader(
        f_big_centre,
        (f_big_right[0] + 14, f_big_centre[1] - 4),
        f"⌀{mount_d:.1f} mount",
    )
    # Captive bearing hole (small boss, Z=gap) — leader to the right.
    # Larger than the mount hole — the plate rides on this hole as a bearing.
    add_leader(
        f_small_centre,
        (face_xy(-r_small, gap)[0] + 14, f_small_centre[1] + 4),
        f"⌀{captive_d:.1f} captive bearing",
    )

    # Tenon Z height — leader on the right side (label too wide for inline dim).
    # Tenon is on the back face — shown as hidden lines in this front-face view.
    add_leader(
        face_xy(0, tenon_height / 2),
        (f_big_right[0] + 14, f_big_centre[1] + 12),
        f"tenon {tenon_height:.1f} tall × {tenon_width:.1f} wide",
    )

    # --- Side view page coords (centred at sx, sy) -------------------------
    # World +X → page +X: page X = sx + SCALE * worldX
    # World +Z → page +Y: page Y = sy + SCALE * (worldZ − z_centre)
    sx, sy = layout.side

    def side_xy(world_x: float, world_z: float) -> tuple[float, float]:
        return (sx + SCALE * world_x, sy + SCALE * (world_z - z_centre))

    s_front = side_xy(-thickness / 2, 0)   # −X face (outboard, captive-screw head side)
    s_back = side_xy(thickness / 2, 0)     # +X face (tenon root face)
    s_top = side_xy(0, z_max)
    s_bot = side_xy(0, z_min)

    # Thickness dim (3 mm) — below the part, measured between the two
    # plate faces (not including the tenon projection past +X).
    add_dim(
        (s_front[0], s_bot[1]),
        (s_back[0], s_bot[1]),
        "below",
        8,
        f"{thickness:.1f}",
    )

    # Tenon projection (1.5 mm past the +X face) — leader pointing at the tenon.
    tenon_tip = side_xy(thickness / 2 + tenon_depth, 0)
    add_leader(
        tenon_tip,
        (tenon_tip[0] + 14, tenon_tip[1] + 12),
        f"tenon {tenon_depth:.1f} proj.",
    )

    # --- Iso view label -----------------------------------------------------
    annotation_text.append(placed_text("ISO VIEW", 3.0, layout.iso[0], layout.iso[1] - 32, left_align=False))

    # --- Frame, title block, notes ------------------------------------------
    frame = page_frame()
    title_lines = title_block_lines()
    title_text = title_block_text(
        part_name="DRIVE PLATE",
        drawing_no="GRM-04",
        scale="3:1",
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
    parts_visible, parts_hidden, frame, dim_shapes, text, annotations = build_drive_plate_drawing(params)
    export_drawing(
        svg_path="/tmp/drive_plate_drawing.svg",
        pdf_path="/tmp/drive_plate_drawing.pdf",
        parts_visible=parts_visible,
        parts_hidden=parts_hidden,
        frame=frame,
        dim_shapes=dim_shapes,
        text=text,
        annotations=annotations,
    )


if __name__ == "__main__":
    main()
