from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.db.database import get_db
from backend.models.contract import Contract
from backend.api.schemas import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractWithDetails,
    PointBalanceResponse,
)
from backend.engine.eligibility import get_eligible_resorts
from backend.engine.use_year import (
    get_use_year_start,
    get_use_year_end,
    get_banking_deadline,
    get_current_use_year,
    build_use_year_timeline,
)

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


def _build_timeline_summary(use_year_month: int) -> dict:
    """Build a use year timeline summary for the current use year."""
    current_uy = get_current_use_year(use_year_month)
    return build_use_year_timeline(use_year_month, current_uy)


def _enrich_contract(contract: Contract) -> dict:
    """Convert a Contract ORM object to a ContractWithDetails dict."""
    eligible = get_eligible_resorts(contract.home_resort, contract.purchase_type)
    timeline = _build_timeline_summary(contract.use_year_month)

    balances = [
        PointBalanceResponse.model_validate(pb)
        for pb in (contract.point_balances or [])
    ]

    return ContractWithDetails(
        id=contract.id,
        name=contract.name,
        home_resort=contract.home_resort,
        use_year_month=contract.use_year_month,
        annual_points=contract.annual_points,
        purchase_type=contract.purchase_type,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        point_balances=balances,
        eligible_resorts=eligible,
        use_year_timeline=timeline,
    ).model_dump()


@router.get("/", response_model=list[ContractWithDetails])
async def list_contracts(db: AsyncSession = Depends(get_db)):
    """List all contracts with point balances, eligible resorts, and timeline."""
    result = await db.execute(
        select(Contract).options(selectinload(Contract.point_balances))
    )
    contracts = result.scalars().all()
    return [_enrich_contract(c) for c in contracts]


@router.get("/{contract_id}", response_model=ContractWithDetails)
async def get_contract(contract_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single contract with full details."""
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.point_balances))
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return _enrich_contract(contract)


@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(data: ContractCreate, db: AsyncSession = Depends(get_db)):
    """Create a new contract."""
    contract = Contract(
        name=data.name,
        home_resort=data.home_resort,
        use_year_month=data.use_year_month,
        annual_points=data.annual_points,
        purchase_type=data.purchase_type,
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return contract


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int, data: ContractUpdate, db: AsyncSession = Depends(get_db)
):
    """Update an existing contract (partial update)."""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)

    await db.commit()
    await db.refresh(contract)
    return contract


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(contract_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a contract and cascade-delete its point balances."""
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.point_balances))
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    await db.delete(contract)
    await db.commit()
