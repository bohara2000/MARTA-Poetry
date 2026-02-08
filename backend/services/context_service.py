import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import (
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    GTFS_RT_ENABLED,
    HISTORY_CONTEXT_ENABLED,
    HISTORY_CONTEXT_MAX_ITEMS,
    MAPBOX_ENABLED,
    MAPBOX_TRAFFIC_ENABLED,
    MAPBOX_TRAFFIC_TTL_SECONDS,
    NWS_ENABLED,
    NWS_WEATHER_TTL_SECONDS,
    RAIL_RT_ENABLED,
    SOLAR_EVENTS_ENABLED,
    SOLAR_EVENTS_TTL_SECONDS,
)
from poetry.prompt_builder import load_route_personality
from services.gtfs_realtime_service import fetch_vehicle_positions
from services.history_context_service import fetch_history_context
from services.mapbox_geocode_service import fetch_reverse_geocode
from services.mapbox_traffic_service import fetch_traffic_congestion
from services.rail_realtime_service import fetch_rail_realtime
from services.solar_events_service import fetch_solar_events
from services.weather_service import fetch_weather


@dataclass
class CacheResult:
    value: Any
    hit: bool


class HistoryCache:
    """Persistent cache for historical context snippets."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def get(self, key: str) -> CacheResult:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM history_cache WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()
            if not row:
                return CacheResult(value=[], hit=False)
            try:
                return CacheResult(value=json.loads(row[0]), hit=True)
            except json.JSONDecodeError:
                return CacheResult(value=[], hit=True)

    def set(self, key: str, value: List[Dict[str, Any]]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO history_cache (key, value, updated_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()


class ContextService:
    """Builds a normalized route context payload."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data") / "cache"
        self.history_cache = HistoryCache(self.cache_dir / "history_cache.sqlite")
        self.geocode_cache: Dict[str, Tuple[float, Dict[str, Optional[str]]]] = {}
        self.weather_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self.traffic_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self.solar_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def build_context(self, route_id: str) -> Dict[str, Any]:
        personality = load_route_personality(route_id)
        fallback_anchors = [
            anchor
            for anchor in personality.get("major_stops", [])
            if isinstance(anchor, str) and anchor.strip()
        ]

        route_mode = personality.get("route_mode", "bus")
        live_anchor, geocode_hit, live_position = self._get_live_anchor(route_id, route_mode)
        history, history_hit = self._get_history_context(live_anchor, fallback_anchors)

        weather = self._get_weather(DEFAULT_LATITUDE, DEFAULT_LONGITUDE)
        traffic = self._get_traffic(live_position)
        solar = self._get_solar_events(DEFAULT_LATITUDE, DEFAULT_LONGITUDE)

        signals = {
            "traffic": traffic,
            "weather": weather,
            "solar": solar,
            "alerts": self._get_service_alerts(route_id),
        }

        payload = {
            "route_id": route_id,
            "live_anchor": live_anchor,
            "fallback_anchors": fallback_anchors,
            "signals": signals,
            "history": history,
            "meta": {
                "source_timestamps": {
                    "gtfs_rt": live_position.get("timestamp") if live_position else None,
                },
                "cache_hits": {
                    "geocode": geocode_hit,
                    "history": history_hit,
                },
                "live_position": live_position,
            },
        }

        return payload

    def _get_live_anchor(self, route_id: str, route_mode: str) -> Tuple[Dict[str, Optional[str]], bool, Optional[Dict[str, Any]]]:
        """Resolve live anchor via vehicle position + reverse geocode.

        Placeholder implementation until GTFS-RT + Mapbox are wired.
        """
        live_position = None
        if route_mode in ["train", "rail"] and RAIL_RT_ENABLED:
            try:
                rail_data = fetch_rail_realtime()
                if rail_data:
                    live_position = {
                        "route_id": route_id,
                        "rail_realtime": rail_data,
                    }
            except Exception:
                live_position = None
        elif GTFS_RT_ENABLED:
            try:
                live_position = fetch_vehicle_positions(route_id)
            except Exception:
                live_position = None

        lat = None
        lon = None
        if live_position and "latitude" in live_position and "longitude" in live_position:
            lat = live_position["latitude"]
            lon = live_position["longitude"]

        cache_key = f"{route_id}:live_anchor"
        if lat is not None and lon is not None:
            cache_key = f"{route_id}:{lat:.5f},{lon:.5f}"

        cached = self.geocode_cache.get(cache_key)
        if cached:
            return cached[1], True, live_position

        live_anchor = {
            "neighborhood": None,
            "place": None,
            "poi": None,
        }

        if MAPBOX_ENABLED and lat is not None and lon is not None:
            try:
                geocoded = fetch_reverse_geocode(lat, lon)
                if geocoded:
                    live_anchor.update(geocoded)
            except Exception:
                pass
        self.geocode_cache[cache_key] = (datetime.now(timezone.utc).timestamp(), live_anchor)
        return live_anchor, False, live_position

    def _get_history_context(
        self,
        live_anchor: Dict[str, Optional[str]],
        fallback_anchors: List[str]
    ) -> Tuple[List[Dict[str, Any]], bool]:
        key_parts = [value for value in live_anchor.values() if value]
        if not key_parts:
            key_parts = [anchor for anchor in fallback_anchors if isinstance(anchor, str) and anchor.strip()][:3]
        if not key_parts:
            return [], False
        cache_key = "|".join(key_parts)
        cached = self.history_cache.get(cache_key)
        if cached.hit and cached.value:
            return cached.value, True

        if not HISTORY_CONTEXT_ENABLED:
            return cached.value if cached.hit else [], cached.hit

        try:
            fetched = fetch_history_context(key_parts, HISTORY_CONTEXT_MAX_ITEMS)
        except Exception:
            fetched = []

        if fetched:
            self.history_cache.set(cache_key, fetched)
            return fetched, False

        return cached.value if cached.hit else [], cached.hit

    def _get_service_alerts(self, route_id: str) -> List[Dict[str, Any]]:
        return []

    def _get_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        if not NWS_ENABLED:
            return None

        cache_key = f"{lat:.4f},{lon:.4f}"
        cached = self.weather_cache.get(cache_key)
        if cached:
            timestamp, payload = cached
            if time.time() - timestamp < NWS_WEATHER_TTL_SECONDS:
                return payload

        try:
            payload = fetch_weather(lat, lon)
        except Exception:
            return None

        self.weather_cache[cache_key] = (time.time(), payload)
        return payload

    def _get_traffic(self, live_position: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not MAPBOX_TRAFFIC_ENABLED:
            return None

        if not live_position:
            return None

        lat = live_position.get("latitude")
        lon = live_position.get("longitude")
        if lat is None or lon is None:
            return None

        cache_key = f"{lat:.5f},{lon:.5f}"
        cached = self.traffic_cache.get(cache_key)
        if cached:
            timestamp, payload = cached
            if time.time() - timestamp < MAPBOX_TRAFFIC_TTL_SECONDS:
                return payload

        try:
            payload = fetch_traffic_congestion(lat, lon)
        except Exception:
            return None

        if payload is None:
            return None

        self.traffic_cache[cache_key] = (time.time(), payload)
        return payload

    def _get_solar_events(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        if not SOLAR_EVENTS_ENABLED:
            return None

        cache_key = f"{lat:.4f},{lon:.4f}"
        cached = self.solar_cache.get(cache_key)
        if cached:
            timestamp, payload = cached
            if time.time() - timestamp < SOLAR_EVENTS_TTL_SECONDS:
                return payload

        try:
            payload = fetch_solar_events(lat, lon)
        except Exception:
            return None

        if payload is None:
            return None

        self.solar_cache[cache_key] = (time.time(), payload)
        return payload