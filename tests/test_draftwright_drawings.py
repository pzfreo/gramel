"""Contract tests for the second, Draftwright-authored CNC drawing set."""

from importlib.metadata import version as package_version

from gramel.draftwright_drawings import DRAWINGS, cnc_params, is_blocking_lint_code


def test_draftwright_release_is_pinned() -> None:
    assert package_version("draftwright") == "0.4.15"


def test_draftwright_sheets_compile_without_blocking_lint() -> None:
    params = cnc_params()
    assert params.process.prototype is False
    assert [spec.number for spec in DRAWINGS] == [f"GRM-{number:02d}" for number in range(1, 8)]

    for spec in DRAWINGS:
        drawing = spec.builder(params)
        blocking = [
            issue
            for issue in drawing.lint()
            if issue.severity == "error" or is_blocking_lint_code(issue.code)
        ]
        assert not blocking, f"{spec.number}: " + ", ".join(
            f"{issue.severity}:{issue.code}" for issue in blocking
        )
