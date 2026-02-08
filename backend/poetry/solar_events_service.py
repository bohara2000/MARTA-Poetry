"""Compatibility wrapper for solar events service."""

from services.solar_events_service import compute_solar_phase, fetch_solar_events

__all__ = ["compute_solar_phase", "fetch_solar_events"]
