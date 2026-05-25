"""Vendored copy of pzfreo/pip-hinge (commit-pinned snapshot).

Upstream: https://github.com/pzfreo/pip-hinge
Original FreeCAD design by r0berts:
  https://www.printables.com/model/1395662-parametric-print-in-place-hinge-freecad
build123d port: Paul Fremantle (pzfreo).
Both licensed CC BY 4.0.

Vendored as a prototype dependency for `tools/assemble_case_with_pip_hinge.py`.
Do not edit here — change upstream and re-vendor if the design evolves.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from build123d import (
    Axis,
    CenterArc,
    Circle,
    Compound,
    Line,
    Plane,
    Polyline,
    Sketch,
    export_step,
    export_stl,
    extrude,
    make_face,
    revolve,
)
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Compound


@dataclass(frozen=True)
class HingeParams:
    hinge_height: float = 40.0
    hinge_width: float = 30.0
    hinge_thickness: float = 5.0
    pivot_inner: float = 5.0
    pivot_outer: Optional[float] = None
    pivot_clearance: float = 1.0
    clasp_width: Optional[float] = None
    clasp_clearance: float = 0.6
    clasp_center: Optional[float] = None
    pin_cyl_extra: float = 1.5
    pin_end_offset: float = 0.5
    pin_short_cyl_factor: float = 1 / 3
    self_support_ramp: bool = False

    def _resolve(self) -> dict:
        pivot_outer = self.pivot_outer if self.pivot_outer is not None else self.pivot_inner * 2
        clasp_width = self.clasp_width if self.clasp_width is not None else self.hinge_height / 6
        clasp_center = self.clasp_center if self.clasp_center is not None else self.hinge_height / 3
        if self.pivot_clearance >= self.pivot_inner:
            raise ValueError(f"pivot_clearance ({self.pivot_clearance}) must be < pivot_inner ({self.pivot_inner})")
        if pivot_outer <= self.pivot_inner:
            raise ValueError(f"pivot_outer ({pivot_outer}) must be > pivot_inner ({self.pivot_inner})")
        # When self_support_ramp is enabled, the leaf extends from the disc
        # bottom (Z=-T) down to Z=-(T+W) at the outer face, with a 45° ramp
        # from (W, -leaf_height) up to (0, -T). The 45° constraint requires
        # leaf_height - T == W. The leaf inner face becomes a teepee that
        # supports the disc from below when the hinge is laid flat in a
        # clamshell case.
        leaf_height = self.hinge_thickness + self.hinge_width if self.self_support_ramp else self.hinge_thickness
        return dict(
            H=self.hinge_height, W=self.hinge_width, T=self.hinge_thickness,
            Pi=self.pivot_inner, Po=pivot_outer, Pc=self.pivot_clearance,
            Cw=clasp_width, Cc=self.clasp_clearance, Cz=clasp_center,
            pin_cyl_extra=self.pin_cyl_extra, pin_end_offset=self.pin_end_offset,
            pin_short=self.pin_short_cyl_factor,
            leaf_height=leaf_height,
        )


def make_hinge_parts(params: HingeParams = None) -> tuple[Compound, Compound]:
    """Build pip-hinge and return (cylinder_side, pin_side) as separate compounds.

    Each may contain multiple solids (the comb pocket can split a leaf into
    several disconnected pieces, and the pin is 4 capsules). Return them in
    a Compound to preserve the multi-solid structure.
    """
    p = (params or HingeParams())._resolve()
    H, W, T = p["H"], p["W"], p["T"]
    Pi, Po, Pc = p["Pi"], p["Po"], p["Pc"]
    Cw, Cc, Cz = p["Cw"], p["Cc"], p["Cz"]
    Lh = p["leaf_height"]

    Ro = Po / 2
    Ri = Pi / 2
    Rp = Ri - Pc / 2
    Xi = Ro + Pc
    pocket_extrude = Lh + Pc / 2

    cs_profile = Polyline(
        (Ro, 0), (W, 0), (W, -Lh), (0, -T),
    ) + CenterArc(center=(0, 0), radius=Ro, start_angle=270, arc_size=-270)
    cs_sketch = Sketch() + Plane.XZ * (make_face(cs_profile) - Circle(Ri))
    cs_pad = extrude(cs_sketch, amount=H / 2, both=True)

    pad_max = 3.5 * Cw + Cc / 2
    tab1_o = 2.5 * Cw - Cc / 2
    tab1_i = 1.5 * Cw + Cc / 2
    tab0_o = Cw / 2 - Cc / 2
    Xo_cs = Xi - W

    cs_pocket_profile = Polyline(
        (Xo_cs,  pad_max), (Xo_cs, -pad_max),
        ( Xi,   -pad_max),
        ( Xi,   -tab1_o),  (-Xi, -tab1_o),
        (-Xi,   -tab1_i),  ( Xi, -tab1_i),
        ( Xi,   -tab0_o),  (-Xi, -tab0_o),
        (-Xi,    tab0_o),  ( Xi,  tab0_o),
        ( Xi,    tab1_i),  (-Xi,  tab1_i),
        (-Xi,    tab1_o),  ( Xi,  tab1_o),
        ( Xi,    pad_max),
        (Xo_cs,  pad_max),
    )
    cs_pocket = make_face(cs_pocket_profile)
    cylinder_side = cs_pad - extrude(cs_pocket, amount=pocket_extrude, both=True)

    ps_profile = Polyline(
        (-Ro, 0), (-W, 0), (-W, -Lh), (0, -T),
    ) + CenterArc(center=(0, 0), radius=Ro, start_angle=270, arc_size=270)
    ps_sketch = Sketch() + Plane.XZ * make_face(ps_profile)
    ps_pad = extrude(ps_sketch, amount=H / 2, both=True)

    ps_tab_outer = 2.5 * Cw
    ps_tab_mid_o = 1.5 * Cw
    ps_tab_mid_i = 0.5 * Cw
    Xo_ps = 4 * Po - Xi

    ps_pocket_profile = Polyline(
        (-Xi,    -ps_tab_outer),
        ( Xo_ps, -ps_tab_outer),
        ( Xo_ps,  ps_tab_outer),
        (-Xi,     ps_tab_outer),
        (-Xi,     ps_tab_mid_o),  ( Xi,  ps_tab_mid_o),
        ( Xi,     ps_tab_mid_i),  (-Xi,  ps_tab_mid_i),
        (-Xi,    -ps_tab_mid_i),  ( Xi, -ps_tab_mid_i),
        ( Xi,    -ps_tab_mid_o),  (-Xi, -ps_tab_mid_o),
        (-Xi,    -ps_tab_outer),
    )
    ps_pocket = make_face(ps_pocket_profile)
    pin_side = ps_pad - extrude(ps_pocket, amount=pocket_extrude, both=True)

    cyl_long = Cw + p["pin_cyl_extra"]
    cyl_short = Cw * p["pin_short"]
    half_long = cyl_long / 2
    y_centre_long = Cz / 2
    y_long_top = y_centre_long + half_long
    y_long_bot = y_centre_long - half_long
    y_long_cap_t = y_long_top + Rp
    y_long_cap_b = y_long_bot - Rp

    loop0 = (
        Line((Rp, y_long_top), (Rp, y_long_bot))
        + CenterArc(center=(0, y_long_bot), radius=Rp, start_angle=360, arc_size=-90)
        + Line((0, y_long_cap_b), (0, y_long_cap_t))
        + CenterArc(center=(0, y_long_top), radius=Rp, start_angle=90, arc_size=-90)
    )

    loop2 = (
        CenterArc(center=(0, -y_long_bot), radius=Rp, start_angle=0, arc_size=90)
        + Line((0, -y_long_cap_b), (0, -y_long_cap_t))
        + CenterArc(center=(0, -y_long_top), radius=Rp, start_angle=270, arc_size=90)
        + Line((Rp, -y_long_top), (Rp, -y_long_bot))
    )

    y_short_cyl_bot = 2.5 * Cw - p["pin_end_offset"]
    y_short_cyl_top = y_short_cyl_bot + cyl_short
    y_short_outer_flat = y_short_cyl_top
    y_short_cap_bot = y_short_cyl_bot - Rp

    loop1 = (
        Polyline(
            (0, y_short_outer_flat),
            (Rp, y_short_outer_flat),
            (Rp, y_short_cyl_bot),
        )
        + CenterArc(center=(0, y_short_cyl_bot), radius=Rp, start_angle=0, arc_size=-90)
        + Line((0, y_short_cap_bot), (0, y_short_outer_flat))
    )
    loop3 = (
        CenterArc(center=(0, -y_short_cyl_bot), radius=Rp, start_angle=0, arc_size=90)
        + Polyline(
            (0, -y_short_cap_bot),
            (0, -y_short_outer_flat),
            (Rp, -y_short_outer_flat),
            (Rp, -y_short_cyl_bot),
        )
    )

    pin_sketch = make_face(loop0) + make_face(loop1) + make_face(loop2) + make_face(loop3)
    pin_side = pin_side + revolve(pin_sketch, axis=Axis.Y, revolution_arc=-360)

    # The cs boolean subtract sometimes leaves phantom chunks at X ∈ [-Ro, Xi]
    # — pieces that should have been carved away but survive between the cs
    # tabs. Filter cs to keep only solids that include the paddle outer
    # (X > Xi = Ro + Pc), since legitimate cs material is anchored to that
    # spine. ps's wider pocket doesn't have this problem; keep all ps solids.
    def _filter_cs(part) -> list:
        keep = []
        for solid in part.solids():
            bb = solid.bounding_box()
            if bb.max.X > Xi + 0.01:  # touches paddle outer
                keep.append(solid)
        return keep

    cs_clean = _filter_cs(cylinder_side)

    def _to_compound(solids) -> Compound:
        builder = BRep_Builder()
        occ = TopoDS_Compound()
        builder.MakeCompound(occ)
        for solid in solids:
            builder.Add(occ, solid.wrapped)
        return Compound(occ)

    return _to_compound(cs_clean), _to_compound(list(pin_side.solids()))


def make_hinge(params: HingeParams = None) -> Compound:
    p = (params or HingeParams())._resolve()
    H, W, T = p["H"], p["W"], p["T"]
    Pi, Po, Pc = p["Pi"], p["Po"], p["Pc"]
    Cw, Cc, Cz = p["Cw"], p["Cc"], p["Cz"]
    Lh = p["leaf_height"]

    Ro = Po / 2
    Ri = Pi / 2
    Rp = Ri - Pc / 2
    Xi = Ro + Pc
    pocket_extrude = Lh + Pc / 2

    cs_profile = Polyline(
        (Ro, 0), (W, 0), (W, -Lh), (0, -T),
    ) + CenterArc(center=(0, 0), radius=Ro, start_angle=270, arc_size=-270)
    cs_sketch = Sketch() + Plane.XZ * (make_face(cs_profile) - Circle(Ri))
    cs_pad = extrude(cs_sketch, amount=H / 2, both=True)

    pad_max = 3.5 * Cw + Cc / 2
    tab1_o = 2.5 * Cw - Cc / 2
    tab1_i = 1.5 * Cw + Cc / 2
    tab0_o = Cw / 2 - Cc / 2
    Xo_cs = Xi - W

    cs_pocket_profile = Polyline(
        (Xo_cs,  pad_max),
        (Xo_cs, -pad_max),
        ( Xi,   -pad_max),
        ( Xi,   -tab1_o),  (-Xi, -tab1_o),
        (-Xi,   -tab1_i),  ( Xi, -tab1_i),
        ( Xi,   -tab0_o),  (-Xi, -tab0_o),
        (-Xi,    tab0_o),  ( Xi,  tab0_o),
        ( Xi,    tab1_i),  (-Xi,  tab1_i),
        (-Xi,    tab1_o),  ( Xi,  tab1_o),
        ( Xi,    pad_max),
        (Xo_cs,  pad_max),
    )
    cs_pocket = make_face(cs_pocket_profile)
    cylinder_side = cs_pad - extrude(cs_pocket, amount=pocket_extrude, both=True)

    ps_profile = Polyline(
        (-Ro, 0), (-W, 0), (-W, -Lh), (0, -T),
    ) + CenterArc(center=(0, 0), radius=Ro, start_angle=270, arc_size=270)
    ps_sketch = Sketch() + Plane.XZ * make_face(ps_profile)
    ps_pad = extrude(ps_sketch, amount=H / 2, both=True)

    ps_tab_outer = 2.5 * Cw
    ps_tab_mid_o = 1.5 * Cw
    ps_tab_mid_i = 0.5 * Cw
    Xo_ps = 4 * Po - Xi

    ps_pocket_profile = Polyline(
        (-Xi,    -ps_tab_outer),
        ( Xo_ps, -ps_tab_outer),
        ( Xo_ps,  ps_tab_outer),
        (-Xi,     ps_tab_outer),
        (-Xi,     ps_tab_mid_o),  ( Xi,  ps_tab_mid_o),
        ( Xi,     ps_tab_mid_i),  (-Xi,  ps_tab_mid_i),
        (-Xi,    -ps_tab_mid_i),  ( Xi, -ps_tab_mid_i),
        ( Xi,    -ps_tab_mid_o),  (-Xi, -ps_tab_mid_o),
        (-Xi,    -ps_tab_outer),
    )
    ps_pocket = make_face(ps_pocket_profile)
    pin_side = ps_pad - extrude(ps_pocket, amount=pocket_extrude, both=True)

    cyl_long  = Cw + p["pin_cyl_extra"]
    cyl_short = Cw * p["pin_short"]
    half_long = cyl_long / 2
    y_centre_long  = Cz / 2
    y_long_top    = y_centre_long + half_long
    y_long_bot    = y_centre_long - half_long
    y_long_cap_t  = y_long_top + Rp
    y_long_cap_b  = y_long_bot - Rp

    loop0 = (
        Line((Rp, y_long_top), (Rp, y_long_bot))
        + CenterArc(center=(0, y_long_bot), radius=Rp, start_angle=360, arc_size=-90)
        + Line((0, y_long_cap_b), (0, y_long_cap_t))
        + CenterArc(center=(0, y_long_top), radius=Rp, start_angle=90, arc_size=-90)
    )

    loop2 = (
        CenterArc(center=(0, -y_long_bot), radius=Rp, start_angle=0, arc_size=90)
        + Line((0, -y_long_cap_b), (0, -y_long_cap_t))
        + CenterArc(center=(0, -y_long_top), radius=Rp, start_angle=270, arc_size=90)
        + Line((Rp, -y_long_top), (Rp, -y_long_bot))
    )

    y_short_cyl_bot    = 2.5 * Cw - p["pin_end_offset"]
    y_short_cyl_top    = y_short_cyl_bot + cyl_short
    y_short_outer_flat = y_short_cyl_top
    y_short_cap_bot    = y_short_cyl_bot - Rp

    loop1 = (
        Polyline(
            (0, y_short_outer_flat),
            (Rp, y_short_outer_flat),
            (Rp, y_short_cyl_bot),
        )
        + CenterArc(center=(0, y_short_cyl_bot), radius=Rp, start_angle=0, arc_size=-90)
        + Line((0, y_short_cap_bot), (0, y_short_outer_flat))
    )
    loop3 = (
        CenterArc(center=(0, -y_short_cyl_bot), radius=Rp, start_angle=0, arc_size=90)
        + Polyline(
            (0, -y_short_cap_bot),
            (0, -y_short_outer_flat),
            (Rp, -y_short_outer_flat),
            (Rp, -y_short_cyl_bot),
        )
    )

    pin_sketch = make_face(loop0) + make_face(loop1) + make_face(loop2) + make_face(loop3)
    pin_side = pin_side + revolve(pin_sketch, axis=Axis.Y, revolution_arc=-360)

    builder = BRep_Builder()
    occ = TopoDS_Compound()
    builder.MakeCompound(occ)
    for solid in [*cylinder_side.solids(), *pin_side.solids()]:
        builder.Add(occ, solid.wrapped)
    return Compound(occ)
