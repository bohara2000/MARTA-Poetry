from collections import Counter
from typing import Any, Dict, Optional

import httpx

from config import MAPBOX_ACCESS_TOKEN, MAPBOX_DIRECTIONS_BASE_URL


def fetch_traffic_congestion(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Fetch a local traffic congestion summary using Mapbox Directions API.

    Uses a short segment offset north to sample congestion near the point.
    """
    if not MAPBOX_ACCESS_TOKEN:
        return None

    offset_lat = lat + 0.002  # ~200m north for local congestion sample
    coords = f"{lon},{lat};{lon},{offset_lat}"
    url = f"{MAPBOX_DIRECTIONS_BASE_URL}/driving-traffic/{coords}"

    params = {
        "access_token": MAPBOX_ACCESS_TOKEN,
        "annotations": "congestion",
        "overview": "false",
    }

    with httpx.Client(timeout=10) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    routes = data.get("routes", []) if isinstance(data, dict) else []
    if not routes:
        return None

    legs = routes[0].get("legs", [])
    if not legs:
        return None

    annotations = legs[0].get("annotation", {})
    congestion = annotations.get("congestion", [])
    if not congestion:
        return None

    counts = Counter(congestion)
    majority = counts.most_common(1)[0][0]
    return {
        "level": majority,
        "counts": dict(counts),
    }