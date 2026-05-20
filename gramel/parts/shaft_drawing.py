"""
A4 landscape technical drawing of the shaft — CNC handoff package.

Drawing standard: ISO 5457 frame + centering marks, ISO 7200 title block,
ISO 128 line types, ISO 2768-mK general tolerances, ISO 286 fits,
ISO 6410 simplified thread representation.

Layout — horizontal shaft means views stack with X-aligned columns:
  - Top view    (camera at +Z, looking down)
  - Front view  (camera at -Y, looking from front)  → below the top view
  - Right end   (camera at +X, looking at the +X end face)  → right of front
  - Iso view    (camera in +X-Y+Z octant), 1:1

Geometry is built with process.prototype=False so threaded features
(grub-screw end tap, drive-plate mount tap) are plain reference
cylinders at tap-drill diameter — the shop reads the thread spec off
the drawing per ISO 6410.

Dim lines and leader callouts use `build123d_drafting` (`dim_linear`,
`leader`). The custom page frame, title block, and notes block stay
local — they're sheet-specific layout that the library's
`iso_title_block` (170 × 16 mm) doesn't cover.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from build123d import (
    Color,
    Compound,
    Draft,
    Edge,
    ExportSVG,
    LineType,
    Part,
    Shape,
    Text,
    Wire,
)
from build123d_drafting import dim_linear, leader  # type: ignore[import-untyped]

from gramel import threads
from gramel.parameters import PurflingCutterParams
from gramel.parts.shaft import build_shaft

# ---------------------------------------------------------------------------
# Page geometry — ISO 5457 A4 landscape (matches shank_drawing.py)
# ---------------------------------------------------------------------------

PAGE_W = 297.0
PAGE_H = 210.0
FRAME_MARGIN = 10.0
FW = PAGE_W - 2 * FRAME_MARGIN  # 277
FH = PAGE_H - 2 * FRAME_MARGIN  # 190
FX_MAX = FW / 2  # 138.5
FX_MIN = -FX_MAX
FY_MAX = FH / 2  # 95
FY_MIN = -FY_MAX

TB_W = 100.0
TB_H = 50.0
TB_X_MAX = FX_MAX
TB_X_MIN = TB_X_MAX - TB_W
TB_Y_MIN = FY_MIN
TB_Y_MAX = TB_Y_MIN + TB_H

NB_X_MIN = TB_X_MIN
NB_X_MAX = TB_X_MAX
NB_Y_MIN = TB_Y_MAX + 2
NB_Y_MAX = NB_Y_MIN + 50


@dataclass
class ViewPlacement:
    """View centroids on the sheet (frame coords).

    Third-angle projection layout for a horizontal shaft:
      - Top view at upper-left
      - Front view directly below (same X centre)
      - Right end view to the right of front view (same Y centre)
      - Iso view in the lower-left area
    """

    top: tuple[float, float] = (-55.0, 50.0)
    front: tuple[float, float] = (-55.0, 5.0)
    end: tuple[float, float] = (10.0, 5.0)
    iso: tuple[float, float] = (-15.0, -55.0)


# ---------------------------------------------------------------------------
# Helpers (page frame + title/notes blocks)
# ---------------------------------------------------------------------------


def _project(
    shape: Part,
    origin: tuple[float, float, float],
    up: tuple[float, float, float],
    look_at: tuple[float, float, float],
) -> tuple[Compound, Compound]:
    visible, hidden = shape.project_to_viewport(origin, up, look_at)
    return (
        Compound(children=list(visible)),
        Compound(children=list(hidden)),
    )


def _placed_text(text: str, size: float, x: float, y: float, left_align: bool = True) -> Compound:
    txt = Text(txt=text, font_size=size)
    bb = txt.bounding_box()
    dx = x - bb.min.X if left_align else x - (bb.min.X + bb.max.X) / 2
    dy = y - (bb.min.Y + bb.max.Y) / 2
    return txt.translate((dx, dy, 0))


def _line(x1: float, y1: float, x2: float, y2: float) -> Edge:
    return Edge.make_line((x1, y1, 0), (x2, y2, 0))


def _page_frame() -> Compound:
    border = Wire.make_polygon(
        [(FX_MIN, FY_MIN, 0), (FX_MAX, FY_MIN, 0), (FX_MAX, FY_MAX, 0), (FX_MIN, FY_MAX, 0)],
        close=True,
    )
    tick = 3.0
    ticks = [
        _line(0, FY_MIN, 0, FY_MIN - tick),
        _line(0, FY_MAX, 0, FY_MAX + tick),
        _line(FX_MIN, 0, FX_MIN - tick, 0),
        _line(FX_MAX, 0, FX_MAX + tick, 0),
    ]
    return Compound(children=[border, *ticks])


def _title_block_lines() -> Compound:
    box = Wire.make_polygon(
        [
            (TB_X_MIN, TB_Y_MIN, 0),
            (TB_X_MAX, TB_Y_MIN, 0),
            (TB_X_MAX, TB_Y_MAX, 0),
            (TB_X_MIN, TB_Y_MAX, 0),
        ],
        close=True,
    )
    h_lines = [
        _line(TB_X_MIN, TB_Y_MIN + i * 10, TB_X_MAX, TB_Y_MIN + i * 10) for i in (1, 2, 3, 4)
    ]
    mid_x = TB_X_MIN + 30
    v_line = _line(mid_x, TB_Y_MIN, mid_x, TB_Y_MIN + 40)
    return Compound(children=[box, *h_lines, v_line])


def _title_block_text(
    *,
    part_name: str,
    drawing_no: str,
    scale: str,
    sheet: str,
    material: str,
    drawn_by: str,
    drawn_date: str,
) -> Compound:
    label_size = 2.0
    value_size = 2.8
    title_size = 5.0
    mid_x = TB_X_MIN + 30
    txt_x_label = TB_X_MIN + 2
    txt_x_value = mid_x + 2
    title_y_centre = TB_Y_MIN + 45
    return Compound(
        children=[
            _placed_text(part_name, title_size, (TB_X_MIN + TB_X_MAX) / 2, title_y_centre, left_align=False),
            _placed_text("DRAWING NO.", label_size, txt_x_label, TB_Y_MIN + 35),
            _placed_text(drawing_no, value_size, txt_x_value, TB_Y_MIN + 35),
            _placed_text("SCALE", label_size, txt_x_label, TB_Y_MIN + 25),
            _placed_text(f"{scale}   SHEET {sheet}", value_size, txt_x_value, TB_Y_MIN + 25),
            _placed_text("MATERIAL", label_size, txt_x_label, TB_Y_MIN + 15),
            _placed_text(material, value_size, txt_x_value, TB_Y_MIN + 15),
            _placed_text("DRAWN", label_size, txt_x_label, TB_Y_MIN + 5),
            _placed_text(f"{drawn_by}   {drawn_date}", value_size, txt_x_value, TB_Y_MIN + 5),
        ]
    )


def _notes_block_lines() -> Compound:
    box = Wire.make_polygon(
        [
            (NB_X_MIN, NB_Y_MIN, 0),
            (NB_X_MAX, NB_Y_MIN, 0),
            (NB_X_MAX, NB_Y_MAX, 0),
            (NB_X_MIN, NB_Y_MAX, 0),
        ],
        close=True,
    )
    return Compound(children=[box])


def _notes_block_text(notes: list[str]) -> Compound:
    size = 2.4
    line_step = 4.5
    y_top = NB_Y_MAX - 4
    return Compound(
        children=[
            _placed_text(line, size, NB_X_MIN + 2, y_top - i * line_step, left_align=True)
            for i, line in enumerate(notes)
        ]
    )


# ---------------------------------------------------------------------------
# Main composer
# ---------------------------------------------------------------------------


def build_shaft_drawing(
    params: PurflingCutterParams,
) -> tuple[Compound, Compound, Compound, list[Shape[object]], Compound, Compound]:
    """
    Compose the shaft drawing.

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
    slot_y = sp.blade_slot_length     # Y dimension (across)       — 5 mm
    end_to_slot = sp.end_to_slot_distance  # 4 mm — also grub-screw tap depth
    tenon_depth = sp.tenon_depth      # 1 mm — X projection
    tenon_height = sp.tenon_height    # 2 mm — Z height
    grub_thread = params.grub_screw.thread       # M4
    grub_pitch = threads.pitch(grub_thread)
    mount_thread = sp.drive_plate_mount_thread   # M2
    mount_pitch = threads.pitch(mount_thread)
    mount_depth = sp.drive_plate_mount_depth     # 5 mm

    shaft_fit = params.cutting_pair.shaft_fit    # g6

    centroid = (length / 2, 0, 0)
    far = 1000.0

    # --- Project the views ----------------------------------------------------
    # Top view: camera at +Z, up=+Y → world X = page X (+1), world Y = page Y (+1).
    top_v, top_h = _project(shaft, (length / 2, 0, far), (0, 1, 0), centroid)
    # Front view: camera at -Y, up=+Z → world X = page X (+1), world Z = page Y (+1).
    front_v, front_h = _project(shaft, (length / 2, -far, 0), (0, 0, 1), centroid)
    # Right end view: camera at +X, up=+Z → world Y = page X (+1), world Z = page Y (+1).
    end_v, end_h = _project(shaft, (far, 0, 0), (0, 0, 1), centroid)
    # Iso view: camera at +X-Y+Z (mirrors the front-view +X-on-right orientation).
    iso_v, _iso_h = _project(shaft, (far, -far, far), (0, 0, 1), centroid)

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

    # --- Dimensions per view --------------------------------------------------
    draft = Draft(
        font_size=2.0,
        decimal_precision=1,
        arrow_length=1.0,
        line_width=0.1,
    )
    leader_draft = Draft(
        font_size=2.4,
        decimal_precision=1,
        arrow_length=1.0,
        line_width=0.1,
    )

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
        result = dim_linear(
            (p1[0], p1[1], 0),
            (p2[0], p2[1], 0),
            side,
            distance,
            draft,
            label=label,
        )
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
    #
    # Top view (tx, ty):
    #   world X → page X = tx + worldX − length/2  (shaft centroid at length/2)
    #   world Y → page Y = ty + worldY
    # Front view (fx, fy):
    #   world X → page X = fx + worldX − length/2
    #   world Z → page Y = fy + worldZ
    # End view (ex, ey):
    #   world Y → page X = ex + worldY
    #   world Z → page Y = ey + worldZ
    #
    # Helpers: shaft world X spans [-tenon_depth, length] = [-1, 45]. The
    # projection centroid is (length/2, 0, 0) so world X = 0 maps to page X
    # = tx − length/2; world X = length maps to page X = tx + length/2.

    # --- Top view dims (axis horizontal, view shows X×Y plane) ---------------
    tx, ty = layout.top
    t_left = tx - length / 2           # world X = 0 (−X end of cylinder body, NOT tenon)
    t_right = tx + length / 2          # world X = length (+X end face)
    t_tenon_x = t_left - tenon_depth   # world X = -tenon_depth (tenon outer face)
    t_bot = ty - od / 2
    t_top = ty + od / 2

    # Overall length from tenon face to +X end
    add_dim((t_tenon_x, t_top), (t_right, t_top), "above", 10, f"{length + tenon_depth:.1f}")
    # Cylinder length (without tenon)
    add_dim((t_left, t_top), (t_right, t_top), "above", 5, f"{length:.1f}")
    # (Diameter is dimensioned on the end view + as a g6 callout on the front view.)
    # Slot X dim (6 mm) — end-to-slot distance (4 mm) lives in the grub-tap
    # callout on the end view, so no separate dim needed for it.
    slot_x_start_world = length - end_to_slot - slot_w  # world X where slot starts (−X edge of slot)
    slot_x_end_world = length - end_to_slot             # world X where slot ends (+X edge)
    slot_x_start = tx + slot_x_start_world - length / 2
    slot_x_end = tx + slot_x_end_world - length / 2
    add_dim((slot_x_start, t_bot), (slot_x_end, t_bot), "below", 5, f"{slot_w:.0f}")
    # Slot Y opening (5 mm) — small dim inside the slot's footprint
    slot_y_top = ty + slot_y / 2
    # Witness lines extend from the slot's two long edges; dim drawn above slot
    slot_dim_x = (slot_x_start + slot_x_end) / 2
    # Use a leader for the slot Y (small dim on a tight feature)
    add_leader(
        (slot_dim_x, slot_y_top),
        (slot_dim_x + 12, ty + od / 2 + 14),
        f"slot {slot_y:.0f} wide",
    )

    # Tenon X-projection callout (1 mm — too small to dim inline)
    add_leader(
        (t_tenon_x + tenon_depth / 2, t_bot),
        (t_tenon_x - 10, t_bot - 14),
        f"tenon {tenon_depth:.0f} proj.",
    )

    # --- Front view dims (axis X, height Z) ----------------------------------
    fx, fy = layout.front
    f_left = fx - length / 2           # world X = 0
    f_tenon_x = f_left - tenon_depth
    f_bot = fy - od / 2
    f_top = fy + od / 2

    # Flat depth callout — 0.6 mm is too small to dim inline; use a leader.
    add_leader(
        (f_left + 4, f_bot),
        (f_left + 4, f_bot - 14),
        f"flat {flat_depth:.1f} deep",
    )

    # Surface finish + g6 fit callout on the front view's OD
    add_leader(
        (fx, f_top),
        (fx + 18, f_top + 14),
        f"⌀{od:.1f} {shaft_fit}",
    )
    add_leader(
        (fx - 18, f_top),
        (fx - 8, f_top + 14),
        "Ra 1.6",
    )

    # --- Right end view dims (cross-section at +X end) -----------------------
    ex, ey = layout.end
    # (Diameter callout lives on the front view as ⌀8.0 g6; no need to
    # repeat it here. The ⌀ in an 8 mm dim crashes dim_linear anyway.)

    # Grub-screw tap callout — leader pointing up-right from the end view's
    # centre to a label above. Keeps clear of the notes block (X ≥ 38.5).
    add_leader(
        (ex, ey),
        (ex + 4, ey + 16),
        f"{grub_thread}×{grub_pitch} × {end_to_slot:.0f} deep",
    )

    # --- Mount tap callout (M2) on the front view, pointing to the −X end face -
    # The mount tap is on the −X end face (centred on the shaft axis).
    add_leader(
        (f_tenon_x, fy),
        (f_tenon_x - 18, fy - 16),
        f"{mount_thread}×{mount_pitch} × {mount_depth:.0f} deep",
    )

    # --- Tenon height (Z) dim — on the front view ---------------------------
    f_tenon_top = fy + tenon_height / 2
    f_tenon_bot = fy - tenon_height / 2
    add_dim(
        (f_tenon_x, f_tenon_bot), (f_tenon_x, f_tenon_top), "left", 6, f"{tenon_height:.0f}"
    )

    # --- Iso view label ------------------------------------------------------
    iso_label_y = layout.iso[1] - 18
    annotation_text.append(_placed_text("ISO VIEW", 3.0, layout.iso[0], iso_label_y, left_align=False))

    # --- Frame, title block, notes ------------------------------------------
    frame = _page_frame()
    title_lines = _title_block_lines()
    title_text = _title_block_text(
        part_name="SHAFT",
        drawing_no="GRM-02",
        scale="1:1",
        sheet="1/1",
        material="Brass (CuZn37 / C26800)",
        drawn_by="P. Fremantle",
        drawn_date=date.today().isoformat(),
    )
    notes_lines = _notes_block_lines()
    notes_text = _notes_block_text(
        [
            "NOTES:",
            "1. General tolerances per ISO 2768-mK",
            "2. Threads per ISO 6410; class 6H/6g unless noted",
            "3. Surface finish Ra 3.2 unless noted",
            "4. All dimensions in mm",
            "5. Material: Brass (CuZn37 / C26800 equivalent)",
            "6. Break all sharp edges 0.3 max",
        ]
    )
    frame_compound = Compound(children=[frame, title_lines, notes_lines])
    text_compound = Compound(children=[title_text, notes_text, *annotation_text])
    annotations_compound = Compound(children=annotation_lines)

    return parts_visible, parts_hidden, frame_compound, dim_shapes, text_compound, annotations_compound


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    params = PurflingCutterParams()
    parts_visible, parts_hidden, frame, dim_shapes, text, annotations = build_shaft_drawing(params)

    part_color = Color(0, 0, 0)
    hidden_color = Color(0.45, 0.45, 0.45)
    dim_color = Color(0, 0.25, 0.75)

    exporter = ExportSVG(margin=5)
    exporter.add_layer("frame", line_color=part_color, line_weight=0.35, line_type=LineType.CONTINUOUS)
    exporter.add_layer("part", line_color=part_color, line_weight=0.5, line_type=LineType.CONTINUOUS)
    exporter.add_layer(
        "hidden", line_color=hidden_color, line_weight=0.3, line_type=LineType.DASHED
    )
    exporter.add_layer(
        "dims",
        line_color=dim_color,
        fill_color=dim_color,
        line_weight=0.2,
        line_type=LineType.CONTINUOUS,
    )
    exporter.add_layer(
        "text",
        line_color=part_color,
        fill_color=part_color,
        line_weight=0.05,
        line_type=LineType.CONTINUOUS,
    )

    exporter.add_shape(frame, layer="frame")
    exporter.add_shape(parts_visible, layer="part")
    exporter.add_shape(parts_hidden, layer="hidden")
    exporter.add_shape(annotations, layer="part")
    for dim in dim_shapes:
        exporter.add_shape(dim, layer="dims")
    exporter.add_shape(text, layer="text")

    exporter.write("/tmp/shaft_drawing.svg")
    print("Exported /tmp/shaft_drawing.svg")

    try:
        import cairosvg  # type: ignore[import-untyped]

        cairosvg.svg2pdf(url="/tmp/shaft_drawing.svg", write_to="/tmp/shaft_drawing.pdf")
        print("Exported /tmp/shaft_drawing.pdf")
    except ImportError:
        print("cairosvg not installed — skipping PDF export.")


if __name__ == "__main__":
    main()
