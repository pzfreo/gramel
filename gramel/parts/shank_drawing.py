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

Geometry is built with process.prototype=False so threaded features are
plain reference cylinders at major (external) / tap-drill (internal)
diameter — the shop reads the thread spec off the drawing, not the
helical geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from build123d import (
    Color,
    Compound,
    DimensionLine,
    Draft,
    Edge,
    ExportSVG,
    ExtensionLine,
    LineType,
    Part,
    Text,
    Wire,
)

from gramel.parameters import PurflingCutterParams
from gramel.parts.shank import build_shank

# ---------------------------------------------------------------------------
# Page geometry — ISO 5457 A4 landscape
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

# Title block in the bottom-right corner.
TB_W = 100.0
TB_H = 50.0
TB_X_MAX = FX_MAX
TB_X_MIN = TB_X_MAX - TB_W
TB_Y_MIN = FY_MIN
TB_Y_MAX = TB_Y_MIN + TB_H

# Notes block above the title block, same width.
NB_X_MIN = TB_X_MIN
NB_X_MAX = TB_X_MAX
NB_Y_MIN = TB_Y_MAX + 2
NB_Y_MAX = NB_Y_MIN + 50


@dataclass
class ViewPlacement:
    """View centroids on the sheet (frame coords).

    Standard third-angle layout: bottom view is placed directly below the
    side view (same X centre) so the world-X (width) axis aligns vertically
    on the page across both views. Face view sits to the left of the side
    view with a wide gap to host its RHS dim and the bore callouts.
    """

    # Face view far left — limited only by the LHS length dim fitting inside
    # the frame (X ≥ -138.5 with distance=9 + label width ~5).
    face: tuple[float, float] = (-118.0, 0.0)
    # Side view 53 mm to the right of the face view — leaves a ~40 mm clear
    # gap for the face's RHS crossbore-Y dim + bore-callout leaders.
    side: tuple[float, float] = (-65.0, 0.0)
    # Bottom view directly below the side view (same X centre), aligned so
    # world-X (width) reads off the same vertical on the page.
    bottom: tuple[float, float] = (-65.0, -65.0)
    # Iso view in the upper-right area, clear of the orthographic views and
    # the notes/title column. Centred at Y=48 so its 92 mm height fits.
    iso: tuple[float, float] = (12.0, 48.0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _project(
    shape: Part,
    origin: tuple[float, float, float],
    up: tuple[float, float, float],
    look_at: tuple[float, float, float],
) -> tuple[Compound, Compound]:
    """Project and return (visible, hidden) edges as two Compounds, both at Z=0."""
    visible, hidden = shape.project_to_viewport(origin, up, look_at)
    return (
        Compound(children=list(visible)),
        Compound(children=list(hidden)),
    )


def _ext(p1: tuple[float, float], p2: tuple[float, float], offset: float, draft: Draft, label: str) -> ExtensionLine:
    return ExtensionLine(
        border=[(p1[0], p1[1], 0), (p2[0], p2[1], 0)],
        offset=offset,
        draft=draft,
        label=label,
    )


def _dim(p1: tuple[float, float], p2: tuple[float, float], draft: Draft, label: str) -> DimensionLine:
    return DimensionLine(path=[(p1[0], p1[1], 0), (p2[0], p2[1], 0)], draft=draft, label=label)


def _placed_text(text: str, size: float, x: float, y: float, left_align: bool = True) -> Compound:
    """Position text by its bounding-box left edge (or its centre if left_align=False)."""
    txt = Text(txt=text, font_size=size)
    bb = txt.bounding_box()
    dx = x - bb.min.X if left_align else x - (bb.min.X + bb.max.X) / 2
    dy = y - (bb.min.Y + bb.max.Y) / 2
    return txt.translate((dx, dy, 0))


def _line(x1: float, y1: float, x2: float, y2: float) -> Edge:
    return Edge.make_line((x1, y1, 0), (x2, y2, 0))


def _page_frame() -> Compound:
    """ISO 5457 A4 landscape frame + 4 centering marks (one per side midpoint)."""
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
    """Box and internal grid lines for the title block (rendered as thin
    strokes on the frame layer)."""
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
    """Filled text content for the title block (rendered with fill=black)."""
    label_size = 2.0
    value_size = 2.8
    title_size = 5.0

    mid_x = TB_X_MIN + 30
    txt_x_label = TB_X_MIN + 2
    txt_x_value = mid_x + 2

    title_y_centre = TB_Y_MIN + 45
    texts = [
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
    return Compound(children=texts)


def _notes_block_lines() -> Compound:
    """Notes block border (thin stroke on frame layer)."""
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
    """Notes block filled text content."""
    size = 2.4
    line_step = 4.5
    y_top = NB_Y_MAX - 4
    text_shapes = [
        _placed_text(line, size, NB_X_MIN + 2, y_top - i * line_step, left_align=True)
        for i, line in enumerate(notes)
    ]
    return Compound(children=text_shapes)


def _leader(
    feature_xy: tuple[float, float],
    direction: str,  # 'right' or 'left' — which way the leader exits
    elbow_offset: float,
    label_anchor_xy: tuple[float, float],
    label: str,
    label_size: float,
) -> tuple[Compound, Compound]:
    """A diameter-callout leader: line from the feature out to an elbow,
    then horizontal toward the label, stopping just before the label so
    the line does not strike through the text. Returns (lines, text).

    The label is left-aligned (when direction='right') or right-aligned
    (when direction='left') at `label_anchor_xy`, with a 1 mm gap between
    the leader endpoint and the first character.
    """
    fx, fy = feature_xy
    lx, ly = label_anchor_xy
    text_gap = 1.0
    if direction == "right":
        # Elbow goes right of the feature
        elbow_xy = (fx + elbow_offset, fy)
        # Line continues to just before label's left edge
        line_end = (lx - text_gap, ly)
        txt = _placed_text(label, label_size, lx, ly, left_align=True)
    elif direction == "left":
        elbow_xy = (fx - elbow_offset, fy)
        # Right-align the label so its right edge sits at lx; line stops 1mm right of that
        line_end = (lx + text_gap, ly)
        txt_obj = Text(txt=label, font_size=label_size)
        bb = txt_obj.bounding_box()
        # Right-align: shift so the right edge lands at lx
        dx = lx - bb.max.X
        dy = ly - (bb.min.Y + bb.max.Y) / 2
        txt = txt_obj.translate((dx, dy, 0))
    else:
        raise ValueError(f"direction must be 'right' or 'left', got {direction!r}")

    seg1 = _line(fx, fy, elbow_xy[0], elbow_xy[1])
    seg2 = _line(elbow_xy[0], elbow_xy[1], line_end[0], line_end[1])
    return Compound(children=[seg1, seg2]), Compound(children=[txt])


def _dim_outside(
    p1: tuple[float, float],
    p2: tuple[float, float],
    side: str,  # 'left', 'right', 'above', 'below'
    distance: float,
    draft: Draft,
    label: str,
) -> ExtensionLine:
    """Place a dim at `distance` mm on the given side of the line p1→p2,
    computing the correct offset sign from the side (no manual sign-juggling).

    For vertical borders use side='left' or 'right'; for horizontal borders
    use side='above' or 'below'.
    """
    is_vertical = abs(p1[0] - p2[0]) < 1e-6
    is_horizontal = abs(p1[1] - p2[1]) < 1e-6
    if is_vertical:
        going_up = p2[1] > p1[1]
        if side == "right":
            offset = +distance if going_up else -distance
        elif side == "left":
            offset = -distance if going_up else +distance
        else:
            raise ValueError(f"side {side!r} not valid for vertical border")
    elif is_horizontal:
        going_right = p2[0] > p1[0]
        if side == "below":
            offset = +distance if going_right else -distance
        elif side == "above":
            offset = -distance if going_right else +distance
        else:
            raise ValueError(f"side {side!r} not valid for horizontal border")
    else:
        raise ValueError("Only orthogonal borders (horizontal/vertical) are supported")
    return _ext(p1, p2, offset=offset, draft=draft, label=label)


# ---------------------------------------------------------------------------
# Main composer
# ---------------------------------------------------------------------------


def build_shank_drawing(
    params: PurflingCutterParams,
) -> tuple[Compound, Compound, Compound, list[ExtensionLine | DimensionLine], Compound, Compound]:
    """
    Compose the drawing.

    Returns (parts_visible, parts_hidden, frame, dims, text, annotations)
    where `frame` is all thin-stroke linework (page frame + title block
    grid + notes box) and `text` is all filled glyphs (title block text +
    notes text + view labels). Caller routes each to its own SVG layer.
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
    dl_thread_len = sp.depth_lock_threaded_length
    dl_depth = params.depth_lock_bore_depth
    slot_w = sp.relief_slot_width
    ds_thread = params.drive_screw.thread
    ds_pitch = params.drive_screw.thread_pitch
    dl_thread = params.depth_lock.thread

    centroid = (0, 0, length / 2)
    far = 1000.0

    # --- Project the four views ------------------------------------------
    face_v, face_h = _project(shank, (far, 0, length / 2), (0, 0, 1), centroid)
    side_v, side_h = _project(shank, (0, far, length / 2), (0, 0, 1), centroid)
    bottom_v, bottom_h = _project(shank, (0, 0, -far), (0, 1, 0), (0, 0, 0))
    iso_v, _iso_h = _project(shank, (far, far, far), (0, 0, 1), centroid)

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

    # --- Dimensions per view ---------------------------------------------
    draft = Draft(
        font_size=2.0,
        decimal_precision=1,
        arrow_length=1.0,
        line_width=0.1,
    )
    dims: list[ExtensionLine | DimensionLine] = []
    annotation_lines: list[Compound | Edge] = []  # routed to "part" layer (strokes, no fill)
    annotation_text: list[Compound] = []  # routed to "text" layer (fill=black, tiny stroke)

    def add_leader(**kwargs: object) -> None:
        lines_c, text_c = _leader(**kwargs)  # type: ignore[arg-type]
        annotation_lines.append(lines_c)
        annotation_text.append(text_c)

    # Dim placement uses side-aware _dim_outside() so the offset sign is
    # computed automatically from the side ("left", "right", "above",
    # "below"). The view bounding box is computed first; dims are placed
    # at progressive distances from the relevant edge so they don't pile up.

    # Working-face view: page X = world Y (depth), page Y = world Z (length).
    fx, fy = layout.face
    f_left = fx - depth / 2
    f_right = fx + depth / 2
    f_bot = fy - length / 2
    f_top = fy + length / 2
    dims.append(_dim_outside((f_left, f_bot), (f_left, f_top), side="left", distance=9, draft=draft, label=f"{length:.1f}"))
    dims.append(_dim_outside((f_left, f_bot), (f_right, f_bot), side="below", distance=6, draft=draft, label=f"{depth:.1f}"))
    cb_face_y = f_top - cb_x_from_top
    dims.append(_dim_outside((f_right, f_top), (f_right, cb_face_y), side="right", distance=8, draft=draft, label=f"{cb_x_from_top:.1f}"))
    dims.append(_dim_outside((fx - slot_w / 2, f_top), (fx + slot_w / 2, f_top), side="above", distance=10, draft=draft, label=f"{slot_w:.0f}"))

    # Bore callouts pointing RIGHT into the gap between face view and side view.
    sx_for_face = layout.side[0]
    s_left_for_face = sx_for_face - width / 2
    leader_label_x = (f_right + s_left_for_face) / 2
    tap_face_y = f_top - tap_x_from_top
    add_leader(
        feature_xy=(fx, cb_face_y),
        direction="right",
        elbow_offset=(leader_label_x - fx) * 0.5,
        label_anchor_xy=(leader_label_x, cb_face_y - 4),
        label=f"⌀{cb_d:.2f} H7",
        label_size=2.4,
    )
    add_leader(
        feature_xy=(fx, tap_face_y),
        direction="right",
        elbow_offset=(leader_label_x - fx) * 0.5,
        label_anchor_xy=(leader_label_x, tap_face_y + 3),
        label=f"{ds_thread}×{ds_pitch} thru",
        label_size=2.4,
    )

    # Side view: page X = world X (width), page Y = world Z (length).
    sx, sy = layout.side
    s_left = sx - width / 2
    s_right = sx + width / 2
    s_bot = sy - length / 2
    s_top = sy + length / 2
    dims.append(_dim_outside((s_left, s_bot), (s_right, s_bot), side="below", distance=6, draft=draft, label=f"{width:.1f}"))
    cb_side_y = s_top - cb_x_from_top
    tap_side_y = s_top - tap_x_from_top
    dims.append(_dim_outside((s_right, cb_side_y), (s_right, tap_side_y), side="right", distance=8, draft=draft, label=f"{inter_gap:.1f}"))
    s_thread_top = s_bot + dl_thread_len
    dims.append(_dim_outside((s_right, s_bot), (s_right, s_thread_top), side="right", distance=14, draft=draft, label=f"{dl_thread_len:.0f}"))
    dims.append(_dim_outside((s_right, s_thread_top), (s_right, cb_side_y), side="right", distance=20, draft=draft, label=f"{dl_depth - dl_thread_len:.0f}"))
    # Thread-end indicator line across the bore at s_thread_top.
    bore_half = dl_d / 2
    annotation_lines.append(_line(sx - bore_half, s_thread_top, sx + bore_half, s_thread_top))

    # Depth-lock thread + push-rod bore callouts — leaders pointing RIGHT.
    side_label_x = s_right + 28
    add_leader(
        feature_xy=(sx, (s_bot + s_thread_top) / 2),
        direction="right",
        elbow_offset=(s_right - sx) + 8,
        label_anchor_xy=(side_label_x, (s_bot + s_thread_top) / 2),
        label=f"{dl_thread}×1",
        label_size=2.4,
    )
    push_rod_mid_y = (s_thread_top + cb_side_y) / 2
    add_leader(
        feature_xy=(sx, push_rod_mid_y),
        direction="right",
        elbow_offset=(s_right - sx) + 8,
        label_anchor_xy=(side_label_x, push_rod_mid_y),
        label=f"⌀{dl_d:.1f} H8",
        label_size=2.4,
    )

    # Bottom view: width (page X, working-face direction) × depth (page Y).
    bx, by = layout.bottom
    b_left = bx - width / 2
    b_right = bx + width / 2
    b_bot = by - depth / 2
    b_top = by + depth / 2
    dims.append(_dim_outside((b_left, b_bot), (b_right, b_bot), side="below", distance=6, draft=draft, label=f"{width:.1f}"))
    dims.append(_dim_outside((b_right, b_bot), (b_right, b_top), side="right", distance=6, draft=draft, label=f"{depth:.1f}"))

    # Iso view label.
    iso_label_y = layout.iso[1] - 40
    annotation_text.append(_placed_text("ISO VIEW", 3.0, layout.iso[0], iso_label_y, left_align=False))

    # --- Frame, title block, notes ----------------------------------------
    frame = _page_frame()
    title_lines = _title_block_lines()
    title_text = _title_block_text(
        part_name="SHANK",
        drawing_no="GRM-01",
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
            "2. Threads per ISO 6410; class 6H unless noted",
            "3. Surface finish Ra 3.2 unless noted",
            "4. All dimensions in mm",
            "5. Material: Brass (CuZn37 / C26800 equivalent)",
            "6. Break all sharp edges 0.3 max",
        ]
    )
    frame_compound = Compound(children=[frame, title_lines, notes_lines])
    text_compound = Compound(children=[title_text, notes_text, *annotation_text])
    annotations_compound = Compound(children=annotation_lines)

    return parts_visible, parts_hidden, frame_compound, dims, text_compound, annotations_compound


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    params = PurflingCutterParams()
    parts_visible, parts_hidden, frame, dims, text, annotations = build_shank_drawing(params)

    part_color = Color(0, 0, 0)
    hidden_color = Color(0.45, 0.45, 0.45)
    dim_color = Color(0, 0.25, 0.75)

    exporter = ExportSVG(margin=5)
    # Frame layer: thin strokes only, no fill (so Wires render as lines, not blobs).
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
    # Text layer: fill=black so glyph faces render solid (readable),
    # tiny stroke weight so the outline doesn't bloat the characters.
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
    for dim in dims:
        exporter.add_shape(dim, layer="dims")
    exporter.add_shape(text, layer="text")

    exporter.write("/tmp/shank_drawing.svg")
    print("Exported /tmp/shank_drawing.svg")

    # Convert SVG → PDF (cairosvg handles vector to vector, no rasterisation).
    try:
        import cairosvg  # type: ignore[import-untyped]

        cairosvg.svg2pdf(url="/tmp/shank_drawing.svg", write_to="/tmp/shank_drawing.pdf")
        print("Exported /tmp/shank_drawing.pdf")
    except ImportError:
        print("cairosvg not installed — skipping PDF export. Run `uv add cairosvg` to enable.")


if __name__ == "__main__":
    main()
