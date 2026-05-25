"""
Regression test: drawing files must not use fixed-precision number
formatting (``:.0f``, ``:.1f``, …) for dim/leader label strings.

History: in v0.1.6 the shaft drawing showed ``slot 5 wide`` and ``6``
for the blade slot dimensions, while the actual parameters were 4.75
and 6.4. The labels were tied to parameters via f-strings using
``:.0f``, which silently rounded the new measured values back to the
prior integer display values when the parameters changed in v0.1.4.

The fix is the ``dim_label()`` helper in ``gramel/parts/_drawing.py``
(strips trailing zeros, no precision loss). This test enforces it:
any ``{x:.Nf}`` pattern in a drawing file is forbidden, so the failure
mode can't reappear silently.
"""

from __future__ import annotations

import re
from pathlib import Path

PARTS_DIR = Path(__file__).resolve().parent.parent / "gramel" / "parts"
DRAWING_FILES = sorted(PARTS_DIR.glob("*_drawing.py"))

# Match {expr:.Nf} only inside f-strings (which is how all dim labels
# are built). The pattern catches the offending precision suffix
# regardless of what's inside the braces.
FIXED_PRECISION_PATTERN = re.compile(r"\{[^{}]+?:\.\d+f\}")


def test_drawing_files_dont_use_fixed_precision_format() -> None:
    """No drawing file may format a parameter value with ``:.Nf``.

    Use ``dim_label(value)`` from ``gramel.parts._drawing`` instead —
    it preserves precision and strips trailing zeros automatically.
    """
    assert DRAWING_FILES, "no drawing files found — wrong path?"

    offenders: list[tuple[str, int, str]] = []
    for path in DRAWING_FILES:
        text = path.read_text()
        for lineno, line in enumerate(text.splitlines(), start=1):
            # Allow the helper's docstring (only place that legitimately
            # shows the offending pattern as an example).
            if path.name == "_drawing.py":
                continue
            for match in FIXED_PRECISION_PATTERN.finditer(line):
                offenders.append((path.name, lineno, match.group(0)))

    if offenders:
        bullets = "\n".join(
            f"  {name}:{lineno}: {snippet}" for name, lineno, snippet in offenders
        )
        raise AssertionError(
            "Drawing files must not use fixed-precision number formatting "
            "for dim/leader labels — use dim_label(value) instead. "
            f"Found {len(offenders)} offender(s):\n{bullets}"
        )


def test_dim_label_preserves_precision() -> None:
    """``dim_label`` strips trailing zeros but never rounds away
    meaningful precision."""
    from gramel.parts._drawing import dim_label

    cases = [
        (35.0, "35"),
        (6.4, "6.4"),
        (4.75, "4.75"),
        (0.85, "0.85"),
        (0.5, "0.5"),
        (0.0, "0"),
        (10.0, "10"),
        (1.3, "1.3"),
    ]
    for value, expected in cases:
        assert dim_label(value) == expected, (
            f"dim_label({value}) = {dim_label(value)!r}, expected {expected!r}"
        )
