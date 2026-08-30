"""
Build the production manufacturing package.

Outputs to ``dist/``:

  dist/
    step/                              ← per-part STEP files + assembly
      GRM-01_shank.step
      GRM-02_shaft.step
      GRM-03_thumbwheel_drive_screw.step
      GRM-04_drive_plate.step
      GRM-05_depth_lock_bolt.step
      gramil_assembly.step
    case/                              ← FDM sandwich-case STEPs (PETG, print-in-place)
      gramil_case_shell.step
      gramil_case_insert.step
    drawings/                          ← per-drawing SVG + PDF
      GRM-00_assembly.svg / .pdf
      GRM-01_shank.svg    / .pdf
      ... (GRM-02 → GRM-06)
    dxf/                               ← per-drawing DXF (for shops that prefer DXF)
      GRM-00_assembly.dxf
      ... (GRM-01 → GRM-06)
    gramil_drawings.pdf                ← all seven drawings, one file
    quotation-request.pdf              ← RFQ rendered from quotation-request.md

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
from markdown_pdf import MarkdownPdf, Section
from pypdf import PdfWriter

from gramil.assembly import build_assembly
from gramil.case.parameters import SandwichCaseParams
from gramil.case.sandwich import build_insert as build_case_insert
from gramil.case.sandwich import build_print_shell as build_case_shell
from gramil.parameters import PurflingCutterParams
from gramil.parts._drawing import export_drawing, export_dxf_drawing
from gramil.parts.assembly_drawing import build_assembly_drawing
from gramil.parts.blade import build_blade
from gramil.parts.blade_drawing import build_blade_drawing
from gramil.parts.blade_retainer import build_blade_retainer
from gramil.parts.blade_retainer_drawing import build_blade_retainer_drawing
from gramil.parts.depth_lock_bolt import build_depth_lock_bolt
from gramil.parts.depth_lock_bolt_drawing import build_depth_lock_bolt_drawing
from gramil.parts.drive_plate import build_drive_plate
from gramil.parts.drive_plate_drawing import build_drive_plate_drawing
from gramil.parts.shaft import build_shaft
from gramil.parts.shaft_drawing import build_shaft_drawing
from gramil.parts.shank import build_shank
from gramil.parts.shank_drawing import build_shank_drawing
from gramil.parts.thumbwheel_drive_screw import build_thumbwheel_drive_screw
from gramil.parts.thumbwheel_drive_screw_drawing import build_thumbwheel_drawing

DIST = Path(__file__).resolve().parent.parent / "dist"

PARTS: list[tuple[str, str, Callable[[PurflingCutterParams], Part]]] = [
    ("GRM-01", "shank", build_shank),
    ("GRM-02", "shaft", build_shaft),
    ("GRM-03", "thumbwheel_drive_screw", build_thumbwheel_drive_screw),
    ("GRM-04", "drive_plate", build_drive_plate),
    ("GRM-05", "depth_lock_bolt", build_depth_lock_bolt),
    ("GRM-06", "blade_retainer", build_blade_retainer),
    ("GRM-07", "blade", build_blade),
]

DRAWINGS: list[tuple[str, str, Callable[[PurflingCutterParams], Any]]] = [
    ("GRM-00", "assembly", build_assembly_drawing),
    ("GRM-01", "shank", build_shank_drawing),
    ("GRM-02", "shaft", build_shaft_drawing),
    ("GRM-03", "thumbwheel_drive_screw", build_thumbwheel_drawing),
    ("GRM-04", "drive_plate", build_drive_plate_drawing),
    ("GRM-05", "depth_lock_bolt", build_depth_lock_bolt_drawing),
    ("GRM-06", "blade_retainer", build_blade_retainer_drawing),
    ("GRM-07", "blade", build_blade_drawing),
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

    asm = build_assembly(params)
    asm_path = out / "gramil_assembly.step"
    export_step(asm, str(asm_path))
    print(f"  {asm_path.relative_to(DIST.parent)}  (volume = {asm.volume:.1f} mm³)")


def build_case_steps(params: PurflingCutterParams) -> None:
    """Export the FDM sandwich-case STEPs (print-in-place shell + insert).

    The tool pocket is sized from the CNC tool (``params`` already has
    ``prototype=False``), since the case holds the finished brass tool.
    """
    out = DIST / "case"
    out.mkdir(parents=True, exist_ok=True)
    case = SandwichCaseParams()
    targets = {
        "gramil_case_shell": build_case_shell(params, case),
        "gramil_case_insert": build_case_insert(params, case),
    }
    for name, shape in targets.items():
        path = out / f"{name}.step"
        export_step(shape, str(path))
        print(f"  {path.relative_to(DIST.parent)}  (volume = {shape.volume:.1f} mm³)")


def build_drawings(params: PurflingCutterParams) -> tuple[list[Path], list[Path]]:
    """Build SVG + PDF + DXF for each drawing.

    Returns (pdf_paths, dxf_paths) — drawings are rebuilt once and exported
    twice (SVG/PDF and DXF) to avoid repeating the expensive view-projection.
    """
    pdf_out = DIST / "drawings"
    dxf_out = DIST / "dxf"
    pdf_out.mkdir(parents=True, exist_ok=True)
    dxf_out.mkdir(parents=True, exist_ok=True)
    pdfs: list[Path] = []
    dxfs: list[Path] = []
    for grm, name, builder in DRAWINGS:
        parts_visible, parts_hidden, frame, dim_shapes, text, annotations = builder(params)
        svg_path = pdf_out / f"{grm}_{name}.svg"
        pdf_path = pdf_out / f"{grm}_{name}.pdf"
        dxf_path = dxf_out / f"{grm}_{name}.dxf"
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
        export_dxf_drawing(
            dxf_path=str(dxf_path),
            parts_visible=parts_visible,
            parts_hidden=parts_hidden,
            frame=frame,
            dim_shapes=dim_shapes,
            text=text,
            annotations=annotations,
        )
        pdfs.append(pdf_path)
        dxfs.append(dxf_path)
    return pdfs, dxfs


def combine_pdfs(pdfs: list[Path]) -> Path:
    out_path = DIST / "gramil_drawings.pdf"
    writer = PdfWriter()
    for pdf in pdfs:
        writer.append(str(pdf))
    writer.write(str(out_path))
    return out_path


def build_quotation_pdf() -> Path | None:
    """Render quotation-request.md → dist/quotation-request.pdf."""
    src = DIST.parent / "quotation-request.md"
    if not src.exists():
        return None
    out_path = DIST / "quotation-request.pdf"
    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(src.read_text(encoding="utf-8"), root=str(src.parent)))
    pdf.save(out_path)
    return out_path


def release_version() -> str:
    """Resolve the release version from `git describe`, falling back to 'dev'."""
    try:
        out = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip() or "dev"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "dev"


def bundle_zip(version: str) -> Path:
    """Pack the shop-handoff bundle.

    Includes everything the shop needs and nothing they don't:
      - step/        all per-part STEPs + gramil_assembly.step (CNC brass)
      - case/        FDM sandwich-case STEPs (shell + insert, print-in-place)
      - dxf/         per-drawing DXFs (for shops that prefer DXF)
      - gramil_drawings.pdf       combined drawings PDF
      - quotation-request.pdf     RFQ as PDF

    Per-drawing SVGs/PDFs are intentionally excluded — the combined PDF
    covers all seven. specification.md is intentionally excluded — it's
    internal design documentation, not a shop deliverable.
    """
    archive = DIST.parent / f"gramil-{version}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for step in sorted((DIST / "step").glob("*.step")):
            zf.write(step, step.relative_to(DIST))
        for step in sorted((DIST / "case").glob("gramil_case_*.step")):
            zf.write(step, step.relative_to(DIST))
        for dxf in sorted((DIST / "dxf").glob("*.dxf")):
            zf.write(dxf, dxf.relative_to(DIST))
        for top in ("gramil_drawings.pdf", "quotation-request.pdf"):
            src = DIST / top
            if src.exists():
                zf.write(src, top)
    return archive


def main() -> None:
    params = cnc_params()
    DIST.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {DIST}")
    print()
    print("STEP files:")
    build_steps(params)
    print()
    print("Case STEP files (FDM):")
    build_case_steps(params)
    print()
    print("Drawings (SVG + PDF + DXF):")
    pdfs, _ = build_drawings(params)
    print()
    combined = combine_pdfs(pdfs)
    print(f"Combined PDF: {combined.relative_to(DIST.parent)}")
    quotation_pdf = build_quotation_pdf()
    if quotation_pdf is not None:
        print(f"Quotation PDF: {quotation_pdf.relative_to(DIST.parent)}")
    print()
    version = release_version()
    archive = bundle_zip(version)
    print(f"Bundle:       {archive.relative_to(DIST.parent)}  (version: {version})")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
