from typing import Any, Dict, List, Optional

import httpx

from config import RAIL_RT_API_KEY, RAIL_RT_URL


def fetch_rail_realtime() -> Optional[List[Dict[str, Any]]]:
    """Fetch rail realtime arrivals from MARTA rail REST API."""
    if not RAIL_RT_URL:
        return None

    params = {}
    if RAIL_RT_API_KEY:
        params["apiKey"] = RAIL_RT_API_KEY

    with httpx.Client(timeout=10) as client:
        response = client.get(RAIL_RT_URL, params=params)
        response.raise_for_status()
        data = response.json()

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data") or data.get("results") or [data]
    return None