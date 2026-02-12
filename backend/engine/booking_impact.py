from datetime import date

from backend.data.point_charts import calculate_stay_cost
from backend.engine.availability import get_contract_availability


def compute_booking_impact(
    contract: dict,
    point_balances: list[dict],
    reservations: list[dict],
    proposed_resort: str,
    proposed_room_key: str,
    proposed_check_in: date,
    proposed_check_out: date,
) -> dict:
    """
    Compute before/after point impact of a proposed booking.
    Pure function -- no DB access.

    Args:
        contract: dict with id, use_year_month, annual_points
        point_balances: list of dicts with contract_id, use_year, allocation_type, points
        reservations: list of dicts with contract_id, check_in, points_cost, status
        proposed_resort: resort slug
        proposed_room_key: room key
        proposed_check_in: check-in date
        proposed_check_out: check-out date

    Returns:
        Dict with before/after availability snapshots, stay_cost, and points_delta.
        If point chart data is not available, returns dict with "error" key.
    """
    # Filter to only this contract's data
    contract_balances = [b for b in point_balances if b["contract_id"] == contract["id"]]
    contract_reservations = [r for r in reservations if r["contract_id"] == contract["id"]]

    # "Before" state
    before = get_contract_availability(
        contract_id=contract["id"],
        use_year_month=contract["use_year_month"],
        annual_points=contract["annual_points"],
        point_balances=contract_balances,
        reservations=contract_reservations,
        target_date=proposed_check_in,
    )

    # Calculate stay cost (nightly breakdown)
    stay_cost = calculate_stay_cost(
        proposed_resort, proposed_room_key,
        proposed_check_in, proposed_check_out,
    )
    if stay_cost is None:
        return {
            "error": "Could not calculate stay cost -- point chart data not available for these dates"
        }

    # "After" state: add proposed reservation to committed list
    proposed_reservation = {
        "check_in": proposed_check_in,
        "points_cost": stay_cost["total_points"],
        "status": "confirmed",
        "contract_id": contract["id"],
    }
    after_reservations = [*contract_reservations, proposed_reservation]

    after = get_contract_availability(
        contract_id=contract["id"],
        use_year_month=contract["use_year_month"],
        annual_points=contract["annual_points"],
        point_balances=contract_balances,
        reservations=after_reservations,
        target_date=proposed_check_in,
    )

    return {
        "before": before,
        "after": after,
        "stay_cost": stay_cost,
        "points_delta": stay_cost["total_points"],
    }


def compute_banking_warning(
    contract: dict,
    before_availability: dict,
    points_cost: int,
) -> dict | None:
    """
    Conservative banking warning. Warns when a proposed booking would
    consume current-year points that are still eligible for banking.

    Returns None if:
    - Banking deadline has already passed
    - No current-year points in balances
    - Booking can be covered entirely by non-current-year points

    Returns warning dict if the booking MUST dip into current-year
    (bankable) points.
    """
    if before_availability["banking_deadline_passed"]:
        return None

    bankable = before_availability["balances"].get("current", 0)
    if bankable == 0:
        return None

    # If points_cost exceeds the non-bankable portion of available points,
    # the booking must dip into current-year (bankable) points
    non_bankable = before_availability["available_points"] - bankable
    if points_cost > non_bankable:
        return {
            "warning": True,
            "bankable_points": bankable,
            "banking_deadline": before_availability["banking_deadline"],
            "days_until_deadline": before_availability["days_until_banking_deadline"],
            "message": (
                f"This booking could use points that are still eligible for banking. "
                f"Banking deadline: {before_availability['banking_deadline']} "
                f"({before_availability['days_until_banking_deadline']} days away). "
                f"Up to {bankable} points could still be banked."
            ),
        }

    return None
