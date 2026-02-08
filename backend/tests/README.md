# Test Suite

This directory contains test scripts for validating the MARTA Poetry Project functionality.

## Test Scripts

### test_narrative_adherence.py
Comprehensive narrative adherence testing framework. Tests how well generated poems adhere to expected narrative stances based on route personality and story influence levels.

**Usage:**
```bash
cd backend
python3 tests/test_narrative_adherence.py
```

**Features:**
- Tests single story influence levels
- Tests comprehensive sweeps across multiple influence levels (0.1 to 0.9)
- Generates detailed adherence reports
- Validates consistency with route personality traits

**API Integration:**
- `POST /api/narrative/test-adherence` - Run adherence tests
- `GET /api/narrative/test-adherence/{route_id}` - Get test results
- `POST /api/narrative/generate-adherence-report` - Generate report file

### test_generation_quick.py
Quick poetry generation tests for validating core generation pipeline.

**Usage:**
```bash
cd backend
python3 tests/test_generation_quick.py
```

**Purpose:**
- Rapid validation of poetry generation
- Smoke tests for route agents
- Basic integration testing

### test_realtime_adherence.py
Real-time narrative adherence testing with contextual parameters.

**Usage:**
```bash
cd backend
python3 tests/test_realtime_adherence.py
```

**Features:**
- Tests adherence with real-time context (time of day, passenger count, etc.)
- Validates dynamic story influence behavior
- Integration testing with full context stack

### test_context_contract.py
Context service contract validation.

**Usage:**
```bash
cd backend
python3 tests/test_context_contract.py
```

**Purpose:**
- Validates context-service response schema
- Provides sample payload coverage

### test_context_endpoint.py
Integration tests for the `/api/context` endpoint.

**Usage:**
```bash
cd backend
python3 -m pytest tests/test_context_endpoint.py
```

**Purpose:**
- Validates endpoint response schema
- Ensures missing params return validation errors

### test_history_context_service.py
Historical context fetcher tests.

**Usage:**
```bash
cd backend
python3 -m pytest tests/test_history_context_service.py
```

**Purpose:**
- Validates Wikipedia/Wikidata parsing and result combination

### test_weather_service.py
Unit tests for the NWS weather fetcher.

**Usage:**
```bash
cd backend
python3 -m pytest tests/test_weather_service.py
```

**Purpose:**
- Validates NWS point and forecast fetch flow
- Verifies error handling for bad responses

### test_gtfs_realtime_service.py
Unit tests for GTFS-Realtime vehicle positions.

**Usage:**
```bash
cd backend
python3 -m pytest tests/test_gtfs_realtime_service.py
```

**Purpose:**
- Validates parsing of a GTFS-RT vehicle positions feed
- Ensures missing URL returns None

### test_rail_realtime_service.py
Unit tests for rail realtime REST service.

**Usage:**
```bash
cd backend
python3 -m pytest tests/test_rail_realtime_service.py
```

**Purpose:**
- Validates rail realtime response handling
- Ensures missing URL returns None

### test_mapbox_geocode_service.py
Unit tests for Mapbox reverse geocoding.

**Usage:**
```bash
cd backend
python3 -m pytest tests/test_mapbox_geocode_service.py
```

**Purpose:**
- Validates Mapbox feature parsing
- Ensures missing token returns None

### test_mapbox_traffic_service.py
Unit tests for Mapbox traffic congestion.

**Usage:**
```bash
cd backend
python3 -m pytest tests/test_mapbox_traffic_service.py
```

**Purpose:**
- Validates traffic congestion parsing
- Ensures missing token returns None

### test_solar_events_service.py
Unit tests for solar events (sunrise/sunset) service.

**Usage:**
```bash
cd backend
python3 -m pytest tests/test_solar_events_service.py
```

**Purpose:**
- Validates solar events parsing
- Ensures bad API status returns None

## Running Tests

### Run All Tests
```bash
cd backend
python3 -m pytest tests/
```

### Run Individual Test
```bash
cd backend
python3 tests/test_narrative_adherence.py
```

### Run Via API (requires server running)
```bash
# Start server
uvicorn app:app --reload

# In another terminal
curl -X POST http://localhost:8000/api/narrative/test-adherence \
  -H "Content-Type: application/json" \
  -d '{"route_id": "MARTA_5", "comprehensive": true}'
```

## Test Reports

Test reports are saved to `/backend/reports/` directory with timestamps:
- `narrative_adherence_MARTA_5_20260129_123456.txt`
- `graph_report_20260129_123456.txt`

## Adding New Tests

1. Create new test file in this directory: `test_<feature>.py`
2. Import necessary modules from parent directory
3. Follow existing test patterns for consistency
4. Update this README with test description
5. Add API endpoint in `admin_api.py` if needed for UI integration

## Dependencies

Tests require:
- FastAPI server running (for API tests)
- Valid route personalities in `data/route_personalities.json`
- Poetry graph initialized
- OpenAI API key configured
