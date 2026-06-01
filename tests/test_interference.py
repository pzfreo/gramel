"""Regression test: part drawings must stay free of annotation interference.

History: the shank drawing placed the "slot 1 deep, flat floor" leader label
(`s_left - 20`) so its left end overlapped the face-view outline. Whole-bbox
lint did not catch it because the label and the view edge are different kinds
of geometry. The geometry-precise scan in ``tools/check_interference.py`` does.

This test builds every drawing and asserts the scan is clean, so a future
layout edit can't silently reintroduce a label/dimension/witness-line collision.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_TOOL = Path(__file__).resolve().parent.parent / "tools" / "check_interference.py"
_spec = importlib.util.spec_from_file_location("check_interference", _TOOL)
check_interference = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_interference)


@pytest.mark.parametrize("module", check_interference.DRAWING_MODULES)
def test_drawing_has_no_interference_errors(module):
    # Errors are real collisions (label/line/part overlaps, off-frame labels).
    # Redundant collinear lines (chain dims sharing a witness line) are warnings,
    # often legitimate, so they do not fail the suite — see scan_drawing().
    errors, _warnings = check_interference.scan_drawing(module)
    assert errors == [], f"{module}: " + "; ".join(errors)
