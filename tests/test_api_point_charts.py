"""Tests for point chart API endpoints."""
import pytest


@pytest.mark.asyncio
async def test_list_charts(client):
    """GET /api/point-charts returns list including polynesian and riviera 2026."""
    resp = await client.get("/api/point-charts/")
    assert resp.status_code == 200
    data = resp.json()
    resorts = [(c["resort"], c["year"]) for c in data]
    assert ("polynesian", 2026) in resorts
    assert ("riviera", 2026) in resorts


@pytest.mark.asyncio
async def test_get_chart(client):
    """GET /api/point-charts/polynesian/2026 returns full chart JSON."""
    resp = await client.get("/api/point-charts/polynesian/2026")
    assert resp.status_code == 200
    data = resp.json()
    assert data["resort"] == "polynesian"
    assert data["year"] == 2026
    assert len(data["seasons"]) >= 6


@pytest.mark.asyncio
async def test_get_chart_not_found(client):
    """GET /api/point-charts/nonexistent/2026 returns 404."""
    resp = await client.get("/api/point-charts/nonexistent/2026")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_chart_rooms(client):
    """GET /api/point-charts/polynesian/2026/rooms returns parsed room list."""
    resp = await client.get("/api/point-charts/polynesian/2026/rooms")
    assert resp.status_code == 200
    data = resp.json()
    assert data["resort"] == "polynesian"
    assert data["year"] == 2026
    rooms = data["rooms"]
    assert len(rooms) > 0
    # Each room should have key, room_type, view
    for room in rooms:
        assert "key" in room
        assert "room_type" in room
        assert "view" in room
    # Check specific parsed room
    room_keys = [r["key"] for r in rooms]
    assert "deluxe_studio_standard" in room_keys
    assert "bungalow_lake" in room_keys


@pytest.mark.asyncio
async def test_get_chart_rooms_parsed_names(client):
    """Room names are parsed into human-readable room_type and view."""
    resp = await client.get("/api/point-charts/polynesian/2026/rooms")
    data = resp.json()
    rooms_by_key = {r["key"]: r for r in data["rooms"]}
    ds = rooms_by_key["deluxe_studio_standard"]
    assert ds["room_type"] == "Deluxe Studio"
    assert ds["view"] == "Standard"
    bl = rooms_by_key["bungalow_lake"]
    assert bl["room_type"] == "Bungalow"
    assert bl["view"] == "Lake"


@pytest.mark.asyncio
async def test_get_chart_seasons(client):
    """GET /api/point-charts/polynesian/2026/seasons returns season structure."""
    resp = await client.get("/api/point-charts/polynesian/2026/seasons")
    assert resp.status_code == 200
    data = resp.json()
    assert data["resort"] == "polynesian"
    assert data["year"] == 2026
    seasons = data["seasons"]
    assert len(seasons) >= 6
    # Each season has name and date_ranges, but no rooms
    for s in seasons:
        assert "name" in s
        assert "date_ranges" in s
        assert "rooms" not in s


@pytest.mark.asyncio
async def test_calculate_cost_valid(client):
    """POST /api/point-charts/calculate with valid data returns stay cost."""
    resp = await client.post("/api/point-charts/calculate", json={
        "resort": "polynesian",
        "room_key": "deluxe_studio_standard",
        "check_in": "2026-01-12",
        "check_out": "2026-01-15",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["resort"] == "polynesian"
    assert data["room"] == "deluxe_studio_standard"
    assert data["num_nights"] == 3
    # 3 weekday nights in Adventure = 3 x 14 = 42
    assert data["total_points"] == 42
    assert len(data["nightly_breakdown"]) == 3


@pytest.mark.asyncio
async def test_calculate_cost_weekday_weekend_split(client):
    """Nightly breakdown correctly distinguishes weekday vs weekend pricing."""
    # Jan 9 Fri, Jan 10 Sat, Jan 11 Sun
    resp = await client.post("/api/point-charts/calculate", json={
        "resort": "polynesian",
        "room_key": "deluxe_studio_standard",
        "check_in": "2026-01-09",
        "check_out": "2026-01-12",
    })
    assert resp.status_code == 200
    data = resp.json()
    nights = data["nightly_breakdown"]
    assert nights[0]["is_weekend"] is True   # Friday
    assert nights[0]["points"] == 19
    assert nights[1]["is_weekend"] is True   # Saturday
    assert nights[1]["points"] == 19
    assert nights[2]["is_weekend"] is False  # Sunday
    assert nights[2]["points"] == 14
    assert data["total_points"] == 52


@pytest.mark.asyncio
async def test_calculate_cost_multi_season(client):
    """Multi-season stay is calculated correctly."""
    # Jan 31 (Adventure) -> Feb 1 (Choice)
    resp = await client.post("/api/point-charts/calculate", json={
        "resort": "polynesian",
        "room_key": "deluxe_studio_standard",
        "check_in": "2026-01-31",
        "check_out": "2026-02-02",
    })
    assert resp.status_code == 200
    data = resp.json()
    nights = data["nightly_breakdown"]
    assert nights[0]["season"] == "Adventure"
    assert nights[1]["season"] == "Choice"


@pytest.mark.asyncio
async def test_calculate_cost_invalid_room(client):
    """POST /api/point-charts/calculate with invalid room returns 400."""
    resp = await client.post("/api/point-charts/calculate", json={
        "resort": "polynesian",
        "room_key": "nonexistent_room",
        "check_in": "2026-01-12",
        "check_out": "2026-01-15",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_calculate_cost_missing_chart(client):
    """POST /api/point-charts/calculate with missing chart returns 404."""
    resp = await client.post("/api/point-charts/calculate", json={
        "resort": "nonexistent",
        "room_key": "deluxe_studio_standard",
        "check_in": "2026-01-12",
        "check_out": "2026-01-15",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_calculate_cost_checkout_before_checkin(client):
    """POST /api/point-charts/calculate with checkout before checkin returns 400."""
    resp = await client.post("/api/point-charts/calculate", json={
        "resort": "polynesian",
        "room_key": "deluxe_studio_standard",
        "check_in": "2026-01-15",
        "check_out": "2026-01-12",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_calculate_cost_exceeds_max_nights(client):
    """POST /api/point-charts/calculate with >14 nights returns 400."""
    resp = await client.post("/api/point-charts/calculate", json={
        "resort": "polynesian",
        "room_key": "deluxe_studio_standard",
        "check_in": "2026-01-01",
        "check_out": "2026-01-20",
    })
    assert resp.status_code == 400
