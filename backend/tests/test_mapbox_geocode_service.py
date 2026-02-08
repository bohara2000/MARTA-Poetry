"""Unit tests for Mapbox reverse geocode service."""

import services.mapbox_geocode_service as mapbox_service


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


def test_fetch_reverse_geocode(monkeypatch):
    monkeypatch.setattr(mapbox_service, "MAPBOX_ACCESS_TOKEN", "test-token")

    payload = {
        "features": [
            {"text": "Midtown", "place_type": ["neighborhood"]},
            {"text": "Atlanta", "place_type": ["place"]},
            {"text": "Piedmont Park", "place_type": ["poi"]},
        ]
    }

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(DummyResponse(payload))

    monkeypatch.setattr(mapbox_service.httpx, "Client", dummy_client_factory)

    result = mapbox_service.fetch_reverse_geocode(33.75, -84.39)
    assert result == {
        "neighborhood": "Midtown",
        "place": "Atlanta",
        "poi": "Piedmont Park",
    }


def test_fetch_reverse_geocode_no_token(monkeypatch):
    monkeypatch.setattr(mapbox_service, "MAPBOX_ACCESS_TOKEN", None)
    result = mapbox_service.fetch_reverse_geocode(33.75, -84.39)
    assert result is None
