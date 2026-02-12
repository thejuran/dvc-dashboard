import pytest

VALID_CONTRACT = {
    "home_resort": "polynesian",
    "use_year_month": 6,
    "annual_points": 160,
    "purchase_type": "resale",
    "name": "Poly Contract",
}


@pytest.mark.asyncio
async def test_create_contract(client):
    """POST /api/contracts with valid data -> 201, returns contract."""
    resp = await client.post("/api/contracts/", json=VALID_CONTRACT)
    assert resp.status_code == 201
    data = resp.json()
    assert data["home_resort"] == "polynesian"
    assert data["use_year_month"] == 6
    assert data["annual_points"] == 160
    assert data["purchase_type"] == "resale"
    assert data["name"] == "Poly Contract"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_contract_invalid_use_year_month(client):
    """POST /api/contracts with invalid use_year_month (5) -> 422."""
    payload = {**VALID_CONTRACT, "use_year_month": 5}
    resp = await client.post("/api/contracts/", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_contract_invalid_resort(client):
    """POST /api/contracts with invalid resort slug -> 422."""
    payload = {**VALID_CONTRACT, "home_resort": "nonexistent_resort"}
    resp = await client.post("/api/contracts/", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_contracts(client):
    """GET /api/contracts -> returns list including created contract."""
    await client.post("/api/contracts/", json=VALID_CONTRACT)
    resp = await client.get("/api/contracts/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    contract = data[0]
    assert contract["home_resort"] == "polynesian"
    assert "eligible_resorts" in contract
    assert "use_year_timeline" in contract
    assert "point_balances" in contract


@pytest.mark.asyncio
async def test_get_contract_by_id(client):
    """GET /api/contracts/{id} -> returns contract with details."""
    create_resp = await client.post("/api/contracts/", json=VALID_CONTRACT)
    contract_id = create_resp.json()["id"]

    resp = await client.get(f"/api/contracts/{contract_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == contract_id
    assert "point_balances" in data
    assert "eligible_resorts" in data
    assert "use_year_timeline" in data
    # Resale at polynesian -> 14 original resorts
    assert len(data["eligible_resorts"]) == 14


@pytest.mark.asyncio
async def test_update_contract(client):
    """PUT /api/contracts/{id} -> updates specified fields only."""
    create_resp = await client.post("/api/contracts/", json=VALID_CONTRACT)
    contract_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/contracts/{contract_id}",
        json={"annual_points": 200},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["annual_points"] == 200
    # Other fields unchanged
    assert data["home_resort"] == "polynesian"
    assert data["name"] == "Poly Contract"


@pytest.mark.asyncio
async def test_delete_contract(client):
    """DELETE /api/contracts/{id} -> 204."""
    create_resp = await client.post("/api/contracts/", json=VALID_CONTRACT)
    contract_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/contracts/{contract_id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_get_deleted_contract_returns_404(client):
    """GET /api/contracts/{deleted_id} -> 404."""
    create_resp = await client.post("/api/contracts/", json=VALID_CONTRACT)
    contract_id = create_resp.json()["id"]

    await client.delete(f"/api/contracts/{contract_id}")

    resp = await client.get(f"/api/contracts/{contract_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_direct_contract_gets_all_resorts(client):
    """Direct purchase contract should have all 17 resorts as eligible."""
    payload = {**VALID_CONTRACT, "purchase_type": "direct"}
    create_resp = await client.post("/api/contracts/", json=payload)
    contract_id = create_resp.json()["id"]

    resp = await client.get(f"/api/contracts/{contract_id}")
    data = resp.json()
    assert len(data["eligible_resorts"]) == 17


@pytest.mark.asyncio
async def test_resale_restricted_resort_gets_only_home(client):
    """Resale at restricted resort should only have home resort as eligible."""
    payload = {**VALID_CONTRACT, "home_resort": "riviera"}
    create_resp = await client.post("/api/contracts/", json=payload)
    contract_id = create_resp.json()["id"]

    resp = await client.get(f"/api/contracts/{contract_id}")
    data = resp.json()
    assert data["eligible_resorts"] == ["riviera"]
