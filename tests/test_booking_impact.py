from datetime import date

from backend.engine.booking_impact import compute_banking_warning, compute_booking_impact

# --- compute_booking_impact tests ---


def test_booking_impact_basic():
    """
    Basic booking impact: before.available > after.available,
    points_delta matches stay_cost total.
    Uses polynesian/deluxe_studio_standard for a date in Jan 2026
    (Adventure season: weekday=14, weekend=19).
    """
    contract = {"id": 1, "use_year_month": 2, "annual_points": 200}
    point_balances = [
        {"contract_id": 1, "use_year": 2025, "allocation_type": "current", "points": 200},
    ]
    reservations = []

    # Jan 12 (Mon) to Jan 15 (Thu) 2026 = 3 weekday nights in Adventure season
    # Cost: 3 * 14 = 42 points
    result = compute_booking_impact(
        contract=contract,
        point_balances=point_balances,
        reservations=reservations,
        proposed_resort="polynesian",
        proposed_room_key="deluxe_studio_standard",
        proposed_check_in=date(2026, 1, 12),
        proposed_check_out=date(2026, 1, 15),
    )

    assert "error" not in result
    assert result["before"]["available_points"] == 200
    assert result["after"]["available_points"] == 200 - result["points_delta"]
    assert result["points_delta"] == result["stay_cost"]["total_points"]
    assert result["stay_cost"]["num_nights"] == 3
    assert len(result["stay_cost"]["nightly_breakdown"]) == 3


def test_booking_impact_with_existing_reservations():
    """Booking impact with existing reservations already committed."""
    contract = {"id": 1, "use_year_month": 2, "annual_points": 200}
    point_balances = [
        {"contract_id": 1, "use_year": 2025, "allocation_type": "current", "points": 200},
    ]
    reservations = [
        {"contract_id": 1, "check_in": date(2025, 5, 10), "points_cost": 50, "status": "confirmed"},
    ]

    result = compute_booking_impact(
        contract=contract,
        point_balances=point_balances,
        reservations=reservations,
        proposed_resort="polynesian",
        proposed_room_key="deluxe_studio_standard",
        proposed_check_in=date(2026, 1, 12),
        proposed_check_out=date(2026, 1, 15),
    )

    assert "error" not in result
    # Before should reflect the existing 50-point reservation
    assert result["before"]["committed_points"] == 50
    assert result["before"]["available_points"] == 150
    # After should include both existing + proposed
    assert result["after"]["committed_points"] == 50 + result["points_delta"]


def test_booking_impact_no_point_chart():
    """When point chart data is unavailable, return error dict."""
    contract = {"id": 1, "use_year_month": 2, "annual_points": 200}
    point_balances = [
        {"contract_id": 1, "use_year": 2025, "allocation_type": "current", "points": 200},
    ]

    result = compute_booking_impact(
        contract=contract,
        point_balances=point_balances,
        reservations=[],
        proposed_resort="nonexistent_resort",
        proposed_room_key="deluxe_studio",
        proposed_check_in=date(2026, 1, 12),
        proposed_check_out=date(2026, 1, 15),
    )

    assert "error" in result
    assert "point chart" in result["error"].lower()


def test_booking_impact_filters_by_contract():
    """Booking impact only considers balances/reservations for the given contract."""
    contract = {"id": 1, "use_year_month": 2, "annual_points": 200}
    point_balances = [
        {"contract_id": 1, "use_year": 2025, "allocation_type": "current", "points": 200},
        {"contract_id": 2, "use_year": 2025, "allocation_type": "current", "points": 300},
    ]
    reservations = [
        {"contract_id": 2, "check_in": date(2025, 5, 10), "points_cost": 100, "status": "confirmed"},
    ]

    result = compute_booking_impact(
        contract=contract,
        point_balances=point_balances,
        reservations=reservations,
        proposed_resort="polynesian",
        proposed_room_key="deluxe_studio_standard",
        proposed_check_in=date(2026, 1, 12),
        proposed_check_out=date(2026, 1, 15),
    )

    assert "error" not in result
    # Before should only reflect contract 1's data (200 pts, 0 committed)
    assert result["before"]["total_points"] == 200
    assert result["before"]["committed_points"] == 0


# --- compute_banking_warning tests ---


def test_banking_warning_fires_when_dipping_into_bankable():
    """Warning fires when booking must consume current-year (bankable) points."""
    before_availability = {
        "banking_deadline_passed": False,
        "banking_deadline": "2026-01-31",
        "days_until_banking_deadline": 30,
        "balances": {"current": 200},
        "available_points": 200,
        "committed_points": 0,
    }
    contract = {"id": 1, "use_year_month": 2, "annual_points": 200}

    # Cost of 50 > non-bankable portion (200 - 200 = 0), so warning fires
    result = compute_banking_warning(contract, before_availability, 50)

    assert result is not None
    assert result["warning"] is True
    assert result["bankable_points"] == 200
    assert result["banking_deadline"] == "2026-01-31"
    assert result["days_until_deadline"] == 30
    assert "banking" in result["message"].lower()


def test_banking_warning_no_warning_when_deadline_passed():
    """No warning when banking deadline has passed."""
    before_availability = {
        "banking_deadline_passed": True,
        "banking_deadline": "2025-09-30",
        "days_until_banking_deadline": -30,
        "balances": {"current": 200},
        "available_points": 200,
        "committed_points": 0,
    }
    contract = {"id": 1, "use_year_month": 2, "annual_points": 200}

    result = compute_banking_warning(contract, before_availability, 50)
    assert result is None


def test_banking_warning_no_warning_when_no_current_points():
    """No warning when no current-year points in balances."""
    before_availability = {
        "banking_deadline_passed": False,
        "banking_deadline": "2026-01-31",
        "days_until_banking_deadline": 30,
        "balances": {"banked": 100},
        "available_points": 100,
        "committed_points": 0,
    }
    contract = {"id": 1, "use_year_month": 2, "annual_points": 200}

    result = compute_banking_warning(contract, before_availability, 50)
    assert result is None


def test_banking_warning_no_warning_when_covered_by_non_current():
    """No warning when cost is covered entirely by non-current-year points."""
    before_availability = {
        "banking_deadline_passed": False,
        "banking_deadline": "2026-01-31",
        "days_until_banking_deadline": 30,
        "balances": {"current": 200, "banked": 100},
        "available_points": 300,
        "committed_points": 0,
    }
    contract = {"id": 1, "use_year_month": 2, "annual_points": 200}

    # Cost of 50 <= non-bankable portion (300 - 200 = 100), no warning
    result = compute_banking_warning(contract, before_availability, 50)
    assert result is None
