from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.models.contract import Contract, PurchaseType, UseYearMonth
from backend.models.point_balance import PointAllocationType, PointBalance
from backend.models.reservation import Reservation, ReservationStatus


@pytest.mark.asyncio
async def test_create_contract(db_session):
    """Test creating a contract and verifying all fields persist."""
    contract = Contract(
        name="Our Poly contract",
        home_resort="polynesian",
        use_year_month=6,
        annual_points=160,
        purchase_type=PurchaseType.RESALE.value,
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)

    assert contract.id is not None
    assert contract.name == "Our Poly contract"
    assert contract.home_resort == "polynesian"
    assert contract.use_year_month == 6
    assert contract.annual_points == 160
    assert contract.purchase_type == "resale"
    assert contract.created_at is not None
    assert contract.updated_at is not None


@pytest.mark.asyncio
async def test_create_point_balance(db_session):
    """Test creating a point balance linked to a contract."""
    contract = Contract(
        home_resort="polynesian",
        use_year_month=6,
        annual_points=160,
        purchase_type=PurchaseType.RESALE.value,
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)

    balance = PointBalance(
        contract_id=contract.id,
        use_year=2026,
        allocation_type=PointAllocationType.CURRENT.value,
        points=160,
    )
    db_session.add(balance)
    await db_session.commit()
    await db_session.refresh(balance)

    assert balance.id is not None
    assert balance.contract_id == contract.id
    assert balance.use_year == 2026
    assert balance.allocation_type == "current"
    assert balance.points == 160


@pytest.mark.asyncio
async def test_contract_point_balance_relationship(db_session):
    """Test that the relationship between Contract and PointBalance works."""
    contract = Contract(
        home_resort="polynesian",
        use_year_month=6,
        annual_points=160,
        purchase_type=PurchaseType.RESALE.value,
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)

    balance = PointBalance(
        contract_id=contract.id,
        use_year=2026,
        allocation_type=PointAllocationType.CURRENT.value,
        points=160,
    )
    db_session.add(balance)
    await db_session.commit()

    # Use selectinload to eagerly load relationship in async context
    result = await db_session.execute(
        select(Contract)
        .options(selectinload(Contract.point_balances))
        .where(Contract.id == contract.id)
    )
    loaded_contract = result.scalar_one()
    assert len(loaded_contract.point_balances) == 1
    assert loaded_contract.point_balances[0].points == 160
    assert loaded_contract.point_balances[0].allocation_type == "current"


@pytest.mark.asyncio
async def test_cascade_delete(db_session):
    """Test that deleting a contract cascades to its point balances."""
    contract = Contract(
        home_resort="polynesian",
        use_year_month=6,
        annual_points=160,
        purchase_type=PurchaseType.RESALE.value,
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)

    balance = PointBalance(
        contract_id=contract.id,
        use_year=2026,
        allocation_type=PointAllocationType.CURRENT.value,
        points=160,
    )
    db_session.add(balance)
    await db_session.commit()

    # Reload contract with relationships for cascade delete
    result = await db_session.execute(
        select(Contract)
        .options(selectinload(Contract.point_balances))
        .where(Contract.id == contract.id)
    )
    loaded_contract = result.scalar_one()

    # Delete the contract
    await db_session.delete(loaded_contract)
    await db_session.commit()

    # Verify the point balance was also deleted
    result = await db_session.execute(select(PointBalance))
    remaining = result.scalars().all()
    assert len(remaining) == 0


def test_use_year_month_enum_valid():
    """Test that UseYearMonth enum has exactly the valid DVC months."""
    valid_months = {2, 3, 4, 6, 8, 9, 10, 12}
    enum_months = {m.value for m in UseYearMonth}
    assert enum_months == valid_months


def test_use_year_month_enum_invalid():
    """Test that invalid months are not in the UseYearMonth enum."""
    invalid_months = [1, 5, 7, 11]
    for month in invalid_months:
        with pytest.raises(ValueError):
            UseYearMonth(month)


def test_purchase_type_enum():
    """Test PurchaseType enum values."""
    assert PurchaseType.RESALE.value == "resale"
    assert PurchaseType.DIRECT.value == "direct"


def test_point_allocation_type_enum():
    """Test PointAllocationType enum values."""
    assert PointAllocationType.CURRENT.value == "current"
    assert PointAllocationType.BANKED.value == "banked"
    assert PointAllocationType.BORROWED.value == "borrowed"
    assert PointAllocationType.HOLDING.value == "holding"


# --- Reservation model tests ---


@pytest.mark.asyncio
async def test_create_reservation(db_session):
    """Test creating a Reservation linked to a Contract."""
    contract = Contract(
        home_resort="polynesian",
        use_year_month=6,
        annual_points=160,
        purchase_type=PurchaseType.RESALE.value,
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)

    reservation = Reservation(
        contract_id=contract.id,
        resort="polynesian",
        room_key="deluxe_studio_standard",
        check_in=date(2026, 3, 15),
        check_out=date(2026, 3, 20),
        points_cost=85,
        status=ReservationStatus.CONFIRMED.value,
        confirmation_number="ABC123",
        notes="Spring break trip",
    )
    db_session.add(reservation)
    await db_session.commit()
    await db_session.refresh(reservation)

    assert reservation.id is not None
    assert reservation.contract_id == contract.id
    assert reservation.resort == "polynesian"
    assert reservation.room_key == "deluxe_studio_standard"
    assert reservation.check_in == date(2026, 3, 15)
    assert reservation.check_out == date(2026, 3, 20)
    assert reservation.points_cost == 85
    assert reservation.status == "confirmed"
    assert reservation.confirmation_number == "ABC123"
    assert reservation.notes == "Spring break trip"
    assert reservation.created_at is not None
    assert reservation.updated_at is not None


@pytest.mark.asyncio
async def test_contract_reservation_relationship(db_session):
    """Test contract.reservations returns the reservation."""
    contract = Contract(
        home_resort="polynesian",
        use_year_month=6,
        annual_points=160,
        purchase_type=PurchaseType.RESALE.value,
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)

    reservation = Reservation(
        contract_id=contract.id,
        resort="polynesian",
        room_key="deluxe_studio_standard",
        check_in=date(2026, 3, 15),
        check_out=date(2026, 3, 20),
        points_cost=85,
    )
    db_session.add(reservation)
    await db_session.commit()

    result = await db_session.execute(
        select(Contract)
        .options(selectinload(Contract.reservations))
        .where(Contract.id == contract.id)
    )
    loaded_contract = result.scalar_one()
    assert len(loaded_contract.reservations) == 1
    assert loaded_contract.reservations[0].points_cost == 85
    assert loaded_contract.reservations[0].resort == "polynesian"


@pytest.mark.asyncio
async def test_reservation_cascade_delete(db_session):
    """Test that deleting a contract cascade-deletes its reservations."""
    contract = Contract(
        home_resort="polynesian",
        use_year_month=6,
        annual_points=160,
        purchase_type=PurchaseType.RESALE.value,
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)

    reservation = Reservation(
        contract_id=contract.id,
        resort="polynesian",
        room_key="deluxe_studio_standard",
        check_in=date(2026, 3, 15),
        check_out=date(2026, 3, 20),
        points_cost=85,
    )
    db_session.add(reservation)
    await db_session.commit()

    # Reload with relationships for cascade
    result = await db_session.execute(
        select(Contract)
        .options(selectinload(Contract.reservations), selectinload(Contract.point_balances))
        .where(Contract.id == contract.id)
    )
    loaded_contract = result.scalar_one()
    await db_session.delete(loaded_contract)
    await db_session.commit()

    result = await db_session.execute(select(Reservation))
    remaining = result.scalars().all()
    assert len(remaining) == 0


def test_reservation_status_enum():
    """Test ReservationStatus enum values."""
    assert ReservationStatus.CONFIRMED.value == "confirmed"
    assert ReservationStatus.PENDING.value == "pending"
    assert ReservationStatus.CANCELLED.value == "cancelled"


@pytest.mark.asyncio
async def test_multiple_reservations_for_contract(db_session):
    """Test creating multiple reservations for one contract."""
    contract = Contract(
        home_resort="polynesian",
        use_year_month=6,
        annual_points=160,
        purchase_type=PurchaseType.RESALE.value,
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)

    for i in range(3):
        reservation = Reservation(
            contract_id=contract.id,
            resort="polynesian",
            room_key="deluxe_studio_standard",
            check_in=date(2026, 3 + i, 15),
            check_out=date(2026, 3 + i, 20),
            points_cost=80 + i * 5,
        )
        db_session.add(reservation)
    await db_session.commit()

    result = await db_session.execute(
        select(Contract)
        .options(selectinload(Contract.reservations))
        .where(Contract.id == contract.id)
    )
    loaded_contract = result.scalar_one()
    assert len(loaded_contract.reservations) == 3
