from datetime import date

from dateutil.relativedelta import relativedelta


def _dvc_subtract_months(check_in: date, months: int) -> date:
    """
    Subtract months from check_in using DVC's booking window rule.

    DVC rule: booking window opens on the same day-of-month, N months prior.
    If that day doesn't exist in the target month, the window opens on the
    1st of the NEXT month (NOT the last day of the target month).

    Example: check_in Sep 30, 7 months back:
      - relativedelta gives Feb 28 (clips backward)
      - DVC rule gives Mar 1 (rolls forward)
    """
    naive = check_in - relativedelta(months=months)
    # If relativedelta clipped the day, DVC rolls forward to 1st of next month
    if naive.day < check_in.day:
        # The target month didn't have enough days
        # Roll to 1st of next month
        if naive.month == 12:
            return date(naive.year + 1, 1, 1)
        else:
            return date(naive.year, naive.month + 1, 1)
    return naive


def compute_booking_windows(check_in: date, is_home_resort: bool) -> dict:
    """
    Compute booking window open dates for a given check-in date.

    Returns 11-month (home resort) and 7-month (any resort) window dates
    with status relative to today.
    """
    home_window_date = _dvc_subtract_months(check_in, 11)
    any_resort_window_date = _dvc_subtract_months(check_in, 7)
    today = date.today()

    return {
        "home_resort_window": home_window_date.isoformat(),
        "home_resort_window_open": today >= home_window_date,
        "days_until_home_window": (home_window_date - today).days,
        "any_resort_window": any_resort_window_date.isoformat(),
        "any_resort_window_open": today >= any_resort_window_date,
        "days_until_any_window": (any_resort_window_date - today).days,
        "is_home_resort": is_home_resort,
    }
