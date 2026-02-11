import pytest
from datetime import date
from unittest.mock import patch
from backend.engine.booking_windows import _dvc_subtract_months, compute_booking_windows


# --- _dvc_subtract_months edge cases ---


def test_standard_11_month_window():
    """Standard case: March 15 check-in -> April 15 previous year."""
    result = _dvc_subtract_months(date(2026, 3, 15), 11)
    assert result == date(2025, 4, 15)


def test_standard_7_month_window():
    """Standard case: March 15 check-in -> August 15 previous year."""
    result = _dvc_subtract_months(date(2026, 3, 15), 7)
    assert result == date(2025, 8, 15)


def test_end_of_month_sept30_rolls_forward():
    """DVC rule: Sept 30 - 7 months = March 1 (NOT Feb 28)."""
    result = _dvc_subtract_months(date(2026, 9, 30), 7)
    assert result == date(2026, 3, 1)  # NOT Feb 28


def test_end_of_month_sept29_non_leap():
    """DVC rule: Sept 29 - 7 months = March 1 in non-leap year (NOT Feb 28)."""
    # 2026 is not a leap year, so Feb has 28 days, 29 > 28 => clips => roll forward
    result = _dvc_subtract_months(date(2026, 9, 29), 7)
    assert result == date(2026, 3, 1)  # 2026 is not a leap year


def test_end_of_month_sept29_leap_year():
    """Leap year: Sept 29 - 7 months = Feb 29 (day exists)."""
    result = _dvc_subtract_months(date(2028, 9, 29), 7)
    assert result == date(2028, 2, 29)  # 2028 IS a leap year


def test_end_of_month_oct31():
    """Oct 31 - 7 months = March 31 (both have 31 days, no clipping)."""
    result = _dvc_subtract_months(date(2026, 10, 31), 7)
    assert result == date(2026, 3, 31)


def test_end_of_month_jan31_11_months():
    """Jan 31 - 11 months = March 1 (NOT Feb 28)."""
    result = _dvc_subtract_months(date(2026, 1, 31), 11)
    assert result == date(2025, 3, 1)  # Feb doesn't have 31 days


def test_december_boundary():
    """Dec 31 - 7 months = May 31 (no clipping needed)."""
    result = _dvc_subtract_months(date(2026, 12, 31), 7)
    assert result == date(2026, 5, 31)


# --- compute_booking_windows ---


def test_compute_booking_windows_all_fields_present():
    """compute_booking_windows returns all expected fields."""
    with patch("backend.engine.booking_windows.date") as mock_date:
        mock_date.today.return_value = date(2026, 1, 15)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        result = compute_booking_windows(date(2026, 12, 15), is_home_resort=True)

    assert "home_resort_window" in result
    assert "home_resort_window_open" in result
    assert "days_until_home_window" in result
    assert "any_resort_window" in result
    assert "any_resort_window_open" in result
    assert "days_until_any_window" in result
    assert "is_home_resort" in result
    assert result["is_home_resort"] is True

    # 11 months before Dec 15, 2026 = Jan 15, 2026
    assert result["home_resort_window"] == "2026-01-15"
    # 7 months before Dec 15, 2026 = May 15, 2026
    assert result["any_resort_window"] == "2026-05-15"


def test_compute_booking_windows_home_open_any_not():
    """Home window open but any-resort window not yet open."""
    with patch("backend.engine.booking_windows.date") as mock_date:
        mock_date.today.return_value = date(2026, 2, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        result = compute_booking_windows(date(2026, 12, 15), is_home_resort=True)

    assert result["home_resort_window_open"] is True
    assert result["any_resort_window_open"] is False
    assert result["days_until_home_window"] < 0  # already passed
    assert result["days_until_any_window"] > 0   # still in the future


def test_compute_booking_windows_not_home_resort():
    """is_home_resort=False is passed through."""
    result = compute_booking_windows(date(2026, 12, 15), is_home_resort=False)
    assert result["is_home_resort"] is False
