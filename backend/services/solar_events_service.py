from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

import httpx


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def compute_solar_phase(
    sunrise: Optional[str],
    sunset: Optional[str],
    reference_time: Optional[str]
) -> Optional[str]:
    sunrise_dt = _parse_iso_datetime(sunrise)
    sunset_dt = _parse_iso_datetime(sunset)
    reference_dt = _parse_iso_datetime(reference_time)

    if not sunrise_dt or not sunset_dt or not reference_dt:
        return None

    if reference_dt < sunrise_dt or reference_dt > sunset_dt:
        return "night"

    if reference_dt <= sunrise_dt + timedelta(minutes=90):
        return "dawn"

    return "day"


def fetch_solar_events(lat: float, lon: float, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch solar events (sunrise/sunset) from sunrise-sunset.org.

    Args:
        lat: Latitude
        lon: Longitude
        date: Optional date in YYYY-MM-DD format (defaults to today)
    """
    params = {
        "lat": lat,
        "lng": lon,
        "formatted": 0,
    }
    if date:
        params["date"] = date

    with httpx.Client(timeout=10) as client:
        response = client.get("https://api.sunrise-sunset.org/json", params=params)
        response.raise_for_status()
        data = response.json()

    if not isinstance(data, dict) or data.get("status") != "OK":
        return None

    results = data.get("results", {})
    sunrise = results.get("sunrise")
    sunset = results.get("sunset")

    retrieved_at = datetime.now(timezone.utc).isoformat()
    phase = compute_solar_phase(sunrise, sunset, retrieved_at)

    return {
        "sunrise": sunrise,
        "sunset": sunset,
        "timezone": "UTC",
        "retrieved_at": retrieved_at,
        "phase": phase,
    }