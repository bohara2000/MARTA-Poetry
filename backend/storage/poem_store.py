import os
import json
from datetime import datetime

class PoemStore:
    def __init__(self, storage_dir="poems"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _poem_filename(self, route, timestamp):
        safe_timestamp = timestamp.replace(":", "-").replace("T", "_")
        return os.path.join(self.storage_dir, f"route_{route}_{safe_timestamp}.json")

    def save_poem(self, route, poem_text, story_influence, traits, timestamp=None):
        if not timestamp:
            timestamp = datetime.utcnow().isoformat()
        poem_data = {
            "route": route,
            "timestamp": timestamp,
            "story_influence": story_influence,
            "poem": poem_text,
            "traits": traits
        }
        filename = self._poem_filename(route, timestamp)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(poem_data, f, indent=2)
        return filename

    def get_poems_for_route(self, route):
        poems = []
        for fname in os.listdir(self.storage_dir):
            if fname.startswith(f"route_{route}_"):
                with open(os.path.join(self.storage_dir, fname), "r", encoding="utf-8") as f:
                    poems.append(json.load(f))
        return poems

    def get_all_poems(self):
        poems = []
        for fname in os.listdir(self.storage_dir):
            if fname.endswith(".json"):
                with open(os.path.join(self.storage_dir, fname), "r", encoding="utf-8") as f:
                    poems.append(json.load(f))
        return poems
    
    def delete_poem(self, route, timestamp):
        safe_timestamp = timestamp.replace(":", "-").replace("T", "_")
        filename = self._poem_filename(route, safe_timestamp)
        if os.path.exists(filename):
            os.remove(filename)
            return True
        return False
