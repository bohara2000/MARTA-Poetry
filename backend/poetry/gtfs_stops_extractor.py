"""
Extract major stops from GTFS data for a given route.
"""
import csv
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter

GTFS_DIR = Path(__file__).parent.parent / "data" / "gtfs"


def get_major_stops_for_route(route_id: str, limit: int = 5) -> List[str]:
    """
    Extract the most frequently served stops for a given route from GTFS data.
    
    Args:
        route_id: The GTFS route_id (e.g., "27331" for Route 12)
        limit: Maximum number of stops to return (default 5)
    
    Returns:
        List of stop names, ordered by frequency (most common first)
    """
    # Step 1: Get all trip_ids for this route
    trip_ids: Set[str] = set()
    trips_file = GTFS_DIR / "trips.txt"
    
    with open(trips_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['route_id'] == route_id:
                trip_ids.add(row['trip_id'])
    
    if not trip_ids:
        return []
    
    # Step 2: Get all stop_ids from stop_times for these trips
    stop_counter = Counter()
    stop_times_file = GTFS_DIR / "stop_times.txt"
    
    with open(stop_times_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['trip_id'] in trip_ids:
                stop_counter[row['stop_id']] += 1
    
    # Step 3: Get the most common stops
    most_common_stop_ids = [stop_id for stop_id, _ in stop_counter.most_common(limit * 3)]
    
    # Step 4: Map stop_ids to stop_names
    stop_names: Dict[str, str] = {}
    stops_file = GTFS_DIR / "stops.txt"
    
    with open(stops_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['stop_id'] in most_common_stop_ids:
                stop_names[row['stop_id']] = row['stop_name']
    
    # Step 5: Return top stop names, deduplicated
    result = []
    seen_names = set()
    
    for stop_id in most_common_stop_ids:
        if stop_id in stop_names:
            name = stop_names[stop_id]
            # Simple deduplication - skip if we've seen this exact name
            if name not in seen_names:
                result.append(name)
                seen_names.add(name)
                if len(result) >= limit:
                    break
    
    return result


def get_route_id_from_number(route_number: str) -> str:
    """
    Find the GTFS route_id for a given route number.
    
    Args:
        route_number: The route number (e.g., "5", "12", "27")
    
    Returns:
        The GTFS route_id, or empty string if not found
    """
    routes_file = GTFS_DIR / "routes.txt"
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['route_short_name'] == route_number:
                return row['route_id']
    
    return ""


if __name__ == "__main__":
    # Test with Route 12
    route_id = get_route_id_from_number("12")
    if route_id:
        print(f"Route 12 GTFS ID: {route_id}")
        stops = get_major_stops_for_route(route_id)
        print(f"Major stops: {stops}")
