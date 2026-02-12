from datetime import date

from fastapi import APIRouter

from backend.api.errors import NotFoundError, ValidationError
from backend.api.schemas import (
    PointChartSummary,
    PointCostRequest,
    StayCostResponse,
)
from backend.data.point_charts import (
    calculate_stay_cost,
    get_available_charts,
    load_point_chart,
)
from backend.data.resorts import get_resort_by_slug

router = APIRouter(prefix="/api/point-charts", tags=["point-charts"])


def _humanize(slug: str) -> str:
    """Convert underscore-separated slug to Title Case."""
    return slug.replace("_", " ").title()


def _parse_room_key(room_key: str, view_categories: list[str]) -> dict:
    """Parse a room key into room_type and view components.

    Tries to match the longest view_category suffix first.
    E.g., 'deluxe_studio_theme_park' with view_categories=['standard', 'theme_park']
    -> room_type='Deluxe Studio', view='Theme Park'
    """
    for view in sorted(view_categories, key=len, reverse=True):
        if room_key.endswith(f"_{view}"):
            room_type_slug = room_key[: -(len(view) + 1)]  # strip _view
            return {
                "key": room_key,
                "room_type": _humanize(room_type_slug),
                "view": _humanize(view),
            }
    # Fallback: treat entire key as room type with unknown view
    return {"key": room_key, "room_type": _humanize(room_key), "view": "Standard"}


@router.get("/", response_model=list[PointChartSummary])
async def list_charts():
    """List all available point charts."""
    return get_available_charts()


@router.get("/{resort}/{year}")
async def get_chart(resort: str, year: int):
    """Get a specific resort's point chart for a year."""
    chart = load_point_chart(resort, year)
    if chart is None:
        raise NotFoundError("Point chart not found")
    return chart


@router.get("/{resort}/{year}/rooms")
async def get_chart_rooms(resort: str, year: int):
    """Get parsed room types for a resort/year chart."""
    chart = load_point_chart(resort, year)
    if chart is None:
        raise NotFoundError("Point chart not found")

    # Get view categories from resorts.json for smart parsing
    resort_data = get_resort_by_slug(resort)
    view_categories = resort_data["view_categories"] if resort_data else ["standard"]

    # Extract unique room keys from the first season
    room_keys = list(chart["seasons"][0]["rooms"].keys())
    rooms = [_parse_room_key(key, view_categories) for key in sorted(room_keys)]

    return {"resort": resort, "year": year, "rooms": rooms}


@router.get("/{resort}/{year}/seasons")
async def get_chart_seasons(resort: str, year: int):
    """Get season structure (names and date ranges) without room costs."""
    chart = load_point_chart(resort, year)
    if chart is None:
        raise NotFoundError("Point chart not found")

    seasons = [
        {"name": s["name"], "date_ranges": s["date_ranges"]}
        for s in chart["seasons"]
    ]
    return {"resort": resort, "year": year, "seasons": seasons}


@router.post("/calculate", response_model=StayCostResponse)
async def calculate_cost(request: PointCostRequest):
    """Calculate stay cost for a given resort, room, and date range."""
    try:
        check_in = date.fromisoformat(request.check_in)
        check_out = date.fromisoformat(request.check_out)
    except ValueError as exc:
        raise ValidationError(
            "Validation failed",
            fields=[{"field": "check_in", "issue": "Invalid date format. Use ISO format (YYYY-MM-DD)."}],
        ) from exc

    if check_out <= check_in:
        raise ValidationError(
            "Validation failed",
            fields=[{"field": "check_out", "issue": "Check-out must be after check-in."}],
        )

    if (check_out - check_in).days > 14:
        raise ValidationError(
            "Validation failed",
            fields=[{"field": "check_out", "issue": "Maximum stay is 14 nights."}],
        )

    # Check chart exists
    chart = load_point_chart(request.resort, check_in.year)
    if chart is None:
        raise NotFoundError("Point chart not found for this resort/year.")

    # Validate room key exists
    room_keys = set()
    for season in chart["seasons"]:
        room_keys.update(season["rooms"].keys())
    if request.room_key not in room_keys:
        raise ValidationError(
            "Validation failed",
            fields=[{"field": "room_key", "issue": f"Invalid room key '{request.room_key}'. Available: {sorted(room_keys)}"}],
        )

    result = calculate_stay_cost(request.resort, request.room_key, check_in, check_out)
    if result is None:
        raise ValidationError("Could not calculate cost. Dates may be out of range.")

    return result
