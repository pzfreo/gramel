"""Contract tests for the second, Draftwright-authored CNC drawing set."""

from importlib.metadata import version as package_version

from gramel.draftwright_drawings import (
    DRAWINGS,
    blocking_issues,
    build_drawing,
    cnc_params,
    is_blocking_lint_code,
    is_waived,
)

# The scale each sheet is authored at.  A sheet that quietly falls back to a
# smaller scale is a different drawing from the one the title block claims.
EXPECTED_SCALES = {
    "GRM-01": 1.0,
    "GRM-02": 2.0,
    "GRM-03": 5.0,
    "GRM-04": 5.0,
    "GRM-05": 2.0,
    "GRM-06": 5.0,
    "GRM-07": 5.0,
}

# Nominals that carry more precision than Draftwright's one-decimal default.
# They are drawn from the parameter tree via exact-label requirements, so a
# rounded label here means the shop would be handed the wrong number.
EXACT_LABELS = {
    "GRM-01": {"13.55"},
    "GRM-05": {"Ø6.25", "32"},
    "GRM-06": {"0.85", "6.25"},
}


def test_draftwright_release_is_pinned() -> None:
    assert package_version("draftwright") == "0.4.15"


def test_draftwright_sheets_compile_without_blocking_lint() -> None:
    params = cnc_params()
    assert params.process.prototype is False
    assert [spec.number for spec in DRAWINGS] == [f"GRM-{number:02d}" for number in range(1, 8)]

    for spec in DRAWINGS:
        drawing, scale_dropped = build_drawing(spec, params)
        assert not scale_dropped, f"{spec.number}: " + "; ".join(scale_dropped)
        assert drawing.scale == EXPECTED_SCALES[spec.number], spec.number
        blocking = blocking_issues(spec.number, drawing.lint())
        assert not blocking, f"{spec.number}: " + ", ".join(
            f"{issue['severity']}:{issue['code']}" for issue in blocking
        )


def test_critical_callouts_reach_the_sheet() -> None:
    """The features the notes call critical must carry a graphical callout."""
    params = cnc_params()
    required = {
        # The M3x0.5 drive thread and the Ø4 journal that runs in GRM-04's
        # Ø4.2 bore were both missing a diameter callout.
        "GRM-03": ("ø3 M3x0.5", "ø4"),
        # The depth-lock bore is blind; it once read "THRU".
        "GRM-01": ("⌀5 H8 ↧ 66",),
    }
    for number, expected in required.items():
        spec = next(spec for spec in DRAWINGS if spec.number == number)
        drawing, _ = build_drawing(spec, params)
        labels = {
            str(getattr(annotation, "text", None) or getattr(annotation, "label", ""))
            for _key, annotation in drawing.iter_annotations()
        }
        for label in expected:
            assert label in labels, f"{number} is missing the {label!r} callout"


def test_exact_nominals_are_not_rounded() -> None:
    params = cnc_params()
    for number, expected in EXACT_LABELS.items():
        spec = next(spec for spec in DRAWINGS if spec.number == number)
        drawing, _ = build_drawing(spec, params)
        labels = {
            str(getattr(annotation, "text", None) or getattr(annotation, "label", ""))
            for _key, annotation in drawing.iter_annotations()
        }
        assert expected <= labels, f"{number} is missing {sorted(expected - labels)}"


def test_lint_waivers_are_narrow() -> None:
    """A waiver must not disarm the gate for anything but its own finding."""
    assert is_blocking_lint_code("feature_not_dimensioned")
    assert is_waived("GRM-01", "feature_not_dimensioned", "cylindrical feature ø6.3 ...")
    assert not is_waived("GRM-03", "feature_not_dimensioned", "cylindrical feature ø6.3 ...")
    assert not is_waived("GRM-01", "feature_not_dimensioned", "cylindrical feature ø9 ...")
    assert not is_waived("GRM-01", "feature_not_located", "cylindrical feature ø6.3 ...")
