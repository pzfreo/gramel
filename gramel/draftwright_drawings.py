"""Draftwright v0.4.15 CNC drawings for the seven manufactured parts.

The hand-authored drawings in :mod:`gramel.parts` remain the proven quotation
baseline.  This module builds a second, side-by-side set with Draftwright's
declarative ``Sheet`` API.  Geometry comes from the live CNC-mode builders;
manufacturing intent that a B-rep cannot carry (threads, fits, knurls, finish,
material and process notes) is declared here.

Draftwright currently formats ordinary dimensions to one decimal place.  A few
Gramel nominals carry more precision (13.55, 6.25, 4.75, 0.85 and 1.875 mm).
Those requirements use ``measured_dimension`` with witnesses derived from the
same parameter tree, so the visible label retains the full nominal rather than
silently rounding it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from build123d import Part
from draftwright import Drawing, Sheet
from draftwright.model import (
    BossFeature,
    ChamferFeature,
    DimensionParameterId,
    EnvelopeFeature,
    Feature,
    HoleFeature,
    PocketFeature,
    SlotFeature,
    StepFeature,
)

from gramel.parameters import PurflingCutterParams
from gramel.parts.blade import build_blade
from gramel.parts.blade_retainer import build_blade_retainer
from gramel.parts.depth_lock_bolt import build_depth_lock_bolt
from gramel.parts.drive_plate import build_drive_plate
from gramel.parts.shaft import build_shaft
from gramel.parts.shank import build_shank
from gramel.parts.thumbwheel_drive_screw import build_thumbwheel_drive_screw_features

BRASS = "H62 brass (CuZn40)"
DRAWN_BY = "P. Fremantle"
GENERAL_TOLERANCE = "ISO 2768-mK"

STANDARD_NOTES = (
    "ALL DIMENSIONS IN MM; BREAK SHARP EDGES 0.3 MAX; DEBURR",
    "Ra 3.2 UNLESS NOTED",
    "THREADS CLASS 6H/6g; CUT AND GAUGE WITH STANDARD TAPS/DIES",
)

BLOCKING_LINT_CODES = frozenset(
    {
        "annotation_ink_overlap",
        "annotation_out_of_bounds",
        "annotation_overlap",
        "placement_unsatisfiable",
        "view_annotation_overlap",
    }
)


@dataclass(frozen=True)
class DrawingSpec:
    number: str
    name: str
    builder: Callable[[PurflingCutterParams], Drawing]


def is_blocking_lint_code(code: str) -> bool:
    """Return whether a Draftwright issue makes a shop handoff unsafe."""
    if code == "section_dropped":
        # Draftwright may propose an additional inferred section even when
        # the authored orthographic set and feature-linked requirements are
        # complete.  Losing that unrequested extra view is not data loss.
        return False
    return code in BLOCKING_LINT_CODES or code.endswith("_dropped") or code.endswith("_withheld")


def cnc_params() -> PurflingCutterParams:
    """Return the production parameter set with simplified ISO 6410 threads."""
    params = PurflingCutterParams()
    return params.model_copy(
        update={"process": params.process.model_copy(update={"prototype": False})}
    )


def _sheet(
    part: Part,
    *,
    title: str,
    number: str,
    material: str,
    scale: float,
    page: str = "A4",
) -> Sheet:
    # Detection is the layout baseline: it gives Draftwright ownership of
    # principal/detail/section selection and feature-aware placement.  The
    # builders below take over only the dimension set, replacing rounded or
    # post-fillet measurements with the manufacturing requirements.
    detected = Sheet.from_part(part)
    sheet = Sheet(
        part,
        title=title,
        number=number,
        drawn_by=DRAWN_BY,
        tolerance=GENERAL_TOLERANCE,
        scale=scale,
        scale_policy="fallback",
        page=page,
        material=material,
        date=date.today().isoformat(),
        revision="A",
    )
    for feature in detected.features:
        sheet.add(feature)
    sheet.authored_dimensions()
    return sheet


def _seed_detected(
    sheet: Sheet,
    *,
    keep: Callable[[Feature], bool],
) -> list[tuple[Feature, Any]]:
    """Return fluent handles for selected recogniser-baseline features."""
    selected = [feature for feature in sheet.features if keep(feature)]
    seeded: list[tuple[Feature, Any]] = []
    for feature in selected:
        handle: Any
        try:
            handle = sheet.of(feature)
        except ValueError:
            handle = sheet.add(feature)
        seeded.append((feature, handle))
    return seeded


def _one(
    seeded: Iterable[tuple[Feature, Any]],
    cls: type[Feature],
    predicate: Callable[[Any], bool] = lambda _feature: True,
) -> Any:
    matches = [
        handle for feature, handle in seeded if isinstance(feature, cls) and predicate(feature)
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one {cls.__name__}, found {len(matches)}")
    return matches[0]


def _dimensions(sheet: Sheet, feature: Any, *roles: DimensionParameterId) -> None:
    for role in roles:
        sheet.dimension(feature, role)


def _exact_linear(
    sheet: Sheet,
    *,
    value: float,
    label: str,
    axis: str,
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
) -> None:
    """Declare an exact-label linear requirement with physical witnesses."""
    sheet.measured_dimension(
        kind="linear",
        value=value,
        label=label,
        dominant_axis=axis.upper(),
        ref_pts=(p1, p2),
        source="sheet",
        source_kind="gramel_parameter",
    )


def _finish(
    sheet: Sheet,
    notes: Iterable[str],
    *,
    standard_notes: tuple[str, ...] = STANDARD_NOTES,
) -> Drawing:
    sheet.notes((*standard_notes, *notes), prefer="tr")
    return sheet.build()


def build_shank_drawing(params: PurflingCutterParams) -> Drawing:
    part = build_shank(params)
    sp = params.shank
    sheet = _sheet(
        part,
        title="SHANK",
        number="GRM-01",
        material=BRASS,
        scale=1.0,
        page="A3",
    )
    crossbore_z = sp.length - sp.crossbore_position_from_top
    tap_z = sp.length - params.tapped_bore_position_from_top
    seeded = _seed_detected(
        sheet,
        keep=lambda feature: isinstance(feature, (HoleFeature, PocketFeature)),
    )
    bottom_bore = _one(
        seeded,
        HoleFeature,
        lambda feature: feature.frame.axis == "z" and abs(feature.diameter - 5.0) < 0.01,
    ).fit("H8")
    crossbore = _one(
        seeded,
        HoleFeature,
        lambda feature: feature.frame.axis == "x" and abs(feature.diameter - 8.0) < 0.01,
    ).fit("H7")
    drive_tap = _one(
        seeded,
        HoleFeature,
        lambda feature: feature.frame.axis == "x" and abs(feature.diameter - 2.5) < 0.01,
    ).thread("M3x0.5")
    _one(seeded, PocketFeature)  # assert that the baseline recognised the relief slot

    _dimensions(sheet, bottom_bore, "bore.diameter")
    _dimensions(sheet, crossbore, "bore.diameter")
    _dimensions(sheet, drive_tap, "bore.diameter")
    sheet.section_view("A", through=bottom_bore)

    exact_dimensions = (
        (sp.length, "80", "z", (0, 0, 0), (0, 0, sp.length)),
        (
            sp.crossbore_position_from_top,
            "14",
            "z",
            (0, 0, crossbore_z),
            (0, 0, sp.length),
        ),
        (
            sp.crossbore_to_tapped_bore_gap,
            "9.5",
            "z",
            (0, 0, crossbore_z),
            (0, 0, tap_z),
        ),
        (sp.depth, "11", "y", (0, -sp.depth / 2, 0), (0, sp.depth / 2, 0)),
        (sp.width, "13.55", "x", (-sp.width / 2, 0, 0), (sp.width / 2, 0, 0)),
    )
    for value, label, axis, p1, p2 in exact_dimensions:
        _exact_linear(sheet, value=value, label=label, axis=axis, p1=p1, p2=p2)

    return _finish(
        sheet,
        (
            "VISIBLE BRASS SURFACES: CLEAN SATIN FINISH",
            "TRIAL FIT Ø8 g6 SHAFT IN Ø8 H7 BORE",
            "TAP M3x0.5 THRU; Ø2.5 TAP DRILL; CRITICAL - GAUGE AND TRIAL FIT WITH GRM-03",
            "PROFILED BORE FROM BOTTOM: Ø6.35 x 5.5 DEEP; TAP M6x1 x 12 DEEP; Ø5 H8 x 48.5 DEEP",
            "RELIEF SLOT: 2 x 66 x 1 DEEP; FLAT FLOOR",
            "5x R1 EXTERNAL FILLETS",
            "DEPTH-LOCK BORE AXIS AT X0 Y0",
        ),
    )


def build_shaft_drawing(params: PurflingCutterParams) -> Drawing:
    part = build_shaft(params)
    sp = params.shaft
    sheet = _sheet(
        part,
        title="SHAFT",
        number="GRM-02",
        material=BRASS,
        scale=2.0,
        page="A3",
    )
    seeded = _seed_detected(
        sheet,
        keep=lambda feature: isinstance(
            feature,
            (SlotFeature, BossFeature, EnvelopeFeature, ChamferFeature),
        ),
    )
    envelope = _one(seeded, EnvelopeFeature)
    slot = _one(seeded, SlotFeature)
    shaft_od = _one(seeded, BossFeature).fit("g6")
    mount_tap = sheet.hole(
        diameter=1.6,
        at=(0, 0, 0),
        axis="x",
        through=False,
        depth=sp.drive_plate_mount_depth,
    ).thread("M2x0.4")
    grub_tap = sheet.hole(
        diameter=3.3,
        at=(sp.length, 0, 0),
        axis="x",
        through=False,
        depth=sp.end_to_slot_distance,
    ).thread("M4x0.7")
    end_chamfer = _one(seeded, ChamferFeature)

    _dimensions(sheet, envelope, "width.length")
    _dimensions(sheet, shaft_od, "boss.diameter", "boss_height.length")
    _dimensions(sheet, mount_tap, "bore.diameter", "bore.depth")
    _dimensions(sheet, grub_tap, "bore.diameter")
    _dimensions(sheet, slot, "location")
    _dimensions(sheet, end_chamfer, "chamfer.length")
    _exact_linear(
        sheet,
        value=sp.blade_slot_length,
        label="4.75",
        axis="y",
        p1=(sp.length - sp.end_to_slot_distance - sp.blade_slot_width, -2.375, 0),
        p2=(sp.length - sp.end_to_slot_distance - sp.blade_slot_width, 2.375, 0),
    )

    return _finish(
        sheet,
        (
            "BLADE SLOT: 6.4 ALONG X x 4.75 ACROSS Y; NEAR WALL 4 FROM +X END",
            "END SLOT AT -X: 1.5 DEEP x 3 HIGH, OPEN FULL WIDTH",
            "UNDERSIDE FLAT 0.6 DEEP",
            "SHAFT OD Ø8 g6, Ra 1.6; TRIAL FIT IN GRM-01 Ø8 H7",
            "M2x0.4 TAP 5 DEEP; M4x0.7 TAP 4 DEEP TO BLADE SLOT",
            "VISIBLE BRASS SURFACES: CLEAN SATIN FINISH",
        ),
    )


def build_thumbwheel_drawing(params: PurflingCutterParams) -> Drawing:
    features = build_thumbwheel_drive_screw_features(params)
    tw = params.thumbwheel
    ds = params.drive_screw
    sheet = _sheet(
        features.body,
        title="THUMBWHEEL + DRIVE SCREW",
        number="GRM-03",
        material=BRASS,
        scale=2.0,
    )

    journal = sheet.step(features.journal)
    boss = sheet.step(features.boss)
    disc = sheet.step(features.disc).knurl(str(tw.knurl_pitch), tw.knurl.upper())
    collar = sheet.step(features.unthreaded)
    drive_thread = sheet.step(features.thread).thread("M3x0.5")
    tap = sheet.hole(features.tap, through=False, depth=ds.left_face_tap_depth).thread("M2x0.4")
    disc_chamfer_a = sheet.chamfer(
        axis="x", leg=tw.disc_edge_chamfer, at=(tw.boss_length, 0, tw.diameter / 2), turned=True
    )
    disc_chamfer_b = sheet.chamfer(
        axis="x",
        leg=tw.disc_edge_chamfer,
        at=(tw.boss_length + tw.thickness, 0, tw.diameter / 2),
        turned=True,
    )
    tip_chamfer = sheet.chamfer(
        axis="x",
        leg=ds.tip_chamfer,
        at=(tw.boss_length + tw.thickness + ds.unthreaded_length + ds.length, 0, 0),
        turned=True,
    )
    envelope = sheet.envelope()

    for step in (journal, boss, disc, collar, drive_thread):
        _dimensions(sheet, step, "step.length", "step.diameter")
    _dimensions(sheet, tap, "bore.diameter", "bore.depth")
    for chamfer in (disc_chamfer_a, disc_chamfer_b, tip_chamfer):
        _dimensions(sheet, chamfer, "chamfer.length")
    _dimensions(sheet, envelope, "width.length", "height.length")

    return _finish(
        sheet,
        (
            "M3x0.5 EXTERNAL THREAD IS CRITICAL; CUT AND GAUGE",
            "M2x0.4 TAP 7 DEEP; DRILL 8 DEEP FOR CHIP RELIEF",
            "TURNED STEPS: Ø4x3.2; Ø6x0.5; Ø10x2; Ø5x3; M3x0.5x20",
            "M3 THREAD Ra 1.6; STRAIGHT KNURL, 0.8 PITCH",
            "TRIAL FIT M3x0.5 THREAD WITH GRM-01 DRIVE TAP",
            "VISIBLE BRASS SURFACES: CLEAN SATIN FINISH",
        ),
    )


def build_drive_plate_drawing(params: PurflingCutterParams) -> Drawing:
    part = build_drive_plate(params)
    dp = params.drive_plate
    gap = params.shank.crossbore_to_tapped_bore_gap
    sheet = _sheet(
        part,
        title="DRIVE PLATE",
        number="GRM-04",
        material=BRASS,
        scale=3.0,
    )
    seeded = _seed_detected(
        sheet,
        keep=lambda feature: isinstance(feature, (HoleFeature, BossFeature)),
    )
    bearing = _one(seeded, HoleFeature, lambda feature: abs(feature.diameter - 4.2) < 0.01)
    mount = _one(seeded, HoleFeature, lambda feature: abs(feature.diameter - 2.4) < 0.01)
    big_boss = _one(seeded, BossFeature)
    _dimensions(sheet, bearing, "bore.diameter")
    _dimensions(sheet, mount, "bore.diameter")
    _dimensions(sheet, big_boss, "boss.diameter")

    _exact_linear(
        sheet,
        value=gap,
        label="9.5",
        axis="z",
        p1=(0, 0, 0),
        p2=(0, 0, gap),
    )
    _exact_linear(
        sheet,
        value=dp.thickness,
        label="3",
        axis="x",
        p1=(-dp.thickness / 2, 0, 0),
        p2=(dp.thickness / 2, 0, 0),
    )
    _exact_linear(
        sheet,
        value=dp.tenon_depth,
        label="1.5",
        axis="x",
        p1=(dp.thickness / 2, 0, 0),
        p2=(dp.thickness / 2 + dp.tenon_depth, 0, 0),
    )
    _exact_linear(
        sheet,
        value=dp.tenon_height,
        label="3",
        axis="z",
        p1=(dp.thickness / 2 + dp.tenon_depth, 0, -dp.tenon_height / 2),
        p2=(dp.thickness / 2 + dp.tenon_depth, 0, dp.tenon_height / 2),
    )

    return _finish(
        sheet,
        (
            "EGG PROFILE: Ø8 SHAFT END, Ø6 THUMB END; CENTRES 9.5",
            "Ø4.2 HOLE IS RUNNING CLEARANCE ON GRM-03 Ø4 JOURNAL",
            "TENON: 1.5 PROJECTION x 3 HIGH; WIDTH FOLLOWS EGG PROFILE",
            "Ø2.4 MOUNT HOLE PASSES THROUGH PLATE AND TENON",
            "VISIBLE BRASS SURFACES: CLEAN SATIN FINISH",
        ),
    )


def build_depth_lock_bolt_drawing(params: PurflingCutterParams) -> Drawing:
    part = build_depth_lock_bolt(params)
    dl = params.depth_lock
    sheet = _sheet(
        part,
        title="DEPTH-LOCK BOLT",
        number="GRM-05",
        material=BRASS,
        scale=2.0,
    )
    seeded = _seed_detected(
        sheet,
        keep=lambda feature: isinstance(feature, (StepFeature, ChamferFeature)),
    )
    knob = _one(seeded, StepFeature, lambda feature: abs(feature.diameter - 10) < 0.01)
    knob.knurl(str(dl.knurl_pitch), "STRAIGHT")
    collar = _one(seeded, StepFeature, lambda feature: abs(feature.diameter - 6.25) < 0.01)
    thread = _one(seeded, StepFeature, lambda feature: abs(feature.diameter - 6.0) < 0.01).thread(
        "M6x1"
    )
    chamfers = [handle for feature, handle in seeded if isinstance(feature, ChamferFeature)]

    _dimensions(sheet, knob, "step.length", "step.diameter")
    _dimensions(sheet, collar, "step.length")
    _dimensions(sheet, thread, "step.length", "step.diameter")
    for chamfer in chamfers:
        _dimensions(sheet, chamfer, "chamfer.length")
    _exact_linear(
        sheet,
        value=dl.bolt_collar_diameter,
        label="Ø6.25",
        axis="x",
        p1=(-dl.bolt_collar_diameter / 2, 0, dl.knob_thickness + dl.bolt_collar_length / 2),
        p2=(dl.bolt_collar_diameter / 2, 0, dl.knob_thickness + dl.bolt_collar_length / 2),
    )
    _exact_linear(
        sheet,
        value=dl.knob_thickness + dl.bolt_collar_length + dl.bolt_thread_length,
        label="32",
        axis="z",
        p1=(0, 0, 0),
        p2=(0, 0, 32),
    )

    return _finish(
        sheet,
        (
            "M6x1 EXTERNAL THREAD; CUT AND GAUGE",
            "STRAIGHT KNURL, 0.8 PITCH",
            "Ø6.25 COLLAR GUIDES IN GRM-01 BOTTOM COUNTERBORE",
            "M6 THREAD Ra 1.6; THREAD TIP C1; KNOB BOTTOM C1.5",
            "VISIBLE BRASS SURFACES: CLEAN SATIN FINISH",
        ),
    )


def build_blade_retainer_drawing(params: PurflingCutterParams) -> Drawing:
    part = build_blade_retainer(params)
    rp = params.blade_retainer
    sheet = _sheet(
        part,
        title="BLADE RETAINER",
        number="GRM-06",
        material="Annealed Cu",
        scale=5.0,
    )
    end_block = (rp.length - rp.middle_length) / 2
    dims = (
        (rp.thickness, "0.85", "x", (-rp.thickness / 2, 0, 0), (rp.thickness / 2, 0, 0)),
        (rp.length, "10", "z", (0, 0, -rp.length / 2), (0, 0, rp.length / 2)),
        (
            rp.end_width,
            "5.5",
            "y",
            (0, -rp.end_width / 2, rp.length / 2),
            (0, rp.end_width / 2, rp.length / 2),
        ),
        (rp.middle_width, "4.3", "y", (0, -rp.middle_width / 2, 0), (0, rp.middle_width / 2, 0)),
        (
            rp.middle_length,
            "6.25",
            "z",
            (0, 0, -rp.middle_length / 2),
            (0, 0, rp.middle_length / 2),
        ),
        (end_block, "1.875", "z", (0, 0, rp.middle_length / 2), (0, 0, rp.length / 2)),
    )
    for value, label, axis, p1, p2 in dims:
        _exact_linear(sheet, value=value, label=label, axis=axis, p1=p1, p2=p2)

    return _finish(
        sheet,
        (
            "OUTLINE ±0.1; THICKNESS 0.85 ±0.05",
            "4x R1.3 OUTER CORNERS; 4x R0.5 SHOULDER CORNERS",
            "LASER CUT OR STAMP; DEBURR; AS-RECEIVED SHEET FINISH OK",
            "QUANTITY 4 PER TOOL",
        ),
        standard_notes=("ALL DIMENSIONS IN MM",),
    )


def build_blade_drawing(params: PurflingCutterParams) -> Drawing:
    part = build_blade(params)
    bp = params.blade
    sheet = _sheet(
        part,
        title="BLADE",
        number="GRM-07",
        material="O1 / 60 HRC",
        scale=5.0,
    )
    dims = (
        (bp.thickness, "0.7", "x", (-bp.thickness / 2, 0, 0), (bp.thickness / 2, 0, 0)),
        (bp.width, "3.6", "y", (0, -bp.width / 2, 0), (0, bp.width / 2, 0)),
        (bp.length, "23", "z", (0, 0, -bp.length / 2), (0, 0, bp.length / 2)),
    )
    for value, label, axis, p1, p2 in dims:
        _exact_linear(sheet, value=value, label=label, axis=axis, p1=p1, p2=p2)

    return _finish(
        sheet,
        (
            "OUTLINE ±0.05; THICKNESS ±0.025",
            "25 DEG SINGLE BEVEL; PRIMARY GRIND AND HONE BY LUTHIER",
            "TIP R1.8, ROUNDED AND POLISHED",
            "HARDEN AND TEMPER TO APPROX. 60 HRC; QUANTITY 2 PER TOOL",
        ),
        standard_notes=("ALL DIMENSIONS IN MM; DEBURR",),
    )


DRAWINGS: tuple[DrawingSpec, ...] = (
    DrawingSpec("GRM-01", "shank", build_shank_drawing),
    DrawingSpec("GRM-02", "shaft", build_shaft_drawing),
    DrawingSpec("GRM-03", "thumbwheel_drive_screw", build_thumbwheel_drawing),
    DrawingSpec("GRM-04", "drive_plate", build_drive_plate_drawing),
    DrawingSpec("GRM-05", "depth_lock_bolt", build_depth_lock_bolt_drawing),
    DrawingSpec("GRM-06", "blade_retainer", build_blade_retainer_drawing),
    DrawingSpec("GRM-07", "blade", build_blade_drawing),
)


def export_drawings(
    out_dir: Path,
    params: PurflingCutterParams | None = None,
) -> tuple[list[Path], dict[str, list[dict[str, str]]]]:
    """Export PDF/SVG/DXF drawings and return their paths plus lint records."""
    params = params or cnc_params()
    drawings_dir = out_dir / "drawings"
    dxf_dir = out_dir / "dxf"
    drawings_dir.mkdir(parents=True, exist_ok=True)
    dxf_dir.mkdir(parents=True, exist_ok=True)
    pdfs: list[Path] = []
    lint: dict[str, list[dict[str, str]]] = {}

    for spec in DRAWINGS:
        drawing = spec.builder(params)
        stem = f"{spec.number}_{spec.name}"
        exported: Any = drawing.export(str(drawings_dir / stem), formats=("pdf", "svg"))
        drawing.export(str(dxf_dir / stem), formats=("dxf",))
        pdfs.append(Path(exported["pdf"]))
        lint[spec.number] = [
            {"severity": issue.severity, "code": issue.code, "message": issue.message}
            for issue in drawing.lint()
        ]
        blocking = [
            issue
            for issue in lint[spec.number]
            if issue["severity"] == "error" or is_blocking_lint_code(issue["code"])
        ]
        if blocking:
            summary = ", ".join(issue["code"] for issue in blocking)
            raise RuntimeError(f"{spec.number} has blocking Draftwright lint: {summary}")
    return pdfs, lint
