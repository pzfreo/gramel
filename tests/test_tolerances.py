"""Tests for ISO 286 tolerance lookups."""

import pytest

from gramil import tolerances


class TestITValues:
    @pytest.mark.parametrize(
        "nominal, grade, expected_um",
        [
            # ISO 286-1 Table 1 spot checks
            (3.0, "IT7", 10),
            (5.0, "IT7", 12),
            (8.0, "IT7", 15),
            (8.0, "IT6", 9),
            (15.0, "IT7", 18),
            (25.0, "IT8", 33),
        ],
    )
    def test_known_values(self, nominal, grade, expected_um):
        assert tolerances.it_tolerance_um(nominal, grade) == expected_um

    def test_unknown_grade_raises(self):
        with pytest.raises(ValueError, match="Unsupported IT grade"):
            tolerances.it_tolerance_um(8.0, "IT9")

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError, match="outside the supported range"):
            tolerances.it_tolerance_um(50.0, "IT7")


class TestLimits:
    def test_H7_at_8mm(self):
        """⌀8 H7 = 8.000 to 8.015 mm (ISO 286-1)."""
        lim = tolerances.limits(8.0, "H7")
        assert lim.upper == pytest.approx(0.015)
        assert lim.lower == pytest.approx(0.0)
        assert lim.min(8.0) == pytest.approx(8.000)
        assert lim.max(8.0) == pytest.approx(8.015)

    def test_g6_at_8mm(self):
        """⌀8 g6 = 7.986 to 7.995 mm (ISO 286-1)."""
        lim = tolerances.limits(8.0, "g6")
        assert lim.upper == pytest.approx(-0.005)
        assert lim.lower == pytest.approx(-0.014)
        assert lim.min(8.0) == pytest.approx(7.986)
        assert lim.max(8.0) == pytest.approx(7.995)

    def test_H8_at_5mm(self):
        """⌀5 H8 = 5.000 to 5.018 mm."""
        lim = tolerances.limits(5.0, "H8")
        assert lim.upper == pytest.approx(0.018)
        assert lim.lower == pytest.approx(0.0)

    def test_unsupported_fit_class_raises(self):
        with pytest.raises(ValueError, match="Unsupported fit class"):
            tolerances.limits(8.0, "k6")  # interference fit not yet supported


class TestClearances:
    def test_H7_g6_at_8mm(self):
        """ISO 286 H7/g6 sliding fit @ ⌀8 has 0.005 to 0.029 mm clearance."""
        assert tolerances.best_case_clearance(
            8.0, hole_fit="H7", shaft_fit="g6"
        ) == pytest.approx(0.005)
        assert tolerances.worst_case_clearance(
            8.0, hole_fit="H7", shaft_fit="g6"
        ) == pytest.approx(0.029)

    def test_clearance_positive_for_clearance_fits(self):
        """H7/g6 must always produce positive worst-case clearance — no interference."""
        for d in (3.0, 5.0, 8.0, 15.0, 25.0):
            wc = tolerances.worst_case_clearance(d, hole_fit="H7", shaft_fit="g6")
            bc = tolerances.best_case_clearance(d, hole_fit="H7", shaft_fit="g6")
            assert wc > bc > 0, f"H7/g6 must give clearance fit at ⌀{d}"
