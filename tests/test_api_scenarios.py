import pytest

VALID_CONTRACT = {
    "home_resort": "polynesian",
    "use_year_month": 6,
    "annual_points": 200,
    "purchase_type": "direct",
    "name": "Poly Direct",
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
        "points": overrides.get("annual_points", 200),
    }
    resp = await client.post(f"/api/contracts/{cid}/points", json=balance_payload)
    assert resp.status_code == 201
    return cid


# --- Scenario evaluation endpoint tests ---


@pytest.mark.asyncio
async def test_evaluate_valid_hypothetical(client):
    """POST /api/scenarios/evaluate with valid booking -> 200 with full response."""
    cid = await _create_contract_with_balance(client)

    resp = await client.post(
        "/api/scenarios/evaluate",
        json={
            "hypothetical_bookings": [
                {
                    "contract_id": cid,
                    "resort": "polynesian",
                    "room_key": "deluxe_studio_standard",
                    "check_in": "2026-01-12",
                    "check_out": "2026-01-15",
                }
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    # Top-level structure
    assert "contracts" in data
    assert "summary" in data
    assert "resolved_bookings" in data
    assert "errors" in data

    # Contract results
    assert len(data["contracts"]) == 1
    cr = data["contracts"][0]
    assert cr["contract_id"] == cid
    assert cr["baseline_available"] > cr["scenario_available"]
    assert cr["impact"] > 0

    # Summary
    assert data["summary"]["total_impact"] > 0
    assert data["summary"]["num_hypothetical_bookings"] == 1

    # Resolved bookings
    assert len(data["resolved_bookings"]) == 1
    rb = data["resolved_bookings"][0]
    assert rb["contract_id"] == cid
    assert rb["resort"] == "polynesian"
    assert rb["points_cost"] > 0
    assert rb["num_nights"] == 3

    # No errors
    assert len(data["errors"]) == 0


@pytest.mark.asyncio
async def test_evaluate_empty_bookings(client):
    """POST /api/scenarios/evaluate with empty list -> 200, zero impact."""
    await _create_contract_with_balance(client)

    resp = await client.post(
        "/api/scenarios/evaluate",
        json={
            "hypothetical_bookings": [],
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["summary"]["total_impact"] == 0
    assert data["summary"]["baseline_available"] == data["summary"]["scenario_available"]
    assert len(data["resolved_bookings"]) == 0
    assert len(data["errors"]) == 0


@pytest.mark.asyncio
async def test_evaluate_ineligible_resort(client):
    """POST with ineligible resort (resale contract + restricted resort) -> 422."""
    # Resale at polynesian (original 14) can book other original 14 but NOT riviera
    cid = await _create_contract_with_balance(client, purchase_type="resale")

    resp = await client.post(
        "/api/scenarios/evaluate",
        json={
            "hypothetical_bookings": [
                {
                    "contract_id": cid,
                    "resort": "riviera",
                    "room_key": "tower_studio",
                    "check_in": "2026-01-12",
                    "check_out": "2026-01-15",
                }
            ],
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["type"] == "VALIDATION_ERROR"
    assert "not eligible" in body["error"]["fields"][0]["issue"].lower()


@pytest.mark.asyncio
async def test_evaluate_missing_contract(client):
    """POST with non-existent contract_id -> 422 with structured error."""
    # Create at least one contract so we don't get the empty-contracts shortcut
    await _create_contract_with_balance(client)

    resp = await client.post(
        "/api/scenarios/evaluate",
        json={
            "hypothetical_bookings": [
                {
                    "contract_id": 999,
                    "resort": "polynesian",
                    "room_key": "deluxe_studio_standard",
                    "check_in": "2026-01-12",
                    "check_out": "2026-01-15",
                }
            ],
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["type"] == "VALIDATION_ERROR"
    field_names = [f["field"] for f in body["error"]["fields"]]
    assert "hypothetical_bookings[0].contract_id" in field_names


@pytest.mark.asyncio
async def test_evaluate_checkout_before_checkin(client):
    """POST with check_out before check_in -> 422 with structured error."""
    cid = await _create_contract_with_balance(client)

    resp = await client.post(
        "/api/scenarios/evaluate",
        json={
            "hypothetical_bookings": [
                {
                    "contract_id": cid,
                    "resort": "polynesian",
                    "room_key": "deluxe_studio_standard",
                    "check_in": "2026-01-15",
                    "check_out": "2026-01-12",
                }
            ],
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["type"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_evaluate_multiple_bookings_cumulative(client):
    """POST with multiple bookings -> cumulative impact in summary."""
    cid = await _create_contract_with_balance(client)

    resp = await client.post(
        "/api/scenarios/evaluate",
        json={
            "hypothetical_bookings": [
                {
                    "contract_id": cid,
                    "resort": "polynesian",
                    "room_key": "deluxe_studio_standard",
                    "check_in": "2026-01-12",
                    "check_out": "2026-01-15",
                },
                {
                    "contract_id": cid,
                    "resort": "polynesian",
                    "room_key": "deluxe_studio_standard",
                    "check_in": "2026-01-19",
                    "check_out": "2026-01-22",
                },
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    # Both bookings resolved
    assert len(data["resolved_bookings"]) == 2
    assert data["summary"]["num_hypothetical_bookings"] == 2

    # Cumulative impact: total_impact = sum of both costs
    total_cost = sum(rb["points_cost"] for rb in data["resolved_bookings"])
    assert data["summary"]["total_impact"] == total_cost
    assert data["summary"]["total_impact"] > 0


@pytest.mark.asyncio
async def test_evaluate_no_contracts(client):
    """POST when no contracts exist -> 200 with empty results."""
    resp = await client.post(
        "/api/scenarios/evaluate",
        json={
            "hypothetical_bookings": [],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["contracts"] == []
    assert data["summary"]["total_impact"] == 0


@pytest.mark.asyncio
async def test_evaluate_empty_scenario(client):
    """POST with empty bookings list and existing contracts -> 200, zero impact."""
    await _create_contract_with_balance(client)
    resp = await client.post(
        "/api/scenarios/evaluate",
        json={
            "hypothetical_bookings": [],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_impact"] == 0
    assert data["summary"]["baseline_available"] == data["summary"]["scenario_available"]
    assert len(data["resolved_bookings"]) == 0


@pytest.mark.asyncio
async def test_evaluate_ineligible_resort_structured(client):
    """POST with ineligible resort -> 422 with field detail."""
    cid = await _create_contract_with_balance(client, purchase_type="resale")
    resp = await client.post(
        "/api/scenarios/evaluate",
        json={
            "hypothetical_bookings": [
                {
                    "contract_id": cid,
                    "resort": "riviera",
                    "room_key": "tower_studio",
                    "check_in": "2026-01-12",
                    "check_out": "2026-01-15",
                }
            ],
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["type"] == "VALIDATION_ERROR"
    field_names = [f["field"] for f in body["error"]["fields"]]
    assert "hypothetical_bookings[0].resort" in field_names
