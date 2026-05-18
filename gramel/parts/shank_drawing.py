"""
A4 landscape technical drawing of the shank.

Layout: shank long axis (Z) is horizontal on every view, which fits A4
landscape cleanly. Four views composed onto one sheet:

  - Working-face view (camera at +X, looking at the +X face)
  - Side view         (camera at +Y, looking at the -Y face)
  - Bottom view       (camera at -Z, looking at the bottom face)
  - Isometric view    (camera in +Z +X +Y octant), scaled 1:2 to fit

Each orthogonal view shows both visible and hidden edges; centre lines
mark the bore axes. Dimension lines are drawn as thin dotted blue
(ISO_DOT line type) so they are clearly distinct from the part lines.

Export defaults to SVG (vector — prints clean at any size); pass the
result through a converter for PNG previews.
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
    LineType,
    PageSize,
    Part,
    TechnicalDrawing,
)

from gramel.parameters import PurflingCutterParams
from gramel.parts.shank import build_shank

# ---------------------------------------------------------------------------
# Layout — positions on the A4 landscape sheet (mm, origin at sheet centre)
# ---------------------------------------------------------------------------


@dataclass
class ViewPlacement:
    """
    View centroids on the sheet. A4 drawable area is roughly ±143×±100 mm.

    Views are arranged for a vertically-oriented shank (long axis along
    page Y). Each orthogonal view shows the shank standing up.
    """

    face: tuple[float, float] = (-110.0, 10.0)
    side: tuple[float, float] = (-65.0, 10.0)
    bottom: tuple[float, float] = (-10.0, 50.0)
    iso: tuple[float, float] = (70.0, 10.0)

    iso_scale: float = 0.5  # iso view rendered at half scale


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


# ---------------------------------------------------------------------------
# Main composer
# ---------------------------------------------------------------------------


def build_shank_drawing(
    params: PurflingCutterParams,
) -> tuple[Compound, Compound, Compound, list[ExtensionLine | DimensionLine]]:
    """
    Compose the drawing.

    Returns (parts_compound, hidden_compound, title_block, dimension_list)
    so the caller can route each to a different SVG layer.
    """
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

    centroid = (0, 0, length / 2)
    far = 1000.0

    # --- Project the four views ------------------------------------------
    # Each view places the shank's long axis (Z) vertical on the page.

    # Working-face view: camera at +X, looking at the +X face. up = +Z so shank stands vertical.
    face_v, face_h = _project(shank, (far, 0, length / 2), (0, 0, 1), centroid)

    # Side view: camera at +Y, perpendicular to the working face. up = +Z.
    side_v, side_h = _project(shank, (0, far, length / 2), (0, 0, 1), centroid)

    # Bottom view: camera at -Z, looking up at the bottom face. up = +Y.
    bottom_v, bottom_h = _project(shank, (0, 0, -far), (0, 1, 0), (0, 0, 0))

    # Iso view: camera in +X+Y+Z octant.
    iso_v, _iso_h = _project(shank, (far, far, far), (0, 0, 1), centroid)

    layout = ViewPlacement()

    def place(compound: Compound, pos: tuple[float, float]) -> Compound:
        return compound.translate((pos[0], pos[1], 0))

    parts_visible = Compound(
        children=[
            place(face_v, layout.face),
            place(side_v, layout.side),
            place(bottom_v, layout.bottom),
            place(iso_v.scale(layout.iso_scale), layout.iso),
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
    # All views show the shank vertically (long axis = page Y).
    # Working-face view: page X = world Y (depth across face), page Y = world Z (length up).
    # Side view: page X = world X (width through shank), page Y = world Z (length up).
    # Bottom view: page X = world Y (depth), page Y = world X (width).

    draft = Draft(
        font_size=1.8,
        decimal_precision=1,
        arrow_length=0.8,
        line_width=0.1,
    )
    dims: list[ExtensionLine | DimensionLine] = []

    # Working-face view: depth × length on the page.
    fx, fy = layout.face
    f_left = fx - depth / 2
    f_right = fx + depth / 2
    f_bot = fy - length / 2
    f_top = fy + length / 2
    # Overall length (vertical dim on the LHS).
    dims.append(_ext((f_left, f_bot), (f_left, f_top), offset=-9, draft=draft, label=f"{length:.1f}"))
    # Overall depth across the working face (horizontal dim at the bottom).
    dims.append(_ext((f_left, f_bot), (f_right, f_bot), offset=-5, draft=draft, label=f"{depth:.1f}"))
    # Crossbore position from top (vertical dim on the RHS).
    cb_face_y = f_top - cb_x_from_top
    dims.append(_ext((f_right, f_top), (f_right, cb_face_y), offset=7, draft=draft, label=f"{cb_x_from_top:.1f}"))
    # Crossbore diameter (horizontal dim through the visible circle).
    dims.append(
        _dim((fx - cb_d / 2, cb_face_y), (fx + cb_d / 2, cb_face_y), draft=draft, label=f"⌀{cb_d:.1f}")
    )
    # Tapped bore drill diameter — small horizontal dim above the crossbore.
    tap_face_y = f_top - tap_x_from_top
    dims.append(
        _dim((fx - tap_d / 2, tap_face_y), (fx + tap_d / 2, tap_face_y), draft=draft, label=f"⌀{tap_d:.1f} tap")
    )
    # Slot width (horizontal dim at the top of the view, above the bores).
    dims.append(_ext((fx - slot_w / 2, f_top), (fx + slot_w / 2, f_top), offset=14, draft=draft, label=f"{slot_w:.0f}"))

    # Side view: width × length on the page.
    sx, sy = layout.side
    s_left = sx - width / 2
    s_right = sx + width / 2
    s_bot = sy - length / 2
    s_top = sy + length / 2
    # Width (horizontal dim at the bottom).
    dims.append(_ext((s_left, s_bot), (s_right, s_bot), offset=-5, draft=draft, label=f"{width:.1f}"))
    # Inter-bore gap (vertical dim on the RHS between bore centres).
    cb_side_y = s_top - cb_x_from_top
    tap_side_y = s_top - tap_x_from_top
    dims.append(_ext((s_right, cb_side_y), (s_right, tap_side_y), offset=7, draft=draft, label=f"{inter_gap:.1f}"))

    # Bottom view: depth (page X) × width (page Y).
    bx, by = layout.bottom
    b_left = bx - depth / 2
    b_right = bx + depth / 2
    b_bot = by - width / 2
    b_top = by + width / 2
    # Depth (horizontal dim at the bottom).
    dims.append(_ext((b_left, b_bot), (b_right, b_bot), offset=-5, draft=draft, label=f"{depth:.1f}"))
    # Width (vertical dim on the RHS).
    dims.append(_ext((b_right, b_bot), (b_right, b_top), offset=5, draft=draft, label=f"{width:.1f}"))
    # Depth-lock bore diameter (centred).
    dims.append(_dim((bx - dl_d / 2, by), (bx + dl_d / 2, by), draft=draft, label=f"⌀{dl_d:.1f}"))

    # --- Title block ------------------------------------------------------

    iso_scale_str = f"iso 1:{round(1 / layout.iso_scale)}"
    title_block = TechnicalDrawing(
        designed_by="gramel",
        page_size=PageSize.A4,
        title="Shank",
        sub_title=f"1:1 · {iso_scale_str}",
        drawing_number="SHK-001",
        drawing_scale=1.0,
    )

    return parts_visible, parts_hidden, title_block, dims


# ---------------------------------------------------------------------------
# CLI — exports SVG with engineering line types per ExportSVG layers
# ---------------------------------------------------------------------------


def main() -> None:
    params = PurflingCutterParams()
    parts_visible, parts_hidden, title_block, dims = build_shank_drawing(params)

    part_color = Color(0, 0, 0)
    hidden_color = Color(0.3, 0.3, 0.3)
    dim_color = Color(0, 0.2, 0.7)

    exporter = ExportSVG(margin=5)
    exporter.add_layer("frame", line_color=part_color, line_weight=0.4, line_type=LineType.CONTINUOUS)
    exporter.add_layer("part", line_color=part_color, line_weight=0.5, line_type=LineType.CONTINUOUS)
    exporter.add_layer("hidden", line_color=hidden_color, line_weight=0.25, line_type=LineType.HIDDEN)
    exporter.add_layer(
        "dims",
        line_color=dim_color,
        fill_color=dim_color,  # clean dim ticks
        line_weight=0.18,
        line_type=LineType.ISO_DASH,  # distinct dashed dim lines (user's "dotted" intent)
    )

    exporter.add_shape(title_block, layer="frame")
    exporter.add_shape(parts_visible, layer="part")
    exporter.add_shape(parts_hidden, layer="hidden")
    for dim in dims:
        exporter.add_shape(dim, layer="dims")

    exporter.write("/tmp/shank_drawing.svg")
    print("Exported /tmp/shank_drawing.svg")


if __name__ == "__main__":
    main()
