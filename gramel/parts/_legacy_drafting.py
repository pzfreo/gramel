"""Compatibility helpers for the original hand-authored drawing set.

Draftwright 0.4.15 requires build123d-drafting-helpers 0.14.2, which removed
the old functional ``dim_linear`` and ``leader`` API.  The baseline Gramel
drawings intentionally retain that API and its established page geometry.
These two small adapters preserve the 0.1.2 behaviour while the installed
package supplies Draftwright's current object-oriented API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from build123d import (
    Align,
    Arrow,
    Compound,
    Draft,
    Edge,
    ExtensionLine,
    Location,
    Mode,
    Text,
    Vector,
)
from build123d.operations_generic import sweep


@dataclass(frozen=True)
class DimResult:
    shape: Compound


@dataclass(frozen=True)
class LeaderResult:
    lines: Compound
    text: Compound


_SIDE_VECTORS: dict[str, tuple[float, float, float]] = {
    "above": (0.0, 1.0, 0.0),
    "below": (0.0, -1.0, 0.0),
    "left": (-1.0, 0.0, 0.0),
    "right": (1.0, 0.0, 0.0),
}


def _offset_sign(
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    toward: tuple[float, float, float],
) -> int:
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    right = Vector(dy, -dx, 0.0)
    if right.length < 1e-10:
        return 1
    return 1 if right.normalized().dot(Vector(*toward).normalized()) >= 0 else -1


def dim_linear(
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    side: Literal["above", "below", "left", "right"] | tuple[float, float, float],
    distance: float,
    draft: Draft,
    label: str | None = None,
    tolerance: float | tuple[float, float] | None = None,
) -> DimResult:
    """Build a legacy linear dimension with a named placement side."""
    toward = _SIDE_VECTORS[side] if isinstance(side, str) else side
    offset = _offset_sign(p1, p2, toward) * abs(distance)
    shape = ExtensionLine(
        border=[p1, p2],
        offset=offset,
        draft=draft,
        label=label,
        tolerance=tolerance,
        mode=Mode.PRIVATE,
    )
    return DimResult(shape=shape)


def leader(
    tip: tuple[float, float, float],
    elbow: tuple[float, float, float],
    label: str,
    draft: Draft,
) -> LeaderResult:
    """Build a legacy arrow, shelf and filled-text leader annotation."""
    tip_v = Vector(tip[0], tip[1], 0.0)
    elbow_v = Vector(elbow[0], elbow[1], 0.0)
    gap = draft.pad_around_text
    shelf_direction = 1.0 if elbow_v.X >= tip_v.X else -1.0
    shelf_end = Vector(elbow_v.X + shelf_direction * gap, elbow_v.Y, 0.0)

    shaft = Edge.make_line(tip_v, elbow_v)
    arrow = Arrow(
        arrow_size=draft.arrow_length,
        shaft_path=shaft,
        shaft_width=draft.line_width,
        head_at_start=True,
        mode=Mode.PRIVATE,
    )
    shelf_edge = Edge.make_line(elbow_v, shelf_end)
    shelf_pen = shelf_edge.perpendicular_line(draft.line_width, 0)
    shelf = sweep(shelf_pen, shelf_edge, mode=Mode.PRIVATE)

    if shelf_direction > 0:
        text_align = (Align.MIN, Align.CENTER)
        text_x = elbow_v.X + gap
    else:
        text_align = (Align.MAX, Align.CENTER)
        text_x = elbow_v.X - gap
    glyphs = Text(
        txt=label,
        font_size=draft.font_size,
        font=draft.font,
        align=text_align,
        mode=Mode.PRIVATE,
    ).moved(Location(Vector(text_x, elbow_v.Y, 0.0)))

    return LeaderResult(
        lines=Compound(children=[arrow, shelf]),
        text=Compound(children=[glyphs]),
    )
