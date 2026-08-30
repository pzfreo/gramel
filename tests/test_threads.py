"""Tests for the thread-table lookup module."""

import pytest

from gramil import threads


class TestMajorDiameter:
    @pytest.mark.parametrize(
        "thread, expected",
        [("M2", 2.0), ("M2.5", 2.5), ("M3", 3.0), ("M4", 4.0), ("M5", 5.0), ("M6", 6.0)],
    )
    def test_returns_nominal_major(self, thread, expected):
        assert threads.major_diameter(thread) == pytest.approx(expected)

    def test_radius_is_half_of_diameter(self):
        for t in threads.known_threads():
            assert threads.major_radius(t) == pytest.approx(threads.major_diameter(t) / 2)


class TestTapDrill:
    @pytest.mark.parametrize(
        "thread, expected_d",
        [("M2", 1.6), ("M3", 2.5), ("M4", 3.3), ("M6", 5.0)],
    )
    def test_diameter(self, thread, expected_d):
        assert threads.tap_drill_diameter(thread) == pytest.approx(expected_d)

    def test_radius_is_half_of_diameter(self):
        for t in threads.known_threads():
            assert threads.tap_drill_radius(t) == pytest.approx(
                threads.tap_drill_diameter(t) / 2
            )

    def test_tap_drill_strictly_smaller_than_major(self):
        """Sanity: a tap drill must be smaller than the thread's major diameter."""
        for t in threads.known_threads():
            assert threads.tap_drill_diameter(t) < threads.major_diameter(t)


class TestPitch:
    @pytest.mark.parametrize(
        "thread, expected",
        [("M2", 0.4), ("M2.5", 0.45), ("M3", 0.5), ("M4", 0.7), ("M5", 0.8), ("M6", 1.0)],
    )
    def test_coarse_pitches(self, thread, expected):
        assert threads.pitch(thread) == pytest.approx(expected)


class TestUnknownThread:
    @pytest.mark.parametrize(
        "func",
        [
            threads.major_diameter,
            threads.major_radius,
            threads.tap_drill_diameter,
            threads.tap_drill_radius,
            threads.pitch,
        ],
    )
    def test_unknown_thread_raises(self, func):
        with pytest.raises(ValueError, match="Unknown thread spec"):
            func("M99")

    def test_error_message_lists_valid_threads(self):
        with pytest.raises(ValueError) as excinfo:
            threads.major_diameter("M99")
        msg = str(excinfo.value)
        for t in ("M2", "M3", "M6"):
            assert t in msg


class TestKnownThreads:
    def test_returns_tuple(self):
        assert isinstance(threads.known_threads(), tuple)

    def test_is_sorted(self):
        ks = threads.known_threads()
        assert list(ks) == sorted(ks)

    def test_covers_M2_through_M6(self):
        ks = threads.known_threads()
        for expected in ("M2", "M2.5", "M3", "M4", "M5", "M6"):
            assert expected in ks
