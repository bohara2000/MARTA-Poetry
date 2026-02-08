"""Unit tests for GTFS-Realtime service."""

from typing import Dict

import pytest
from google.transit import gtfs_realtime_pb2

import services.gtfs_realtime_service as gtfs_service


class DummyResponse:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


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


def _build_feed_without_position(route_id: str) -> bytes:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    entity = feed.entity.add()
    entity.id = "vehicle-1"
    entity.vehicle.trip.route_id = route_id
    entity.vehicle.timestamp = 1700000000
    return feed.SerializeToString()


def _build_feed_without_trip(route_id: str) -> bytes:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    entity = feed.entity.add()
    entity.id = "vehicle-1"
    entity.vehicle.position.latitude = 33.75
    entity.vehicle.position.longitude = -84.39
    return feed.SerializeToString()


def test_fetch_vehicle_positions(monkeypatch):
    route_id = "MARTA_5"
    url = "https://example.com/vehicle_positions.pb"

    monkeypatch.setattr(gtfs_service, "GTFS_RT_VEHICLE_POSITIONS_URL", url)
    monkeypatch.setattr(gtfs_service, "GTFS_RT_API_KEY", None)

    responses = {
        url: DummyResponse(_build_feed(route_id))
    }

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(responses)

    monkeypatch.setattr(gtfs_service.httpx, "Client", dummy_client_factory)

    result = gtfs_service.fetch_vehicle_positions(route_id)
    assert result is not None
    assert result["latitude"] == 33.75
    assert result["longitude"] == pytest.approx(-84.39)


def test_fetch_vehicle_positions_no_url(monkeypatch):
    monkeypatch.setattr(gtfs_service, "GTFS_RT_VEHICLE_POSITIONS_URL", None)
    result = gtfs_service.fetch_vehicle_positions("MARTA_5")
    assert result is None


def test_fetch_vehicle_positions_no_matching_route(monkeypatch):
    url = "https://example.com/vehicle_positions.pb"

    monkeypatch.setattr(gtfs_service, "GTFS_RT_VEHICLE_POSITIONS_URL", url)
    monkeypatch.setattr(gtfs_service, "GTFS_RT_API_KEY", None)

    responses = {
        url: DummyResponse(_build_feed("MARTA_99"))
    }

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(responses)

    monkeypatch.setattr(gtfs_service.httpx, "Client", dummy_client_factory)

    result = gtfs_service.fetch_vehicle_positions("MARTA_5")
    assert result is None


def test_fetch_vehicle_positions_missing_position(monkeypatch):
    url = "https://example.com/vehicle_positions.pb"

    monkeypatch.setattr(gtfs_service, "GTFS_RT_VEHICLE_POSITIONS_URL", url)
    monkeypatch.setattr(gtfs_service, "GTFS_RT_API_KEY", None)

    responses = {
        url: DummyResponse(_build_feed_without_position("MARTA_5"))
    }

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(responses)

    monkeypatch.setattr(gtfs_service.httpx, "Client", dummy_client_factory)

    result = gtfs_service.fetch_vehicle_positions("MARTA_5")
    assert result is None


def test_fetch_vehicle_positions_missing_trip(monkeypatch):
    url = "https://example.com/vehicle_positions.pb"

    monkeypatch.setattr(gtfs_service, "GTFS_RT_VEHICLE_POSITIONS_URL", url)
    monkeypatch.setattr(gtfs_service, "GTFS_RT_API_KEY", None)

    responses = {
        url: DummyResponse(_build_feed_without_trip("MARTA_5"))
    }

    def dummy_client_factory(*args, **kwargs):
        return DummyClient(responses)

    monkeypatch.setattr(gtfs_service.httpx, "Client", dummy_client_factory)

    result = gtfs_service.fetch_vehicle_positions("MARTA_5")
    assert result is None


def test_fetch_vehicle_positions_with_api_key(monkeypatch):
    route_id = "MARTA_5"
    url = "https://example.com/vehicle_positions.pb"

    monkeypatch.setattr(gtfs_service, "GTFS_RT_VEHICLE_POSITIONS_URL", url)
    monkeypatch.setattr(gtfs_service, "GTFS_RT_API_KEY", "test-key")

    responses = {
        url: DummyResponse(_build_feed(route_id))
    }

    client = DummyClient(responses)

    def dummy_client_factory(*args, **kwargs):
        return client

    monkeypatch.setattr(gtfs_service.httpx, "Client", dummy_client_factory)

    result = gtfs_service.fetch_vehicle_positions(route_id)
    assert result is not None
    assert client.requests[0][1] == {"x-api-key": "test-key"}
