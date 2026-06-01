"""Geometry-precise interference scan for the part drawings.

Decomposes each annotation into its label box + structural line segments and
flags real collisions that whole-bbox checks miss:

  - line↔label  : a dim/witness/leader line passing through another label
  - label↔label : two labels physically overlapping
  - part↔label  : a visible part edge crossing a label
  - label↔frame : a label extending outside the drawing frame

Pure 2-D analytic geometry (Liang–Barsky segment-vs-box), no OCCT booleans.

Run as a script to report, or call ``scan_all()`` from a test:

    uv run python tools/check_interference.py
"""
from __future__ import annotations

import importlib

import build123d_drafting as bdd
from build123d import Compound, GeomType

from gramel.parameters import PurflingCutterParams

DRAWING_MODULES = [
    "shaft_drawing", "shank_drawing", "blade_drawing", "blade_retainer_drawing",
    "depth_lock_bolt_drawing", "drive_plate_drawing",
    "thumbwheel_drive_screw_drawing", "assembly_drawing",
]

_MIN_LEN = 3.5  # mm — ignore glyph strokes / arrowhead edges below this
MIN_RUN = 1.5   # mm — minimum collinear overlap to call two lines redundant


def _label_box(result):
    box = getattr(result, "label_bbox", None)
    if box is None:
        text = getattr(result, "text", None)
        if text is not None and text.faces():
            bb = text.bounding_box()
            box = (bb.min.X, bb.min.Y, bb.max.X, bb.max.Y)
    return box


def _segments(shape, label_box=None):
    out = []
    if shape is None:
        return out
    for e in shape.edges():
        try:
            if e.geom_type != GeomType.LINE or e.length <= _MIN_LEN:
                continue
            a, b = e.position_at(0), e.position_at(1)
            if label_box is not None:
                mx, my = (a.X + b.X) / 2, (a.Y + b.Y) / 2
                if (label_box[0] - 0.3 <= mx <= label_box[2] + 0.3
                        and label_box[1] - 0.3 <= my <= label_box[3] + 0.3):
                    continue
            out.append(((a.X, a.Y), (b.X, b.Y)))
        except Exception:
            continue
    return out


def _seg_hits_box(p, q, box, pad=0.2):
    minx, miny, maxx, maxy = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    x0, y0 = p
    dx, dy = q[0] - x0, q[1] - y0
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, x0 - minx), (dx, maxx - x0), (-dy, y0 - miny), (dy, maxy - y0)):
        if abs(pp) < 1e-12:
            if qq < 0:
                return False
        else:
            r = qq / pp
            if pp < 0:
                if r > t1:
                    return False
                t0 = max(t0, r)
            else:
                if r < t0:
                    return False
                t1 = min(t1, r)
    return t0 <= t1


def _box_overlap(a, b, m=0.5):
    return (min(a[2], b[2]) - max(a[0], b[0]) > m
            and min(a[3], b[3]) - max(a[1], b[1]) > m)


def _box_inside(i, o):
    return i[0] >= o[0] and i[1] >= o[1] and i[2] <= o[2] and i[3] <= o[3]


def _collinear_overlap(a, b, tol=0.15):
    """Length (mm) over which segments a and b lie on the same line and overlap."""
    import math
    (ax0, ay0), (ax1, ay1) = a
    (bx0, by0), (bx1, by1) = b
    dax, day = ax1 - ax0, ay1 - ay0
    la = math.hypot(dax, day)
    if la < 1e-9:
        return 0.0
    ux, uy = dax / la, day / la
    if (abs((bx0 - ax0) * uy - (by0 - ay0) * ux) > tol
            or abs((bx1 - ax0) * uy - (by1 - ay0) * ux) > tol):
        return 0.0
    pb0 = (bx0 - ax0) * ux + (by0 - ay0) * uy
    pb1 = (bx1 - ax0) * ux + (by1 - ay0) * uy
    return max(0.0, min(la, max(pb0, pb1)) - max(0.0, min(pb0, pb1)))


def _as_compound(x):
    if isinstance(x, (list, tuple)):
        kids = [c for c in x if hasattr(c, "edges")]
        return Compound(children=kids) if kids else None
    return x if hasattr(x, "edges") else None


def scan_drawing(module_name, params=None):
    """Build one drawing and return ``(errors, warnings)`` message lists.

    Errors are real readability problems (label/line/part collisions, labels off
    the frame). Warnings are redundant collinear lines (e.g. chain dims sharing
    a witness line) — often legitimate, advisory only.
    """
    params = params or PurflingCutterParams()
    mod = importlib.import_module(f"gramel.parts.{module_name}")
    build_fn = next(getattr(mod, n) for n in dir(mod)
                    if n.startswith("build_") and n.endswith("_drawing"))

    captured = []
    orig_dim, orig_leader = mod.dim_linear, mod.leader

    def wrap_dim(*a, **k):
        r = orig_dim(*a, **k)
        captured.append(r)
        return r

    def wrap_leader(*a, **k):
        r = orig_leader(*a, **k)
        captured.append(r)
        return r

    mod.dim_linear, mod.leader = wrap_dim, wrap_leader
    try:
        ret = build_fn(params)
    finally:
        mod.dim_linear, mod.leader = orig_dim, orig_leader

    # Keep every annotation, even those with no label box (e.g. some dims) —
    # their structural lines still matter for the line-based checks.
    anns = []
    for r in captured:
        box = _label_box(r)
        src = getattr(r, "lines", None) or getattr(r, "shape", None)
        anns.append((getattr(r, "label_str", "?"), box, _segments(src, box)))

    parts_vis = _as_compound(ret[0]) if isinstance(ret, (list, tuple)) and ret else None
    frame = _as_compound(ret[2]) if isinstance(ret, (list, tuple)) and len(ret) > 2 else None
    part_segs = _segments(parts_vis)
    frame_box = None
    if frame is not None:
        try:
            bb = frame.bounding_box()
            frame_box = (bb.min.X, bb.min.Y, bb.max.X, bb.max.Y)
        except Exception:
            frame_box = None

    # ERRORS — real readability problems a drawing should not ship with.
    errors = []
    for i, (name_i, box_i, _segs_i) in enumerate(anns):
        if box_i is None:
            continue
        for name_j, box_j, _ in anns[i + 1:]:
            if box_j is not None and _box_overlap(box_i, box_j):
                errors.append(f'label↔label : "{name_i}" & "{name_j}" overlap')
        if any(_seg_hits_box(p, q, box_i) for (p, q) in part_segs):
            errors.append(f'part↔label  : a part edge crosses "{name_i}"')
        if frame_box is not None and not _box_inside(box_i, frame_box):
            errors.append(f'label↔frame : "{name_i}" extends outside the frame')
    for i, (name_i, _bi, segs_i) in enumerate(anns):
        for j, (name_j, box_j, _) in enumerate(anns):
            if i != j and box_j is not None and any(_seg_hits_box(p, q, box_j) for (p, q) in segs_i):
                errors.append(f'line↔label  : "{name_i}" line pierces "{name_j}" label')

    # WARNINGS — redundant collinear lines (e.g. chain dims that share a witness
    # line). Often legitimate; advisory so an author/LLM can reduce them.
    warnings = []
    for i in range(len(anns)):
        name_i, _, segs_i = anns[i]
        for j in range(i + 1, len(anns)):
            name_j, _, segs_j = anns[j]
            if any(_collinear_overlap(p, q) > MIN_RUN for p in segs_i for q in segs_j):
                warnings.append(f'line↔line   : "{name_i}" & "{name_j}" share a collinear line')
        if any(_collinear_overlap(p, q) > MIN_RUN for p in segs_i for q in part_segs):
            warnings.append(f'line↔part   : "{name_i}" runs along a part edge')
    return errors, warnings


def scan_all(params=None):
    """Return {module_name: (errors, warnings)} for every part drawing."""
    return {m: scan_drawing(m, params) for m in DRAWING_MODULES}


def main():
    n_err = n_warn = 0
    for module, (errors, warnings) in scan_all().items():
        n_err += len(errors)
        n_warn += len(warnings)
        print(f"\n### {module}: {len(errors)} error(s), {len(warnings)} warning(s)")
        for s in errors:
            print(f"  ERROR  {s}")
        for s in warnings:
            print(f"  warn   {s}")
    print(f"\n==== TOTAL: {n_err} error(s), {n_warn} warning(s) ====")
    return 1 if n_err else 0


if __name__ == "__main__":
    raise SystemExit(main())
