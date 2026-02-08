import os
from dotenv import load_dotenv

load_dotenv()

GTFS_API_KEY = os.getenv("GTFS_API_KEY")
POETRY_MODE = os.getenv("POETRY_MODE", "production")
DEFAULT_STORY_INFLUENCE = float(os.getenv("DEFAULT_STORY_INFLUENCE", 0.7))
DEFAULT_LATITUDE = float(os.getenv("DEFAULT_LATITUDE", 33.7490))
DEFAULT_LONGITUDE = float(os.getenv("DEFAULT_LONGITUDE", -84.3880))
NWS_ENABLED = os.getenv("NWS_ENABLED", "false").lower() == "true"
NWS_WEATHER_TTL_SECONDS = int(os.getenv("NWS_WEATHER_TTL_SECONDS", 300))
GTFS_RT_ENABLED = os.getenv("GTFS_RT_ENABLED", "false").lower() == "true"
GTFS_RT_VEHICLE_POSITIONS_URL = os.getenv("GTFS_RT_VEHICLE_POSITIONS_URL")
GTFS_RT_API_KEY = os.getenv("GTFS_RT_API_KEY")
RAIL_RT_ENABLED = os.getenv("RAIL_RT_ENABLED", "false").lower() == "true"
RAIL_RT_URL = os.getenv("RAIL_RT_URL")
RAIL_RT_API_KEY = os.getenv("RAIL_RT_API_KEY")
MAPBOX_ENABLED = os.getenv("MAPBOX_ENABLED", "false").lower() == "true"
MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
MAPBOX_GEOCODE_BASE_URL = os.getenv(
    "MAPBOX_GEOCODE_BASE_URL",
    "https://api.mapbox.com/geocoding/v5/mapbox.places",
)
MAPBOX_GEOCODE_LIMIT = int(os.getenv("MAPBOX_GEOCODE_LIMIT", 5))
MAPBOX_TRAFFIC_ENABLED = os.getenv("MAPBOX_TRAFFIC_ENABLED", "false").lower() == "true"
MAPBOX_DIRECTIONS_BASE_URL = os.getenv(
    "MAPBOX_DIRECTIONS_BASE_URL",
    "https://api.mapbox.com/directions/v5/mapbox",
)
MAPBOX_TRAFFIC_TTL_SECONDS = int(os.getenv("MAPBOX_TRAFFIC_TTL_SECONDS", 120))
SOLAR_EVENTS_ENABLED = os.getenv("SOLAR_EVENTS_ENABLED", "false").lower() == "true"
SOLAR_EVENTS_TTL_SECONDS = int(os.getenv("SOLAR_EVENTS_TTL_SECONDS", 3600))
HISTORY_CONTEXT_ENABLED = os.getenv("HISTORY_CONTEXT_ENABLED", "false").lower() == "true"
HISTORY_CONTEXT_MAX_ITEMS = int(os.getenv("HISTORY_CONTEXT_MAX_ITEMS", 3))
HISTORY_CONTEXT_LOCATION_HINT = os.getenv("HISTORY_CONTEXT_LOCATION_HINT", "Atlanta, GA")
WIKIPEDIA_SUMMARY_BASE_URL = os.getenv(
    "WIKIPEDIA_SUMMARY_BASE_URL",
    "https://en.wikipedia.org/api/rest_v1/page/summary",
)
WIKIDATA_SEARCH_URL = os.getenv(
    "WIKIDATA_SEARCH_URL",
    "https://www.wikidata.org/w/api.php",
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_API_KEY_TITLES = os.getenv("AZURE_OPENAI_API_KEY_TITLES", AZURE_OPENAI_API_KEY)
AZURE_OPENAI_ENDPOINT_TITLES = os.getenv("AZURE_OPENAI_ENDPOINT_TITLES", AZURE_OPENAI_ENDPOINT)
AZURE_OPENAI_DEPLOYMENT_NAME_TITLES = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_TITLES", "gpt-4o")
AZURE_OPENAI_API_VERSION_TITLES = os.getenv("AZURE_OPENAI_API_VERSION_TITLES", AZURE_OPENAI_API_VERSION)

CHARACTER_DEFAULTS = {
    "alignment": "neutral",
    "tone": "reflective",
    "quirks": ["likes jazz", "hums at stops"],
}
