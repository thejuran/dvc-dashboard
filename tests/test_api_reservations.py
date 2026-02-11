import pytest


VALID_CONTRACT = {
    "home_resort": "polynesian",
    "use_year_month": 6,
    "annual_points": 160,
    "purchase_type": "resale",
    "name": "Poly Contract",
}

VALID_RESERVATION = {
    "resort": "polynesian",
    "room_key": "deluxe_studio_standard",
    "check_in": "2026-03-15",
    "check_out": "2026-03-20",
    "points_cost": 85,
}


async def _create_contract(client, **overrides):
    """Helper to create a contract and return its id."""
    payload = {**VALID_CONTRACT, **overrides}
    resp = await client.post("/api/contracts/", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_reservation(client, contract_id, **overrides):
    """Helper to create a reservation and return the response data."""
    payload = {**VALID_RESERVATION, **overrides}
    resp = await client.post(f"/api/contracts/{contract_id}/reservations", json=payload)
    return resp


# --- CRUD tests ---


@pytest.mark.asyncio
async def test_create_reservation(client):
    """POST reservation with valid data -> 201, returns reservation."""
    cid = await _create_contract(client)
    resp = await _create_reservation(client, cid)
    assert resp.status_code == 201
    data = resp.json()
    assert data["contract_id"] == cid
    assert data["resort"] == "polynesian"
    assert data["room_key"] == "deluxe_studio_standard"
    assert data["check_in"] == "2026-03-15"
    assert data["check_out"] == "2026-03-20"
    assert data["points_cost"] == 85
    assert data["status"] == "confirmed"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_reservation_nonexistent_contract(client):
    """POST reservation for non-existent contract -> 404."""
    payload = {**VALID_RESERVATION}
    resp = await client.post("/api/contracts/999/reservations", json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_reservation_ineligible_resort(client):
    """POST reservation at ineligible resort (resale + restricted) -> 422."""
    # Resale at polynesian cannot book at riviera
    cid = await _create_contract(client)
    resp = await _create_reservation(client, cid, resort="riviera")
    assert resp.status_code == 422
    assert "not eligible" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_reservation_checkout_before_checkin(client):
    """POST reservation with check_out before check_in -> 422."""
    cid = await _create_contract(client)
    resp = await _create_reservation(
        client, cid, check_in="2026-03-20", check_out="2026-03-15"
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_reservation_exceeds_14_nights(client):
    """POST reservation exceeding 14 nights -> 422."""
    cid = await _create_contract(client)
    resp = await _create_reservation(
        client, cid, check_in="2026-03-01", check_out="2026-03-20"
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_all_reservations(client):
    """GET /api/reservations -> returns list."""
    cid = await _create_contract(client)
    await _create_reservation(client, cid)
    await _create_reservation(client, cid, check_in="2026-04-10", check_out="2026-04-15", points_cost=90)

    resp = await client.get("/api/reservations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_reservations_filter_by_contract(client):
    """GET /api/reservations?contract_id=X -> filtered."""
    cid1 = await _create_contract(client)
    cid2 = await _create_contract(client, name="Second")
    await _create_reservation(client, cid1)
    await _create_reservation(client, cid2, check_in="2026-04-10", check_out="2026-04-15")

    resp = await client.get(f"/api/reservations?contract_id={cid1}")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["contract_id"] == cid1


@pytest.mark.asyncio
async def test_list_reservations_filter_by_status(client):
    """GET /api/reservations?status=confirmed -> filtered."""
    cid = await _create_contract(client)
    await _create_reservation(client, cid)
    await _create_reservation(
        client, cid, check_in="2026-04-10", check_out="2026-04-15", status="pending"
    )

    resp = await client.get("/api/reservations?status=confirmed")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "confirmed"


@pytest.mark.asyncio
async def test_list_contract_reservations(client):
    """GET /api/contracts/{id}/reservations -> returns contract's reservations."""
    cid = await _create_contract(client)
    await _create_reservation(client, cid)

    resp = await client.get(f"/api/contracts/{cid}/reservations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["contract_id"] == cid


@pytest.mark.asyncio
async def test_get_single_reservation(client):
    """GET /api/reservations/{id} -> returns single reservation."""
    cid = await _create_contract(client)
    create_resp = await _create_reservation(client, cid)
    rid = create_resp.json()["id"]

    resp = await client.get(f"/api/reservations/{rid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == rid


@pytest.mark.asyncio
async def test_update_reservation(client):
    """PUT updates specified fields only."""
    cid = await _create_contract(client)
    create_resp = await _create_reservation(client, cid)
    rid = create_resp.json()["id"]

    resp = await client.put(f"/api/reservations/{rid}", json={"points_cost": 100})
    assert resp.status_code == 200
    data = resp.json()
    assert data["points_cost"] == 100
    assert data["resort"] == "polynesian"  # unchanged


@pytest.mark.asyncio
async def test_update_reservation_status_to_cancelled(client):
    """PUT status to cancelled."""
    cid = await _create_contract(client)
    create_resp = await _create_reservation(client, cid)
    rid = create_resp.json()["id"]

    resp = await client.put(f"/api/reservations/{rid}", json={"status": "cancelled"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_delete_reservation(client):
    """DELETE -> 204, subsequent GET returns 404."""
    cid = await _create_contract(client)
    create_resp = await _create_reservation(client, cid)
    rid = create_resp.json()["id"]

    resp = await client.delete(f"/api/reservations/{rid}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/reservations/{rid}")
    assert resp.status_code == 404


# --- Edge cases ---


@pytest.mark.asyncio
async def test_resale_at_home_resort_allowed(client):
    """Resale contract at restricted resort can book at its own home resort."""
    cid = await _create_contract(client, home_resort="riviera")
    resp = await _create_reservation(client, cid, resort="riviera")
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_resale_at_original_14_allowed(client):
    """Resale contract at original resort can book other original-14 resorts."""
    cid = await _create_contract(client, home_resort="polynesian")
    resp = await _create_reservation(client, cid, resort="bay_lake_tower")
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_multiple_reservations_for_same_contract(client):
    """Multiple reservations for same contract all returned."""
    cid = await _create_contract(client)
    await _create_reservation(client, cid)
    await _create_reservation(client, cid, check_in="2026-04-10", check_out="2026-04-15")
    await _create_reservation(client, cid, check_in="2026-05-01", check_out="2026-05-05")

    resp = await client.get(f"/api/contracts/{cid}/reservations")
    assert len(resp.json()) == 3


# --- Preview endpoint tests ---


async def _create_contract_with_balance(client, **overrides):
    """Helper: create contract + point balance, return contract_id."""
    cid = await _create_contract(client, **overrides)
    # Add point balance for UY 2025 (June UY covers Jan-May 2026)
    balance_payload = {
        "use_year": 2025,
        "allocation_type": "current",
        "points": overrides.get("annual_points", 160),
    }
    resp = await client.post(f"/api/contracts/{cid}/points", json=balance_payload)
    assert resp.status_code == 201
    return cid


@pytest.mark.asyncio
async def test_preview_valid_contract(client):
    """POST /api/reservations/preview with valid data -> 200 with before/after/booking_windows."""
    cid = await _create_contract_with_balance(client)

    # Use dates in Jan 2026, Adventure season for polynesian
    # deluxe_studio_standard weekday=14, weekend=19
    resp = await client.post("/api/reservations/preview", json={
        "contract_id": cid,
        "resort": "polynesian",
        "room_key": "deluxe_studio_standard",
        "check_in": "2026-01-12",  # Monday
        "check_out": "2026-01-15",  # Thursday -> 3 weekday nights
    })
    assert resp.status_code == 200
    data = resp.json()

    # Check top-level structure
    assert "before" in data
    assert "after" in data
    assert "points_delta" in data
    assert "nightly_breakdown" in data
    assert "total_points" in data
    assert "num_nights" in data
    assert "booking_windows" in data

    # Check before/after
    assert data["before"]["available_points"] > data["after"]["available_points"]
    assert data["points_delta"] == data["total_points"]
    assert data["num_nights"] == 3

    # Check booking windows has all fields
    bw = data["booking_windows"]
    assert "home_resort_window" in bw
    assert "home_resort_window_open" in bw
    assert "days_until_home_window" in bw
    assert "any_resort_window" in bw
    assert "any_resort_window_open" in bw
    assert "days_until_any_window" in bw
    assert "is_home_resort" in bw
    # polynesian is the home resort for this contract
    assert bw["is_home_resort"] is True


@pytest.mark.asyncio
async def test_preview_invalid_contract(client):
    """POST /api/reservations/preview with invalid contract_id -> 404."""
    resp = await client.post("/api/reservations/preview", json={
        "contract_id": 999,
        "resort": "polynesian",
        "room_key": "deluxe_studio_standard",
        "check_in": "2026-01-12",
        "check_out": "2026-01-15",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_preview_no_point_chart(client):
    """POST /api/reservations/preview with resort that has no point chart -> 422."""
    cid = await _create_contract_with_balance(
        client, home_resort="bay_lake_tower", purchase_type="direct"
    )

    resp = await client.post("/api/reservations/preview", json={
        "contract_id": cid,
        "resort": "bay_lake_tower",
        "room_key": "deluxe_studio",
        "check_in": "2026-01-12",
        "check_out": "2026-01-15",
    })
    assert resp.status_code == 422
    assert "point chart" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_preview_nightly_breakdown_count(client):
    """Preview nightly_breakdown has correct number of nights."""
    cid = await _create_contract_with_balance(client)

    resp = await client.post("/api/reservations/preview", json={
        "contract_id": cid,
        "resort": "polynesian",
        "room_key": "deluxe_studio_standard",
        "check_in": "2026-01-12",
        "check_out": "2026-01-16",  # 4 nights
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nightly_breakdown"]) == 4
    assert data["num_nights"] == 4


@pytest.mark.asyncio
async def test_preview_booking_windows_fields(client):
    """Preview booking_windows has all expected fields with correct types."""
    cid = await _create_contract_with_balance(client)

    resp = await client.post("/api/reservations/preview", json={
        "contract_id": cid,
        "resort": "polynesian",
        "room_key": "deluxe_studio_standard",
        "check_in": "2026-01-12",
        "check_out": "2026-01-15",
    })
    assert resp.status_code == 200
    bw = resp.json()["booking_windows"]

    # Verify types
    assert isinstance(bw["home_resort_window"], str)
    assert isinstance(bw["home_resort_window_open"], bool)
    assert isinstance(bw["days_until_home_window"], int)
    assert isinstance(bw["any_resort_window"], str)
    assert isinstance(bw["any_resort_window_open"], bool)
    assert isinstance(bw["days_until_any_window"], int)
    assert isinstance(bw["is_home_resort"], bool)
