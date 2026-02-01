# Adding and Editing Routes

## Route Data Structure

Each route needs a complete personality profile with these fields:

```json
{
  "MARTA_5": {
    "name": "Route 5 - Peachtree",
    "description": "Downtown's pulse, alliterative and alive",
    "route_mode": "bus",
    "major_stops": [
      "Peachtree & Ellis",
      "Peachtree Center",
      "Peachtree & North Avenue",
      "Peachtree & 5th",
      "Peachtree Station"
    ],
    "loyalty_to_canon": 0.9,
    "rebellious_mode": null,
    "sound_preferences": {
      "alliteration": 0.95,
      "repetition": 0.8,
      "internal_rhyme": 0.4
    },
    "theme_affinities": {
      "urban_life": 0.95,
      "morning": 0.8,
      "transition": 0.7
    }
  }
}
```

## Required Fields

- **`name`** (string): Route identifier with corridor (e.g., "Route 5 - Peachtree")
- **`description`** (string): 1-2 sentence poetic description of the route's character
- **`route_mode`** (string): Either `"bus"` or `"train"` - determines what imagery constraints apply
- **`major_stops`** (array): 3-5 main stops the route serves (for geographic grounding)
- **`loyalty_to_canon`** (float): 0.0-1.0 - How much does this route adhere to the core narrative?
  - 0.0-0.3: Rebellious, inverts or ignores the canon
  - 0.4-0.6: Balanced, engages selectively
  - 0.7-1.0: Loyal, supports and embraces canonical themes
- **`rebellious_mode`** (string or null): How does the route relate to canon?
  - `null`: No special rebellious behavior
  - `"ignore"`: Ignores canon, does own thing
  - `"invert"`: Subverts and inverts canonical themes
  - `"create_new"`: Pioneers entirely unexplored territory
- **`sound_preferences`** (object): Sound device affinities (0.0-1.0)
  - `alliteration`, `repetition`, `internal_rhyme`, `anaphora`, `assonance`, `consonance`
- **`theme_affinities`** (object): Thematic preferences (0.0-1.0)
  - Examples: `urban_life`, `transition`, `isolation`, `community`, `observation`, `surveillance`, `freedom`

## Adding a New Route

### Option 1: Use the Admin UI (Recommended)

1. Open the admin panel in the web interface (click "Admin Panel" button)
2. Navigate to "Route Personalities" tab
3. Click "+ Create New Route"
4. Select an unassigned route from the dropdown
5. Fill in description, loyalty_to_canon, and preferences
6. Click Save

**Automatic GTFS Integration:** When creating a route through the UI or API, the system automatically:
- Fetches the 5 most frequently-served stops from GTFS data
- Sets `route_mode` to "bus" or "train" based on GTFS route type (train lines are labeled as train in the dropdown)
- Validates all required fields

No need to manually specify stops - they're extracted from real transit data!

### Option 2: Use the REST API

```bash
curl -X POST http://localhost:8000/api/routes/create \
  -H "Content-Type: application/json" \
  -d '{
    "route_number": "27",
    "route_name": "North Avenue",
    "description": "Quick-paced uptown runner",
    "loyalty_to_canon": 0.6,
    "rebellious_mode": null
  }'
```

Or via the personalities endpoint:

```bash
curl -X PUT http://localhost:8000/api/personalities/MARTA_27 \
  -H "Content-Type: application/json" \
  -d '{
    "personality": {
      "name": "Route 27 - North Avenue",
      "description": "Quick-paced uptown runner",
      "loyalty_to_canon": 0.6,
      "rebellious_mode": null,
      "sound_preferences": {},
      "theme_affinities": {"urban_life": 0.9}
    }
  }'
```

**Note:** Both endpoints automatically fetch GTFS stops if not provided.

### Option 3: Use Python Template Generator

```python
from poetry.route_schema import get_route_template
import json

# Create template (stops auto-populated from GTFS)
template = get_route_template("27", "North Avenue", "bus")

# Customize
template["description"] = "Quick-paced uptown runner"
template["loyalty_to_canon"] = 0.6
template["theme_affinities"]["urban_life"] = 0.9

# Save
routes = json.load(open("data/route_personalities.json"))
routes["MARTA_27"] = template
json.dump(routes, open("data/route_personalities.json", "w"), indent=2)
```

### Option 4: Manual Edit (Advanced)

1. Open `backend/data/route_personalities.json`
2. Copy Route 5 entry and modify
3. Change all fields to match your route
4. Ensure `route_mode` matches GTFS data (bus vs train)
5. You can manually specify `major_stops`, or leave empty and run the API endpoints to auto-populate

## GTFS Integration

The system automatically extracts real stop data from GTFS (General Transit Feed Specification) files:

**How it works:**
1. Route number or GTFS ID is provided (e.g., "39" or "27345")
2. System looks up the route in `data/gtfs/routes.txt`
3. Finds all trips for that route in `data/gtfs/trips.txt`
4. Counts stop frequencies across all trips in `data/gtfs/stop_times.txt`
5. Returns the 5 most frequently-served stops

**Supported formats:**
- Short route names: "5", "39", "12" (e.g., MARTA_5)
- GTFS route IDs: "27345", "27331" (e.g., MARTA_27345)

If a route doesn't exist in GTFS data, the system falls back to placeholder stops: `["[Stop 1]", "[Stop 2]", "[Stop 3]"]`

## Validation

To check if all routes have valid schemas:

```bash
cd backend
python3 poetry/route_schema.py
```

To migrate and fill in defaults for any incomplete routes:

```bash
python3 poetry/route_schema.py migrate
```

This will create a backup file and update any missing required fields with sensible defaults.

## Key Rules for Authentic Poems

1. **Bus routes**: Use bus imagery (diesel, hydraulic doors, mirrors, rubber, asphalt)
2. **Train routes**: Use train imagery (steel rails, third rails, overhead lines, stations)
3. **Never mention route number directly** in poems (use stops and human names)
4. **Use geographic grounding** - reference actual stops and corridors
5. **Respect loyalty**: High-loyalty routes embrace canonical themes, low-loyalty routes resist/invert them

## Example Routes

### High Loyalty (0.8+)
- Route 5 - Peachtree: "Downtown's pulse" embraces surveillance/control narrative
- Action: Emphasize camera networks, observation, system efficiency

### Low Loyalty (0.3-)
- Route 21 - Memorial Drive: "Night runner, rebellious voice" inverts narrative
- Action: Emphasize escape routes, hidden spaces, resistance

### Balanced (0.4-0.6)
- Action: Mix canonical and subversive elements, show ambivalence
