from backend.engine.eligibility import get_eligible_resorts
from backend.data.resorts import (
    get_resort_slugs,
    get_original_resort_slugs,
    get_restricted_resort_slugs,
)


def test_direct_purchase_gets_all_resorts():
    """Direct purchase at any resort: returns all 17 resorts."""
    result = get_eligible_resorts("polynesian", "direct")
    all_slugs = get_resort_slugs()
    assert set(result) == set(all_slugs)
    assert len(result) == 17


def test_direct_purchase_at_restricted_resort_gets_all():
    """Direct purchase at restricted resort still gets all resorts."""
    result = get_eligible_resorts("riviera", "direct")
    assert len(result) == 17


def test_resale_at_original_resort_gets_14():
    """Resale at polynesian (original): returns exactly the 14 original resort slugs."""
    result = get_eligible_resorts("polynesian", "resale")
    original = get_original_resort_slugs()
    assert set(result) == set(original)
    assert len(result) == 14


def test_resale_at_riviera_gets_only_home():
    """Resale at riviera (restricted): returns ['riviera'] only."""
    result = get_eligible_resorts("riviera", "resale")
    assert result == ["riviera"]


def test_resale_at_disneyland_hotel_gets_only_home():
    """Resale at disneyland_hotel (restricted): returns ['disneyland_hotel'] only."""
    result = get_eligible_resorts("disneyland_hotel", "resale")
    assert result == ["disneyland_hotel"]


def test_resale_at_cabins_fort_wilderness_gets_only_home():
    """Resale at cabins_fort_wilderness (restricted): returns ['cabins_fort_wilderness'] only."""
    result = get_eligible_resorts("cabins_fort_wilderness", "resale")
    assert result == ["cabins_fort_wilderness"]


def test_resale_at_bay_lake_tower_gets_original_14():
    """Resale at bay_lake_tower (original): returns the 14 original resort slugs."""
    result = get_eligible_resorts("bay_lake_tower", "resale")
    original = get_original_resort_slugs()
    assert set(result) == set(original)
    assert len(result) == 14


def test_resale_at_original_excludes_restricted():
    """Verify no restricted resorts appear in resale-at-original results."""
    result = get_eligible_resorts("polynesian", "resale")
    restricted = set(get_restricted_resort_slugs())
    result_set = set(result)
    assert result_set.isdisjoint(restricted), (
        f"Restricted resorts found in resale results: {result_set & restricted}"
    )
