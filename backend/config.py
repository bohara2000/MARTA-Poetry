import os
from dotenv import load_dotenv

load_dotenv()

GTFS_API_KEY = os.getenv("GTFS_API_KEY")
POETRY_MODE = os.getenv("POETRY_MODE", "production")
DEFAULT_STORY_INFLUENCE = float(os.getenv("DEFAULT_STORY_INFLUENCE", 0.7))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

CHARACTER_DEFAULTS = {
    "alignment": "neutral",
    "tone": "reflective",
    "quirks": ["likes jazz", "hums at stops"],
}
