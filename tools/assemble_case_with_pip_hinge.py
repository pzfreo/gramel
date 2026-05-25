"""Prototype: gramel case + pip-hinge piano hinge (alternative to Oral-B reference hinge).

Builds the case body without hinge, then fuses two pip-hinge piano hinges
(one near each CX end of the back edge) using build123d boolean union.
No trimesh round-trip required.

Does NOT modify the Oral-B variant — `tools/assemble_case_with_reference_hinge.py`
and `gramel/case/printable/case_print_in_place.stl` remain intact. This
script outputs to `dist/case/case_pip_hinge_print.stl`.

Layout (in print orientation):

  print Z↑                                knuckles (pivot)
                                              ●●
   case_top = 8 ───┬──────┬─── 6mm gap ───┬──────┬───
                   │\\    │  ←── hinge ──→│    /│
                   │ ╲   │                 │   ╱ │   ← 45° self-support ramps
                   │base╲│                 │/ lid│     (part of pip-hinge with
   bed = 0 ────────┴────·┴─────────────────┴·────┴───   self_support_ramp=True)
                   print Y →                ▲
                 ext_cy_max=29.4   axis=32.4     35.4

  Each hinge's cs-leaf (2mm thick at the top) fuses with the base's
  2mm-thick back wall at print Y ∈ [27.4, 29.4]. ps-leaf fuses with the
  lid's back wall at Y ∈ [35.4, 37.4]. Knuckles (Ø6) sit in the 6mm
  gap, sticking up to print Z ≈ 11.

  With self_support_ramp enabled, each leaf extends from the disc-bottom
  level (Z=5) all the way down to the bed (Z=0). The inner face of each
  leaf is a 45° ramp going from the outer-bottom corner of the case wall
  (Y=27.4 or Y=37.4, Z=0) up to the disc bottom apex (Y=32.4, Z=5).
  Both ramps converge at the disc bottom, forming a teepee that supports
  the disc from below — no print supports required.

  The 45° geometry is fully driven by case_z_extent (=8) and the back
  wall thickness (=2): pivot_outer/2 = Ro = (case_z_extent - wall_thickness)/2 = 3,
  hinge_width = W = Ro + wall_thickness = 5.
"""

from __future__ import annotations

import sys
from pathlib import Path

from build123d import Compound, Part, Pos, Rot, export_step, export_stl

from gramel.case import CaseParams, build_case
from gramel.case.case import _case_bounds
from gramel.parameters import PurflingCutterParams

sys.path.insert(0, str(Path(__file__).parent))
from pip_hinge import HingeParams, make_hinge_parts

PROJ = Path(__file__).parent.parent
OUT_DIR = PROJ / "dist" / "case"

# Hinge sizing. NOTE: pip-hinge requires hinge_thickness == pivot_outer/2
# (the cs cross-section loop only closes when these match). Don't decouple.
HINGE_HEIGHT = 25.0      # length along hinge axis (= along case CX)
HINGE_WIDTH = 5.0        # leaf depth — gives paddle width W-Ro = 2 mm = wall_thickness
HINGE_THICKNESS = 3.0    # = pivot_outer / 2 (required by pip-hinge geometry)
PIVOT_INNER = 3.0
PIVOT_OUTER = 6.0
PIVOT_CLEARANCE = 0.6
CLASP_CLEARANCE = 0.4

CLUSTER_END_MARGIN = 17.5   # = HINGE_HEIGHT/2 + 5 mm inset from case end


def build_and_assemble() -> None:
    cutter = PurflingCutterParams().model_copy(
        update={"process": PurflingCutterParams().process.model_copy(update={"prototype": False})}
    )
    case = CaseParams()
    body = build_case(cutter, case, include_hinge=False)
    base_b3d, lid_b3d = body.children
    bounds = _case_bounds(cutter, case)

    case_z_extent = -bounds["ext_cz_min"]              # = case half thickness
    ro = PIVOT_OUTER / 2                                # knuckle radius
    hinge_axis_cy = bounds["ext_cy_max"] + ro          # axis sits ro out from back wall

    print(f"case half thickness: {case_z_extent:.2f}")
    print(f"hinge axis at print Y = {hinge_axis_cy:.2f} (= ext_cy_max + Ro)")
    print(f"hinge axis at print Z = {case_z_extent:.2f} (= case top)")
    print(f"gap between halves in print Y: {ro * 2:.2f} mm (= pivot_outer)")

    # Rotate lid 180° about (CY=hinge_axis_cy, CZ=0) so it lands flat-open
    # next to the base, with a 6mm gap (pivot_outer wide) between them.
    lid_open = (
        Pos(0, hinge_axis_cy, 0)
        * Rot(180, 0, 0)
        * Pos(0, -hinge_axis_cy, 0)
        * lid_b3d
    )

    # Shift both halves so base bottom sits on the bed (print z=0).
    shift = case_z_extent
    base_print = Part() + (Pos(0, 0, shift) * base_b3d)
    lid_print = Part() + (Pos(0, 0, shift) * lid_open)

    print(f"\nbase bbox: {base_print.bounding_box()}")
    print(f"lid bbox:  {lid_print.bounding_box()}")

    # Cluster CX positions
    cx_min_centre = bounds["ext_cx_min"] + CLUSTER_END_MARGIN
    cx_max_centre = bounds["ext_cx_max"] - CLUSTER_END_MARGIN
    cluster_cx_centres = [cx_min_centre, cx_max_centre]
    print(f"\ncluster CX positions: {cluster_cx_centres}")

    # Build pip-hinge and fuse into each half at each cluster.
    # self_support_ramp=True extends each leaf from the disc bottom down to
    # the bed with a 45° inner ramp, making the assembly printable without
    # supports. Requires hinge_width == case half-height − pivot_outer/2
    # (=case_z_extent − Ro) so the ramp lands exactly at 45°.
    hinge_params = HingeParams(
        hinge_height=HINGE_HEIGHT,
        hinge_width=HINGE_WIDTH,
        hinge_thickness=HINGE_THICKNESS,
        pivot_inner=PIVOT_INNER,
        pivot_outer=PIVOT_OUTER,
        pivot_clearance=PIVOT_CLEARANCE,
        clasp_clearance=CLASP_CLEARANCE,
        self_support_ramp=True,
    )

    for cluster_cx in cluster_cx_centres:
        cs, ps = make_hinge_parts(hinge_params)

        # Pip-hinge local frame: axis along +Y, cs leaf at +X, ps leaf at -X,
        # leaves at Z ∈ [-T, 0], knuckle bulges to +Z.
        # Rot(0, 0, -90): local +Y → +X print, local +X → -Y print.
        cs_oriented = Rot(0, 0, -90) * cs
        ps_oriented = Rot(0, 0, -90) * ps

        cs_placed = Pos(cluster_cx, hinge_axis_cy, case_z_extent) * cs_oriented
        ps_placed = Pos(cluster_cx, hinge_axis_cy, case_z_extent) * ps_oriented

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
    # Export base and lid separately, load as meshes, rotate the lid in
    # trimesh space (cheap), and use manifold3d boolean intersection.
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
        # Boolean unions in OCP leave zero-volume degenerate triangle slivers
        # at the seams. Drop them — keep only the watertight body.
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
    axis_point = np.array([0.0, hinge_axis_cy, case_z_extent])
    axis_dir = np.array([1.0, 0.0, 0.0])  # hinge axis = print X

    for angle_deg in [180, 150, 120, 90, 60, 30, 0]:
        # angle_deg = opening angle: 180=flat-open, 0=closed.
        # Lid mesh is in print-flat (180°). To get to angle_deg we need to
        # rotate by +(180 - angle_deg) CCW about +X (this brings the lid
        # UP and OVER the base, the physical closing direction).
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
