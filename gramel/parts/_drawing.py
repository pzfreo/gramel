"""
Shared infrastructure for A4 landscape CNC-handoff drawings.

Each part drawing (`shank_drawing.py`, `shaft_drawing.py`, …) owns its
view layout and dim/leader calls. The pieces that repeat — page frame
+ centering marks, title block, notes block, SVG layer setup, PDF
conversion — live here.

Drawing standard: ISO 5457 frame, ISO 7200 title block, ISO 128 line
types, ISO 2768-mK general tolerances, ISO 6410 simplified threads.
"""

from __future__ import annotations

from build123d import (
    Color,
    Compound,
    Edge,
    ExportDXF,
    ExportSVG,
    LineType,
    Part,
    Shape,
    Text,
    Unit,
    Wire,
)
from build123d.exporters import ColorIndex


def dim_label(value: float, *, min_decimals: int = 0, max_decimals: int = 3) -> str:
    """Format a numeric parameter value into a dimension label without
    losing precision.

    Use this *everywhere* a parameter value is embedded in a dim or
    leader label string. Fixed-precision formats like ``f"{x:.0f}"`` or
    ``f"{x:.1f}"`` will silently round e.g. 4.75 → "5" or 4.75 → "4.8"
    when the parameter changes — the label drifts from the model and
    the shop manufactures the wrong part. This helper always shows the
    full value up to ``max_decimals`` significant decimals, stripping
    trailing zeros down to ``min_decimals``:

        dim_label(35.0)               → "35"
        dim_label(6.4)                → "6.4"
        dim_label(4.75)               → "4.75"
        dim_label(0.85)               → "0.85"
        dim_label(3.0, min_decimals=1) → "3.0"   (forced one decimal)
        dim_label(3.5, min_decimals=1) → "3.5"   (precision unaffected)
        dim_label(3.55, min_decimals=1) → "3.55" (precision NOT lost)

    ``min_decimals=1`` exists for the rare build123d dim_linear bug
    where the rendered label width vs the dim path length triggers
    ``ValueError: Can't get geom adaptor of empty wire`` — forcing
    one decimal place can move the label across the threshold. Use
    sparingly; ``min_decimals=0`` is the default and right for almost
    every label.

    The regression test in ``tests/test_drawing_labels.py`` enforces
    that no drawing file uses raw fixed-precision formats for dim
    labels — change this helper or its callers if precision needs
    explicit rounding.
    """
    rounded = round(value, max_decimals)
    s = f"{rounded:.{max_decimals}f}"
    if "." in s:
        while s.endswith("0") and len(s.split(".")[1]) > min_decimals:
            s = s[:-1]
        if s.endswith("."):
            s = s[:-1]
    return s or "0"

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

# Notes block directly above the title block, same width.
NB_X_MIN = TB_X_MIN
NB_X_MAX = TB_X_MAX
NB_Y_MIN = TB_Y_MAX + 2
NB_Y_MAX = NB_Y_MIN + 50


# ---------------------------------------------------------------------------
# Standard notes-block content
# ---------------------------------------------------------------------------

STANDARD_NOTES: tuple[str, ...] = (
    "NOTES:",
    "1. General tolerances per ISO 2768-mK",
    "2. Threads per ISO 6410; class 6H/6g unless noted",
    "3. Surface finish Ra 3.2 unless noted",
    "4. All dimensions in mm",
    "5. Break all sharp edges 0.3 max",
    "6. Threads: cut & gauge with standard taps/dies",
)
# Material is per-part — it lives in each drawing's title block, not here
# (parts span brass, copper and steel).


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def project_view(
    shape: Part,
    origin: tuple[float, float, float],
    up: tuple[float, float, float],
    look_at: tuple[float, float, float],
) -> tuple[Compound, Compound]:
    """Project a 3D shape and return (visible, hidden) edges at Z=0."""
    visible, hidden = shape.project_to_viewport(origin, up, look_at)
    return (
        Compound(children=list(visible)),
        Compound(children=list(hidden)),
    )


def placed_text(
    text: str, size: float, x: float, y: float, left_align: bool = True
) -> Compound:
    """Position text by its bounding-box left edge (or its centre if `left_align=False`)."""
    txt = Text(txt=text, font_size=size)
    bb = txt.bounding_box()
    dx = x - bb.min.X if left_align else x - (bb.min.X + bb.max.X) / 2
    dy = y - (bb.min.Y + bb.max.Y) / 2
    return txt.translate((dx, dy, 0))


def line_segment(x1: float, y1: float, x2: float, y2: float) -> Edge:
    """Single Edge segment between two 2D points (Z=0)."""
    return Edge.make_line((x1, y1, 0), (x2, y2, 0))


# ---------------------------------------------------------------------------
# Frame, title block, notes block
# ---------------------------------------------------------------------------


def page_frame() -> Compound:
    """ISO 5457 A4 landscape frame + 4 centering marks (one per side midpoint)."""
    border = Wire.make_polygon(
        [(FX_MIN, FY_MIN, 0), (FX_MAX, FY_MIN, 0), (FX_MAX, FY_MAX, 0), (FX_MIN, FY_MAX, 0)],
        close=True,
    )
    tick = 3.0
    ticks = [
        line_segment(0, FY_MIN, 0, FY_MIN - tick),
        line_segment(0, FY_MAX, 0, FY_MAX + tick),
        line_segment(FX_MIN, 0, FX_MIN - tick, 0),
        line_segment(FX_MAX, 0, FX_MAX + tick, 0),
    ]
    return Compound(children=[border, *ticks])


def title_block_lines() -> Compound:
    """Box + internal grid lines for the title block (thin strokes, no fill)."""
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
        line_segment(TB_X_MIN, TB_Y_MIN + i * 10, TB_X_MAX, TB_Y_MIN + i * 10)
        for i in (1, 2, 3, 4)
    ]
    mid_x = TB_X_MIN + 30
    v_line = line_segment(mid_x, TB_Y_MIN, mid_x, TB_Y_MIN + 40)
    return Compound(children=[box, *h_lines, v_line])


def title_block_text(
    *,
    part_name: str,
    drawing_no: str,
    scale: str,
    sheet: str,
    material: str,
    drawn_by: str,
    drawn_date: str,
) -> Compound:
    """Filled glyph content for the title block (route to fill=black layer)."""
    label_size = 2.0
    value_size = 2.8
    title_size = 5.0
    mid_x = TB_X_MIN + 30
    txt_x_label = TB_X_MIN + 2
    txt_x_value = mid_x + 2
    title_y_centre = TB_Y_MIN + 45
    return Compound(
        children=[
            placed_text(part_name, title_size, (TB_X_MIN + TB_X_MAX) / 2, title_y_centre, left_align=False),
            placed_text("DRAWING NO.", label_size, txt_x_label, TB_Y_MIN + 35),
            placed_text(drawing_no, value_size, txt_x_value, TB_Y_MIN + 35),
            placed_text("SCALE", label_size, txt_x_label, TB_Y_MIN + 25),
            placed_text(f"{scale}   SHEET {sheet}", value_size, txt_x_value, TB_Y_MIN + 25),
            placed_text("MATERIAL", label_size, txt_x_label, TB_Y_MIN + 15),
            placed_text(material, value_size, txt_x_value, TB_Y_MIN + 15),
            placed_text("DRAWN", label_size, txt_x_label, TB_Y_MIN + 5),
            placed_text(f"{drawn_by}   {drawn_date}", value_size, txt_x_value, TB_Y_MIN + 5),
        ]
    )


def notes_block_lines() -> Compound:
    """Box border for the notes block (thin stroke, no fill)."""
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


def notes_block_text(notes: list[str] | tuple[str, ...] = STANDARD_NOTES) -> Compound:
    """Filled glyph content for the notes block."""
    size = 2.4
    line_step = 4.5
    y_top = NB_Y_MAX - 4
    return Compound(
        children=[
            placed_text(line, size, NB_X_MIN + 2, y_top - i * line_step, left_align=True)
            for i, line in enumerate(notes)
        ]
    )


# ---------------------------------------------------------------------------
# Export pipeline — standard SVG layer setup + cairosvg PDF conversion
# ---------------------------------------------------------------------------


def export_drawing(
    *,
    svg_path: str,
    parts_visible: Compound,
    parts_hidden: Compound,
    frame: Compound,
    dim_shapes: list[Shape[object]],
    text: Compound,
    annotations: Compound,
    pdf_path: str | None = None,
) -> None:
    """Write the standard 5-layer SVG (and optionally a PDF via cairosvg).

    Layers:
      - frame:  thin strokes, no fill (page border, title/notes box, grid lines)
      - part:   stroked outlines (projected geometry + manually-drawn annotations)
      - hidden: dashed thin strokes (hidden edges)
      - dims:   blue strokes + blue fill (dim lines, arrows, dim labels)
      - text:   black fill (title block text, notes text, leader labels, view labels)
    """
    part_color = Color(0, 0, 0)
    hidden_color = Color(0.45, 0.45, 0.45)
    dim_color = Color(0, 0.25, 0.75)

    exporter = ExportSVG(margin=5)
    exporter.add_layer("frame", line_color=part_color, line_weight=0.35, line_type=LineType.CONTINUOUS)
    exporter.add_layer("part", line_color=part_color, line_weight=0.5, line_type=LineType.CONTINUOUS)
    exporter.add_layer("hidden", line_color=hidden_color, line_weight=0.3, line_type=LineType.DASHED)
    exporter.add_layer(
        "dims", line_color=dim_color, fill_color=dim_color, line_weight=0.2, line_type=LineType.CONTINUOUS
    )
    exporter.add_layer(
        "text", line_color=part_color, fill_color=part_color, line_weight=0.05, line_type=LineType.CONTINUOUS
    )

    exporter.add_shape(frame, layer="frame")
    exporter.add_shape(parts_visible, layer="part")
    exporter.add_shape(parts_hidden, layer="hidden")
    if annotations.children:
        exporter.add_shape(annotations, layer="part")
    for dim in dim_shapes:
        exporter.add_shape(dim, layer="dims")
    exporter.add_shape(text, layer="text")

    exporter.write(svg_path)
    print(f"Exported {svg_path}")

    if pdf_path is None:
        return
    try:
        import cairosvg  # type: ignore[import-untyped]

        cairosvg.svg2pdf(url=svg_path, write_to=pdf_path)
        print(f"Exported {pdf_path}")
    except ImportError:
        print(f"cairosvg not installed — skipping PDF export to {pdf_path}.")


def export_dxf_drawing(
    *,
    dxf_path: str,
    parts_visible: Compound,
    parts_hidden: Compound,
    frame: Compound,
    dim_shapes: list[Shape[object]],
    text: Compound,
    annotations: Compound,
) -> None:
    """Write a DXF mirror of the drawing for shops that prefer DXF over PDF.

    Layers map 1:1 to the SVG layers; colours use the AutoCAD ColorIndex
    palette since DXF doesn't carry RGB the way SVG does.
    """
    exporter = ExportDXF(unit=Unit.MM)
    exporter.add_layer("frame", color=ColorIndex.BLACK, line_weight=0.35, line_type=LineType.CONTINUOUS)
    exporter.add_layer("part", color=ColorIndex.BLACK, line_weight=0.5, line_type=LineType.CONTINUOUS)
    exporter.add_layer("hidden", color=ColorIndex.GRAY, line_weight=0.3, line_type=LineType.DASHED)
    exporter.add_layer("dims", color=ColorIndex.BLUE, line_weight=0.2, line_type=LineType.CONTINUOUS)
    exporter.add_layer("text", color=ColorIndex.BLACK, line_weight=0.05, line_type=LineType.CONTINUOUS)

    exporter.add_shape(frame, layer="frame")
    exporter.add_shape(parts_visible, layer="part")
    exporter.add_shape(parts_hidden, layer="hidden")
    if annotations.children:
        exporter.add_shape(annotations, layer="part")
    for dim in dim_shapes:
        exporter.add_shape(dim, layer="dims")
    exporter.add_shape(text, layer="text")

    exporter.write(dxf_path)
    print(f"Exported {dxf_path}")
