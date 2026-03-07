# Audio Feature Implementation - Integration Guide

## ✅ Implementation Status

**COMPLETE & WORKING** - Audio generation fully functional with all issues resolved.

## What Was Implemented

A complete text-to-speech audio generation system for poetry narration using OpenAI TTS API.

### Backend Changes

1. **New Module: `audio_service.py`**
   - AudioService class handling TTS generation
   - Voice assignment and caching logic
   - File management for generated audio

2. **Updated `app.py`**
   - New `/api/audio/generate` endpoint (POST) - accepts JSON body with Pydantic model
   - Audio file serving `/api/audio/{poem_id}/{voice}` (GET)
   - Voice list endpoint `/api/audio/voices` (GET)
   - Audio deletion endpoint `/api/audio/{poem_id}` (DELETE)
   - Optional `include_audio` parameter on `/api/poetry` endpoint
   - Retry logic for empty poem responses
   - Detailed logging for troubleshooting
   - Added `AudioGenerationRequest` Pydantic model

3. **Updated `config.py`**
   - Ready for Azure Speech Service in future

### Frontend Changes

1. **Updated `components/AudioControls.jsx`**
   - Fully functional audio player with controls
   - Voice selection dropdown
   - Progress bar with time display
   - Real-time feedback (loading, playing, errors)
   - Graceful fallback to default voices if endpoint fails
   - Pause/Resume toggle and Download MP3 button

2. **Updated `App.jsx`**
   - Pass poem text and route ID to AudioControls
   - Component receives necessary props

3. **Updated `frontend/vite.config.js`**
   - Added proxy configuration for `/api/` requests to backend
   - Routes frontend requests to http://localhost:8000

### Infrastructure

1. **Audio Storage: Azure Blob Storage**
   - Container: `audio` in storage account `martastorage53tflkign7mc`
   - Files persist across App Service restarts (unlike ephemeral local disk)
   - File naming: `{route_id}_{poem_hash}_{voice}.mp3`
   - Local `backend/audio/` directory used as fallback when `STORAGE_CONNECTION_STRING` is not set (local dev)
   - Audio served through the backend proxy — storage account has public access disabled

## Issues Encountered & Solutions

### Issue 1: API Endpoint Query vs Body Parameters
**Problem**: Endpoint expected query parameters but frontend sent JSON body
**Solution**: Changed endpoint to use Pydantic `AudioGenerationRequest` model for JSON body

### Issue 2: Frontend Getting HTML Instead of JSON
**Problem**: Browser console showed `content-type: text/html` with Vite HTML
**Solution**: Added Vite proxy in `vite.config.js` to forward `/api/` requests to backend

### Issue 3: Empty Poem Responses
**Problem**: Azure API returned empty content with `finish_reason=length`
**Solution**: 
- Added retry logic for empty responses
- Fixed `max_completion_tokens` parameter (was using wrong param name)
- Added detailed logging to diagnose finish_reason
- Prompt is properly sized for the deployment

### Issue 4: Audio Speed Too Fast
**Problem**: Default TTS speed (1.0x) sounded rushed
**Solution**: Changed default speed to 0.9x for more natural pacing

## How to Use

### For Users (Frontend)
1. Generate a poem using the "Generate Poem" button
2. Click "▶️ Play Audio" button
3. Select a voice from dropdown (optional)
4. Audio will generate and play automatically
5. Use progress bar to seek, Pause/Resume to toggle playback, Stop to reset
6. Download MP3 with the Download button

### For Developers (Backend)

**Generate audio:**
```bash
curl -X POST http://localhost:8000/api/audio/generate \
  -H "Content-Type: application/json" \
  -d '{
    "route": "5",
    "poem_text": "Your poem text here",
    "voice": "nova",
    "speed": 0.9
  }'
```

**Get available voices:**
```bash
curl http://localhost:8000/api/audio/voices
```

## Required Setup

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

No new dependencies were added - OpenAI client already supports TTS!

### 2. Environment Configuration
Ensure `.env` has:
```
OPENAI_API_KEY=your_key_here

# Optional — if set, audio is stored in Azure Blob Storage instead of local disk
STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
AUDIO_CONTAINER_NAME=audio  # defaults to "audio" if not set
```

In production (Azure App Service), `STORAGE_CONNECTION_STRING` is set as an app setting and audio persists in blob storage across restarts. Without it, audio is saved to `backend/audio/` which is fine for local development.

### 3. Start the Backend
```bash
cd backend
uvicorn app:app --reload
```

### 4. Start the Frontend
```bash
cd frontend
npm run dev
```

## Testing the Feature

### Quick Test
1. Open frontend at http://localhost:5173
2. Select a route (e.g., "5")
3. Click "Generate Poem"
4. Wait for poem to appear
5. Click "▶️ Play Audio" button
6. Select a voice and it should generate and play!

### API Test
```bash
# Check voices available
curl http://localhost:8000/api/audio/voices

# Generate audio directly
curl -X POST http://localhost:8000/api/audio/generate \
  -H "Content-Type: application/json" \
  -d '{
    "route": "MARTA_5",
    "poem_text": "The trains dance through the city streets, carrying dreams and hopes.",
    "voice": "nova"
  }'
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  ┌───────────────┐    ┌──────────────────────────────┐  │
│  │ AudioControls │───▶│  PlayButton │ VoiceSelect   │  │
│  │ Component     │    │  Progress   │ StopButton    │  │
│  └───────────────┘    └──────────────────────────────┘  │
│  ┌───────────────┐                                      │
│  │ PoemManager  │  (Admin UI — uses API_BASE directly)  │
│  └───────────────┘                                      │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ HTTPS (absolute backend URL)
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Backend (Python/FastAPI)                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ app.py Routes:                                   │   │
│  │ POST   /api/audio/generate                       │   │
│  │ GET    /api/audio/{audio_id}/{voice}  ← proxy    │   │
│  │ GET    /api/audio/voices                         │   │
│  │ DELETE /api/audio/{audio_id}                     │   │
│  └──────────────────────────────────────────────────┘   │
│               ▲                                          │
│               │ Uses                                     │
│  ┌────────────▼──────────────────────────────────────┐  │
│  │ AudioService (audio_service.py)                  │  │
│  │ - OpenAI TTS API calls (tts-1-hd model)          │  │
│  │ - Voice assignment logic (MD5 hash of route_id)  │  │
│  │ - get_audio_bytes() streams from blob or local   │  │
│  └────────────┬──────────────────────────────────────┘  │
│               │ Stores / Streams                         │
│  ┌────────────▼──────────────────────────────────────┐  │
│  │ Azure Blob Storage (production)                  │  │
│  │ martastorage53tflkign7mc / container: audio      │  │
│  │ ── OR ──                                         │  │
│  │ backend/audio/ (local dev fallback)              │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Voice Assignment Strategy

Each route gets a consistent voice based on MD5 hash of route_id:
- **MARTA_5** → nova
- **MARTA_39** → shimmer
- **MARTA_Blue** → alloy
- etc.

This ensures the same route always "sounds the same" across sessions.

## Caching Strategy

Audio files are generated once and cached. File naming:
```
{route_id}_{poem_hash}_{voice}.mp3
```

Example: `MARTA_5_a1b2c3d4_nova.mp3`

In production, `AudioService` checks if the blob already exists before calling OpenAI — no duplicate generation charges.

To clear cache (local dev):
```bash
rm backend/audio/*.mp3
```

To clear cache (production blob storage):
```bash
az storage blob delete-batch --account-name martastorage53tflkign7mc --source audio
```

## Migration Path

This implementation is designed for easy migration:

### To ElevenLabs (for better quality):
1. Create `elevenlabs_service.py` with same interface
2. Update `app.py` imports
3. No frontend changes needed

### To Azure Speech Service (for higher quality/SSML):
1. Create `azure_speech_service.py` with same interface as `AudioService`
2. Update `app.py` imports
3. Blob storage layer is already in place — no other infrastructure changes needed

## Costs

**OpenAI TTS:**
- ~$0.015 per 1,000 characters
- Average poem (500 chars) ≈ $0.0075
- 1,000 poems ≈ $7.50/month

## Next Steps (Optional)

1. ✅ **Audio Generation** - Done!
2. 🔄 **Batch Generation** - Generate audio for multiple poems
3. 🔄 **Streaming** - Stream audio for long poems
4. 🔄 **SSML Support** - More expressive narration
5. 🔄 **Audio Download** - Download MP3 files
6. 🔄 **Voice Profiles** - Assign unique voices to route personalities

## Troubleshooting

### Audio doesn't play
- Check OPENAI_API_KEY is set
- Check browser console for errors
- Verify `backend/audio/` directory exists

### Generation is slow
- TTS takes ~1-2 sec per 100 chars
- Long poems take longer (normal)
- Check OpenAI rate limits

### "Audio file not found"
- Audio may still be generating — try again
- **Production**: Check blob container `audio` in `martastorage53tflkign7mc`; verify `STORAGE_CONNECTION_STRING` app setting is a valid full connection string (not just `BlobEndpoint=...`)
- **Local dev**: Check file in `backend/audio/`
- If `STORAGE_CONNECTION_STRING` is set but blob init fails, the service logs `⚠️ Blob Storage unavailable` on startup and falls back to local — check App Service logs

## Files Modified

✅ `backend/audio_service.py` - NEW
✅ `backend/app.py` - Updated with audio endpoints
✅ `backend/config.py` - Ready for future services
✅ `backend/.gitignore` - Added audio/ directory
✅ `backend/AUDIO_FEATURE.md` - NEW documentation
✅ `backend/audio/.gitkeep` - Directory structure
✅ `frontend/src/components/AudioControls.jsx` - Fully functional
✅ `frontend/src/App.jsx` - Pass props to AudioControls

## Success Criteria

✅ Audio generates without errors
✅ Frontend can play audio
✅ Voice selection works
✅ Progress bar shows playback progress
✅ Caching prevents duplicate generation
✅ Error handling graceful
✅ Backend remains responsive during generation
## Recent Fixes - Audio Metadata Persistence (Jan 31, 2026)

### Issues Resolved

1. **Audio files not showing after generation**
   - Audio was being saved but not reflected in UI without hard refresh
   - Fixed by including `audio_files` in the response from `/api/audio/generate`

2. **Audio disappearing when navigating away**
   - Previously generated audio would vanish when selecting other poems
   - Fixed by fetching fresh poem data from `/api/poems/{poem_id}` when poems are selected

3. **405 Method Not Allowed on "Generate Similar Poem"**
   - Frontend was sending POST requests to `/api/poetry` but only GET was defined
   - Fixed by adding `@app.post("/api/poetry")` endpoint with `PoemGenerationRequest` model

4. **Nova voice not auto-loading**
   - useEffect dependency array wasn't catching poem object changes
   - Fixed by using full `selectedPoem` object in dependencies instead of just ID

### Backend Improvements

**New POST Endpoint:** `@app.post("/api/poetry")`
- Accepts JSON body with poem generation parameters
- Validates using `PoemGenerationRequest` Pydantic model
- Supports: route, story_influence, route_type, time_of_day, location, passenger_count, include_audio

**Enhanced Audio Response:** `@app.post("/api/audio/generate")`
- Now returns `audio_files` array with updated file list
- Returns full `metadata` object for consistency
- Properly passes `graph` parameter through pipeline

**New Endpoint:** `@app.get("/api/poems/{poem_id}")`
- Returns individual poem details with current metadata
- Allows frontend to fetch fresh data without loading all poems

### Frontend Improvements

**Audio Loading (useEffect - lines 71-101)**
```javascript
// Fixed dependency to use full selectedPoem object
useEffect(() => {
  // ... audio matching logic ...
}, [selectedVoice, selectedPoem]);  // Was: selectedPoem?.id
```

**Poem Selection (handlePoemClick - lines 103-137)**
```javascript
// Now fetches fresh data from /api/poems/{id}
const poemDetailsResponse = await fetch(`${API_BASE}/api/poems/${poem.id}`);
if (poemDetailsResponse.ok) {
  const freshPoemData = await poemDetailsResponse.json();
  // Always get latest audio_files from server
  setSelectedPoem(prevPoem => ({ ...freshPoemData, relationships }));
}
```

**Audio Generation (generateAudio - lines 322-376)**
- Clears audio URL immediately when generation starts
- Updates selectedPoem.audio_files from response immediately
- Fetches fresh poem details after generation completes
- Uses individual poem endpoint for faster refresh

### Data Flow

**Immediate Updates After Generation:**
1. Backend generates audio and updates graph
2. Response includes updated `audio_files` list
3. Frontend updates state immediately
4. useEffect detects change and loads audio player
5. ✅ Audio appears without hard refresh

**Fresh Data When Navigating:**
1. User clicks on poem
2. `handlePoemClick()` fetches from `/api/poems/{id}`
3. Gets latest audio_files from server
4. useEffect auto-loads nova voice
5. ✅ Previously generated audio files persist

### Files Modified (Jan 31, 2026)

✅ `backend/app.py`
   - Added `PoemGenerationRequest` model
   - Created `@app.post("/api/poetry")` endpoint
   - Enhanced audio generation response
   - Added graph parameter to GET poetry endpoint

✅ `backend/admin_api.py`
   - Added `@app.get("/api/poems/{poem_id}")` endpoint

✅ `frontend/src/components/PoemManager.jsx`
   - Updated audio loading useEffect
   - Refactored `handlePoemClick()` for fresh data
   - Enhanced `generateAudio()` flow
   - Improved logging with emoji indicators