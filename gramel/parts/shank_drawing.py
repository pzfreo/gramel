"""
A4 landscape technical drawing of the shank.

Four views composed onto one sheet:
  - Working-face view (looking at the +Y face)
  - Side view (looking along -Z, perpendicular to working face)
  - Bottom view (looking up the +X axis at the bottom of the shank)
  - Isometric view (camera off in the +X +Y +Z octant)

Each view is projected via build123d's project_to_viewport; the resulting
edges land on the Z=0 plane, centred on the look_at point. Views are then
translated to position on the sheet, and key dimensions are added.

Export defaults to SVG; pass `--dxf` for DXF (preferred for CAD interchange).
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import (
    Color,
    Compound,
    DimensionLine,
    Draft,
    ExportSVG,
    ExtensionLine,
    PageSize,
    TechnicalDrawing,
)

from gramel.parameters import PurflingCutterParams
from gramel.parts.shank import build_shank


# ---------------------------------------------------------------------------
# Layout — positions on the A4 landscape sheet (in mm, origin at sheet centre)
# ---------------------------------------------------------------------------


@dataclass
class ViewPlacement:
    """Where each view sits on the sheet (translation of view centroid in mm)."""

    face: tuple[float, float] = (-110.0, 5.0)
    side: tuple[float, float] = (-60.0, 5.0)
    bottom: tuple[float, float] = (-15.0, 40.0)
    iso: tuple[float, float] = (75.0, 5.0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _project(shape, origin, up, look_at) -> Compound:
    """Project shape from a viewport and return visible edges as a Compound."""
    visible, _hidden = shape.project_to_viewport(origin, up, look_at)
    return Compound(children=list(visible))


def _ext_line(p1: tuple[float, float], p2: tuple[float, float], offset: float, draft: Draft, label: str) -> ExtensionLine:
    """ExtensionLine wrapper that takes 2D (x, y) pairs and adds Z=0."""
    return ExtensionLine(
        border=[(p1[0], p1[1], 0), (p2[0], p2[1], 0)],
        offset=offset,
        draft=draft,
        label=label,
    )


def _dim_line(p1: tuple[float, float], p2: tuple[float, float], draft: Draft, label: str) -> DimensionLine:
    """DimensionLine wrapper that takes 2D points and adds Z=0."""
    return DimensionLine(path=[(p1[0], p1[1], 0), (p2[0], p2[1], 0)], draft=draft, label=label)


# ---------------------------------------------------------------------------
# Main composer
# ---------------------------------------------------------------------------


def build_shank_drawing(params: PurflingCutterParams) -> Compound:
    """Compose the A4 landscape tech drawing as one Compound."""
    shank = build_shank(params)
    sp = params.shank
    length, width, depth = sp.length, sp.width, sp.depth

    cb_d = params.crossbore_diameter
    tap_d = params.tapped_bore_drill_diameter
    cb_x_from_top = sp.crossbore_position_from_top
    tap_x_from_top = params.tapped_bore_position_from_top
    inter_gap = sp.crossbore_to_tapped_bore_gap
    dl_d = sp.depth_lock_bore_diameter
    slot_w = sp.relief_slot_width
    slot_d = sp.relief_slot_depth

    centroid = (length / 2, 0, depth / 2)
    far = 1000.0

    # --- Project the four views (all centred at origin on Z=0 plane) ------

    # Working-face view: camera at +Y, X up on page, world Z → page X (right).
    face = _project(shank, (length / 2, far, depth / 2), (1, 0, 0), centroid)

    # Side view: camera at +Z, X up on page, world Y → page -X.
    side = _project(shank, (length / 2, 0, far), (1, 0, 0), centroid)

    # Bottom view: camera at -X (looking up the +X axis). +Z up on page.
    bottom = _project(shank, (-far, 0, depth / 2), (0, 0, 1), (0, 0, depth / 2))

    # Iso view: camera in the +X +Y +Z octant, Z up.
    iso = _project(shank, (far, far, far), (0, 0, 1), centroid)

    layout = ViewPlacement()
    face_v = face.translate((layout.face[0], layout.face[1], 0))
    side_v = side.translate((layout.side[0], layout.side[1], 0))
    bottom_v = bottom.translate((layout.bottom[0], layout.bottom[1], 0))
    iso_v = iso.translate((layout.iso[0], layout.iso[1], 0))

    # --- Dimensions -------------------------------------------------------

    draft = Draft(font_size=2.2, decimal_precision=1, arrow_length=1.5, line_width=0.15)
    dims: list[ExtensionLine | DimensionLine] = []

    # Working-face view: in this view, page Y = world X (long axis), page X = world Z.
    # View is at (layout.face[0], layout.face[1]); world X=0 maps to page Y = layout.face[1] - length/2.
    fx, fy = layout.face
    face_left = fx - depth / 2  # page X at world Z=0
    face_right = fx + depth / 2  # page X at world Z=depth
    face_bottom = fy - length / 2  # page Y at world X=0
    face_top = fy + length / 2  # page Y at world X=length

    # Overall length (along page Y, dimensioned to the left)
    dims.append(_ext_line((face_left, face_bottom), (face_left, face_top), offset=-10, draft=draft, label=f"{length:.0f}"))
    # Overall Z (across the working face, dimensioned at the bottom)
    dims.append(_ext_line((face_left, face_bottom), (face_right, face_bottom), offset=-6, draft=draft, label=f"{depth:.0f}"))
    # Slot width (at the top, on the face view)
    slot_left = fx - slot_w / 2
    slot_right = fx + slot_w / 2
    dims.append(_ext_line((slot_left, face_top), (slot_right, face_top), offset=6, draft=draft, label=f"slot ⌀{slot_w:.1f}"))
    # Crossbore diameter (across the visible circle on the face view)
    cb_face_y = fy + (length - cb_x_from_top) - length / 2  # page Y of crossbore
    dims.append(_dim_line((fx - cb_d / 2, cb_face_y), (fx + cb_d / 2, cb_face_y), draft=draft, label=f"ø{cb_d:.1f}"))
    # Tapped bore drill diameter
    tap_face_y = fy + (length - tap_x_from_top) - length / 2
    dims.append(_dim_line((fx - tap_d / 2, tap_face_y), (fx + tap_d / 2, tap_face_y), draft=draft, label=f"ø{tap_d:.1f} tap"))

    # Side view: page Y = world X, page X = -world Y.
    sx, sy = layout.side
    side_left = sx - width / 2
    side_right = sx + width / 2
    side_bottom = sy - length / 2
    side_top = sy + length / 2

    # Crossbore X position from top (page-Y measurement, on the right of side view)
    cb_side_y = sy + (length - cb_x_from_top) - length / 2
    dims.append(_ext_line((side_right, side_top), (side_right, cb_side_y), offset=10, draft=draft, label=f"{cb_x_from_top:.0f}"))
    # Tapped bore X position from top (further out)
    tap_side_y = sy + (length - tap_x_from_top) - length / 2
    dims.append(_ext_line((side_right, side_top), (side_right, tap_side_y), offset=16, draft=draft, label=f"{tap_x_from_top:.0f}"))
    # Inter-bore gap (between the two bore axes)
    dims.append(_ext_line((side_right, tap_side_y), (side_right, cb_side_y), offset=22, draft=draft, label=f"{inter_gap:.0f}"))
    # Shank Y dimension (depth from front to back, dimensioned at the bottom)
    dims.append(_ext_line((side_left, side_bottom), (side_right, side_bottom), offset=-6, draft=draft, label=f"{width:.0f}"))

    # Bottom view: page Y = world Z (toward working face), page X = -world Y.
    bx, by = layout.bottom
    bot_left = bx - width / 2
    bot_right = bx + width / 2
    bot_bottom = by - depth / 2
    bot_top = by + depth / 2

    # Y dimension (across)
    dims.append(_ext_line((bot_left, bot_bottom), (bot_right, bot_bottom), offset=-5, draft=draft, label=f"{width:.0f}"))
    # Z dimension (toward working face, on the right)
    dims.append(_ext_line((bot_right, bot_bottom), (bot_right, bot_top), offset=5, draft=draft, label=f"{depth:.0f}"))
    # Depth-lock bore diameter (visible as a circle in bottom view, centred)
    dims.append(_dim_line((bx - dl_d / 2, by), (bx + dl_d / 2, by), draft=draft, label=f"ø{dl_d:.1f}"))

    # --- Title block ------------------------------------------------------

    title_block = TechnicalDrawing(
        designed_by="gramel",
        page_size=PageSize.A4,
        title="Purfling Cutter — Shank",
        sub_title="3-view + isometric, 1:1",
        drawing_number="SHK-001",
        drawing_scale=1.0,
    )

    return Compound(
        children=[
            title_block,
            face_v,
            side_v,
            bottom_v,
            iso_v,
            *dims,
        ]
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    params = PurflingCutterParams()
    drawing = build_shank_drawing(params)

    # SVG with two layers, clean line weights (per build123d://drafting cookbook §"Clean SVG").
    part_color = Color(0, 0, 0)
    dim_color = Color(0, 0.2, 0.7)

    exporter = ExportSVG(margin=5)
    exporter.add_layer("part", line_color=part_color, line_weight=0.4)
    exporter.add_layer(
        "dims",
        line_color=dim_color,
        fill_color=dim_color,  # filled witness ticks → clean line ends
        line_weight=0.1,
    )
    exporter.add_shape(drawing, layer="part")
    exporter.write("/tmp/shank_drawing.svg")
    print("Exported /tmp/shank_drawing.svg")


if __name__ == "__main__":
    main()
