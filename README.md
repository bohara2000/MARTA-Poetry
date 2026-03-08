# MARTA-Poetry
The MARTA Poetry Project generates poetry inspired by transit data from the Metro Atlanta Rapid Transit Authority, using route "personalities", narrative elements, and real-time inputs.

The goal is to create a system that interacts with a core canon of poems that serve as what is called The Homunculus. Each route will, based on its personality, either work with or against the narrative elements of The Homunculus.

**Live app:** https://icy-sky-01432f40f.6.azurestaticapps.net

![MARTA-Poetry site - alpha](frontend/src/assets/MARTA-Poetry-example.png)

## Installation and Setup

### Prerequisites

- Python 3.8+ 
- Node.js 18+ and npm
- Git

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd MARTA-Poetry
   ```

2. **Set up Python virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the backend directory with the following entries:
   ```
   POETRY_MODE=[development or production]
   DEFAULT_STORY_INFLUENCE=0.7
   OPENAI_API_KEY=your_OPENAI_API_KEY_here
   AZURE_OPENAI_API_KEY=your_AZURE_OPENAI_API_KEY_here
   AZURE_OPENAI_ENDPOINT=your_AZURE_OPENAI_ENDPOINT_here
   AZURE_OPENAI_DEPLOYMENT_NAME=your_poem_generation_deployment
   AZURE_OPENAI_API_VERSION=2024-12-01-preview
   # Optional: separate deployment for title generation (recommended)
   AZURE_OPENAI_API_KEY_TITLES=your_AZURE_OPENAI_API_KEY_for_titles
   AZURE_OPENAI_ENDPOINT_TITLES=your_AZURE_OPENAI_ENDPOINT_for_titles
   AZURE_OPENAI_DEPLOYMENT_NAME_TITLES=gpt-4o
   AZURE_OPENAI_API_VERSION_TITLES=2024-12-01-preview
   # Route awareness + live context services (optional)
   GTFS_RT_ENABLED=false
   GTFS_RT_VEHICLE_POSITIONS_URL=your_gtfs_rt_vehicle_positions_url
   GTFS_RT_API_KEY=your_gtfs_rt_api_key
   RAIL_RT_ENABLED=false
   RAIL_RT_URL=your_marta_rail_rt_url
   RAIL_RT_API_KEY=your_rail_rt_api_key
   MAPBOX_ENABLED=false
   MAPBOX_ACCESS_TOKEN=your_mapbox_token
   MAPBOX_TRAFFIC_ENABLED=false
   NWS_ENABLED=false
   SOLAR_EVENTS_ENABLED=false
   HISTORY_CONTEXT_ENABLED=false
   HISTORY_CONTEXT_LOCATION_HINT=Atlanta, GA
   # Azure Blob Storage (for audio files and radio stream)
   AZURE_STORAGE_ACCOUNT_NAME=your_storage_account_name
   AZURE_STORAGE_ACCOUNT_KEY=your_storage_account_key
   AZURE_STORAGE_CONTAINER_AUDIO=audio
   AZURE_STORAGE_CONTAINER_RADIO=radio
   # Cosmos DB (poem storage)
   COSMOS_ENDPOINT=your_cosmos_endpoint
   COSMOS_KEY=your_cosmos_key
   COSMOS_DATABASE=poetry
   COSMOS_CONTAINER=poems
   ```

5. **Download GTFS data (required for automatic stop extraction):**
   ```bash
   chmod +x get_gtfs.sh
   ./get_gtfs.sh
   ```
   
   The GTFS data enables automatic extraction of real transit stops when creating new route personalities. Without it, routes will use placeholder stops.

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd ../frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

## Running the Application

### Start the Backend

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Activate virtual environment (if not already active):**
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Start the FastAPI server:**
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

   The backend API will be available at `http://localhost:8000`
   API documentation will be available at `http://localhost:8000/docs`

### Start the Frontend

1. **In a new terminal, navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

### Accessing the Application

Once both servers are running:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## Project Structure

```
MARTA-Poetry/
├── backend/                      # FastAPI backend
│   ├── app.py                    # Main FastAPI application
│   ├── admin_api.py              # Admin endpoints
│   ├── audio_service.py          # Text-to-speech + blob storage
│   ├── stream_generator.py       # Radio stream builder
│   ├── stream_uploader.py        # Uploads stream segments to blob storage
│   ├── config.py                 # Environment config
│   ├── poetry/                   # Core generation modules
│   │   ├── generator.py          # Poem generation engine
│   │   ├── prompt_builder.py     # Prompt construction
│   │   ├── talent_economy.py     # Emotional currency / extraction framework
│   │   ├── narrative_engine.py   # Homunculus + narrative tracking
│   │   ├── personality_routes.py # Per-route personalities
│   │   ├── route_agent.py        # Route-level poem orchestration
│   │   ├── character_agent.py    # Character voice layer
│   │   ├── context_service.py    # Live context aggregation
│   │   ├── graph/                # Poetry knowledge graph
│   │   ├── weather_service.py    # NWS weather signals
│   │   ├── solar_events_service.py
│   │   ├── gtfs_realtime_service.py
│   │   ├── mapbox_geocode_service.py
│   │   ├── mapbox_traffic_service.py
│   │   ├── rail_realtime_service.py
│   │   └── history_context_service.py
│   ├── services/                 # External integrations
│   │   └── cosmos_db_client.py   # Azure Cosmos DB client
│   ├── scripts/                  # Utility scripts
│   │   ├── graph_initializer.py
│   │   ├── narrative_manager.py
│   │   ├── poem_explorer.py
│   │   └── generate_report.py
│   └── data/                     # Local data files + GTFS
├── frontend/                     # React/Vite frontend
│   ├── src/
│   │   ├── App.jsx               # Main app shell
│   │   ├── RadioPage.jsx         # Standalone radio player
│   │   ├── components/           # UI components
│   │   │   ├── RadioPlayer.jsx
│   │   │   ├── PoetryDisplay.jsx
│   │   │   ├── AudioControls.jsx
│   │   │   ├── AdminPanel.jsx
│   │   │   ├── PoemManager.jsx
│   │   │   ├── NarrativeManager.jsx
│   │   │   ├── PersonalityManager.jsx
│   │   │   ├── ThemeManager.jsx
│   │   │   ├── SystemStatus.jsx
│   │   │   └── RouteSelector.jsx
│   │   ├── hooks/
│   │   │   └── useAuth.js        # Azure Static Web Apps auth hook
│   │   └── utils/
│   │       ├── api.js            # API base URL helper
│   │       └── formatPoem.js
│   └── staticwebapp.config.json  # SWA routing + AAD auth config
├── functions/                    # Azure Functions (scheduled jobs)
├── bicep/                        # Azure infrastructure as code
└── scripts/                      # Deployment + configuration scripts
```

## Key Features

### Poem Management
- **Generate Poems**: Create AI-generated poetry for MARTA routes based on personality and narrative
- **Audio Generation**: Convert poems to engaging audio narration with multiple voice options and an audio phrasing toggle
- **Batch Operations**: Mark multiple poems as core, extensions, or delete them
- **Search and Filter**: Find poems by title, route, content, or narrative role
- **Prompt Review**: View the stored prompt used to generate a poem

### Narrative Framework
- **Core Narrative**: Designate canonical poems that form the core narrative (The Homunculus)
- **Extensions**: Create narrative extensions that build on core poems
- **Relationships**: Track thematic connections between poems
- **Entity Tracking**: Manage themes, imagery, emotions, and sound devices

### Talent Economy
Each MARTA route is modeled as an opportunistic harvester of emotional value from its riders. Riders carry emotional currency — joy, dread, nostalgia, exhaustion, hope — and the route extracts it according to its personality and the current market conditions (time of day, weather, traffic, foot traffic patterns). Premium moments (rush hour, storms, late night) command higher extraction rates. This framework shapes the metaphors, imagery, and tone of generated poems: extraction is buried in ecological or economic language rather than stated directly. Some routes prefer positive currencies; others trade in grief or contradiction. The result is poetry that feels structurally shaped by the route itself rather than imposed from outside.

### Radio Stream
- **Continuous Audio Stream**: Auto-generated audio stream stitching together poems, ambient soundscapes, and transit announcements
- **Auto-Regeneration**: Stream is rebuilt every 8 hours via APScheduler running in-process
- **Azure Blob Storage delivery**: Stream and individual audio files are stored in and served from Azure Blob Storage
- **Standalone Player**: Available at `/radio` for listening without the full UI

### Route Awareness + Live Context
- **Context Service**: `GET /api/context?route_id=MARTA_5` returns live anchors, signals, history, and cache metadata
- **Live Anchors**: GTFS-Realtime + Mapbox reverse geocoding (neighborhood/place/POI)
- **Signals**: Weather (NWS), traffic (GTFS-RT congestion or Mapbox), solar events (sunrise/sunset), service alerts
- **History Layer**: Wikipedia/Wikidata snippets with a persistent SQLite cache

### Admin Interface
- Poetry Manager for viewing and organizing poems
- Audio controls for playback and regeneration
- Narrative status monitoring
- Batch delete functionality with audio cleanup

### Azure Infrastructure
- **Backend**: Python FastAPI app deployed to Azure App Service (`marta-poetry-app.azurewebsites.net`)
- **Frontend**: React/Vite app deployed to Azure Static Web Apps (`icy-sky-01432f40f.6.azurestaticapps.net`)
- **Poem Storage**: Azure Cosmos DB with JSON file fallback for local development
- **Audio Storage**: Azure Blob Storage for audio files and radio stream segments
- **Infrastructure as Code**: Bicep templates in `bicep/`

## Documentation

- [Audio Generation Feature](backend/AUDIO_FEATURE.md) - Text-to-speech implementation details
- [Poem Deletion Feature](DELETE_POEMS_QUICKSTART.md) - How to delete poems and audio files
- [Technical Details](DELETE_POEMS_FEATURE.md) - Architecture and API details
- [Route Awareness Spec](docs/route-awareness-spec.md) - Live context and prompt-level constraints

## TODO
* The creator's voice will be present in this poetic ecosystem, so there will be means to add or remove narrative elements, tweak personalities or add additional constraints.

* Eventually human users will be able to comment on routes and even submit their own works. Works presented by humans will not be saved without their explicit consent.
