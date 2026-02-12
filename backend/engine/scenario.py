from datetime import date

from backend.data.point_charts import calculate_stay_cost
from backend.engine.availability import get_contract_availability


def compute_scenario_impact(
    contracts: list[dict],
    point_balances: list[dict],
    reservations: list[dict],
    hypothetical_bookings: list[dict],
    target_date: date,
) -> dict:
    """
    Compute cumulative impact of multiple hypothetical bookings.

    For each contract, computes:
    - baseline: availability with only real reservations
    - scenario: availability with real + all hypothetical reservations

    Hypothetical bookings are resolved to point costs using calculate_stay_cost(),
    then injected as additional reservations into the availability engine.

    Pure function -- no DB access.

    Args:
        contracts: list of dicts with id, use_year_month, annual_points, home_resort, name
        point_balances: list of dicts with contract_id, use_year, allocation_type, points
        reservations: list of dicts with contract_id, check_in, points_cost, status
        hypothetical_bookings: list of dicts with contract_id, resort, room_key, check_in, check_out
        target_date: the date to evaluate availability for

    Returns:
        Dict with target_date, contracts (per-contract baseline/scenario), summary, resolved_bookings, errors.
    """
    # 1. Resolve each hypothetical booking to a point cost
    resolved_hypotheticals = []
    errors = []
    for hb in hypothetical_bookings:
        cost = calculate_stay_cost(
            hb["resort"],
            hb["room_key"],
            hb["check_in"],
            hb["check_out"],
        )
        if cost is None:
            errors.append(
                {
                    "resort": hb["resort"],
                    "room_key": hb["room_key"],
                    "error": "Point chart data not available",
                }
            )
            continue
        resolved_hypotheticals.append(
            {
                "contract_id": hb["contract_id"],
                "check_in": hb["check_in"],
                "check_out": hb["check_out"],
                "points_cost": cost["total_points"],
                "resort": hb["resort"],
                "room_key": hb["room_key"],
                "status": "confirmed",
                "num_nights": cost["num_nights"],
            }
        )

    # 2. Compute baseline and scenario for each contract
    contract_results = []
    for contract in contracts:
        cid = contract["id"]
        c_balances = [b for b in point_balances if b["contract_id"] == cid]
        c_real_reservations = [r for r in reservations if r["contract_id"] == cid]
        c_hypotheticals = [h for h in resolved_hypotheticals if h["contract_id"] == cid]

        baseline = get_contract_availability(
            contract_id=cid,
            use_year_month=contract["use_year_month"],
            annual_points=contract["annual_points"],
            point_balances=c_balances,
            reservations=c_real_reservations,
            target_date=target_date,
        )

        # Scenario = real reservations + resolved hypotheticals
        scenario_reservations = c_real_reservations + [
            {
                "check_in": h["check_in"],
                "points_cost": h["points_cost"],
                "status": "confirmed",
                "contract_id": cid,
            }
            for h in c_hypotheticals
        ]

        scenario = get_contract_availability(
            contract_id=cid,
            use_year_month=contract["use_year_month"],
            annual_points=contract["annual_points"],
            point_balances=c_balances,
            reservations=scenario_reservations,
            target_date=target_date,
        )

        contract_results.append(
            {
                "contract_id": cid,
                "contract_name": contract.get("name") or contract.get("home_resort"),
                "home_resort": contract.get("home_resort"),
                "baseline": baseline,
                "scenario": scenario,
                "hypothetical_bookings": c_hypotheticals,
            }
        )

    # 3. Compute grand totals
    baseline_total = sum(c["baseline"]["available_points"] for c in contract_results)
    scenario_total = sum(c["scenario"]["available_points"] for c in contract_results)

    return {
        "target_date": target_date.isoformat(),
        "contracts": contract_results,
        "summary": {
            "baseline_available": baseline_total,
            "scenario_available": scenario_total,
            "total_impact": baseline_total - scenario_total,
            "num_hypothetical_bookings": len(resolved_hypotheticals),
        },
        "resolved_bookings": resolved_hypotheticals,
        "errors": errors,
    }
