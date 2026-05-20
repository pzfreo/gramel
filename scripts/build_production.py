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

from collections.abc import Callable
from pathlib import Path
from typing import Any

from build123d import Part, export_step
from pypdf import PdfWriter

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
    print("Done.")


if __name__ == "__main__":
    main()
