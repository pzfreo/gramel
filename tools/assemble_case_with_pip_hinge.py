"""Build the default print-in-place case using the pip-hinge piano hinge.

Builds the case body without hinge, then fuses two pip-hinge piano hinges
(one near each CX end of the back edge) using build123d boolean union.
No trimesh round-trip required.

This is the *default* shipped case
(`gramil/case/printable/case_print_in_place.stl`). The Oral-B reference
variant lives at `case_print_in_place_oralb.stl`, built by
`tools/assemble_case_with_reference_hinge.py`. This script outputs to
`dist/case/case_pip_hinge_print.stl` for iteration; copy to the
`printable/` location to ship.

Uses the upstream pip-hinge four-input API with `Knuckle.SMALL`:

  - case_h        = 8 mm   (case half thickness)
  - hinge_length  = 25 mm  (along the hinge axis, = along case CX)
  - stations      = 6      (default; clasp_width = 25/6 ≈ 4.17 mm)
  - knuckle       = SMALL  (Po = max(case_h/2, 5 mm) = 5 mm)

Layout (in print orientation):

  print Z↑                       knuckles Ø5 (small)
                                       ●●
   case_top = 8 ───┬──────┬─ 6 mm gap ─┬──────┬───
                   │\\    │            │    /│
                   │ ╲   │ ramp ramp │   ╱ │   ← ~22° self-supporting ramps
                   │base╲│            │/ lid│     (Knuckle.SMALL → steep ramp)
   bed = 0 ────────┴────·┴────────────┴·────┴───
                   print Y →
                 ext_cy_max=29.4   axis=32.4     35.4

  cs-leaf fuses with the base's 2mm back wall; ps-leaf fuses with the
  lid's back wall after the lid's 180° flat-open rotation. Knuckles
  (Ø5) sit centred in the 6mm gap.
"""

from __future__ import annotations

import sys
from pathlib import Path

from build123d import Compound, Part, Pos, Rot, export_step, export_stl

from gramil.case import CaseParams, build_case
from gramil.case.case import _case_bounds
from gramil.parameters import PurflingCutterParams

sys.path.insert(0, str(Path(__file__).parent))
from pip_hinge import HingeParams, Knuckle, make_hinge

PROJ = Path(__file__).parent.parent
OUT_DIR = PROJ / "dist" / "case"

# Four pip-hinge inputs (everything else derived inside HingeParams).
HINGE_LENGTH = 50.0 / 3          # 2/3 of the previous 25 mm = ~16.67 mm each
STATIONS = 4                     # clasp_width = 16.67/4 ≈ 4.17 mm (same as before)
KNUCKLE = Knuckle.SMALL          # Po = max(case_h/2, 5 mm) = 5 mm at case_h=8

CLUSTER_END_MARGIN = HINGE_LENGTH / 2 + 5  # keep 5 mm inset from each case end


def _split_hinge_by_side(hinge):
    """Sort the hinge's solids into cs-side (+X bias) and ps-side (-X bias).

    With small mounting_flat the cs and ps bodies fragment into the disc
    tabs; each fragment still fuses cleanly into its case wall, but we
    have to classify by bbox X-centre instead of unpacking solids().
    """
    cs, ps = [], []
    for s in hinge.solids():
        bb = s.bounding_box()
        (cs if (bb.min.X + bb.max.X) >= 0 else ps).append(s)
    return Compound(cs), Compound(ps)


def build_and_assemble() -> None:
    cutter = PurflingCutterParams().model_copy(
        update={"process": PurflingCutterParams().process.model_copy(update={"prototype": False})}
    )
    case = CaseParams()
    body = build_case(cutter, case, include_hinge=False)
    base_b3d, lid_b3d = body.children
    bounds = _case_bounds(cutter, case)

    case_h = -bounds["ext_cz_min"]                     # case half thickness = pip-hinge case_h

    # Build the hinge once to derive its W (leaf outer X = Ro + mounting_flat)
    # — used to position the axis just outside the case back wall so the
    # leaf's outer face lands on the wall's inner face.
    hinge_params = HingeParams(
        case_h=case_h,
        hinge_length=HINGE_LENGTH,
        stations=STATIONS,
        knuckle=KNUCKLE,
    )
    resolved = hinge_params._resolve()
    W = resolved["W"]
    Po = resolved["Po"]

    hinge_axis_cy = bounds["ext_cy_max"] + W           # leaf outer face sits on wall inner face
    pz_off = hinge_params.pivot_z_offset               # 0.2 mm by default

    print(f"case_h: {case_h:.2f}")
    print(f"knuckle: {KNUCKLE.name} (Po={Po:.2f} mm, leaf W={W:.2f} mm)")
    print(f"hinge axis at print Y = {hinge_axis_cy:.2f}, Z = {case_h + pz_off:.2f}")
    print(f"gap between halves in print Y: {2 * W:.2f} mm")
    print(f"closed seam Z gap: {2 * pz_off:.2f} mm (= 2 × pivot_z_offset)")

    # Lift the (closed-orientation) lid by 2·pz_off so when rotated about
    # the lifted axis it lands flat on the bed. The 2·pz_off gap shows
    # up at the closed lid-to-base seam — intentional, prevents a high
    # spot on the seam from springing the front of the case open.
    lid_lifted = Pos(0, 0, 2 * pz_off) * lid_b3d

    # Rotate the (lifted) lid 180° about the actual hinge axis at
    # (Y=hinge_axis_cy, Z=pz_off) so it lands flat-open next to the base.
    lid_open = (
        Pos(0, hinge_axis_cy, pz_off)
        * Rot(180, 0, 0)
        * Pos(0, -hinge_axis_cy, -pz_off)
        * lid_lifted
    )

    # Shift both halves so base bottom sits on the bed (print z=0).
    base_print = Part() + (Pos(0, 0, case_h) * base_b3d)
    lid_print = Part() + (Pos(0, 0, case_h) * lid_open)

    print(f"\nbase bbox: {base_print.bounding_box()}")
    print(f"lid bbox:  {lid_print.bounding_box()}")

    # Two clusters along the back edge
    cx_min_centre = bounds["ext_cx_min"] + CLUSTER_END_MARGIN
    cx_max_centre = bounds["ext_cx_max"] - CLUSTER_END_MARGIN
    cluster_cx_centres = [cx_min_centre, cx_max_centre]
    print(f"\ncluster CX positions: {cluster_cx_centres}")

    for cluster_cx in cluster_cx_centres:
        cs, ps = _split_hinge_by_side(make_hinge(hinge_params))

        # Pip-hinge local frame: axis along Y, cs leaf at +X, ps leaf at -X,
        # leaves at Z ∈ [-case_h, 0], knuckle above to +Z.
        # Rot(0, 0, -90): local +Y → print +X (hinge axis along X);
        #                 local +X → print -Y (cs leaf into the base half).
        cs_oriented = Rot(0, 0, -90) * cs
        ps_oriented = Rot(0, 0, -90) * ps

        cs_placed = Pos(cluster_cx, hinge_axis_cy, case_h) * cs_oriented
        ps_placed = Pos(cluster_cx, hinge_axis_cy, case_h) * ps_oriented

        base_print = base_print + cs_placed
        lid_print = lid_print + ps_placed

    combined = Compound(children=[base_print, lid_print])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_stl = OUT_DIR / "case_pip_hinge_print.stl"
    out_step = OUT_DIR / "case_pip_hinge_print.step"
    export_stl(combined, str(out_stl))
    export_step(combined, str(out_step))
    print(f"\nbase final vol: {base_print.volume:.1f}")
    print(f"lid final vol:  {lid_print.volume:.1f}")
    print(f"combined bbox: {combined.bounding_box()}")
    print(f"\nExported {out_stl}")
    print(f"Exported {out_step}")

    # ── Interference check across closing motion (via trimesh, fast) ──
    print("\n=== Interference at multiple opening angles ===")
    print("(rotation about hinge axis in print frame, 180°=flat-open, 0°=closed)")

    import numpy as np
    import trimesh

    base_stl = OUT_DIR / "_pip_base_with_hinges.stl"
    lid_stl = OUT_DIR / "_pip_lid_with_hinges.stl"
    export_stl(base_print, str(base_stl))
    export_stl(lid_print, str(lid_stl))

    def _load_clean(path):
        m = trimesh.load(str(path), force="mesh")
        m.merge_vertices()
        m.process()
        comps = [c for c in m.split(only_watertight=False) if c.is_watertight and c.volume > 1.0]
        if not comps:
            return m
        return max(comps, key=lambda c: c.volume)

    base_mesh = _load_clean(base_stl)
    lid_mesh = _load_clean(lid_stl)
    print(f"  base watertight={base_mesh.is_watertight} vol={base_mesh.volume:.1f}")
    print(f"  lid  watertight={lid_mesh.is_watertight} vol={lid_mesh.volume:.1f}")

    print(f"\n{'angle':>6}  {'inter. vol (mm³)':>20}  {'verdict':<12}")
    print("-" * 50)
    axis_point = np.array([0.0, hinge_axis_cy, case_h + pz_off])
    axis_dir = np.array([1.0, 0.0, 0.0])

    for angle_deg in [180, 150, 120, 90, 60, 30, 0]:
        rot_deg = 180 - angle_deg
        if rot_deg == 0:
            rotated = lid_mesh
        else:
            R = trimesh.transformations.rotation_matrix(
                np.radians(rot_deg), axis_dir, axis_point
            )
            rotated = lid_mesh.copy()
            rotated.apply_transform(R)
        try:
            inter = base_mesh.intersection(rotated)
            vol = float(inter.volume) if inter is not None and len(inter.vertices) else 0.0
        except Exception as e:
            print(f"  {angle_deg:>4}°  ERROR: {e}")
            continue
        verdict = "OK" if vol < 1.0 else "INTERFERES"
        print(f"  {angle_deg:>4}°  {vol:>20.3f}  {verdict:<12}")


if __name__ == "__main__":
    build_and_assemble()
