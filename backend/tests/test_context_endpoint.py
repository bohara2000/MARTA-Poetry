"""Integration tests for /api/context endpoint."""

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from google.transit import gtfs_realtime_pb2

import app as app_module
from app import app
from services.context_contract import validate_context_payload
from services.context_service import HistoryCache


class DummyResponse:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class DummyClient:
    def __init__(self, responses):
        self._responses = responses

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def get(self, url: str, headers=None, params=None):
        return self._responses[url]


def _build_feed(route_id: str) -> bytes:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    entity = feed.entity.add()
    entity.id = "vehicle-1"
    entity.vehicle.trip.route_id = route_id
    entity.vehicle.position.latitude = 33.75
    entity.vehicle.position.longitude = -84.39
    entity.vehicle.timestamp = 1700000000
    return feed.SerializeToString()


client = TestClient(app)


def test_context_endpoint_success():
    response = client.get("/api/context", params={"route_id": "MARTA_5"})
    assert response.status_code == 200
    payload = response.json()
    is_valid, errors = validate_context_payload(payload)
    assert is_valid, f"Invalid payload: {errors}"


def test_context_endpoint_missing_route_id():
    response = client.get("/api/context")
    assert response.status_code == 422


def test_context_endpoint_with_gtfs_rt(monkeypatch):
    route_id = "MARTA_5"
    url = "https://example.com/vehicle_positions.pb"

    responses = {
        url: DummyResponse(_build_feed(route_id))
    }

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(responses)

    monkeypatch.setattr("services.context_service.GTFS_RT_ENABLED", True)
    monkeypatch.setattr("services.gtfs_realtime_service.GTFS_RT_VEHICLE_POSITIONS_URL", url)
    monkeypatch.setattr("services.gtfs_realtime_service.httpx.Client", dummy_client_factory)

    response = client.get("/api/context", params={"route_id": route_id})
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["source_timestamps"]["gtfs_rt"] is not None


def test_context_endpoint_with_weather(monkeypatch):
    monkeypatch.setattr("services.context_service.NWS_ENABLED", True)
    monkeypatch.setattr(
        "services.context_service.fetch_weather",
        lambda lat, lon: {"point": {"properties": {}}, "forecast": {"properties": {}}},
    )

    response = client.get("/api/context", params={"route_id": "MARTA_5"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["signals"]["weather"] is not None


def test_context_endpoint_weather_disabled(monkeypatch):
    monkeypatch.setattr("services.context_service.NWS_ENABLED", False)

    response = client.get("/api/context", params={"route_id": "MARTA_5"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["signals"]["weather"] is None


def test_context_endpoint_with_rail_rt(monkeypatch):
    monkeypatch.setattr("services.context_service.RAIL_RT_ENABLED", True)
    monkeypatch.setattr(
        "services.context_service.load_route_personality",
        lambda route_id: {"name": route_id, "route_mode": "train", "major_stops": []},
    )
    monkeypatch.setattr(
        "services.context_service.fetch_rail_realtime",
        lambda: [{"STATION": "FIVE POINTS", "LINE": "RED"}],
    )

    response = client.get("/api/context", params={"route_id": "MARTA_1"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["live_position"]["rail_realtime"]


def test_context_endpoint_rail_rt_disabled(monkeypatch):
    monkeypatch.setattr("services.context_service.RAIL_RT_ENABLED", False)
    monkeypatch.setattr(
        "services.context_service.load_route_personality",
        lambda route_id: {"name": route_id, "route_mode": "train", "major_stops": []},
    )

    response = client.get("/api/context", params={"route_id": "MARTA_1"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["live_position"] is None


def test_context_endpoint_with_mapbox(monkeypatch):
    app_module.context_service.geocode_cache = {}
    monkeypatch.setattr("services.context_service.MAPBOX_ENABLED", True)
    monkeypatch.setattr(
        "services.context_service.fetch_reverse_geocode",
        lambda lat, lon: {"neighborhood": "Midtown", "place": "Atlanta", "poi": "Piedmont Park"},
    )
    monkeypatch.setattr(
        "services.context_service.fetch_vehicle_positions",
        lambda route_id: {"route_id": route_id, "latitude": 33.751, "longitude": -84.391, "timestamp": "2026-02-07T12:00:00Z"},
    )
    monkeypatch.setattr("services.context_service.GTFS_RT_ENABLED", True)

    response = client.get("/api/context", params={"route_id": "MARTA_5"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["live_anchor"]["neighborhood"] == "Midtown"


def test_context_endpoint_with_traffic(monkeypatch):
    monkeypatch.setattr("services.context_service.MAPBOX_TRAFFIC_ENABLED", True)
    monkeypatch.setattr("services.context_service.GTFS_RT_ENABLED", True)
    monkeypatch.setattr(
        "services.context_service.fetch_vehicle_positions",
        lambda route_id: {"route_id": route_id, "latitude": 33.75, "longitude": -84.39, "timestamp": "2026-02-07T12:00:00Z"},
    )
    monkeypatch.setattr(
        "services.context_service.fetch_traffic_congestion",
        lambda lat, lon: {"level": "moderate", "counts": {"moderate": 2}},
    )

    response = client.get("/api/context", params={"route_id": "MARTA_5"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["signals"]["traffic"]["level"] == "moderate"


def test_context_endpoint_with_solar(monkeypatch):
    app_module.context_service.solar_cache = {}
    monkeypatch.setattr("services.context_service.SOLAR_EVENTS_ENABLED", True)
    monkeypatch.setattr(
        "services.context_service.fetch_solar_events",
        lambda lat, lon: {"sunrise": "2026-02-07T12:00:00+00:00", "sunset": "2026-02-07T22:00:00+00:00"},
    )

    response = client.get("/api/context", params={"route_id": "MARTA_5"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["signals"]["solar"]["sunrise"] == "2026-02-07T12:00:00+00:00"


def test_context_endpoint_with_history(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "history_cache.sqlite"
        app_module.context_service.history_cache = HistoryCache(cache_path)

        monkeypatch.setattr("services.context_service.HISTORY_CONTEXT_ENABLED", True)
        monkeypatch.setattr(
            "services.context_service.fetch_history_context",
            lambda anchors, max_items: [
                {
                    "source": "wikipedia",
                    "title": "Midtown Atlanta",
                    "snippet": "Neighborhood in Atlanta",
                }
            ],
        )
        monkeypatch.setattr(
            "services.context_service.ContextService._get_live_anchor",
            lambda self, route_id, route_mode: (
                {"neighborhood": "Midtown", "place": "Atlanta", "poi": None},
                False,
                None,
            ),
        )

        response = client.get("/api/context", params={"route_id": "MARTA_5"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["history"][0]["source"] == "wikipedia"


def test_context_endpoint_history_fallback_anchors(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "history_cache.sqlite"
        app_module.context_service.history_cache = HistoryCache(cache_path)

        monkeypatch.setattr("services.context_service.HISTORY_CONTEXT_ENABLED", True)
        monkeypatch.setattr(
            "services.context_service.fetch_history_context",
            lambda anchors, max_items: [
                {
                    "source": "wikipedia",
                    "title": anchors[0],
                    "snippet": "Fallback anchor history",
                }
            ],
        )
        monkeypatch.setattr(
            "services.context_service.ContextService._get_live_anchor",
            lambda self, route_id, route_mode: (
                {"neighborhood": None, "place": None, "poi": None},
                False,
                None,
            ),
        )
        monkeypatch.setattr(
            "services.context_service.load_route_personality",
            lambda route_id: {"name": route_id, "route_mode": "bus", "major_stops": ["Cheshire Bridge Road", "Midtown", "East Point"]},
        )

        response = client.get("/api/context", params={"route_id": "MARTA_5"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["history"][0]["snippet"] == "Fallback anchor history"
