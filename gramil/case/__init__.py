"""
Print-in-place clamshell case for the Gramil purfling cutter.

Two-half clamshell with an interlocking knuckle hinge along the back edge
and four 6×3 mm rare-earth magnets (glued, two pairs) holding it closed.
The case is dimensioned from PurflingCutterParams so it tracks any changes
to the tool's geometry.

Public API:
    CaseParams          — pydantic parameter model for the case
    build_case          — returns the case as a Compound (both halves)
    build_case_with_tool — case + tool at a specified extension state
"""

from gramil.case.assembly import build_case_with_tool
from gramil.case.case import build_case
from gramil.case.parameters import CaseParams

__all__ = ["CaseParams", "build_case", "build_case_with_tool"]
