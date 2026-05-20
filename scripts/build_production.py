"""
Build the production manufacturing package.

Outputs to ``dist/``:

  dist/
    step/                              ← per-part STEP files (CNC-clean)
      GRM-01_shank.step
      GRM-02_shaft.step
      GRM-03_thumbwheel_drive_screw.step
      GRM-04_drive_plate.step
      GRM-05_depth_lock_bolt.step
    drawings/                          ← per-drawing SVG + PDF
      GRM-00_assembly.svg / .pdf
      GRM-01_shank.svg    / .pdf
      ... (GRM-02 → GRM-05)
    gramel_drawings.pdf                ← all six drawings, one file

Forces ``process.prototype=False`` so threaded features render as the
clean reference cylinders the shop reads off the drawing callouts (not
the FDM-prototype helical geometry).

Run with::

    uv run python scripts/build_production.py
"""

from __future__ import annotations

import subprocess
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from build123d import Part, export_step
from pypdf import PdfWriter

from gramel.assembly import build_assembly
from gramel.parameters import PurflingCutterParams
from gramel.parts._drawing import export_drawing
from gramel.parts.assembly_drawing import build_assembly_drawing
from gramel.parts.depth_lock_bolt import build_depth_lock_bolt
from gramel.parts.depth_lock_bolt_drawing import build_depth_lock_bolt_drawing
from gramel.parts.drive_plate import build_drive_plate
from gramel.parts.drive_plate_drawing import build_drive_plate_drawing
from gramel.parts.shaft import build_shaft
from gramel.parts.shaft_drawing import build_shaft_drawing
from gramel.parts.shank import build_shank
from gramel.parts.shank_drawing import build_shank_drawing
from gramel.parts.thumbwheel_drive_screw import build_thumbwheel_drive_screw
from gramel.parts.thumbwheel_drive_screw_drawing import build_thumbwheel_drawing

DIST = Path(__file__).resolve().parent.parent / "dist"

# (drawing-number, file-stem, builder)
PARTS: list[tuple[str, str, Callable[[PurflingCutterParams], Part]]] = [
    ("GRM-01", "shank", build_shank),
    ("GRM-02", "shaft", build_shaft),
    ("GRM-03", "thumbwheel_drive_screw", build_thumbwheel_drive_screw),
    ("GRM-04", "drive_plate", build_drive_plate),
    ("GRM-05", "depth_lock_bolt", build_depth_lock_bolt),
]

DRAWINGS: list[tuple[str, str, Callable[[PurflingCutterParams], Any]]] = [
    ("GRM-00", "assembly", build_assembly_drawing),
    ("GRM-01", "shank", build_shank_drawing),
    ("GRM-02", "shaft", build_shaft_drawing),
    ("GRM-03", "thumbwheel_drive_screw", build_thumbwheel_drawing),
    ("GRM-04", "drive_plate", build_drive_plate_drawing),
    ("GRM-05", "depth_lock_bolt", build_depth_lock_bolt_drawing),
]


def cnc_params() -> PurflingCutterParams:
    """Default params with process.prototype forced to False (CNC mode)."""
    p = PurflingCutterParams()
    return p.model_copy(update={"process": p.process.model_copy(update={"prototype": False})})


def build_steps(params: PurflingCutterParams) -> None:
    out = DIST / "step"
    out.mkdir(parents=True, exist_ok=True)
    for grm, name, builder in PARTS:
        part = builder(params)
        path = out / f"{grm}_{name}.step"
        export_step(part, str(path))
        print(f"  {path.relative_to(DIST.parent)}  (volume = {part.volume:.1f} mm³)")

    # Full assembly STEP — for the shop to visualise how the parts mate.
    asm = build_assembly(params)
    asm_path = DIST / "gramel_assembly.step"
    export_step(asm, str(asm_path))
    print(f"  {asm_path.relative_to(DIST.parent)}  (volume = {asm.volume:.1f} mm³)")


def build_drawings(params: PurflingCutterParams) -> list[Path]:
    out = DIST / "drawings"
    out.mkdir(parents=True, exist_ok=True)
    pdfs: list[Path] = []
    for grm, name, builder in DRAWINGS:
        parts_visible, parts_hidden, frame, dim_shapes, text, annotations = builder(params)
        svg_path = out / f"{grm}_{name}.svg"
        pdf_path = out / f"{grm}_{name}.pdf"
        export_drawing(
            svg_path=str(svg_path),
            pdf_path=str(pdf_path),
            parts_visible=parts_visible,
            parts_hidden=parts_hidden,
            frame=frame,
            dim_shapes=dim_shapes,
            text=text,
            annotations=annotations,
        )
        pdfs.append(pdf_path)
    return pdfs


def combine_pdfs(pdfs: list[Path]) -> Path:
    out_path = DIST / "gramel_drawings.pdf"
    writer = PdfWriter()
    for pdf in pdfs:
        writer.append(str(pdf))
    writer.write(str(out_path))
    return out_path


def release_version() -> str:
    """Resolve the release version from `git describe`, falling back to 'dev'.

    Format examples:
      - 'v0.1.0'                  — clean tag
      - 'v0.1.0-3-gabc1234'       — 3 commits past v0.1.0
      - 'v0.1.0-3-gabc1234-dirty' — uncommitted changes
      - 'dev'                     — no git, or git command unavailable
    """
    try:
        out = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip() or "dev"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "dev"


def bundle_zip(version: str) -> Path:
    """Pack the shop-handoff bundle: STEP files, combined drawings PDF, RFQ, spec.

    Filename includes the release version. Per-drawing PDFs/SVGs are
    intentionally excluded — the combined `gramel_drawings.pdf` contains
    all six drawings in one file. The zip is written next to dist/.
    """
    archive = DIST.parent / f"gramel-{version}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        # Per-part STEPs
        for step in sorted((DIST / "step").glob("*.step")):
            zf.write(step, step.relative_to(DIST))
        # Full assembly STEP + combined drawings PDF
        for top in ("gramel_assembly.step", "gramel_drawings.pdf"):
            src = DIST / top
            if src.exists():
                zf.write(src, top)
        # Quotation request and spec as top-level cover documents
        for extra in ("quotation-request.md", "specification.md"):
            src = DIST.parent / extra
            if src.exists():
                zf.write(src, extra)
    return archive


def main() -> None:
    params = cnc_params()
    DIST.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {DIST}")
    print()
    print("STEP files:")
    build_steps(params)
    print()
    print("Drawings (SVG + PDF):")
    pdfs = build_drawings(params)
    print()
    combined = combine_pdfs(pdfs)
    print(f"Combined PDF: {combined.relative_to(DIST.parent)}")
    print()
    version = release_version()
    archive = bundle_zip(version)
    print(f"Bundle:       {archive.relative_to(DIST.parent)}  (version: {version})")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
