"""Unit tests for Mapbox traffic service."""

import services.mapbox_traffic_service as traffic_service


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


def test_fetch_traffic_congestion(monkeypatch):
    monkeypatch.setattr(traffic_service, "MAPBOX_ACCESS_TOKEN", "test-token")

    payload = {
        "routes": [
            {
                "legs": [
                    {
                        "annotation": {
                            "congestion": ["low", "low", "moderate"]
                        }
                    }
                ]
            }
        ]
    }

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(DummyResponse(payload))

    monkeypatch.setattr(traffic_service.httpx, "Client", dummy_client_factory)

    result = traffic_service.fetch_traffic_congestion(33.75, -84.39)
    assert result["level"] == "low"
    assert result["counts"]["moderate"] == 1


def test_fetch_traffic_congestion_no_token(monkeypatch):
    monkeypatch.setattr(traffic_service, "MAPBOX_ACCESS_TOKEN", None)
    result = traffic_service.fetch_traffic_congestion(33.75, -84.39)
    assert result is None
