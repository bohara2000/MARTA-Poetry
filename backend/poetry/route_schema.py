"""
Route Personality Schema and Migration Tool

This ensures all routes have consistent, complete data structure.
"""

import json
from pathlib import Path
from typing import Dict, Any

ROUTE_SCHEMA = {
    "name": "Required: Route # - Primary Street/Corridor",
    "description": "Required: 1-2 sentence poetic description of the route's character",
    "route_mode": "Required: 'bus' or 'train' - determines imagery constraints",
    "major_stops": "Required: List of 3-5 main stops the route serves",
    "loyalty_to_canon": "0.0-1.0: How much does this route adhere to canonical narrative?",
    "rebellious_mode": "null, 'ignore', 'invert', or 'create_new': How does it relate to canon?",
    "sound_preferences": "Dict of sound devices and their affinity (0.0-1.0)",
    "theme_affinities": "Dict of themes and their affinity (0.0-1.0)"
}

REQUIRED_FIELDS = [
    "name",
    "description", 
    "route_mode",
    "major_stops",
    "loyalty_to_canon",
    "rebellious_mode",
    "sound_preferences",
    "theme_affinities"
]

def validate_route(route_id: str, route_data: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate that a route has all required fields.
    
    Returns:
        (is_valid, list_of_missing_fields)
    """
    missing = []
    for field in REQUIRED_FIELDS:
        if field not in route_data:
            missing.append(field)
    
    return len(missing) == 0, missing

def get_route_template(route_number: str, route_name: str, mode: str = "bus") -> Dict[str, Any]:
    """
    Get a template for a new route with all required fields.
    
    Args:
        route_number: Route identifier (e.g., "5", "21", "27339")
        route_name: Primary corridor name (e.g., "Peachtree", "Memorial Drive")
        mode: "bus" or "train"
    
    Returns:
        Template dict ready to be customized
    """
    return {
        "name": f"Route {route_number} - {route_name}",
        "description": f"[FILL IN: 1-2 sentence poetic description of Route {route_number}'s character]",
        "route_mode": mode,
        "major_stops": [
            f"[FILL IN: Stop 1]",
            f"[FILL IN: Stop 2]", 
            f"[FILL IN: Stop 3]",
            f"[FILL IN: Stop 4]",
            f"[FILL IN: Stop 5]"
        ],
        "loyalty_to_canon": 0.5,  # Adjust based on route's relationship to narrative
        "rebellious_mode": None,  # null, 'ignore', 'invert', or 'create_new'
        "sound_preferences": {
            "alliteration": 0.5,
            "repetition": 0.5,
            "internal_rhyme": 0.3,
            "anaphora": 0.3,
            "assonance": 0.2
        },
        "theme_affinities": {
            "urban_life": 0.5,
            "transition": 0.5,
            "isolation": 0.3,
            "community": 0.4,
            "observation": 0.5
        }
    }

def migrate_routes(input_file: Path, output_file: Path) -> None:
    """
    Migrate existing routes to ensure they have all required fields.
    Preserves existing data, fills in defaults for missing fields.
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Route personalities file not found: {input_file}")
    
    with open(input_file, 'r') as f:
        routes = json.load(f)
    
    migrated = {}
    issues = []
    
    for route_id, route_data in routes.items():
        is_valid, missing = validate_route(route_id, route_data)
        
        if is_valid:
            migrated[route_id] = route_data
            print(f"✅ {route_id}: Complete")
        else:
            # Fill in missing fields with defaults
            print(f"⚠️ {route_id}: Missing fields: {', '.join(missing)}")
            issues.append((route_id, missing))
            
            # Add defaults for critical fields
            if "route_mode" not in route_data:
                route_data["route_mode"] = "bus"  # Default to bus
            if "major_stops" not in route_data:
                route_data["major_stops"] = ["[FILL IN STOPS]"]
            
            migrated[route_id] = route_data
    
    # Save migrated data
    with open(output_file, 'w') as f:
        json.dump(migrated, f, indent=2)
    
    print(f"\n📝 Migrated {len(migrated)} routes to {output_file}")
    
    if issues:
        print(f"\n⚠️ {len(issues)} routes need manual review:")
        for route_id, missing in issues:
            print(f"   {route_id}: needs {', '.join(missing)}")

def print_schema():
    """Print the route schema documentation."""
    print("=" * 70)
    print("ROUTE PERSONALITY SCHEMA")
    print("=" * 70)
    for field, description in ROUTE_SCHEMA.items():
        print(f"\n{field}:")
        print(f"  {description}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        input_file = Path(__file__).parent.parent / "data" / "route_personalities.json"
        output_file = input_file.with_stem(input_file.stem + "_migrated")
        migrate_routes(input_file, output_file)
        print(f"\nBackup available at: {output_file}")
    else:
        print_schema()
        print("\n\nTo generate a template for a new route:")
        print("  template = get_route_template('5', 'Peachtree', 'bus')")
        print("\nTo migrate existing routes:")
        print("  python3 route_schema.py migrate")
