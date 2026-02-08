#!/usr/bin/env python3
"""Test Mapbox SDK reverse geocoding."""

import os
import sys
from pathlib import Path

# Ensure backend package imports resolve
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from mapbox import Geocoder


def main() -> int:
    token = os.getenv("MAPBOX_ACCESS_TOKEN")
    if not token:
        print("MAPBOX_ACCESS_TOKEN is not set.")
        return 1

    geocoder = Geocoder(access_token=token)

    # Midtown Atlanta coordinates (lon, lat)
    lon = -84.37285478478512
    lat = 33.763196115045986

    response = geocoder.reverse(lon=lon, lat=lat)

    if response.status_code != 200:
        print(f"Mapbox error: {response.status_code} {response.text}")
        return 2

    data = response.json()

    features = data.get("features", []) if isinstance(data, dict) else []
    neighborhood = None
    place = None
    poi = None

    for feature in features:
        types = feature.get("place_type", [])
        text = feature.get("text")
        if not text:
            continue
        if "neighborhood" in types and neighborhood is None:
            neighborhood = text
        if any(t in types for t in ["place", "locality"]) and place is None:
            place = text
        if "poi" in types and poi is None:
            poi = text

    print({
        "neighborhood": neighborhood,
        "place": place,
        "poi": poi,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
