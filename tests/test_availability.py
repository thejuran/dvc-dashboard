from datetime import date

from backend.engine.availability import get_all_contracts_availability, get_contract_availability

# --- Basic availability tests ---


def test_single_contract_no_reservations():
    """Available = sum of all balances for active use year."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[],
        target_date=date(2026, 3, 15),  # March 2026 -> active UY = 2025 (June UY)
    )
    assert result["total_points"] == 160
    assert result["committed_points"] == 0
    assert result["available_points"] == 160
    assert result["use_year"] == 2025


def test_single_contract_one_reservation():
    """Available = total - reservation points."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[
            {"check_in": date(2026, 3, 15), "points_cost": 85, "status": "confirmed"},
        ],
        target_date=date(2026, 3, 15),
    )
    assert result["total_points"] == 160
    assert result["committed_points"] == 85
    assert result["available_points"] == 75
    assert result["committed_reservation_count"] == 1


def test_cancelled_reservation_not_deducted():
    """Cancelled reservation NOT deducted."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[
            {"check_in": date(2026, 3, 15), "points_cost": 85, "status": "cancelled"},
        ],
        target_date=date(2026, 3, 15),
    )
    assert result["committed_points"] == 0
    assert result["available_points"] == 160


def test_no_balances_for_target_uy():
    """No point balances for target date's UY: available = 0."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2024, "allocation_type": "current", "points": 160},  # Wrong UY
        ],
        reservations=[],
        target_date=date(2026, 3, 15),  # Active UY = 2025
    )
    assert result["total_points"] == 0
    assert result["available_points"] == 0


# --- Multi-allocation tests ---


def test_current_plus_banked():
    """Current (160) + banked (45) for same UY = 205."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
            {"use_year": 2025, "allocation_type": "banked", "points": 45},
        ],
        reservations=[],
        target_date=date(2026, 3, 15),
    )
    assert result["total_points"] == 205
    assert result["balances"] == {"current": 160, "banked": 45}


def test_current_plus_borrowed():
    """Current (160) + borrowed (50) for same UY = 210."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
            {"use_year": 2025, "allocation_type": "borrowed", "points": 50},
        ],
        reservations=[],
        target_date=date(2026, 3, 15),
    )
    assert result["total_points"] == 210
    assert result["balances"] == {"current": 160, "borrowed": 50}


def test_all_four_allocation_types():
    """All 4 allocation types summed correctly."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
            {"use_year": 2025, "allocation_type": "banked", "points": 45},
            {"use_year": 2025, "allocation_type": "borrowed", "points": 50},
            {"use_year": 2025, "allocation_type": "holding", "points": 20},
        ],
        reservations=[],
        target_date=date(2026, 3, 15),
    )
    assert result["total_points"] == 275
    assert result["balances"] == {"current": 160, "banked": 45, "borrowed": 50, "holding": 20}


# --- Use year boundary tests ---


def test_june_uy_march_target():
    """June UY, target March 2026 -> active UY = 2025."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[],
        target_date=date(2026, 3, 15),
    )
    assert result["use_year"] == 2025
    assert result["use_year_start"] == "2025-06-01"
    assert result["use_year_end"] == "2026-05-31"


def test_june_uy_july_target():
    """June UY, target July 2026 -> active UY = 2026."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2026, "allocation_type": "current", "points": 160},
        ],
        reservations=[],
        target_date=date(2026, 7, 15),
    )
    assert result["use_year"] == 2026
    assert result["use_year_start"] == "2026-06-01"
    assert result["use_year_end"] == "2027-05-31"


def test_december_uy_january_target():
    """December UY, target January 2026 -> active UY = 2025."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=12,
        annual_points=200,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 200},
        ],
        reservations=[],
        target_date=date(2026, 1, 15),
    )
    assert result["use_year"] == 2025
    assert result["use_year_start"] == "2025-12-01"
    assert result["use_year_end"] == "2026-11-30"


def test_february_uy_january_target():
    """February UY, target January 2026 -> active UY = 2025."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=2,
        annual_points=150,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 150},
        ],
        reservations=[],
        target_date=date(2026, 1, 15),
    )
    assert result["use_year"] == 2025
    assert result["use_year_start"] == "2025-02-01"
    assert result["use_year_end"] == "2026-01-31"


# --- Reservation deduction tests ---


def test_reservation_checkin_within_uy_deducted():
    """Reservation check_in within UY: deducted."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[
            {"check_in": date(2025, 8, 10), "points_cost": 50, "status": "confirmed"},
        ],
        target_date=date(2025, 7, 1),
    )
    assert result["committed_points"] == 50
    assert result["available_points"] == 110


def test_reservation_checkin_outside_uy_not_deducted():
    """Reservation check_in outside UY (different year): NOT deducted."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[
            # This reservation is in UY 2026 (June 2026 - May 2027)
            {"check_in": date(2026, 8, 10), "points_cost": 50, "status": "confirmed"},
        ],
        target_date=date(2026, 3, 15),  # Active UY = 2025
    )
    assert result["committed_points"] == 0
    assert result["available_points"] == 160


def test_multiple_reservations_all_deducted():
    """Multiple reservations: all deducted from same UY."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[
            {"check_in": date(2025, 8, 10), "points_cost": 50, "status": "confirmed"},
            {"check_in": date(2025, 12, 20), "points_cost": 40, "status": "confirmed"},
            {"check_in": date(2026, 3, 15), "points_cost": 30, "status": "pending"},
        ],
        target_date=date(2025, 7, 1),
    )
    assert result["committed_points"] == 120
    assert result["committed_reservation_count"] == 3
    assert result["available_points"] == 40


def test_deductions_cannot_go_negative():
    """Available = 0 minimum when reservations exceed balance."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 100},
        ],
        reservations=[
            {"check_in": date(2025, 8, 10), "points_cost": 60, "status": "confirmed"},
            {"check_in": date(2025, 12, 20), "points_cost": 60, "status": "confirmed"},
        ],
        target_date=date(2025, 7, 1),
    )
    assert result["committed_points"] == 120
    assert result["available_points"] == 0  # max(0, 100 - 120)


def test_reservation_at_uy_boundary_last_day():
    """Reservation at UY boundary (check_in = last day of UY): deducted."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[
            {"check_in": date(2026, 5, 31), "points_cost": 50, "status": "confirmed"},  # Last day of UY 2025
        ],
        target_date=date(2025, 7, 1),
    )
    assert result["committed_points"] == 50


def test_reservation_at_uy_start():
    """Reservation at UY start (check_in = first day of UY): deducted."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[
            {"check_in": date(2025, 6, 1), "points_cost": 50, "status": "confirmed"},  # First day of UY 2025
        ],
        target_date=date(2025, 7, 1),
    )
    assert result["committed_points"] == 50


# --- Multi-contract tests ---


def test_two_contracts_different_uy():
    """Two contracts with different UY months: correct per-contract breakdown."""
    contracts = [
        {"id": 1, "name": "Poly", "home_resort": "polynesian", "use_year_month": 6, "annual_points": 160},
        {"id": 2, "name": "Riviera", "home_resort": "riviera", "use_year_month": 12, "annual_points": 200},
    ]
    balances = [
        {"contract_id": 1, "use_year": 2025, "allocation_type": "current", "points": 160},
        {"contract_id": 2, "use_year": 2025, "allocation_type": "current", "points": 200},
    ]
    reservations = [
        {"contract_id": 1, "check_in": date(2026, 3, 15), "points_cost": 85, "status": "confirmed"},
        {"contract_id": 2, "check_in": date(2026, 1, 10), "points_cost": 100, "status": "confirmed"},
    ]

    result = get_all_contracts_availability(
        contracts=contracts,
        point_balances=balances,
        reservations=reservations,
        target_date=date(2026, 3, 15),
    )

    assert len(result["contracts"]) == 2

    # Contract 1: June UY, target March 2026 -> UY 2025, 160 - 85 = 75
    c1 = result["contracts"][0]
    assert c1["contract_id"] == 1
    assert c1["use_year"] == 2025
    assert c1["available_points"] == 75

    # Contract 2: December UY, target March 2026 -> UY 2025, 200 - 100 = 100
    c2 = result["contracts"][1]
    assert c2["contract_id"] == 2
    assert c2["use_year"] == 2025
    assert c2["available_points"] == 100


def test_grand_total_matches_sum():
    """Grand total = sum of all contract available points."""
    contracts = [
        {"id": 1, "name": "Poly", "home_resort": "polynesian", "use_year_month": 6, "annual_points": 160},
        {"id": 2, "name": "Riviera", "home_resort": "riviera", "use_year_month": 12, "annual_points": 200},
    ]
    balances = [
        {"contract_id": 1, "use_year": 2025, "allocation_type": "current", "points": 160},
        {"contract_id": 2, "use_year": 2025, "allocation_type": "current", "points": 200},
    ]

    result = get_all_contracts_availability(
        contracts=contracts,
        point_balances=balances,
        reservations=[],
        target_date=date(2026, 3, 15),
    )

    assert result["summary"]["total_contracts"] == 2
    assert result["summary"]["total_points"] == 360
    assert result["summary"]["total_committed"] == 0
    assert result["summary"]["total_available"] == 360


# --- Banking deadline tests ---


def test_banking_deadline_not_passed():
    """Target date before banking deadline: banking_deadline_passed = False."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[],
        target_date=date(2025, 7, 1),  # Banking deadline for June 2025 UY = Jan 31, 2026
    )
    assert result["banking_deadline_passed"] is False
    assert result["days_until_banking_deadline"] > 0


def test_banking_deadline_passed():
    """Target date after banking deadline: banking_deadline_passed = True."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[],
        target_date=date(2026, 3, 15),  # After Jan 31, 2026 banking deadline
    )
    assert result["banking_deadline_passed"] is True
    assert result["days_until_banking_deadline"] < 0


def test_reservation_with_string_checkin():
    """Engine handles check_in as ISO string."""
    result = get_contract_availability(
        contract_id=1,
        use_year_month=6,
        annual_points=160,
        point_balances=[
            {"use_year": 2025, "allocation_type": "current", "points": 160},
        ],
        reservations=[
            {"check_in": "2026-03-15", "points_cost": 85, "status": "confirmed"},
        ],
        target_date=date(2026, 3, 15),
    )
    assert result["committed_points"] == 85
    assert result["available_points"] == 75
