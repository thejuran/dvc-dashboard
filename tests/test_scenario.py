from datetime import date

from backend.engine.scenario import compute_scenario_impact

# Test fixtures mirroring test_booking_impact.py patterns.
# Uses polynesian/deluxe_studio_standard for Jan 2026 (Adventure season: weekday=14, weekend=19).

def _make_contract(id=1, use_year_month=2, annual_points=200, home_resort="polynesian", name=None):
    return {
        "id": id,
        "use_year_month": use_year_month,
        "annual_points": annual_points,
        "home_resort": home_resort,
        "name": name or home_resort,
    }


def _make_balance(contract_id=1, use_year=2025, allocation_type="current", points=200):
    return {
        "contract_id": contract_id,
        "use_year": use_year,
        "allocation_type": allocation_type,
        "points": points,
    }


def test_single_hypothetical_booking():
    """Single hypothetical booking: baseline != scenario, impact > 0."""
    contracts = [_make_contract()]
    balances = [_make_balance()]
    reservations = []
    hypotheticals = [{
        "contract_id": 1,
        "resort": "polynesian",
        "room_key": "deluxe_studio_standard",
        "check_in": date(2026, 1, 12),   # Monday
        "check_out": date(2026, 1, 15),   # Thursday -> 3 weekday nights = 3*14 = 42 pts
    }]

    result = compute_scenario_impact(contracts, balances, reservations, hypotheticals, date(2026, 1, 1))

    assert result["target_date"] == "2026-01-01"
    assert len(result["contracts"]) == 1

    cr = result["contracts"][0]
    assert cr["baseline"]["available_points"] > cr["scenario"]["available_points"]

    summary = result["summary"]
    assert summary["total_impact"] > 0
    assert summary["num_hypothetical_bookings"] == 1
    assert summary["baseline_available"] > summary["scenario_available"]

    assert len(result["resolved_bookings"]) == 1
    assert result["resolved_bookings"][0]["points_cost"] == 42
    assert result["resolved_bookings"][0]["num_nights"] == 3
    assert len(result["errors"]) == 0


def test_multiple_bookings_same_contract_cumulative():
    """Multiple bookings on same contract: cumulative impact."""
    contracts = [_make_contract()]
    balances = [_make_balance()]
    reservations = []
    hypotheticals = [
        {
            "contract_id": 1,
            "resort": "polynesian",
            "room_key": "deluxe_studio_standard",
            "check_in": date(2026, 1, 12),
            "check_out": date(2026, 1, 15),   # 3 weekday nights = 42 pts
        },
        {
            "contract_id": 1,
            "resort": "polynesian",
            "room_key": "deluxe_studio_standard",
            "check_in": date(2026, 1, 19),   # Monday
            "check_out": date(2026, 1, 22),   # Thursday -> 3 weekday nights = 42 pts
        },
    ]

    result = compute_scenario_impact(contracts, balances, reservations, hypotheticals, date(2026, 1, 1))

    # Both bookings resolved
    assert len(result["resolved_bookings"]) == 2
    assert result["summary"]["num_hypothetical_bookings"] == 2

    # Cumulative impact: scenario sees both bookings
    total_cost = sum(rb["points_cost"] for rb in result["resolved_bookings"])
    assert result["summary"]["total_impact"] == total_cost

    cr = result["contracts"][0]
    assert cr["scenario"]["committed_points"] == total_cost


def test_bookings_across_different_contracts():
    """Bookings across different contracts: each contract shows correct impact."""
    contracts = [
        _make_contract(id=1, home_resort="polynesian", name="Poly"),
        _make_contract(id=2, home_resort="polynesian", name="Poly 2", annual_points=300),
    ]
    balances = [
        _make_balance(contract_id=1, points=200),
        _make_balance(contract_id=2, points=300),
    ]
    reservations = []
    hypotheticals = [
        {
            "contract_id": 1,
            "resort": "polynesian",
            "room_key": "deluxe_studio_standard",
            "check_in": date(2026, 1, 12),
            "check_out": date(2026, 1, 15),   # 42 pts
        },
        {
            "contract_id": 2,
            "resort": "polynesian",
            "room_key": "deluxe_studio_standard",
            "check_in": date(2026, 1, 19),
            "check_out": date(2026, 1, 22),   # 42 pts
        },
    ]

    result = compute_scenario_impact(contracts, balances, reservations, hypotheticals, date(2026, 1, 1))

    assert len(result["contracts"]) == 2

    # Contract 1 should have 1 hypothetical
    c1 = next(c for c in result["contracts"] if c["contract_id"] == 1)
    assert len(c1["hypothetical_bookings"]) == 1
    assert c1["baseline"]["available_points"] == 200
    assert c1["scenario"]["available_points"] == 200 - 42

    # Contract 2 should have 1 hypothetical
    c2 = next(c for c in result["contracts"] if c["contract_id"] == 2)
    assert len(c2["hypothetical_bookings"]) == 1
    assert c2["baseline"]["available_points"] == 300
    assert c2["scenario"]["available_points"] == 300 - 42

    # Grand totals
    assert result["summary"]["baseline_available"] == 500
    assert result["summary"]["scenario_available"] == 500 - 84
    assert result["summary"]["total_impact"] == 84


def test_invalid_booking_goes_to_errors():
    """Invalid booking (no point chart data): goes to errors, other bookings still processed."""
    contracts = [_make_contract()]
    balances = [_make_balance()]
    reservations = []
    hypotheticals = [
        {
            "contract_id": 1,
            "resort": "nonexistent_resort",
            "room_key": "fake_room",
            "check_in": date(2026, 1, 12),
            "check_out": date(2026, 1, 15),
        },
        {
            "contract_id": 1,
            "resort": "polynesian",
            "room_key": "deluxe_studio_standard",
            "check_in": date(2026, 1, 19),
            "check_out": date(2026, 1, 22),   # 42 pts -- valid
        },
    ]

    result = compute_scenario_impact(contracts, balances, reservations, hypotheticals, date(2026, 1, 1))

    # One error, one resolved
    assert len(result["errors"]) == 1
    assert result["errors"][0]["resort"] == "nonexistent_resort"
    assert "not available" in result["errors"][0]["error"].lower()

    assert len(result["resolved_bookings"]) == 1
    assert result["resolved_bookings"][0]["resort"] == "polynesian"

    # Impact still computed from valid booking
    assert result["summary"]["total_impact"] == 42
    assert result["summary"]["num_hypothetical_bookings"] == 1


def test_empty_hypothetical_bookings():
    """Empty hypothetical_bookings list: baseline == scenario, zero impact."""
    contracts = [_make_contract()]
    balances = [_make_balance()]
    reservations = []

    result = compute_scenario_impact(contracts, balances, reservations, [], date(2026, 1, 1))

    assert result["summary"]["total_impact"] == 0
    assert result["summary"]["baseline_available"] == result["summary"]["scenario_available"]
    assert result["summary"]["num_hypothetical_bookings"] == 0
    assert len(result["resolved_bookings"]) == 0
    assert len(result["errors"]) == 0

    cr = result["contracts"][0]
    assert cr["baseline"]["available_points"] == cr["scenario"]["available_points"]


def test_cancelled_reservation_excluded_from_baseline():
    """Cancelled reservations in real data are excluded from baseline."""
    contracts = [_make_contract()]
    balances = [_make_balance()]
    reservations = [
        {"contract_id": 1, "check_in": date(2025, 5, 10), "points_cost": 50, "status": "cancelled"},
        {"contract_id": 1, "check_in": date(2025, 6, 10), "points_cost": 30, "status": "confirmed"},
    ]

    result = compute_scenario_impact(contracts, balances, reservations, [], date(2026, 1, 1))

    cr = result["contracts"][0]
    # Cancelled reservation should not reduce available points
    # Only the confirmed 30-point reservation should be committed
    assert cr["baseline"]["committed_points"] == 30
    assert cr["baseline"]["available_points"] == 200 - 30
