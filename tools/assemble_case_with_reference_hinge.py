"""Final case assembly: parametric case body + reference hinge (via trimesh).

THE MERGE HAPPENS IN PRINT (OPEN-FLAT) ORIENTATION.

Hinge handling (no scaling):
  - Reference hinge is used at native size.
  - Bottom is cropped at ref z=2 (cropped slab sits on the bed) so that
    the TOP of the full-width side plate ends up flush with the case top.
  - The narrow tab region (ref z=2..3.5, ≈0.8 mm thick) is kept on
    purpose: it acts as an anti-sag bridge under the first widening of
    the plate so the whole hinge prints supportless.
  - Above the case top, the teardrop body + apex protrude as the
    pivot pin (correct print-in-place geometry — pivot is above the
    mating-face level, which is what makes a clamshell pivot cleanly).

Reference hinge structure (z-slab analysis of the STL):
  z = 0    – 2    : tab tip (X ≈ 0.8, narrow Y) – cropped away
  z = 2    – 3.5  : tab (X ≈ 0.8, Y widening 9 → 15) – anti-sag bridge
  z = 3.5  – 6.5  : side plate ramping (X 0.9 → 3.81, full Y)
  z = 6.5  – 9.75 : full-width side plate (X = 3.81)         ← merges with case wall
  z = 10   – 12.5 : round teardrop body + apex               ← protrudes above case top

With case half thickness = 8 mm and crop at ref z=2, drop by 2:
  print z = 0..6   : tab + ramp (anchors in lower case wall)
  print z = 6..8   : full side plate (merges with upper case wall)
  print z = 8..10.5: teardrop + apex (pivot above case top)

Pipeline:
  1. Build case body without hinge in build123d (closed orientation)
  2. Rotate LID 180° about the hinge axis to put it next to BASE in
     PRINT orientation, both halves flat on the bed
  3. Export base + (rotated) lid as STLs, load with trimesh
  4. Crop reference hinges at ref z=REF_HINGE_CROP_Z, translate down by
     the same amount
  5. Position at cluster CX positions, with hinge axis at the gap between
     the case halves (print Y = ext_cy_max + HINGE_WIDTH/2)
  6. Boolean union: case_lid ∪ lid_hinges, case_base ∪ base_hinges
  7. Export final printable STLs
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh

from build123d import Pos, Rot, export_stl

from gramel.parameters import PurflingCutterParams
from gramel.case import CaseParams, build_case
from gramel.case.case import _case_bounds


PROJ = Path(__file__).parent.parent
HINGE_STL_DIR = PROJ / "gramel" / "case" / "hinge_stls"
OUT_DIR = PROJ / "dist" / "case"

# Reference-hinge frame constants (from STL inspection):
REF_HINGE_WIDTH = 7.62              # ref X full span (split direction)
REF_HINGE_LEN = 15.05               # ref Y full span (along hinge axis)
# Crop level chosen so the TOP of the full-width side plate (ref z ≈ 10)
# lands flush with the case top (print z = case_z_extent = 8). With drop
# = REF_HINGE_CROP_Z, this puts ref z=10 at print z = 10 − 2 = 8. The
# kept slice (ref z=2..3.5) is the anti-sag tab that lets the hinge
# print supportless; cropping above z=3.5 would remove that bridge.
REF_HINGE_CROP_Z = 2.0
REF_SIDE_PLATE_TOP_Z = 10.0         # top of full-width side plate in ref frame


def _crop_below(mesh: trimesh.Trimesh, z_plane: float) -> trimesh.Trimesh:
    """Crop mesh keeping only material with z >= z_plane, capped flat.

    Uses boolean intersection with a generous box above z_plane (manifold3d).
    """
    b = mesh.bounds
    pad = 10.0
    xmin, xmax = b[0][0] - pad, b[1][0] + pad
    ymin, ymax = b[0][1] - pad, b[1][1] + pad
    zmax = b[1][2] + pad
    extents = [xmax - xmin, ymax - ymin, zmax - z_plane]
    keep_box = trimesh.creation.box(extents=extents)
    centre = [(xmin + xmax) / 2, (ymin + ymax) / 2, (z_plane + zmax) / 2]
    keep_box.apply_translation(centre)
    out = mesh.intersection(keep_box)
    out.merge_vertices()
    out.process()
    return out


def build_and_assemble():
    print("=== Build hinge-less case body in build123d ===")
    cutter = PurflingCutterParams().model_copy(
        update={"process": PurflingCutterParams().process.model_copy(update={"prototype": False})}
    )
    case = CaseParams()
    body = build_case(cutter, case, include_hinge=False)
    base_b3d, lid_b3d = body.children
    bounds = _case_bounds(cutter, case)

    case_z_extent = -bounds["ext_cz_min"]  # case half thickness (~8 mm)
    print(f"  case half thickness: {case_z_extent:.2f} mm")
    print(f"  side-plate top will sit at print z = {REF_SIDE_PLATE_TOP_Z - REF_HINGE_CROP_Z:.2f} mm")
    print(f"  case top is at        print z = {case_z_extent:.2f} mm")

    # Hinge axis sits OUTSIDE the case body in the gap between halves
    hinge_cy_axis = bounds["ext_cy_max"] + REF_HINGE_WIDTH / 2

    # --- Move to PRINT orientation ----------------------------------------
    shift = -bounds["ext_cz_min"]
    base_print = Pos(0, 0, shift) * base_b3d
    lid_open = (
        Pos(0, hinge_cy_axis, 0)
        * Rot(180, 0, 0)
        * Pos(0, -hinge_cy_axis, 0)
        * lid_b3d
    )
    lid_print = Pos(0, 0, shift) * lid_open

    print(f"  base bbox in print: {base_print.bounding_box()}")
    print(f"  lid bbox in print:  {lid_print.bounding_box()}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base_stl = OUT_DIR / "_case_base_nohinge_print.stl"
    lid_stl = OUT_DIR / "_case_lid_nohinge_print.stl"
    export_stl(base_print, str(base_stl))
    export_stl(lid_print, str(lid_stl))

    print("\n=== Load meshes ===")
    base_mesh = trimesh.load(str(base_stl), force="mesh")
    lid_mesh = trimesh.load(str(lid_stl), force="mesh")
    for m in (base_mesh, lid_mesh):
        m.merge_vertices()
        m.process()
    print(f"  base in print: vol={base_mesh.volume:.1f}  watertight={base_mesh.is_watertight}")
    print(f"  lid in print:  vol={lid_mesh.volume:.1f}  watertight={lid_mesh.is_watertight}")

    ref_lid_hinge = trimesh.load(str(HINGE_STL_DIR / "reference_hinge_lid.stl"))
    ref_base_hinge = trimesh.load(str(HINGE_STL_DIR / "reference_hinge_base.stl"))
    print(f"  ref LID  hinge (native): vol={ref_lid_hinge.volume:.1f}  bbox={ref_lid_hinge.bounds}")
    print(f"  ref BASE hinge (native): vol={ref_base_hinge.volume:.1f}  bbox={ref_base_hinge.bounds}")

    # --- Crop bottom tabs at ref z=3.5 ------------------------------------
    print(f"\n=== Crop hinge bottom tabs at ref z={REF_HINGE_CROP_Z} ===")
    ref_lid_hinge = _crop_below(ref_lid_hinge, REF_HINGE_CROP_Z)
    ref_base_hinge = _crop_below(ref_base_hinge, REF_HINGE_CROP_Z)
    print(f"  cropped LID  vol={ref_lid_hinge.volume:.1f}  bbox Z[{ref_lid_hinge.bounds[0][2]:.2f},{ref_lid_hinge.bounds[1][2]:.2f}]  watertight={ref_lid_hinge.is_watertight}")
    print(f"  cropped BASE vol={ref_base_hinge.volume:.1f}  bbox Z[{ref_base_hinge.bounds[0][2]:.2f},{ref_base_hinge.bounds[1][2]:.2f}]  watertight={ref_base_hinge.is_watertight}")

    # --- Translate down so cropped bottom sits on the bed -----------------
    drop_z = np.eye(4)
    drop_z[2, 3] = -REF_HINGE_CROP_Z
    ref_lid_hinge.apply_transform(drop_z)
    ref_base_hinge.apply_transform(drop_z)
    print(f"  after drop, LID  Z[{ref_lid_hinge.bounds[0][2]:.2f},{ref_lid_hinge.bounds[1][2]:.2f}]")
    print(f"  after drop, BASE Z[{ref_base_hinge.bounds[0][2]:.2f},{ref_base_hinge.bounds[1][2]:.2f}]")

    # --- Rotate ref → print axes ------------------------------------------
    # ref Y (hinge axis) → print X
    # ref X (split direction; LID at ref X<0, BASE at ref X>0) → print -Y
    # ref Z → print Z
    R = np.array(
        [
            [0, 1, 0, 0],
            [-1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ],
        dtype=float,
    )

    # 2 clusters at the CX ends of the case back edge
    cx_min_centre = bounds["ext_cx_min"] + 12.0
    cx_max_centre = bounds["ext_cx_max"] - 12.0
    cluster_cx_centres = [cx_min_centre, cx_max_centre]

    print("\n=== Position hinge halves ===")
    print(f"  cluster CX positions: {cluster_cx_centres}")
    print(f"  hinge axis at print Y = {hinge_cy_axis:.2f}")
    print(f"  hinge gap: print Y {bounds['ext_cy_max']:.2f} to {bounds['ext_cy_max'] + REF_HINGE_WIDTH:.2f}")

    lid_hinges: list[trimesh.Trimesh] = []
    base_hinges: list[trimesh.Trimesh] = []
    for cluster_cx in cluster_cx_centres:
        # After R: ref(rx, ry, rz) → print(ry, -rx, rz)
        # ref Y midpoint (REF_HINGE_LEN/2) should map to print X = cluster_cx
        # ref X = 0 should map to print Y = hinge_cy_axis
        # ref Z = 0 should map to print Z = 0 (already there after crop+drop)
        # After R: print_X = ry, print_Y = -rx. So we need translation:
        #   print_X = ry - REF_HINGE_LEN/2 + cluster_cx  → tx = cluster_cx - REF_HINGE_LEN/2
        #   print_Y = -rx + hinge_cy_axis              → ty = hinge_cy_axis
        tx = cluster_cx - REF_HINGE_LEN / 2
        ty = hinge_cy_axis
        tz = 0.0

        T = R.copy()
        T[0, 3] = tx
        T[1, 3] = ty
        T[2, 3] = tz

        # LID half (ref X < 0) → print Y > hinge_cy_axis (LID side of gap) ✓
        lid_copy = ref_lid_hinge.copy()
        lid_copy.apply_transform(T)
        lid_hinges.append(lid_copy)

        # BASE half (ref X > 0) → print Y < hinge_cy_axis (BASE side) ✓
        base_copy = ref_base_hinge.copy()
        base_copy.apply_transform(T)
        base_hinges.append(base_copy)

    for i, h in enumerate(lid_hinges):
        b = h.bounds
        print(f"  lid hinge #{i}:  X[{b[0][0]:6.2f},{b[1][0]:6.2f}]  Y[{b[0][1]:6.2f},{b[1][1]:6.2f}]  Z[{b[0][2]:5.2f},{b[1][2]:5.2f}]")
    for i, h in enumerate(base_hinges):
        b = h.bounds
        print(f"  base hinge #{i}: X[{b[0][0]:6.2f},{b[1][0]:6.2f}]  Y[{b[0][1]:6.2f},{b[1][1]:6.2f}]  Z[{b[0][2]:5.2f},{b[1][2]:5.2f}]")

    print("\n=== Boolean union ===")
    for hinge in lid_hinges:
        lid_mesh = lid_mesh.union(hinge)
    for hinge in base_hinges:
        base_mesh = base_mesh.union(hinge)
    print(f"  final LID:  vol={lid_mesh.volume:.1f}  watertight={lid_mesh.is_watertight}")
    print(f"  final BASE: vol={base_mesh.volume:.1f}  watertight={base_mesh.is_watertight}")

    print("\n=== Export final STLs (PRINT orientation, ready to slice) ===")
    lid_out = OUT_DIR / "case_final_lid_print.stl"
    base_out = OUT_DIR / "case_final_base_print.stl"
    combined_out = OUT_DIR / "case_final_combined_print.stl"
    lid_mesh.export(str(lid_out))
    base_mesh.export(str(base_out))
    combined = trimesh.util.concatenate([lid_mesh, base_mesh])
    combined.export(str(combined_out))
    print(f"  {lid_out}")
    print(f"  {base_out}")
    print(f"  {combined_out}")


if __name__ == "__main__":
    build_and_assemble()
