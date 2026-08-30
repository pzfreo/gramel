"""Build the side-by-side Draftwright CNC quotation package.

The original hand-authored drawing set remains untouched and continues to be
built by ``scripts/build_production.py``.  This command uses Draftwright for
GRM-01 through GRM-07, retains the proven assembly sheet for GRM-00, and
packages the drawings with fresh CNC-mode STEP files.

Run with::

    uv run --python 3.12 python scripts/build_draftwright.py
"""

from __future__ import annotations

import json
import zipfile
from importlib.metadata import version as package_version
from pathlib import Path

from pypdf import PdfWriter

from gramil.draftwright_drawings import (
    LINT_WAIVERS,
    blocking_issues,
    cnc_params,
    export_drawings,
)
from gramil.parts._drawing import export_drawing, export_dxf_drawing
from gramil.parts.assembly_drawing import build_assembly_drawing
from scripts import build_production

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
DW_DIST = DIST / "draftwright"


def build_assembly_sheet() -> Path:
    """Export the proven GRM-00 assembly sheet beside the DW part sheets."""
    params = cnc_params()
    visible, hidden, frame, dimensions, text, annotations = build_assembly_drawing(params)
    drawings_dir = DW_DIST / "drawings"
    dxf_dir = DW_DIST / "dxf"
    drawings_dir.mkdir(parents=True, exist_ok=True)
    dxf_dir.mkdir(parents=True, exist_ok=True)
    stem = "GRM-00_assembly"
    pdf_path = drawings_dir / f"{stem}.pdf"
    export_drawing(
        svg_path=str(drawings_dir / f"{stem}.svg"),
        pdf_path=str(pdf_path),
        parts_visible=visible,
        parts_hidden=hidden,
        frame=frame,
        dim_shapes=dimensions,
        text=text,
        annotations=annotations,
    )
    export_dxf_drawing(
        dxf_path=str(dxf_dir / f"{stem}.dxf"),
        parts_visible=visible,
        parts_hidden=hidden,
        frame=frame,
        dim_shapes=dimensions,
        text=text,
        annotations=annotations,
    )
    return pdf_path


def combine_pdfs(pdfs: list[Path]) -> Path:
    """Combine the assembly and seven part sheets into the shop PDF."""
    out_path = DW_DIST / "gramil_draftwright_cnc_drawings.pdf"
    writer = PdfWriter()
    for pdf in pdfs:
        writer.append(str(pdf))
    writer.write(str(out_path))
    writer.close()
    return out_path


def write_lint_report(records: dict[str, dict[str, object]]) -> Path:
    """Record compiler version, effective scales and all audit findings."""
    blocking = {
        number: found
        for number, record in records.items()
        if (found := blocking_issues(number, record["issues"]))
    }
    report = {
        "draftwright_version": package_version("draftwright"),
        "blocking_issues": sum(len(found) for found in blocking.values()),
        "blocking_by_drawing": blocking,
        "waivers": [
            {
                "drawing": waiver.drawing,
                "code": waiver.code,
                "contains": waiver.contains,
                "reason": waiver.reason,
            }
            for waiver in LINT_WAIVERS
        ],
        "drawings": records,
    }
    path = DW_DIST / "lint-report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def bundle_zip(combined: Path, lint_report: Path) -> Path:
    """Create the CNC shop handoff archive."""
    release = build_production.release_version()
    archive = ROOT / f"gramil-{release}-draftwright-cnc.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for step in sorted((DIST / "step").glob("*.step")):
            zf.write(step, step.relative_to(DIST))
        for dxf in sorted((DW_DIST / "dxf").glob("*.dxf")):
            zf.write(dxf, Path("dxf") / dxf.name)
        # Must not collide with the baseline bundle's gramil_drawings.pdf:
        # unpacking both archives into one folder would silently overwrite
        # one drawing package with the other.
        zf.write(combined, combined.name)
        zf.write(lint_report, lint_report.name)
        quotation = DIST / "quotation-request.pdf"
        if quotation.exists():
            zf.write(quotation, quotation.name)
    return archive


def main() -> None:
    """Build, audit and package the Draftwright drawing iteration."""
    params = cnc_params()
    DW_DIST.mkdir(parents=True, exist_ok=True)

    print("CNC STEP files:")
    build_production.build_steps(params)
    print("\nDraftwright part drawings:")
    part_pdfs, lint = export_drawings(DW_DIST, params)
    assembly_pdf = build_assembly_sheet()
    lint_report = write_lint_report(lint)
    combined = combine_pdfs([assembly_pdf, *part_pdfs])
    build_production.build_quotation_pdf()
    archive = bundle_zip(combined, lint_report)

    print(f"\nCombined PDF: {combined.relative_to(ROOT)}")
    print(f"QA report:    {lint_report.relative_to(ROOT)}")
    print(f"Bundle:       {archive.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
