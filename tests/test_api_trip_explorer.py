"""Trip Explorer API integration tests.

Tests the /api/trip-explorer endpoint for valid queries, validation errors,
and edge cases (empty DB, checkout before checkin, >14 nights).
"""

import pytest

VALID_CONTRACT = {
    "home_resort": "polynesian",
    "use_year_month": 6,
    "annual_points": 160,
    "purchase_type": "resale",
    "name": "Poly Contract",
}


async def _create_contract(client, **overrides):
    """Helper to create a contract and return its id."""
    payload = {**VALID_CONTRACT, **overrides}
    resp = await client.post("/api/contracts/", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_contract_with_balance(client, **overrides):
    """Helper: create contract + point balance, return contract_id."""
    cid = await _create_contract(client, **overrides)
    balance_payload = {
        "use_year": 2025,
        "allocation_type": "current",
        "points": overrides.get("annual_points", 160),
    }
    resp = await client.post(f"/api/contracts/{cid}/points", json=balance_payload)
    assert resp.status_code == 201
    return cid


@pytest.mark.asyncio
async def test_trip_explorer_valid_dates(client):
    """GET /api/trip-explorer with valid dates -> 200 with options."""
    await _create_contract_with_balance(client)

    resp = await client.get("/api/trip-explorer?check_in=2026-01-12&check_out=2026-01-14")
    assert resp.status_code == 200
    data = resp.json()
    assert "options" in data
    assert "num_nights" in data
    assert data["num_nights"] == 2
    assert "resorts_checked" in data
    assert "total_options" in data


@pytest.mark.asyncio
async def test_trip_explorer_checkout_before_checkin(client):
    """GET with check_out before check_in -> 422 with structured error."""
    resp = await client.get("/api/trip-explorer?check_in=2026-01-15&check_out=2026-01-12")
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["type"] == "VALIDATION_ERROR"
    field_names = [f["field"] for f in body["error"]["fields"]]
    assert "check_out" in field_names


@pytest.mark.asyncio
async def test_trip_explorer_over_14_nights(client):
    """GET with stay > 14 nights -> 422 with structured error."""
    resp = await client.get("/api/trip-explorer?check_in=2026-01-01&check_out=2026-01-20")
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["type"] == "VALIDATION_ERROR"
    field_names = [f["field"] for f in body["error"]["fields"]]
    assert "check_out" in field_names


@pytest.mark.asyncio
async def test_trip_explorer_no_contracts(client):
    """GET with empty DB -> 200 with empty options."""
    resp = await client.get("/api/trip-explorer?check_in=2026-01-12&check_out=2026-01-14")
    assert resp.status_code == 200
    data = resp.json()
    assert data["options"] == []
    assert data["total_options"] == 0


@pytest.mark.asyncio
async def test_trip_explorer_missing_dates(client):
    """GET without query params -> 422 with structured error."""
    resp = await client.get("/api/trip-explorer")
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["type"] == "VALIDATION_ERROR"
    assert len(body["error"]["fields"]) > 0
