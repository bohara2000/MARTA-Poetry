import os
from typing import Any, Dict

import httpx


NWS_USER_AGENT = os.getenv("NWS_USER_AGENT", "MARTA-Poetry/1.0 (contact: dev@example.com)")


def fetch_nws_point(lat: float, lon: float) -> Dict[str, Any]:
    """Fetch NWS gridpoint metadata for a lat/lon."""
    url = f"https://api.weather.gov/points/{lat},{lon}"
    headers = {"User-Agent": NWS_USER_AGENT}
    with httpx.Client(timeout=10) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


def fetch_nws_forecast(forecast_url: str) -> Dict[str, Any]:
    """Fetch NWS forecast from a forecast URL."""
    headers = {"User-Agent": NWS_USER_AGENT}
    with httpx.Client(timeout=10) as client:
        response = client.get(forecast_url, headers=headers)
        response.raise_for_status()
        return response.json()


def fetch_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Fetch NWS forecast data for a lat/lon."""
    point_data = fetch_nws_point(lat, lon)
    forecast_url = point_data["properties"]["forecast"]
    forecast_data = fetch_nws_forecast(forecast_url)
    return {
        "point": point_data,
        "forecast": forecast_data,
    }