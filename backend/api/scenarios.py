from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.models.contract import Contract
from backend.models.point_balance import PointBalance
from backend.models.reservation import Reservation
from backend.api.schemas import (
    ScenarioEvaluateRequest,
    ScenarioEvaluateResponse,
    ContractScenarioResult,
    ResolvedBooking,
)
from backend.engine.eligibility import get_eligible_resorts
from backend.engine.scenario import compute_scenario_impact

router = APIRouter(tags=["scenarios"])


@router.post("/api/scenarios/evaluate", response_model=ScenarioEvaluateResponse)
async def evaluate_scenario(
    data: ScenarioEvaluateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Evaluate a what-if scenario with multiple hypothetical bookings.

    Returns baseline vs scenario availability per contract, grand totals,
    resolved booking costs, and any errors from unresolvable bookings.
    """
    # 1. Load all contracts
    result = await db.execute(select(Contract))
    all_contracts = result.scalars().all()

    if not all_contracts:
        return ScenarioEvaluateResponse(
            contracts=[],
            summary={
                "baseline_available": 0,
                "scenario_available": 0,
                "total_impact": 0,
                "num_hypothetical_bookings": 0,
            },
            resolved_bookings=[],
            errors=[],
        )

    # 2. Build contract lookup for eligibility validation
    contract_map = {c.id: c for c in all_contracts}

    # 3. Validate resort eligibility for each hypothetical booking
    for hb in data.hypothetical_bookings:
        contract = contract_map.get(hb.contract_id)
        if not contract:
            raise HTTPException(
                status_code=422,
                detail=f"Contract {hb.contract_id} not found",
            )
        eligible = get_eligible_resorts(contract.home_resort, contract.purchase_type)
        if hb.resort not in eligible:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Resort '{hb.resort}' is not eligible for contract {hb.contract_id} "
                    f"({contract.purchase_type} at {contract.home_resort}). "
                    f"Eligible resorts: {eligible}"
                ),
            )

    # 4. Load all point balances
    result = await db.execute(select(PointBalance))
    all_balances = result.scalars().all()

    # 5. Load all non-cancelled reservations
    result = await db.execute(
        select(Reservation).where(Reservation.status != "cancelled")
    )
    all_reservations = result.scalars().all()

    # 6. Convert ORM objects to dicts (same pattern as reservations.py)
    contracts_data = [
        {
            "id": c.id,
            "use_year_month": c.use_year_month,
            "annual_points": c.annual_points,
            "home_resort": c.home_resort,
            "name": c.name,
        }
        for c in all_contracts
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

    hypotheticals_data = [
        {
            "contract_id": hb.contract_id,
            "resort": hb.resort,
            "room_key": hb.room_key,
            "check_in": hb.check_in,
            "check_out": hb.check_out,
        }
        for hb in data.hypothetical_bookings
    ]

    # 7. Call engine
    engine_result = compute_scenario_impact(
        contracts=contracts_data,
        point_balances=balances_data,
        reservations=reservations_data,
        hypothetical_bookings=hypotheticals_data,
        target_date=date.today(),
    )

    # 8. Map engine result to response schema
    contract_responses = []
    for cr in engine_result["contracts"]:
        contract_responses.append(ContractScenarioResult(
            contract_id=cr["contract_id"],
            contract_name=cr["contract_name"],
            home_resort=cr["home_resort"],
            baseline_available=cr["baseline"]["available_points"],
            baseline_total=cr["baseline"]["total_points"],
            baseline_committed=cr["baseline"]["committed_points"],
            scenario_available=cr["scenario"]["available_points"],
            scenario_total=cr["scenario"]["total_points"],
            scenario_committed=cr["scenario"]["committed_points"],
            impact=cr["baseline"]["available_points"] - cr["scenario"]["available_points"],
        ))

    resolved_responses = [
        ResolvedBooking(
            contract_id=rb["contract_id"],
            resort=rb["resort"],
            room_key=rb["room_key"],
            check_in=rb["check_in"],
            check_out=rb["check_out"],
            points_cost=rb["points_cost"],
            num_nights=rb["num_nights"],
        )
        for rb in engine_result["resolved_bookings"]
    ]

    return ScenarioEvaluateResponse(
        contracts=contract_responses,
        summary=engine_result["summary"],
        resolved_bookings=resolved_responses,
        errors=engine_result["errors"],
    )
