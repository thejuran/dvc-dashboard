"""Trip Explorer engine -- answers 'what can I afford?' for given dates."""

from datetime import date

from backend.data.point_charts import (
    calculate_stay_cost,
    get_available_charts,
    load_point_chart,
)
from backend.data.resorts import load_resorts
from backend.engine.availability import get_contract_availability
from backend.engine.eligibility import get_eligible_resorts


def find_affordable_options(
    contracts: list[dict],
    point_balances: list[dict],
    reservations: list[dict],
    check_in: date,
    check_out: date,
) -> dict:
    """
    Find all resort/room options affordable with current point balances.

    Pure function: takes data as arguments, no database access.

    Args:
        contracts: List of contract dicts (id, name, home_resort, use_year_month,
                   annual_points, purchase_type)
        point_balances: List of balance dicts (contract_id, use_year, allocation_type, points)
        reservations: List of reservation dicts (contract_id, check_in, points_cost, status)
        check_in: Desired check-in date
        check_out: Desired check-out date

    Returns:
        Dict with options list sorted by total_points ascending, plus metadata.
    """
    num_nights = (check_out - check_in).days

    # Build set of resorts that have chart data for the check-in year
    all_charts = get_available_charts()
    resorts_with_charts = {c["resort"] for c in all_charts if c["year"] == check_in.year}

    # Build resort slug-to-name mapping
    resort_list = load_resorts()
    resort_name_map = {r["slug"]: r["name"] for r in resort_list}

    results = []
    resorts_checked: set[str] = set()
    resorts_skipped: set[str] = set()

    for contract in contracts:
        contract_id = contract["id"]

        # Filter balances and reservations for this contract
        c_balances = [b for b in point_balances if b["contract_id"] == contract_id]
        c_reservations = [r for r in reservations if r["contract_id"] == contract_id]

        # Calculate availability using check_in date (NOT today)
        availability = get_contract_availability(
            contract_id=contract_id,
            use_year_month=contract["use_year_month"],
            annual_points=contract["annual_points"],
            point_balances=c_balances,
            reservations=c_reservations,
            target_date=check_in,
        )

        available_points = availability["available_points"]
        if available_points <= 0:
            continue

        contract_name = contract.get("name") or contract.get("home_resort", "Unknown")

        # Get eligible resorts for this contract
        eligible = get_eligible_resorts(contract["home_resort"], contract["purchase_type"])

        for resort_slug in eligible:
            if resort_slug not in resorts_with_charts:
                resorts_skipped.add(resort_slug)
                continue

            resorts_checked.add(resort_slug)

            # Load the point chart for this resort
            chart = load_point_chart(resort_slug, check_in.year)
            if chart is None:
                resorts_skipped.add(resort_slug)
                continue

            # Collect all unique room keys across all seasons
            room_keys: set[str] = set()
            for season in chart["seasons"]:
                room_keys.update(season["rooms"].keys())

            # Check each room type
            for room_key in sorted(room_keys):
                cost_result = calculate_stay_cost(resort_slug, room_key, check_in, check_out)
                if cost_result is not None and cost_result["total_points"] <= available_points:
                    results.append(
                        {
                            "contract_id": contract_id,
                            "contract_name": contract_name,
                            "available_points": available_points,
                            "resort": resort_slug,
                            "resort_name": resort_name_map.get(resort_slug, resort_slug),
                            "room_key": room_key,
                            "total_points": cost_result["total_points"],
                            "num_nights": cost_result["num_nights"],
                            "points_remaining": available_points - cost_result["total_points"],
                            "nightly_avg": round(
                                cost_result["total_points"] / cost_result["num_nights"]
                            ),
                        }
                    )

    # Sort by total_points ascending (cheapest first)
    results.sort(key=lambda r: r["total_points"])

    return {
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "num_nights": num_nights,
        "options": results,
        "resorts_checked": sorted(resorts_checked),
        "resorts_skipped": sorted(resorts_skipped),
        "total_options": len(results),
    }
