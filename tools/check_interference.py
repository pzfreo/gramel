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


def _as_compound(x):
    if isinstance(x, (list, tuple)):
        kids = [c for c in x if hasattr(c, "edges")]
        return Compound(children=kids) if kids else None
    return x if hasattr(x, "edges") else None


def scan_drawing(module_name, params=None):
    """Build one drawing and return a list of interference message strings."""
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

    anns = []
    for r in captured:
        box = _label_box(r)
        if box is None:
            continue
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

    issues = []
    for i, (name_i, box_i, segs_i) in enumerate(anns):
        for name_j, box_j, _ in anns[i + 1:]:
            if _box_overlap(box_i, box_j):
                issues.append(f'label↔label : "{name_i}" & "{name_j}" overlap')
        for j, (name_j, box_j, _) in enumerate(anns):
            if i != j and any(_seg_hits_box(p, q, box_j) for (p, q) in segs_i):
                issues.append(f'line↔label  : "{name_i}" line pierces "{name_j}" label')
        if any(_seg_hits_box(p, q, box_i) for (p, q) in part_segs):
            issues.append(f'part↔label  : a part edge crosses "{name_i}"')
        if frame_box is not None and not _box_inside(box_i, frame_box):
            issues.append(f'label↔frame : "{name_i}" extends outside the frame')
    return issues


def scan_all(params=None):
    """Return {module_name: [issue, ...]} for every part drawing."""
    return {m: scan_drawing(m, params) for m in DRAWING_MODULES}


def main():
    total = 0
    for module, issues in scan_all().items():
        total += len(issues)
        print(f"\n### {module}: {len(issues)} issue(s)")
        for s in issues:
            print(f"     {s}")
    print(f"\n==== TOTAL: {total} interference issue(s) ====")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
