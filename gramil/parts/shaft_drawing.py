"""
A4 landscape technical drawing of the shaft — CNC handoff package.

Third-angle layout for a horizontal shaft:
  - Top view    (camera at +Z, looking down)
  - Front view  (camera at -Y, looking from front) — below the top view
  - Right end   (camera at +X, looking at the +X end face) — right of front
  - Iso view    (camera at +X-Y+Z), 1:1

Shared page frame / title block / notes block / export pipeline live in
`gramil.parts._drawing`. Dim lines and leader callouts come from
`build123d_drafting` (`dim_linear`, `leader`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from build123d import Compound, Draft, Shape

from gramil import threads
from gramil.parameters import PurflingCutterParams
from gramil.parts._drawing import (
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
from gramil.parts._legacy_drafting import dim_linear, leader
from gramil.parts.shaft import build_shaft


@dataclass
class ViewPlacement:
    """View centroids on the sheet (frame coords).

    Third-angle projection for a horizontal shaft:
      - Top view at upper-left
      - Front view directly below (same X centre)
      - Right end view to the right of front view (same Y centre)
      - Iso view in the lower-left
    """

    top: tuple[float, float] = (-55.0, 50.0)
    front: tuple[float, float] = (-55.0, 5.0)
    end: tuple[float, float] = (10.0, 5.0)
    iso: tuple[float, float] = (-15.0, -55.0)


def build_shaft_drawing(
    params: PurflingCutterParams,
) -> tuple[Compound, Compound, Compound, list[Shape[object]], Compound, Compound]:
    """Compose the shaft drawing.

    Returns (parts_visible, parts_hidden, frame, dim_shapes, text, annotations).
    """
    # Force CNC representation: clean reference cylinders for threaded features.
    params = params.model_copy(update={"process": params.process.model_copy(update={"prototype": False})})

    shaft = build_shaft(params)
    sp = params.shaft
    od = params.shaft_outer_diameter
    length = sp.length
    flat_depth = sp.flat_depth
    slot_w = sp.blade_slot_width      # X dimension (along shaft) — 6 mm
    slot_y = sp.blade_slot_length     # Y dimension (across) — 5 mm
    end_to_slot = sp.end_to_slot_distance  # 4 mm; also grub-screw tap depth
    end_chamfer = sp.end_chamfer           # 45° chamfer on the +X end OD rim
    # The shaft now has a slot in the −X end face (the tenon lives on the
    # drive plate), so these are the SLOT dims — same values, mirror role.
    slot_x_depth = params.drive_plate.tenon_depth    # 1.5 mm into the end face
    slot_z_height = params.drive_plate.tenon_height  # 3.0 mm Z extent
    grub_thread = params.grub_screw.thread       # M4
    grub_pitch = threads.pitch(grub_thread)
    mount_thread = sp.drive_plate_mount_thread   # M2
    mount_pitch = threads.pitch(mount_thread)
    mount_depth = sp.drive_plate_mount_depth     # 5 mm

    shaft_fit = params.cutting_pair.shaft_fit    # g6

    centroid = (length / 2, 0, 0)
    far = 1000.0

    # --- Project the views --------------------------------------------------
    # Top view: world X → page X (+1), world Y → page Y (+1).
    top_v, top_h = project_view(shaft, (length / 2, 0, far), (0, 1, 0), centroid)
    # Front view: world X → page X (+1), world Z → page Y (+1).
    front_v, front_h = project_view(shaft, (length / 2, -far, 0), (0, 0, 1), centroid)
    # Right end view: world Y → page X (+1), world Z → page Y (+1).
    end_v, end_h = project_view(shaft, (far, 0, 0), (0, 0, 1), centroid)
    # Iso view: camera in +X-Y+Z octant (mirrors the front-view +X-on-right).
    iso_v, _iso_h = project_view(shaft, (far, -far, far), (0, 0, 1), centroid)

    layout = ViewPlacement()

    def place(compound: Compound, pos: tuple[float, float]) -> Compound:
        return compound.translate((pos[0], pos[1], 0))

    parts_visible = Compound(
        children=[
            place(top_v, layout.top),
            place(front_v, layout.front),
            place(end_v, layout.end),
            place(iso_v, layout.iso),
        ]
    )
    parts_hidden = Compound(
        children=[
            place(top_h, layout.top),
            place(front_h, layout.front),
            place(end_h, layout.end),
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

    # World coords → page coords for each view:
    #   Top view (tx, ty):     page X = tx + worldX − length/2; page Y = ty + worldY
    #   Front view (fx, fy):   page X = fx + worldX − length/2; page Y = fy + worldZ
    #   End view (ex, ey):     page X = ex + worldY;            page Y = ey + worldZ

    # --- Top view dims ------------------------------------------------------
    tx, ty = layout.top
    t_left = tx - length / 2           # cylinder −X end
    t_right = tx + length / 2          # cylinder +X end
    t_bot = ty - od / 2
    t_top = ty + od / 2

    add_dim((t_left, t_top), (t_right, t_top), "above", 5, dim_label(length, min_decimals=1))
    slot_x_start_world = length - end_to_slot - slot_w
    slot_x_end_world = length - end_to_slot
    slot_x_start = tx + slot_x_start_world - length / 2
    slot_x_end = tx + slot_x_end_world - length / 2
    slot_y_top = ty + slot_y / 2
    # Slot dimensions as one combined leader — the slot is only ~6 mm
    # wide, too short to host an inline dim label with the new
    # full-precision value.
    add_leader(
        ((slot_x_start + slot_x_end) / 2, slot_y_top),
        (slot_x_end + 6, ty + od / 2 + 14),
        f"slot {dim_label(slot_w)} × {dim_label(slot_y)}",
    )
    # End-face slot (anti-rotation, receives the drive-plate tenon) —
    # leader on the top view at the −X end.
    add_leader(
        (t_left + slot_x_depth / 2, t_bot),
        (t_left - 8, t_bot - 14),
        f"end slot {dim_label(slot_x_depth)} deep",
    )
    # Blade-slot POSITION along the shaft: dimension the slot's inboard (−X)
    # wall from the +X end face. (The outboard wall is end_to_slot = 4 mm from
    # the +X end, but 4 mm is too short for an inline dim at 1:1 — locate the
    # inboard wall; the 6.4 slot width on the leader gives the outboard wall.)
    add_dim(
        (slot_x_start, t_bot),
        (t_right, t_bot),
        "below",
        6,
        dim_label(end_to_slot + slot_w, min_decimals=1),
    )

    # --- Front view dims ----------------------------------------------------
    fx, fy = layout.front
    f_left = fx - length / 2
    f_bot = fy - od / 2
    f_top = fy + od / 2

    # Flat depth (0.6 mm) — leader because it's too small to dim inline.
    add_leader((f_left + 4, f_bot), (f_left + 4, f_bot - 14), f"flat {dim_label(flat_depth)} deep")
    # Surface finish + g6 fit on the OD.
    add_leader((fx, f_top), (fx + 18, f_top + 14), f"Ø{dim_label(od)} {shaft_fit}")
    add_leader((fx - 18, f_top), (fx - 8, f_top + 14), "Ra 1.6")
    # Mount tap on the −X end face.
    add_leader(
        (f_left, fy),
        (f_left - 18, fy - 16),
        f"{mount_thread}×{mount_pitch} × {dim_label(mount_depth)} deep",
    )
    # End-face slot Z height — dim inline near the −X end face.
    # min_decimals=1 forces "3.0" rather than "3" to avoid a build123d
    # dim_linear bug at certain path-length / label-width ratios.
    f_slot_top = fy + slot_z_height / 2
    f_slot_bot = fy - slot_z_height / 2
    add_dim((f_left, f_slot_bot), (f_left, f_slot_top), "left", 6, dim_label(slot_z_height, min_decimals=1))
    # Chamfer on the +X end OD rim (the grub-screw / blade end). Leader down
    # to the lower-right — the top of the front view is busy (Ø, Ra callouts).
    if end_chamfer > 0:
        f_right = fx + length / 2
        add_leader(
            (f_right, f_bot + 2),
            (f_right + 8, f_bot - 12),
            f"{dim_label(end_chamfer)} × 45° chamfer",
        )

    # --- Right end view -----------------------------------------------------
    ex, ey = layout.end
    # Diameter callout lives on the front view as Ø8.0 g6 — no need to repeat.
    # Grub-screw tap callout points up-right to clear the notes block (X ≥ 38.5).
    add_leader(
        (ex, ey),
        (ex + 4, ey + 16),
        f"{grub_thread}×{grub_pitch} × {dim_label(end_to_slot)} deep",
    )

    # --- Iso view label -----------------------------------------------------
    iso_label_y = layout.iso[1] - 18
    annotation_text.append(placed_text("ISO VIEW", 3.0, layout.iso[0], iso_label_y, left_align=False))

    # --- Frame, title block, notes ------------------------------------------
    frame = page_frame()
    title_lines = title_block_lines()
    title_text = title_block_text(
        part_name="SHAFT",
        drawing_no="GRM-02",
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
    parts_visible, parts_hidden, frame, dim_shapes, text, annotations = build_shaft_drawing(params)
    export_drawing(
        svg_path="/tmp/shaft_drawing.svg",
        pdf_path="/tmp/shaft_drawing.pdf",
        parts_visible=parts_visible,
        parts_hidden=parts_hidden,
        frame=frame,
        dim_shapes=dim_shapes,
        text=text,
        annotations=annotations,
    )


if __name__ == "__main__":
    main()
