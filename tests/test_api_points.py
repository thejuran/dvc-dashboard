from datetime import date

import pytest

from backend.engine.use_year import (
    build_use_year_timeline,
    get_banking_deadline,
    get_current_use_year,
    get_use_year_status,
)

VALID_CONTRACT = {
    "home_resort": "polynesian",
    "use_year_month": 6,
    "annual_points": 160,
    "purchase_type": "resale",
    "name": "Poly Contract",
}


async def _create_contract(client, contract_data=None):
    """Helper to create a contract and return its id."""
    data = contract_data or VALID_CONTRACT
    resp = await client.post("/api/contracts/", json=data)
    assert resp.status_code == 201
    return resp.json()["id"]


# --- Point Balance CRUD Tests ---


@pytest.mark.asyncio
async def test_create_point_balance(client):
    """POST point balance -> 201, returns balance."""
    contract_id = await _create_contract(client)
    resp = await client.post(
        f"/api/contracts/{contract_id}/points",
        json={"use_year": 2026, "allocation_type": "current", "points": 160},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["contract_id"] == contract_id
    assert data["use_year"] == 2026
    assert data["allocation_type"] == "current"
    assert data["points"] == 160


@pytest.mark.asyncio
async def test_get_contract_points_grouped(client):
    """GET /api/contracts/{id}/points -> returns grouped balances with correct totals."""
    contract_id = await _create_contract(client)

    # Add multiple balance entries
    await client.post(
        f"/api/contracts/{contract_id}/points",
        json={"use_year": 2026, "allocation_type": "current", "points": 160},
    )
    await client.post(
        f"/api/contracts/{contract_id}/points",
        json={"use_year": 2025, "allocation_type": "banked", "points": 45},
    )
    await client.post(
        f"/api/contracts/{contract_id}/points",
        json={"use_year": 2026, "allocation_type": "borrowed", "points": 30},
    )

    resp = await client.get(f"/api/contracts/{contract_id}/points")
    assert resp.status_code == 200
    data = resp.json()

    assert data["contract_id"] == contract_id
    assert data["annual_points"] == 160

    # Check 2025 balances
    assert "2025" in data["balances_by_year"]
    year_2025 = data["balances_by_year"]["2025"]
    assert year_2025["banked"] == 45
    assert year_2025["total"] == 45

    # Check 2026 balances
    assert "2026" in data["balances_by_year"]
    year_2026 = data["balances_by_year"]["2026"]
    assert year_2026["current"] == 160
    assert year_2026["borrowed"] == 30
    assert year_2026["total"] == 190

    # Grand total
    assert data["grand_total"] == 235


@pytest.mark.asyncio
async def test_duplicate_point_balance_returns_409(client):
    """POST duplicate (same contract + use_year + allocation_type) -> 409."""
    contract_id = await _create_contract(client)

    resp1 = await client.post(
        f"/api/contracts/{contract_id}/points",
        json={"use_year": 2026, "allocation_type": "current", "points": 160},
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        f"/api/contracts/{contract_id}/points",
        json={"use_year": 2026, "allocation_type": "current", "points": 100},
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_update_point_balance(client):
    """PUT updates the points value."""
    contract_id = await _create_contract(client)
    create_resp = await client.post(
        f"/api/contracts/{contract_id}/points",
        json={"use_year": 2026, "allocation_type": "current", "points": 160},
    )
    balance_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/points/{balance_id}",
        json={"points": 100},
    )
    assert resp.status_code == 200
    assert resp.json()["points"] == 100


@pytest.mark.asyncio
async def test_delete_point_balance(client):
    """DELETE removes the balance entry."""
    contract_id = await _create_contract(client)
    create_resp = await client.post(
        f"/api/contracts/{contract_id}/points",
        json={"use_year": 2026, "allocation_type": "current", "points": 160},
    )
    balance_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/points/{balance_id}")
    assert resp.status_code == 204

    # Verify it's gone
    resp = await client.get(f"/api/contracts/{contract_id}/points")
    data = resp.json()
    assert data["grand_total"] == 0


@pytest.mark.asyncio
async def test_create_point_balance_nonexistent_contract(client):
    """POST point balance for non-existent contract -> 404."""
    resp = await client.post(
        "/api/contracts/9999/points",
        json={"use_year": 2026, "allocation_type": "current", "points": 160},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_banked_points_cannot_exceed_annual(client):
    """Banked points exceeding annual_points -> 422."""
    contract_id = await _create_contract(client)
    resp = await client.post(
        f"/api/contracts/{contract_id}/points",
        json={"use_year": 2026, "allocation_type": "banked", "points": 200},
    )
    assert resp.status_code == 422


# --- Timeline Tests ---


@pytest.mark.asyncio
async def test_get_contract_timeline(client):
    """GET /api/contracts/{id}/timeline -> returns timeline with correct structure."""
    contract_id = await _create_contract(client)
    resp = await client.get(f"/api/contracts/{contract_id}/timeline")
    assert resp.status_code == 200
    data = resp.json()

    assert data["contract_id"] == contract_id
    assert data["use_year_month"] == 6
    assert len(data["timelines"]) == 2

    # First timeline is current UY, second is next
    current_tl = data["timelines"][0]
    next_tl = data["timelines"][1]

    assert "start" in current_tl
    assert "end" in current_tl
    assert "banking_deadline" in current_tl
    assert "status" in current_tl
    assert current_tl["status"] in ("active", "expired", "upcoming")
    assert next_tl["use_year"] == current_tl["use_year"] + 1


# --- Use Year Engine Unit Tests ---


def test_june_use_year_banking_deadline_is_january_31():
    """June UY banking deadline is January 31 of the following year."""
    deadline = get_banking_deadline(6, 2026)
    assert deadline == date(2027, 1, 31)


def test_december_use_year_banking_deadline_is_july_31():
    """December UY banking deadline is July 31 of the following year."""
    deadline = get_banking_deadline(12, 2025)
    assert deadline == date(2026, 7, 31)


def test_get_current_use_year_after_uy_start():
    """If today is after UY start month, current UY is this year."""
    # June UY, as_of=August 2026 -> current UY is 2026
    result = get_current_use_year(6, as_of=date(2026, 8, 15))
    assert result == 2026


def test_get_current_use_year_before_uy_start():
    """If today is before UY start month, current UY is last year."""
    # June UY, as_of=March 2026 -> current UY is 2025
    result = get_current_use_year(6, as_of=date(2026, 3, 15))
    assert result == 2025


def test_status_active_for_current_uy():
    """Active status for a use year that is currently running."""
    # June 2026 UY, as_of=August 2026 -> active (between Jun 1 2026 and May 31 2027)
    status = get_use_year_status(6, 2026, as_of=date(2026, 8, 15))
    assert status == "active"


def test_status_upcoming_for_next_uy():
    """Upcoming status for a use year that hasn't started yet."""
    # June 2027 UY, as_of=March 2027 -> upcoming (hasn't started)
    status = get_use_year_status(6, 2027, as_of=date(2027, 3, 15))
    assert status == "upcoming"


def test_status_expired_for_past_uy():
    """Expired status for a use year that has ended."""
    # June 2024 UY (ends May 31 2025), as_of=June 2025 -> expired
    status = get_use_year_status(6, 2024, as_of=date(2025, 6, 1))
    assert status == "expired"


def test_build_use_year_timeline_structure():
    """build_use_year_timeline returns all expected fields."""
    tl = build_use_year_timeline(6, 2026, as_of=date(2026, 8, 15))
    assert tl["use_year"] == 2026
    assert tl["label"] == "2026 Use Year"
    assert tl["start"] == "2026-06-01"
    assert tl["end"] == "2027-05-31"
    assert tl["banking_deadline"] == "2027-01-31"
    assert tl["point_expiration"] == "2027-05-31"
    assert tl["status"] == "active"
    assert isinstance(tl["banking_deadline_passed"], bool)
    assert isinstance(tl["days_until_banking_deadline"], int)
    assert isinstance(tl["days_until_expiration"], int)
