"""
A4 landscape assembly drawing of the purfling cutter.

Three views (side, front, iso) of the full assembled tool, plus a
Bill of Materials in place of the notes block.

The assembly is built via ``gramel.assembly.build_assembly`` so the
mating positions match the live model. Forced to CNC representation
(clean cylinders + thread callouts in the drawings) — the FDM-prototype
helical threads are not rendered here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from build123d import Compound, Draft, Part, Shape, Wire
from build123d_drafting import dim_linear, leader  # type: ignore[import-untyped]

from gramel.assembly import build_assembly
from gramel.parameters import PurflingCutterParams
from gramel.parts._drawing import (
    FX_MAX,
    NB_X_MAX,
    NB_X_MIN,
    NB_Y_MAX,
    NB_Y_MIN,
    export_drawing,
    line_segment,
    page_frame,
    placed_text,
    project_view,
    title_block_lines,
    title_block_text,
)


@dataclass
class ViewPlacement:
    """View centroids on the sheet (frame coords). Drawn at 1:1.

    The assembly is 54 × 11 × 95 mm. Layout:
      - Side view (main) at left, showing the long axis (Z up, X across)
      - Front view (working-face) to its right — narrow profile
      - Iso view bottom-left
    """

    # Orthographics in the upper-left, all at 1:1. The exploded iso (also
    # at 1:1, 2D bbox ~118×138) sits in the lower portion and right
    # portion of the left column. The iso's upper-left corner is sparsely
    # occupied so we tolerate a little nominal overlap with the side view.
    side: tuple[float, float] = (-95.0, 20.0)
    front: tuple[float, float] = (-57.0, 20.0)
    iso: tuple[float, float] = (5.0, -10.0)


# ---------------------------------------------------------------------------
# Bill of Materials
# ---------------------------------------------------------------------------

# (item #, description, ref, qty)
BOM: tuple[tuple[str, str, str, str], ...] = (
    ("1", "Shank", "GRM-01", "1"),
    ("2", "Shaft", "GRM-02", "1"),
    ("3", "Thumbwheel + drive screw", "GRM-03", "1"),
    ("4", "Drive plate", "GRM-04", "1"),
    ("5", "Depth-lock bolt + knob", "GRM-05", "1"),
    ("6", "Push rod, ⌀4.5 × 45", "—", "1"),
    ("7", "Captive screw, M2 × 6", "stock", "1"),
    ("8", "Mount screw, M2", "stock", "1"),
    ("9", "Grub screw, M4", "stock", "1"),
    ("10", "Blade", "[TBM]", "2"),
    ("11", "Blade retainer", "(custom)", "4"),
    ("12", "Spacer", "[TBM]", "0–1"),
)


def bom_block_lines() -> Compound:
    """Border + horizontal rules + column dividers for the BOM block."""
    box = Wire.make_polygon(
        [
            (NB_X_MIN, NB_Y_MIN, 0),
            (NB_X_MAX, NB_Y_MIN, 0),
            (NB_X_MAX, NB_Y_MAX, 0),
            (NB_X_MIN, NB_Y_MAX, 0),
        ],
        close=True,
    )
    # Header row at the top — 4 mm tall.
    header_y = NB_Y_MAX - 4
    header_line = line_segment(NB_X_MIN, header_y, NB_X_MAX, header_y)
    # Column dividers: item # | description | ref | qty
    x_item = NB_X_MIN + 8
    x_desc = NB_X_MIN + 60
    x_ref = NB_X_MIN + 84
    v_lines = [
        line_segment(x_item, NB_Y_MIN, x_item, NB_Y_MAX),
        line_segment(x_desc, NB_Y_MIN, x_desc, NB_Y_MAX),
        line_segment(x_ref, NB_Y_MIN, x_ref, NB_Y_MAX),
    ]
    return Compound(children=[box, header_line, *v_lines])


def bom_block_text() -> Compound:
    """Header + each BOM row as placed text inside the BOM block."""
    label_size = 1.8
    row_size = 2.0
    x_item = NB_X_MIN + 8
    x_desc = NB_X_MIN + 60
    x_ref = NB_X_MIN + 84

    header_y = NB_Y_MAX - 2.5
    children: list[Shape[object]] = [
        placed_text("#", label_size, (NB_X_MIN + x_item) / 2, header_y, left_align=False),
        placed_text("DESCRIPTION", label_size, (x_item + x_desc) / 2, header_y, left_align=False),
        placed_text("REF.", label_size, (x_desc + x_ref) / 2, header_y, left_align=False),
        placed_text("QTY", label_size, (x_ref + NB_X_MAX) / 2, header_y, left_align=False),
    ]
    row_step = 3.6
    row_y_top = NB_Y_MAX - 4 - 2.2
    for i, (num, desc, ref, qty) in enumerate(BOM):
        y = row_y_top - i * row_step
        children.extend(
            [
                placed_text(num, row_size, (NB_X_MIN + x_item) / 2, y, left_align=False),
                placed_text(desc, row_size, x_item + 2, y, left_align=True),
                placed_text(ref, row_size, (x_desc + x_ref) / 2, y, left_align=False),
                placed_text(qty, row_size, (x_ref + NB_X_MAX) / 2, y, left_align=False),
            ]
        )
    return Compound(children=children)


def build_assembly_drawing(
    params: PurflingCutterParams,
) -> tuple[Compound, Compound, Compound, list[Shape[object]], Compound, Compound]:
    """Compose the full-assembly drawing.

    Returns (parts_visible, parts_hidden, frame, dim_shapes, text, annotations).
    """
    params = params.model_copy(update={"process": params.process.model_copy(update={"prototype": False})})

    # Both Compound and Part have project_to_viewport; pass them directly.
    assembly = build_assembly(params)
    bb = assembly.bounding_box()

    # Separate "exploded" version for the iso view — each part translated
    # outward along its natural disassembly direction.
    exploded = build_assembly(params, explode=1.0)
    centroid = (
        (bb.min.X + bb.max.X) / 2,
        (bb.min.Y + bb.max.Y) / 2,
        (bb.min.Z + bb.max.Z) / 2,
    )

    far = 1000.0

    # --- Project the views --------------------------------------------------
    # Side view: camera at -Y, up=+Z → world X = page X (+1), world Z = page Y (+1).
    side_v, side_h = project_view(assembly, (centroid[0], -far, centroid[2]), (0, 0, 1), centroid)
    # Front view: camera at +X (looking at working face), up=+Z →
    # world Y = page -X, world Z = page Y.
    front_v, front_h = project_view(assembly, (far, centroid[1], centroid[2]), (0, 0, 1), centroid)
    # Iso view of the EXPLODED assembly from the +X+Y+Z octant. Use a
    # centroid based on the exploded shape so the view sits roughly centred.
    ebb = exploded.bounding_box()
    exploded_centroid = (
        (ebb.min.X + ebb.max.X) / 2,
        (ebb.min.Y + ebb.max.Y) / 2,
        (ebb.min.Z + ebb.max.Z) / 2,
    )
    iso_v, _iso_h = project_view(
        exploded, (far, far, far), (0, 0, 1), exploded_centroid
    )

    layout = ViewPlacement()

    def place(compound: Compound, pos: tuple[float, float]) -> Compound:
        return compound.translate((pos[0], pos[1], 0))

    # Everything at 1:1.
    parts_visible = Compound(
        children=[
            place(side_v, layout.side),
            place(front_v, layout.front),
            place(iso_v, layout.iso),
        ]
    )
    parts_hidden = Compound(
        children=[
            place(side_h, layout.side),
            place(front_h, layout.front),
        ]
    )

    # --- Overall dimensions on the side view -------------------------------
    draft = Draft(font_size=2.0, decimal_precision=1, arrow_length=1.0, line_width=0.1)

    dim_shapes: list[Shape[object]] = []
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

    # Side view: world X → page X, world Z → page Y at 1:1.
    sx, sy = layout.side
    side_left = sx + (bb.min.X - centroid[0])
    side_right = sx + (bb.max.X - centroid[0])
    side_top = sy + (bb.max.Z - centroid[2])
    side_bot = sy + (bb.min.Z - centroid[2])

    add_dim((side_left, side_top), (side_right, side_top), "above", 5, f"{bb.size.X:.0f}")
    add_dim((side_left, side_bot), (side_left, side_top), "left", 5, f"{bb.size.Z:.0f}")

    # Front view: overall width (Y) along the bottom
    fx, fy = layout.front
    front_left = fx + (bb.min.Y - centroid[1])
    front_right = fx + (bb.max.Y - centroid[1])
    front_bot = fy + (bb.min.Z - centroid[2])
    add_dim((front_left, front_bot), (front_right, front_bot), "below", 5, f"{bb.size.Y:.0f}")

    # --- View labels --------------------------------------------------------
    annotation_text.append(placed_text("SIDE VIEW", 3.0, layout.side[0], side_bot - 8, left_align=False))
    annotation_text.append(placed_text("FRONT", 3.0, layout.front[0], front_bot - 8, left_align=False))
    annotation_text.append(placed_text("EXPLODED VIEW", 3.0, layout.iso[0], layout.iso[1] - 75, left_align=False))

    # --- Frame, title block, BOM (in place of notes block) ------------------
    frame = page_frame()
    title_lines = title_block_lines()
    title_text = title_block_text(
        part_name="ASSEMBLY",
        drawing_no="GRM-00",
        scale="1:1",
        sheet="1/1",
        material="See BOM",
        drawn_by="P. Fremantle",
        drawn_date=date.today().isoformat(),
    )
    bom_lines = bom_block_lines()
    bom_text = bom_block_text()
    frame_compound = Compound(children=[frame, title_lines, bom_lines])
    text_compound = Compound(children=[title_text, bom_text, *annotation_text])
    annotations_compound = Compound(children=[])

    return parts_visible, parts_hidden, frame_compound, dim_shapes, text_compound, annotations_compound


def main() -> None:
    params = PurflingCutterParams()
    parts_visible, parts_hidden, frame, dim_shapes, text, annotations = build_assembly_drawing(params)
    export_drawing(
        svg_path="/tmp/assembly_drawing.svg",
        pdf_path="/tmp/assembly_drawing.pdf",
        parts_visible=parts_visible,
        parts_hidden=parts_hidden,
        frame=frame,
        dim_shapes=dim_shapes,
        text=text,
        annotations=annotations,
    )


if __name__ == "__main__":
    main()
