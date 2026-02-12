"""Engine-level edge case tests for success criteria coverage.

Pure-function tests (no DB, no async) covering:
- 0 contracts / 0 points
- Expired use years
- Boundary dates (UY first day, last day, next day, banking deadline)
"""

from datetime import date

from backend.engine.availability import (
    get_all_contracts_availability,
    get_contract_availability,
)
from backend.engine.booking_impact import compute_booking_impact
from backend.engine.scenario import compute_scenario_impact
from backend.engine.trip_explorer import find_affordable_options

# ---- Fixtures ----


def _contract(
    id=1,
    use_year_month=6,
    annual_points=160,
    home_resort="polynesian",
    purchase_type="resale",
    name="Poly",
):
    return {
        "id": id,
        "use_year_month": use_year_month,
        "annual_points": annual_points,
        "home_resort": home_resort,
        "purchase_type": purchase_type,
        "name": name,
    }


def _balance(contract_id=1, use_year=2025, allocation_type="current", points=160):
    return {
        "contract_id": contract_id,
        "use_year": use_year,
        "allocation_type": allocation_type,
        "points": points,
    }


# ====================================================
# 0 contracts / 0 points
# ====================================================


def test_availability_zero_contracts():
    """get_all_contracts_availability with empty contracts list -> summary all zeros."""
    result = get_all_contracts_availability(
        contracts=[],
        point_balances=[],
        reservations=[],
        target_date=date(2026, 3, 15),
    )
    assert result["contracts"] == []
    assert result["summary"]["total_contracts"] == 0
    assert result["summary"]["total_points"] == 0
    assert result["summary"]["total_committed"] == 0
    assert result["summary"]["total_available"] == 0


def test_availability_zero_points():
    """Contract exists but no point balances -> available_points = 0."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[],
        reservations=[],
        target_date=date(2026, 3, 15),
    )
    assert result["total_points"] == 0
    assert result["available_points"] == 0
    assert result["committed_points"] == 0


def test_scenario_zero_contracts():
    """compute_scenario_impact with empty contracts -> empty results."""
    result = compute_scenario_impact(
        contracts=[],
        point_balances=[],
        reservations=[],
        hypothetical_bookings=[],
        target_date=date(2026, 3, 15),
    )
    assert result["contracts"] == []
    assert result["summary"]["total_impact"] == 0
    assert result["summary"]["baseline_available"] == 0
    assert result["summary"]["scenario_available"] == 0
    assert result["summary"]["num_hypothetical_bookings"] == 0


def test_trip_explorer_zero_contracts():
    """find_affordable_options with empty contracts -> empty options."""
    result = find_affordable_options(
        contracts=[],
        point_balances=[],
        reservations=[],
        check_in=date(2026, 1, 12),
        check_out=date(2026, 1, 15),
    )
    assert result["options"] == []
    assert result["total_options"] == 0


def test_booking_impact_zero_points():
    """Contract with no balances -> before.available_points = 0."""
    contract = {"id": 1, "use_year_month": 2, "annual_points": 200}
    result = compute_booking_impact(
        contract=contract,
        point_balances=[],
        reservations=[],
        proposed_resort="polynesian",
        proposed_room_key="deluxe_studio_standard",
        proposed_check_in=date(2026, 1, 12),
        proposed_check_out=date(2026, 1, 15),
    )
    # Should still get a result (not an error), before.available = 0
    assert "error" not in result
    assert result["before"]["available_points"] == 0
    assert result["before"]["total_points"] == 0


# ====================================================
# Expired use years
# ====================================================


def test_availability_expired_use_year():
    """Target date well past UY end -> returns 0 points for that UY.

    June 2023 UY ends May 31 2024. Target date March 2026 -> active UY = 2025.
    Balance for UY 2023 should NOT count.
    """
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2023, "allocation_type": "current", "points": 160},
        ],
        reservations=[],
        target_date=date(2026, 3, 15),  # Active UY = 2025
    )
    assert result["use_year"] == 2025
    assert result["total_points"] == 0
    assert result["available_points"] == 0


def test_availability_only_old_balances():
    """All balances for UY 2022, target date 2026 -> available = 0."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2022, "allocation_type": "current", "points": 160},
            {"use_year": 2022, "allocation_type": "banked", "points": 45},
        ],
        reservations=[],
        target_date=date(2026, 3, 15),  # Active UY = 2025
    )
    assert result["total_points"] == 0
    assert result["available_points"] == 0


# ====================================================
# Boundary dates
# ====================================================


def test_availability_uy_first_day():
    """target_date = exact first day of UY -> correct UY selected.

    June UY 2026 starts June 1, 2026. Target = June 1, 2026 -> UY = 2026.
    """
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2026, "allocation_type": "current", "points": 160},
        ],
        reservations=[],
        target_date=date(2026, 6, 1),  # Exact first day
    )
    assert result["use_year"] == 2026
    assert result["total_points"] == 160
    assert result["available_points"] == 160


def test_availability_uy_last_day():
    """target_date = exact last day of UY -> correct UY selected.

    June UY 2025 ends May 31, 2026. Target = May 31, 2026 -> UY = 2025.
    """
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[],
        target_date=date(2026, 5, 31),  # Last day of UY 2025
    )
    assert result["use_year"] == 2025
    assert result["total_points"] == 160
    assert result["available_points"] == 160


def test_availability_uy_boundary_next_day():
    """target_date = one day after UY end -> next UY.

    June UY 2025 ends May 31, 2026. Target = June 1, 2026 -> UY = 2026.
    Need balance for UY 2026 to have points.
    """
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
            {"use_year": 2026, "allocation_type": "current", "points": 160},
        ],
        reservations=[],
        target_date=date(2026, 6, 1),  # First day of UY 2026
    )
    assert result["use_year"] == 2026
    assert result["total_points"] == 160  # UY 2026 balance only


def test_reservation_check_in_on_uy_start():
    """Reservation check_in on exact UY start date: deducted from that UY."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[
            {"check_in": date(2025, 6, 1), "points_cost": 50, "status": "confirmed"},
        ],
        target_date=date(2025, 7, 1),
    )
    assert result["committed_points"] == 50
    assert result["available_points"] == 110


def test_reservation_check_in_on_uy_end():
    """Reservation check_in on exact UY end date: deducted from that UY."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[
            {"check_in": date(2026, 5, 31), "points_cost": 50, "status": "confirmed"},
        ],
        target_date=date(2025, 7, 1),
    )
    assert result["committed_points"] == 50
    assert result["available_points"] == 110


def test_banking_deadline_exact_day():
    """target_date = exact banking deadline date -> banking_deadline_passed = False.

    June UY 2025 banking deadline = Jan 31, 2026.
    Target = Jan 31, 2026 -> banking_deadline_passed should be False (not past yet).
    """
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[],
        target_date=date(2026, 1, 31),  # Exact banking deadline
    )
    # target_date > banking_deadline is False when equal
    assert result["banking_deadline_passed"] is False
    assert result["days_until_banking_deadline"] == 0
