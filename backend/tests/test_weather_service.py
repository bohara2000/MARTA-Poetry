"""Unit tests for NWS weather service."""

from typing import Any, Dict

import services.weather_service as weather_service


class DummyResponse:
    def __init__(self, payload: Dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> Dict[str, Any]:
        return self._payload


class DummyClient:
    def __init__(self, responses: Dict[str, DummyResponse]):
        self._responses = responses
        self.requests = []

    def __enter__(self) -> "DummyClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, url: str, headers=None):
        self.requests.append((url, headers))
        return self._responses[url]


def test_fetch_weather_happy_path(monkeypatch):
    lat, lon = 33.75, -84.39
    point_url = f"https://api.weather.gov/points/{lat},{lon}"
    forecast_url = "https://api.weather.gov/gridpoints/FFC/52,88/forecast"

    point_payload = {
        "properties": {
            "forecast": forecast_url,
        }
    }
    forecast_payload = {
        "properties": {
            "periods": [
                {"name": "Tonight", "temperature": 65, "shortForecast": "Clear"}
            ]
        }
    }

    responses = {
        point_url: DummyResponse(point_payload),
        forecast_url: DummyResponse(forecast_payload),
    }

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(responses)

    monkeypatch.setattr(weather_service.httpx, "Client", dummy_client_factory)

    result = weather_service.fetch_weather(lat, lon)
    assert result["point"]["properties"]["forecast"] == forecast_url
    assert result["forecast"]["properties"]["periods"][0]["name"] == "Tonight"


def test_fetch_nws_point_error(monkeypatch):
    lat, lon = 0.0, 0.0
    point_url = f"https://api.weather.gov/points/{lat},{lon}"

    responses = {
        point_url: DummyResponse({"error": "bad"}, status_code=500)
    }

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(responses)

    monkeypatch.setattr(weather_service.httpx, "Client", dummy_client_factory)

    try:
        weather_service.fetch_nws_point(lat, lon)
        assert False, "Expected error"
    except RuntimeError as exc:
        assert "HTTP 500" in str(exc)
