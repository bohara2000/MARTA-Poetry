from typing import Any, Dict, Optional

import httpx

from config import MAPBOX_ACCESS_TOKEN, MAPBOX_GEOCODE_BASE_URL, MAPBOX_GEOCODE_LIMIT


def fetch_reverse_geocode(lat: float, lon: float) -> Optional[Dict[str, Optional[str]]]:
    """Fetch reverse geocode data from Mapbox and extract neighborhood/place/poi."""
    if not MAPBOX_ACCESS_TOKEN:
        return None

    url = f"{MAPBOX_GEOCODE_BASE_URL}/{lon},{lat}.json"
    params = {
        "access_token": MAPBOX_ACCESS_TOKEN,
        "types": "poi,neighborhood,place,locality,address",
    }

    with httpx.Client(timeout=10) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    features = data.get("features", []) if isinstance(data, dict) else []
    neighborhood = None
    place = None
    poi = None

    for feature in features:
        types = feature.get("place_type", [])
        text = feature.get("text")
        if not text:
            continue
        if "neighborhood" in types and neighborhood is None:
            neighborhood = text
        if any(t in types for t in ["place", "locality"]) and place is None:
            place = text
        if "poi" in types and poi is None:
            poi = text

    return {
        "neighborhood": neighborhood,
        "place": place,
        "poi": poi,
    }