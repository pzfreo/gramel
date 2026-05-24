"""
Case + tool assembly at any cutter extension / blade drop position.

The case is built in CASE FRAME (lying flat); the tool assembly is built in
TOOL FRAME (shank vertical). To combine them we rotate the tool into case
frame: tool_X → case_Y, tool_Y → case_Z, tool_Z → case_X.
"""

from typing import Literal

from build123d import Compound, Rot

from gramel.assembly import build_assembly
from gramel.case.case import build_case
from gramel.case.parameters import CaseParams
from gramel.parameters import PurflingCutterParams


def _tool_to_case_frame(tool: Compound) -> Compound:
    """Rotate a tool-frame Compound so its axes align with case frame.

    Achieves: tool_X → case_Y, tool_Y → case_Z, tool_Z → case_X.
    Empirically verified — Rot(0, 90, 90) is the build123d Rot incantation
    that produces this mapping with build123d's Bryant-angle convention.
    """
    rotated = Rot(0, 90, 90) * tool
    return rotated  # type: ignore[return-value]


def build_case_with_tool(
    cutter: PurflingCutterParams,
    case: CaseParams,
    shaft_x_offset: float = 0.0,
    blade_drop_below_retainers: float | None = None,
) -> Compound:
    """Build the case (closed) with the tool inside at the given position."""
    tool = build_assembly(
        cutter,
        shaft_x_offset=shaft_x_offset,
        blade_drop_below_retainers=blade_drop_below_retainers,
    )
    tool_in_case_frame = _tool_to_case_frame(tool)
    case_geom = build_case(cutter, case)
    return Compound(children=[case_geom, tool_in_case_frame])


Position = Literal["min_x_min_drop", "min_x_max_drop", "max_x_min_drop", "max_x_max_drop"]


def position_params(case: CaseParams, position: Position) -> tuple[float, float]:
    """Return (shaft_x_offset, blade_drop) for one of the four extreme positions."""
    travel = case.cutter_x_travel
    if position == "min_x_min_drop":
        return (-travel, case.blade_drop_min)
    if position == "min_x_max_drop":
        return (-travel, case.blade_drop_max)
    if position == "max_x_min_drop":
        return (+travel, case.blade_drop_min)
    if position == "max_x_max_drop":
        return (+travel, case.blade_drop_max)
    raise ValueError(f"Unknown position: {position}")


def check_4_positions(
    cutter: PurflingCutterParams, case: CaseParams
) -> dict[Position, dict[str, float]]:
    """Build case+tool at all four extreme positions and report interference."""
    results: dict[Position, dict[str, float]] = {}
    positions: list[Position] = [
        "min_x_min_drop",
        "min_x_max_drop",
        "max_x_min_drop",
        "max_x_max_drop",
    ]
    from build123d import Part

    case_geom = build_case(cutter, case)
    # Build a single Part containing both halves
    case_part = Part()
    for child in case_geom.children:
        case_part = case_part + child

    from functools import reduce
    from operator import add

    for pos in positions:
        sx, drop = position_params(case, pos)
        tool = build_assembly(
            cutter,
            shaft_x_offset=sx,
            blade_drop_below_retainers=drop,
        )
        tool_solid_tool_frame = reduce(add, tool.children)
        tool_solid = Rot(0, 90, 90) * tool_solid_tool_frame

        inter_vol = _check_intersection_volume(case_part, tool_solid)
        results[pos] = {
            "shaft_x_offset": sx,
            "blade_drop": drop,
            "tool_volume": tool_solid.volume,
            "case_volume": case_part.volume,
            "intersection_volume": inter_vol,
        }
    return results


def _check_intersection_volume(a, b) -> float:
    """Helper: return volume of a ∩ b, handling Part, ShapeList, and None."""
    from build123d import Part
    # Wrap in Part to ensure consistent shape type behaviour
    a_part = a if isinstance(a, Part) else Part() + a
    b_part = b if isinstance(b, Part) else Part() + b
    inter = a_part & b_part
    if inter is None:
        return 0.0
    if hasattr(inter, "volume"):
        return inter.volume
    return sum(s.volume for s in inter)


def check_open_closed_self_interference(
    cutter: PurflingCutterParams, case: CaseParams
) -> dict[str, float]:
    """Check the case for self-interference in both closed and open states.

    In CLOSED state: base and lid sit together at the split plane. Other than
    the hinge knuckles' designed interlock (where teardrops fit into cavities),
    base and lid should not occupy the same space. Some interlock IS expected
    (the teardrops sit inside the matching cavities — that's by design).

    In OPEN state: lid rotated 180° about the hinge axis. Base and lid should
    have NO overlap — the case can't actually open if they do.
    """
    from gramel.case.case import _case_bounds
    from build123d import Pos, Rot

    case_geom = build_case(cutter, case)
    base, lid = case_geom.children

    bounds = _case_bounds(cutter, case)
    teardrop_r = case.hinge_pin_round_diameter
    hinge_cy_axis = bounds["ext_cy_max"] + teardrop_r - case.hinge_axis_offset
    hinge_cz_axis = 0.0

    lid_open = Pos(0, hinge_cy_axis, hinge_cz_axis) * Rot(180, 0, 0) * Pos(0, -hinge_cy_axis, -hinge_cz_axis) * lid

    closed_inter = _check_intersection_volume(base, lid)
    open_inter = _check_intersection_volume(base, lid_open)

    return {
        "closed_self_interference": closed_inter,
        "open_self_interference": open_inter,
    }


__all__ = [
    "build_case_with_tool",
    "check_4_positions",
    "check_open_closed_self_interference",
    "position_params",
]
