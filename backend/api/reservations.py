from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.errors import NotFoundError, ValidationError
from backend.api.schemas import (
    AvailabilitySnapshot,
    BookingWindowInfo,
    ReservationCreate,
    ReservationPreviewRequest,
    ReservationPreviewResponse,
    ReservationResponse,
    ReservationUpdate,
)
from backend.db.database import get_db
from backend.engine.booking_impact import compute_banking_warning, compute_booking_impact
from backend.engine.booking_windows import compute_booking_windows
from backend.engine.eligibility import get_eligible_resorts
from backend.models.contract import Contract
from backend.models.point_balance import PointBalance
from backend.models.reservation import Reservation

router = APIRouter(tags=["reservations"])


@router.get("/api/reservations", response_model=list[ReservationResponse])
async def list_reservations(
    contract_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    upcoming: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """List all reservations with optional filters."""
    query = select(Reservation)

    if contract_id is not None:
        query = query.where(Reservation.contract_id == contract_id)
    if status_filter is not None:
        query = query.where(Reservation.status == status_filter)
    if upcoming:
        query = query.where(Reservation.check_in >= date.today())

    query = query.order_by(Reservation.check_in.asc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/api/contracts/{contract_id}/reservations",
    response_model=list[ReservationResponse],
)
async def list_contract_reservations(contract_id: int, db: AsyncSession = Depends(get_db)):
    """List reservations for a specific contract."""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    if not result.scalar_one_or_none():
        raise NotFoundError("Contract not found")

    result = await db.execute(
        select(Reservation)
        .where(Reservation.contract_id == contract_id)
        .order_by(Reservation.check_in.asc())
    )
    return result.scalars().all()


@router.post(
    "/api/reservations/preview",
    response_model=ReservationPreviewResponse,
)
async def preview_reservation(
    data: ReservationPreviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Preview the impact of a proposed reservation on point balances."""
    # 1. Load contract
    result = await db.execute(select(Contract).where(Contract.id == data.contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise NotFoundError("Contract not found")

    # 2. Load all point balances for this contract
    result = await db.execute(
        select(PointBalance).where(PointBalance.contract_id == data.contract_id)
    )
    all_balances = result.scalars().all()

    # 3. Load all non-cancelled reservations for this contract
    result = await db.execute(
        select(Reservation).where(
            Reservation.contract_id == data.contract_id,
            Reservation.status != "cancelled",
        )
    )
    all_reservations = result.scalars().all()

    # 4. Convert ORM objects to dicts (same pattern as availability API)
    contract_dict = {
        "id": contract.id,
        "use_year_month": contract.use_year_month,
        "annual_points": contract.annual_points,
        "home_resort": contract.home_resort,
    }

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

    # 5. Compute booking impact
    impact = compute_booking_impact(
        contract=contract_dict,
        point_balances=balances_data,
        reservations=reservations_data,
        proposed_resort=data.resort,
        proposed_room_key=data.room_key,
        proposed_check_in=data.check_in,
        proposed_check_out=data.check_out,
    )

    # 6. If error (no point chart), return 422
    if "error" in impact:
        raise ValidationError(impact["error"])

    # 7. Compute banking warning
    banking_warning = compute_banking_warning(
        contract=contract_dict,
        before_availability=impact["before"],
        points_cost=impact["stay_cost"]["total_points"],
    )

    # 8. Determine home resort and compute booking windows
    is_home_resort = contract.home_resort == data.resort
    booking_windows = compute_booking_windows(data.check_in, is_home_resort)

    # 9. Assemble response
    return ReservationPreviewResponse(
        before=AvailabilitySnapshot(
            total_points=impact["before"]["total_points"],
            committed_points=impact["before"]["committed_points"],
            available_points=impact["before"]["available_points"],
            balances=impact["before"]["balances"],
        ),
        after=AvailabilitySnapshot(
            total_points=impact["after"]["total_points"],
            committed_points=impact["after"]["committed_points"],
            available_points=impact["after"]["available_points"],
            balances=impact["after"]["balances"],
        ),
        points_delta=impact["points_delta"],
        nightly_breakdown=impact["stay_cost"]["nightly_breakdown"],
        total_points=impact["stay_cost"]["total_points"],
        num_nights=impact["stay_cost"]["num_nights"],
        booking_windows=BookingWindowInfo(**booking_windows),
        banking_warning=banking_warning,
    )


@router.get("/api/reservations/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(reservation_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single reservation."""
    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise NotFoundError("Reservation not found")
    return reservation


@router.post(
    "/api/contracts/{contract_id}/reservations",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_reservation(
    contract_id: int, data: ReservationCreate, db: AsyncSession = Depends(get_db)
):
    """Create a reservation for a contract."""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise NotFoundError("Contract not found")

    # Validate resort eligibility
    eligible = get_eligible_resorts(contract.home_resort, contract.purchase_type)
    if data.resort not in eligible:
        raise ValidationError(
            "Validation failed",
            fields=[
                {
                    "field": "resort",
                    "issue": f"Resort '{data.resort}' is not eligible for this {contract.purchase_type} contract at {contract.home_resort}. Eligible resorts: {eligible}",
                }
            ],
        )

    reservation = Reservation(
        contract_id=contract_id,
        resort=data.resort,
        room_key=data.room_key,
        check_in=data.check_in,
        check_out=data.check_out,
        points_cost=data.points_cost,
        status=data.status,
        confirmation_number=data.confirmation_number,
        notes=data.notes,
    )
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)
    return reservation


@router.put("/api/reservations/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: int, data: ReservationUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a reservation (partial update)."""
    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise NotFoundError("Reservation not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reservation, field, value)

    await db.commit()
    await db.refresh(reservation)
    return reservation


@router.delete("/api/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(reservation_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a reservation."""
    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise NotFoundError("Reservation not found")

    await db.delete(reservation)
    await db.commit()
