"""Unit tests for rail realtime service."""

from typing import Any, Dict

import services.rail_realtime_service as rail_service


class DummyResponse:
    def __init__(self, payload: Any, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> Any:
        return self._payload


class DummyClient:
    def __init__(self, responses: Dict[str, DummyResponse]):
        self._responses = responses

    def __enter__(self) -> "DummyClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, url: str, params=None):
        return self._responses[url]


def test_fetch_rail_realtime(monkeypatch):
    url = "https://example.com/rail"
    payload = [{"STATION": "FIVE POINTS", "LINE": "RED"}]

    monkeypatch.setattr(rail_service, "RAIL_RT_URL", url)
    monkeypatch.setattr(rail_service, "RAIL_RT_API_KEY", "test-key")

    responses = {url: DummyResponse(payload)}

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(responses)

    monkeypatch.setattr(rail_service.httpx, "Client", dummy_client_factory)

    result = rail_service.fetch_rail_realtime()
    assert result == payload


def test_fetch_rail_realtime_no_url(monkeypatch):
    monkeypatch.setattr(rail_service, "RAIL_RT_URL", None)
    result = rail_service.fetch_rail_realtime()
    assert result is None
