import random
import json
import os

# Optional: Load route-specific profiles from JSON (for future expansion)
CHARACTER_PROFILES_PATH = os.path.join(os.path.dirname(__file__), "../data/character_profiles.json")

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
    """
    random.seed(route_id)  # Deterministic for the same route

    # Optionally: Load predefined profiles
    try:
        with open(CHARACTER_PROFILES_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)
            if str(route_id) in profiles:
                return profiles[str(route_id)]
    except FileNotFoundError:
        profiles = {}

    # Fallback: Generate random traits
    personality = {
        "alignment": random.choice(ALIGNMENTS),
        "tone": random.choice(TONES),
        "quirks": random.sample(QUIRKS, 2)
    }
    
    # Save the generated personality to the profiles
    profiles[str(route_id)] = personality
    try:
        with open(CHARACTER_PROFILES_PATH, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=4)
    except Exception:
        pass  # Ignore file write errors
        
    # Return the personality traits
    return personality
