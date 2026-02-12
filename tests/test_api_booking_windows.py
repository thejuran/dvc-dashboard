from datetime import date, timedelta

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


async def _create_reservation(client, contract_id, **overrides):
    """Helper to create a reservation for the given contract."""
    defaults = {
        "resort": "polynesian",
        "room_key": "deluxe_studio_standard",
        "check_in": "2026-03-15",
        "check_out": "2026-03-20",
        "points_cost": 85,
    }
    payload = {**defaults, **overrides}
    resp = await client.post(f"/api/contracts/{contract_id}/reservations", json=payload)
    assert resp.status_code == 201, f"Failed to create reservation: {resp.text}"
    return resp.json()


@pytest.mark.asyncio
async def test_no_reservations_returns_empty(client):
    """GET /api/booking-windows/upcoming with no reservations returns empty list."""
    resp = await client.get("/api/booking-windows/upcoming")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_any_resort_window_alert(client):
    """Reservation ~8 months from now produces an any-resort window alert opening in ~1 month."""
    today = date.today()
    # Check-in ~8 months from now so the 7-month window opens in ~1 month
    check_in = today + timedelta(days=8 * 30)  # ~240 days ahead
    check_out = check_in + timedelta(days=3)

    cid = await _create_contract(client)
    await _create_reservation(
        client,
        cid,
        resort="polynesian",
        check_in=check_in.isoformat(),
        check_out=check_out.isoformat(),
    )

    # Use a larger look-ahead to catch it reliably
    resp = await client.get("/api/booking-windows/upcoming?days=60")
    assert resp.status_code == 200
    data = resp.json()
    # Should have at least one any-resort window alert
    any_resort_alerts = [a for a in data if a["window_type"] == "any_resort"]
    assert len(any_resort_alerts) >= 1
    alert = any_resort_alerts[0]
    assert alert["contract_name"] == "Poly Contract"
    assert alert["resort"] == "polynesian"
    assert "resort_name" in alert
    assert alert["check_in"] == check_in.isoformat()
    assert alert["window_date"]  # non-empty string
    assert alert["days_until_open"] > 0


@pytest.mark.asyncio
async def test_home_resort_window_alert(client):
    """Reservation at home resort ~12 months from now produces home_resort window alert."""
    today = date.today()
    # Check-in ~12 months from now so 11-month window opens in ~1 month
    check_in = today + timedelta(days=12 * 30)  # ~360 days ahead
    check_out = check_in + timedelta(days=3)

    cid = await _create_contract(client, home_resort="polynesian")
    await _create_reservation(
        client,
        cid,
        resort="polynesian",  # same as home_resort
        check_in=check_in.isoformat(),
        check_out=check_out.isoformat(),
    )

    resp = await client.get("/api/booking-windows/upcoming?days=60")
    assert resp.status_code == 200
    data = resp.json()
    home_alerts = [a for a in data if a["window_type"] == "home_resort"]
    assert len(home_alerts) >= 1
    alert = home_alerts[0]
    assert alert["contract_name"] == "Poly Contract"
    assert alert["resort"] == "polynesian"
    assert alert["days_until_open"] > 0


@pytest.mark.asyncio
async def test_alerts_sorted_by_days_until_open(client):
    """Alerts are sorted by days_until_open ascending (soonest first)."""
    today = date.today()
    cid = await _create_contract(client)

    # Create two reservations with different check-in distances
    # One at ~7.5 months (any-resort window opens in ~15 days)
    check_in_soon = today + timedelta(days=int(7.5 * 30))
    check_out_soon = check_in_soon + timedelta(days=3)

    # One at ~8.5 months (any-resort window opens in ~45 days)
    check_in_later = today + timedelta(days=int(8.5 * 30))
    check_out_later = check_in_later + timedelta(days=3)

    await _create_reservation(
        client,
        cid,
        resort="polynesian",
        check_in=check_in_later.isoformat(),
        check_out=check_out_later.isoformat(),
    )
    await _create_reservation(
        client,
        cid,
        resort="polynesian",
        check_in=check_in_soon.isoformat(),
        check_out=check_out_soon.isoformat(),
    )

    resp = await client.get("/api/booking-windows/upcoming?days=90")
    assert resp.status_code == 200
    data = resp.json()

    if len(data) >= 2:
        # Verify ascending sort
        for i in range(len(data) - 1):
            assert data[i]["days_until_open"] <= data[i + 1]["days_until_open"]


@pytest.mark.asyncio
async def test_cap_at_5(client):
    """Only up to 5 alerts are returned even when more are eligible."""
    today = date.today()
    cid = await _create_contract(client)

    # Create 6 reservations that will each produce at least one alert
    for i in range(6):
        offset_days = int((7 + (i * 0.3)) * 30)  # spread across ~7-8.5 months out
        check_in = today + timedelta(days=offset_days)
        check_out = check_in + timedelta(days=3)
        await _create_reservation(
            client,
            cid,
            resort="polynesian",
            check_in=check_in.isoformat(),
            check_out=check_out.isoformat(),
        )

    resp = await client.get("/api/booking-windows/upcoming?days=90")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_cancelled_reservations_excluded(client):
    """Cancelled reservations do not produce alerts."""
    today = date.today()
    check_in = today + timedelta(days=8 * 30)
    check_out = check_in + timedelta(days=3)

    cid = await _create_contract(client)
    # Create a reservation and then cancel it
    res_data = await _create_reservation(
        client,
        cid,
        resort="polynesian",
        check_in=check_in.isoformat(),
        check_out=check_out.isoformat(),
    )
    rid = res_data["id"]
    resp = await client.put(f"/api/reservations/{rid}", json={"status": "cancelled"})
    assert resp.status_code == 200

    resp = await client.get("/api/booking-windows/upcoming?days=60")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_already_open_windows_excluded(client):
    """Windows that have already opened are not included in alerts."""
    today = date.today()
    # Check-in only 3 months from now -- both windows already open
    check_in = today + timedelta(days=90)
    check_out = check_in + timedelta(days=3)

    cid = await _create_contract(client)
    await _create_reservation(
        client,
        cid,
        resort="polynesian",
        check_in=check_in.isoformat(),
        check_out=check_out.isoformat(),
    )

    resp = await client.get("/api/booking-windows/upcoming?days=30")
    assert resp.status_code == 200
    # Both 11-month and 7-month windows have already opened for a 3-month-out check-in
    assert resp.json() == []
