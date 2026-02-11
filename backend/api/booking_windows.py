from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.models.contract import Contract
from backend.models.reservation import Reservation
from backend.engine.booking_windows import compute_booking_windows
from backend.data.resorts import get_resort_by_slug

router = APIRouter(tags=["booking-windows"])


@router.get("/api/booking-windows/upcoming")
async def get_upcoming_booking_windows(
    days: int = Query(30, ge=1, le=90, description="Look-ahead window in days"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return upcoming booking window openings for existing reservations.

    Finds reservations with future check-in dates whose 11-month (home resort)
    or 7-month (any resort) booking windows open within the next `days` days.
    Returns at most 5 alerts sorted by soonest opening.
    """
    today = date.today()

    # Load all contracts
    result = await db.execute(select(Contract))
    contracts = result.scalars().all()
    contracts_by_id = {c.id: c for c in contracts}

    # Load all non-cancelled reservations with future check-in
    result = await db.execute(
        select(Reservation).where(
            Reservation.status != "cancelled",
            Reservation.check_in >= today,
        )
    )
    reservations = result.scalars().all()

    alerts = []

    for res in reservations:
        contract = contracts_by_id.get(res.contract_id)
        if contract is None:
            continue

        is_home_resort = contract.home_resort == res.resort
        window_data = compute_booking_windows(res.check_in, is_home_resort)

        # Home resort window (11-month): include if not yet open, within look-ahead, and is home resort
        if (
            is_home_resort
            and not window_data["home_resort_window_open"]
            and 0 < window_data["days_until_home_window"] <= days
        ):
            resort_info = get_resort_by_slug(res.resort)
            resort_name = resort_info["name"] if resort_info else res.resort
            alerts.append({
                "contract_name": contract.name or f"Contract #{contract.id}",
                "resort": res.resort,
                "resort_name": resort_name,
                "check_in": res.check_in.isoformat(),
                "window_type": "home_resort",
                "window_date": window_data["home_resort_window"],
                "days_until_open": window_data["days_until_home_window"],
            })

        # Any resort window (7-month): include if not yet open and within look-ahead
        if (
            not window_data["any_resort_window_open"]
            and 0 < window_data["days_until_any_window"] <= days
        ):
            resort_info = get_resort_by_slug(res.resort)
            resort_name = resort_info["name"] if resort_info else res.resort
            alerts.append({
                "contract_name": contract.name or f"Contract #{contract.id}",
                "resort": res.resort,
                "resort_name": resort_name,
                "check_in": res.check_in.isoformat(),
                "window_type": "any_resort",
                "window_date": window_data["any_resort_window"],
                "days_until_open": window_data["days_until_any_window"],
            })

    # Sort by soonest opening first
    alerts.sort(key=lambda a: a["days_until_open"])

    # Cap at 5
    return alerts[:5]
