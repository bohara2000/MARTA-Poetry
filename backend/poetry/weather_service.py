"""Compatibility wrapper for weather service."""

from services.weather_service import fetch_nws_forecast, fetch_nws_point, fetch_weather

__all__ = ["fetch_nws_forecast", "fetch_nws_point", "fetch_weather"]
