"""Booking eligibility resolver -- determines which resorts a contract can book."""

from backend.data.resorts import get_resort_slugs, get_original_resort_slugs, get_restricted_resort_slugs


def get_eligible_resorts(home_resort: str, purchase_type: str) -> list[str]:
    """
    Determine which resorts a contract can book at.

    Rules:
    - Direct purchase: can book at ALL resorts
    - Resale at original 14 resort: can book at any of the original 14
    - Resale at restricted resort (Riviera, DLH, Cabins FW): can ONLY book home resort
    """
    if purchase_type == "direct":
        return get_resort_slugs()  # all resorts

    # Resale contract
    restricted = get_restricted_resort_slugs()

    if home_resort in restricted:
        # Post-2019 resort resale: home resort only
        return [home_resort]
    else:
        # Original 14 resort resale: can book any of the original 14
        return get_original_resort_slugs()
