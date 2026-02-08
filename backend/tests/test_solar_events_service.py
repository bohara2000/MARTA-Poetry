"""Unit tests for solar events service."""

from datetime import datetime, timezone

import services.solar_events_service as solar_service


class DummyResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class DummyClient:
    def __init__(self, response: DummyResponse):
        self._response = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def get(self, url: str, params=None):
        return self._response


def test_fetch_solar_events(monkeypatch):
    payload = {
        "status": "OK",
        "results": {
            "sunrise": "2026-02-07T12:00:00+00:00",
            "sunset": "2026-02-07T22:00:00+00:00",
        },
    }

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(DummyResponse(payload))

    monkeypatch.setattr(solar_service.httpx, "Client", dummy_client_factory)

    result = solar_service.fetch_solar_events(33.75, -84.39)
    assert result["sunrise"] == "2026-02-07T12:00:00+00:00"
    assert result["sunset"] == "2026-02-07T22:00:00+00:00"
    assert "phase" in result


def test_fetch_solar_events_bad_status(monkeypatch):
    payload = {"status": "INVALID_REQUEST"}

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(DummyResponse(payload))

    monkeypatch.setattr(solar_service.httpx, "Client", dummy_client_factory)

    result = solar_service.fetch_solar_events(33.75, -84.39)
    assert result is None


def test_compute_solar_phase():
    sunrise = "2026-02-07T12:00:00+00:00"
    sunset = "2026-02-07T22:00:00+00:00"

    dawn_time = datetime(2026, 2, 7, 12, 30, tzinfo=timezone.utc).isoformat()
    day_time = datetime(2026, 2, 7, 15, 0, tzinfo=timezone.utc).isoformat()
    night_time = datetime(2026, 2, 7, 23, 0, tzinfo=timezone.utc).isoformat()

    assert solar_service.compute_solar_phase(sunrise, sunset, dawn_time) == "dawn"
    assert solar_service.compute_solar_phase(sunrise, sunset, day_time) == "day"
    assert solar_service.compute_solar_phase(sunrise, sunset, night_time) == "night"
