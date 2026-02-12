from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.errors import ValidationError
from backend.db.database import get_db
from backend.engine.trip_explorer import find_affordable_options
from backend.models.contract import Contract
from backend.models.point_balance import PointBalance
from backend.models.reservation import Reservation

router = APIRouter(tags=["trip-explorer"])


@router.get("/api/trip-explorer")
async def trip_explorer(
    check_in: date = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Check-out date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Find all affordable resort/room options for the given dates.

    Composes availability, eligibility, and cost calculation across all
    contracts to answer "what can I afford?".
    """
    # Validation
    if check_out <= check_in:
        raise ValidationError(
            "Validation failed",
            fields=[{"field": "check_out", "issue": "check_out must be after check_in"}],
        )
    num_nights = (check_out - check_in).days
    if num_nights > 14:
        raise ValidationError(
            "Validation failed",
            fields=[{"field": "check_out", "issue": "Stay cannot exceed 14 nights"}],
        )

    # Load all contracts
    result = await db.execute(select(Contract))
    contracts = result.scalars().all()

    # Load all point balances
    result = await db.execute(select(PointBalance))
    all_balances = result.scalars().all()

    # Load all non-cancelled reservations
    result = await db.execute(select(Reservation).where(Reservation.status != "cancelled"))
    all_reservations = result.scalars().all()

    # Convert ORM objects to dicts for the pure-function engine
    contracts_data = [
        {
            "id": c.id,
            "name": c.name,
            "home_resort": c.home_resort,
            "use_year_month": c.use_year_month,
            "annual_points": c.annual_points,
            "purchase_type": c.purchase_type,
        }
        for c in contracts
    ]

    balances_data = [
        {
            "contract_id": b.contract_id,
            "use_year": b.use_year,
            "allocation_type": b.allocation_type,
            "points": b.points,
        }
        for b in all_balances
    ]

    reservations_data = [
        {
            "contract_id": r.contract_id,
            "check_in": r.check_in,
            "points_cost": r.points_cost,
            "status": r.status,
        }
        for r in all_reservations
    ]

    return find_affordable_options(
        contracts=contracts_data,
        point_balances=balances_data,
        reservations=reservations_data,
        check_in=check_in,
        check_out=check_out,
    )
