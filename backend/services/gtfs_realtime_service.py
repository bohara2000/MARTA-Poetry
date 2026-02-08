from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from google.transit import gtfs_realtime_pb2

from config import GTFS_RT_API_KEY, GTFS_RT_VEHICLE_POSITIONS_URL


def fetch_vehicle_positions(route_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a vehicle position for the given route_id.

    Returns a dict with lat/lon/timestamp if found, else None.
    """
    if not GTFS_RT_VEHICLE_POSITIONS_URL:
        return None

    headers = {}
    if GTFS_RT_API_KEY:
        headers["x-api-key"] = GTFS_RT_API_KEY

    feed = gtfs_realtime_pb2.FeedMessage()
    with httpx.Client(timeout=10) as client:
        response = client.get(GTFS_RT_VEHICLE_POSITIONS_URL, headers=headers)
        response.raise_for_status()
        feed.ParseFromString(response.content)

    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        vehicle = entity.vehicle
        if not vehicle.HasField("trip"):
            continue
        if vehicle.trip.route_id != route_id:
            continue
        if not vehicle.HasField("position"):
            continue
        position = vehicle.position

        return {
            "route_id": route_id,
            "latitude": position.latitude,
            "longitude": position.longitude,
            "timestamp": datetime.fromtimestamp(vehicle.timestamp or 0, tz=timezone.utc).isoformat(),
            "congestion_level": vehicle.congestion_level.name if vehicle.congestion_level else None,
        }

    return None