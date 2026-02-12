from datetime import date

from backend.engine.use_year import (
    get_banking_deadline,
    get_current_use_year,
    get_use_year_end,
    get_use_year_start,
    get_use_year_status,
)


def get_contract_availability(
    contract_id: int,
    use_year_month: int,
    annual_points: int,
    point_balances: list[dict],
    reservations: list[dict],
    target_date: date,
) -> dict:
    """
    Calculate point availability for a single contract on a target date.

    Args:
        contract_id: The contract ID
        use_year_month: The contract's use year month (2,3,4,...,12)
        annual_points: The contract's annual point allocation
        point_balances: List of dicts with keys: use_year, allocation_type, points
        reservations: List of dicts with keys: check_in (date), points_cost (int), status (str)
        target_date: The date to calculate availability for

    Returns:
        Dict with per-use-year breakdown, committed points, and available total.
    """
    # Determine which use year is active on the target date
    current_uy = get_current_use_year(use_year_month, as_of=target_date)

    uy_start = get_use_year_start(use_year_month, current_uy)
    uy_end = get_use_year_end(use_year_month, current_uy)
    banking_deadline = get_banking_deadline(use_year_month, current_uy)

    # Gather point balances for this use year
    balances_by_type = {}
    total_points = 0
    for b in point_balances:
        if b["use_year"] == current_uy:
            alloc_type = b["allocation_type"]
            pts = b["points"]
            balances_by_type[alloc_type] = balances_by_type.get(alloc_type, 0) + pts
            total_points += pts

    # Sum reservations committed against this use year
    # A reservation deducts from a use year if its check_in falls within the UY range
    committed_points = 0
    committed_reservations = []
    for r in reservations:
        check_in = (
            r["check_in"] if isinstance(r["check_in"], date) else date.fromisoformat(r["check_in"])
        )
        if r.get("status", "confirmed") == "cancelled":
            continue
        if uy_start <= check_in <= uy_end:
            committed_points += r["points_cost"]
            committed_reservations.append(r)

    available_points = max(0, total_points - committed_points)

    return {
        "contract_id": contract_id,
        "use_year": current_uy,
        "use_year_start": uy_start.isoformat(),
        "use_year_end": uy_end.isoformat(),
        "use_year_status": get_use_year_status(use_year_month, current_uy, as_of=target_date),
        "banking_deadline": banking_deadline.isoformat(),
        "banking_deadline_passed": target_date > banking_deadline,
        "days_until_banking_deadline": (banking_deadline - target_date).days,
        "days_until_expiration": (uy_end - target_date).days,
        "balances": balances_by_type,
        "total_points": total_points,
        "committed_points": committed_points,
        "committed_reservation_count": len(committed_reservations),
        "available_points": available_points,
    }


def get_all_contracts_availability(
    contracts: list[dict],
    point_balances: list[dict],
    reservations: list[dict],
    target_date: date,
) -> dict:
    """
    Calculate point availability across ALL contracts for a target date.

    Args:
        contracts: List of dicts with keys: id, use_year_month, annual_points, home_resort, purchase_type, name
        point_balances: All point balances across all contracts
        reservations: All reservations across all contracts
        target_date: The date to calculate availability for

    Returns:
        Dict with per-contract breakdowns and grand total.
    """
    contract_results = []
    grand_total_points = 0
    grand_committed = 0
    grand_available = 0

    for c in contracts:
        # Filter balances and reservations for this contract
        c_balances = [b for b in point_balances if b["contract_id"] == c["id"]]
        c_reservations = [r for r in reservations if r["contract_id"] == c["id"]]

        result = get_contract_availability(
            contract_id=c["id"],
            use_year_month=c["use_year_month"],
            annual_points=c["annual_points"],
            point_balances=c_balances,
            reservations=c_reservations,
            target_date=target_date,
        )

        # Enrich with contract metadata
        result["contract_name"] = c.get("name") or c.get("home_resort", "Unknown")
        result["home_resort"] = c.get("home_resort")
        result["annual_points"] = c["annual_points"]

        contract_results.append(result)
        grand_total_points += result["total_points"]
        grand_committed += result["committed_points"]
        grand_available += result["available_points"]

    return {
        "target_date": target_date.isoformat(),
        "contracts": contract_results,
        "summary": {
            "total_contracts": len(contracts),
            "total_points": grand_total_points,
            "total_committed": grand_committed,
            "total_available": grand_available,
        },
    }
