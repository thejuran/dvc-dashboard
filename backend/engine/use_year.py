from datetime import date
from dateutil.relativedelta import relativedelta

USE_YEAR_MONTHS = [2, 3, 4, 6, 8, 9, 10, 12]

def get_use_year_start(use_year_month: int, year: int) -> date:
    """Return the start date of a use year (1st of use_year_month in given year)."""
    return date(year, use_year_month, 1)

def get_use_year_end(use_year_month: int, year: int) -> date:
    """Return the end date of a use year (last day before next UY starts)."""
    start = get_use_year_start(use_year_month, year)
    return start + relativedelta(years=1) - relativedelta(days=1)

def get_banking_deadline(use_year_month: int, year: int) -> date:
    """Banking deadline is 8 months into the use year."""
    start = get_use_year_start(use_year_month, year)
    # Last day of the 8th month of the use year
    eight_months = start + relativedelta(months=8)
    return eight_months - relativedelta(days=1)


def get_current_use_year(use_year_month: int, as_of: date = None) -> int:
    """Determine which use year is current as of a given date."""
    if as_of is None:
        as_of = date.today()
    # If we're past this year's UY start, current UY is this year
    # Otherwise it's last year's UY
    if as_of.month >= use_year_month:
        return as_of.year
    else:
        return as_of.year - 1


def get_use_year_status(use_year_month: int, use_year: int, as_of: date = None) -> str:
    """Return 'expired', 'active', or 'upcoming' for a use year."""
    if as_of is None:
        as_of = date.today()
    start = get_use_year_start(use_year_month, use_year)
    end = get_use_year_end(use_year_month, use_year)
    if as_of > end:
        return "expired"
    elif as_of >= start:
        return "active"
    else:
        return "upcoming"


def build_use_year_timeline(use_year_month: int, use_year: int, as_of: date = None) -> dict:
    """Build a complete timeline dict for a given use year."""
    if as_of is None:
        as_of = date.today()
    start = get_use_year_start(use_year_month, use_year)
    end = get_use_year_end(use_year_month, use_year)
    banking_deadline = get_banking_deadline(use_year_month, use_year)
    return {
        "use_year": use_year,
        "label": f"{use_year} Use Year",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "banking_deadline": banking_deadline.isoformat(),
        "banking_deadline_passed": as_of > banking_deadline,
        "days_until_banking_deadline": (banking_deadline - as_of).days,
        "point_expiration": end.isoformat(),
        "days_until_expiration": (end - as_of).days,
        "status": get_use_year_status(use_year_month, use_year, as_of),
    }
