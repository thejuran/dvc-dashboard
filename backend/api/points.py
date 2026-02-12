import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.errors import ConflictError, NotFoundError, ValidationError
from backend.api.schemas import PointBalanceCreate, PointBalanceResponse, PointBalanceUpdate
from backend.db.database import get_db
from backend.engine.use_year import build_use_year_timeline, get_current_use_year
from backend.models.app_setting import AppSetting
from backend.models.contract import Contract
from backend.models.point_balance import PointBalance

logger = logging.getLogger(__name__)

router = APIRouter(tags=["points"])


async def get_borrowing_limit_pct(db: AsyncSession) -> int:
    """Get the borrowing limit percentage from app settings."""
    result = await db.execute(select(AppSetting).where(AppSetting.key == "borrowing_limit_pct"))
    setting = result.scalar_one_or_none()
    return int(setting.value) if setting else 100


@router.get("/api/contracts/{contract_id}/points")
async def get_contract_points(contract_id: int, db: AsyncSession = Depends(get_db)):
    """Get all point balances for a contract, grouped by use year."""
    # Verify contract exists
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise NotFoundError("Contract not found")

    # Fetch all point balances for this contract
    result = await db.execute(
        select(PointBalance)
        .where(PointBalance.contract_id == contract_id)
        .order_by(PointBalance.use_year, PointBalance.allocation_type)
    )
    balances = result.scalars().all()

    # Group by use year
    balances_by_year: dict[str, dict] = {}
    for pb in balances:
        year_key = str(pb.use_year)
        if year_key not in balances_by_year:
            balances_by_year[year_key] = {
                "current": 0,
                "banked": 0,
                "borrowed": 0,
                "holding": 0,
                "total": 0,
            }
        balances_by_year[year_key][pb.allocation_type] = pb.points
        balances_by_year[year_key]["total"] = sum(
            balances_by_year[year_key][t] for t in ("current", "banked", "borrowed", "holding")
        )

    grand_total = sum(info["total"] for info in balances_by_year.values())

    return {
        "contract_id": contract_id,
        "contract_name": contract.name,
        "annual_points": contract.annual_points,
        "balances_by_year": balances_by_year,
        "grand_total": grand_total,
    }


@router.post(
    "/api/contracts/{contract_id}/points",
    response_model=PointBalanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_point_balance(
    contract_id: int, data: PointBalanceCreate, db: AsyncSession = Depends(get_db)
):
    """Add a point balance entry for a contract."""
    # Verify contract exists
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise NotFoundError("Contract not found")

    # Check for duplicate (same contract + use_year + allocation_type)
    result = await db.execute(
        select(PointBalance).where(
            and_(
                PointBalance.contract_id == contract_id,
                PointBalance.use_year == data.use_year,
                PointBalance.allocation_type == data.allocation_type,
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise ConflictError(
            f"Point balance already exists for contract {contract_id}, "
            f"use year {data.use_year}, type '{data.allocation_type}'. "
            "Use PUT to update it."
        )

    # Validate: banked points cannot exceed annual_points
    if data.allocation_type == "banked" and data.points > contract.annual_points:
        raise ValidationError(
            "Validation failed",
            fields=[
                {
                    "field": "points",
                    "issue": f"Banked points ({data.points}) cannot exceed annual points ({contract.annual_points})",
                }
            ],
        )

    # Enforce borrowing policy
    if data.allocation_type == "borrowed":
        borrowing_limit_pct = await get_borrowing_limit_pct(db)
        max_borrowed = int(contract.annual_points * borrowing_limit_pct / 100)
        if data.points > max_borrowed:
            raise ValidationError(
                "Validation failed",
                fields=[
                    {
                        "field": "points",
                        "issue": (
                            f"Borrowed points ({data.points}) exceed borrowing limit "
                            f"({borrowing_limit_pct}% of {contract.annual_points} = {max_borrowed} points)"
                        ),
                    }
                ],
            )

    balance = PointBalance(
        contract_id=contract_id,
        use_year=data.use_year,
        allocation_type=data.allocation_type,
        points=data.points,
    )
    db.add(balance)
    await db.commit()
    await db.refresh(balance)
    return balance


@router.put("/api/points/{balance_id}", response_model=PointBalanceResponse)
async def update_point_balance(
    balance_id: int, data: PointBalanceUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a point balance entry."""
    result = await db.execute(select(PointBalance).where(PointBalance.id == balance_id))
    balance = result.scalar_one_or_none()
    if not balance:
        raise NotFoundError("Point balance not found")

    # If updating a borrowed balance, enforce borrowing policy
    if balance.allocation_type == "borrowed":
        contract_result = await db.execute(
            select(Contract).where(Contract.id == balance.contract_id)
        )
        contract = contract_result.scalar_one_or_none()
        if contract:
            borrowing_limit_pct = await get_borrowing_limit_pct(db)
            max_borrowed = int(contract.annual_points * borrowing_limit_pct / 100)
            if data.points > max_borrowed:
                raise ValidationError(
                    "Validation failed",
                    fields=[
                        {
                            "field": "points",
                            "issue": (
                                f"Borrowed points ({data.points}) exceed borrowing limit "
                                f"({borrowing_limit_pct}% of {contract.annual_points} = {max_borrowed} points)"
                            ),
                        }
                    ],
                )

    balance.points = data.points
    await db.commit()
    await db.refresh(balance)
    return balance


@router.delete("/api/points/{balance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_point_balance(balance_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a point balance entry."""
    result = await db.execute(select(PointBalance).where(PointBalance.id == balance_id))
    balance = result.scalar_one_or_none()
    if not balance:
        raise NotFoundError("Point balance not found")

    await db.delete(balance)
    await db.commit()


@router.get("/api/contracts/{contract_id}/timeline")
async def get_contract_timeline(contract_id: int, db: AsyncSession = Depends(get_db)):
    """Return the complete use year timeline for a contract."""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise NotFoundError("Contract not found")

    use_year_month = contract.use_year_month
    current_uy = get_current_use_year(use_year_month)
    next_uy = current_uy + 1

    timelines = [
        build_use_year_timeline(use_year_month, current_uy),
        build_use_year_timeline(use_year_month, next_uy),
    ]

    return {
        "contract_id": contract_id,
        "use_year_month": use_year_month,
        "timelines": timelines,
    }
