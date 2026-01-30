import random
import json
import os
from .route_schema import validate_route, get_route_template

# Optional: Load route-specific profiles from JSON (for future expansion)
CHARACTER_PROFILES_PATH = os.path.join(os.path.dirname(__file__), "../data/character_profiles.json")
ROUTE_PERSONALITIES_PATH = os.path.join(os.path.dirname(__file__), "../data/route_personalities.json")

# Default trait pools
ALIGNMENTS = ["lawful good", "chaotic good", "neutral", "chaotic neutral", "lawful evil"]
TONES = ["dreamy", "gritty", "urgent", "reflective", "chaotic"]
QUIRKS = [
    "hums at stops",
    "tells tall tales",
    "pauses for graffiti",
    "prefers left turns",
    "compulsively syncopates",
    "refuses to stop for geese"
]

# Simple function for now; could expand to use loaded profiles later
def get_route_personality(route_id):
    """
    Retrieve a character profile based on the route ID.
    Loads from route_personalities.json (new enriched format).
    Falls back to character_profiles.json (legacy format).
    Validates that all required fields are present.
    """
    route_key = f"MARTA_{route_id}" if not str(route_id).startswith("MARTA_") else str(route_id)
    
    # Try new enriched route_personalities.json first
    try:
        with open(ROUTE_PERSONALITIES_PATH, "r", encoding="utf-8") as f:
            personalities = json.load(f)
            if route_key in personalities:
                personality = personalities[route_key]
                is_valid, missing = validate_route(route_key, personality)
                if not is_valid:
                    print(f"⚠️ Route {route_key} missing fields: {missing}")
                    # Fill in defaults for missing fields
                    for field in missing:
                        if field == "route_mode":
                            personality["route_mode"] = "bus"
                        elif field == "major_stops":
                            personality["major_stops"] = ["[Unknown Stop]"]
                return personality
    except FileNotFoundError:
        pass
    
    # Fall back to legacy character_profiles.json
    try:
        with open(CHARACTER_PROFILES_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)
            if str(route_id) in profiles:
                return profiles[str(route_id)]
    except FileNotFoundError:
        pass

    # Fallback: Generate random traits with required fields
    personality = {
        "name": f"Route {route_id}",
        "description": "A MARTA route finding its voice",
        "route_mode": "bus",
        "major_stops": ["[Stop 1]", "[Stop 2]", "[Stop 3]"],
        "alignment": random.choice(ALIGNMENTS),
        "tone": random.choice(TONES),
        "quirks": random.sample(QUIRKS, 2),
        "loyalty_to_canon": 0.5,
        "rebellious_mode": None,
        "sound_preferences": {
            "alliteration": 0.5,
            "repetition": 0.5,
            "internal_rhyme": 0.3
        },
        "theme_affinities": {
            "urban_life": 0.5,
            "transition": 0.5
        }
    }
    
    return personality
        
    # Return the personality traits
    return personality
