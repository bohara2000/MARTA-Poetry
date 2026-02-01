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

1. **Audio Storage: `backend/audio/`**
   - Caches generated MP3 files
   - .gitignore configured to exclude audio files
   - Directory structure: `{route_id}_{poem_hash}_{voice}.mp3`

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
```

Your existing OpenAI key will work (it already has TTS access).

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
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ HTTP
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Backend (Python/FastAPI)                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ app.py Routes:                                   │   │
│  │ POST   /api/audio/generate                       │   │
│  │ GET    /api/audio/{poem_id}/{voice}              │   │
│  │ GET    /api/audio/voices                         │   │
│  │ DELETE /api/audio/{poem_id}                      │   │
│  └──────────────────────────────────────────────────┘   │
│               ▲                                          │
│               │ Uses                                     │
│  ┌────────────▼──────────────────────────────────────┐  │
│  │ AudioService (audio_service.py)                  │  │
│  │ - OpenAI TTS API calls                           │  │
│  │ - Voice assignment logic                         │  │
│  │ - Audio caching                                  │  │
│  └────────────┬──────────────────────────────────────┘  │
│               │ Stores                                   │
│  ┌────────────▼──────────────────────────────────────┐  │
│  │ backend/audio/                                   │  │
│  │ Cache of generated MP3 files                     │  │
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

To clear cache:
```bash
rm backend/audio/*.mp3
```

## Migration Path

This implementation is designed for easy migration:

### To ElevenLabs (for better quality):
1. Create `elevenlabs_service.py` with same interface
2. Update `app.py` imports
3. No frontend changes needed

### To Azure Speech Service (for production):
1. Create `azure_speech_service.py`
2. Update `app.py` imports
3. Store audio in Azure Blob Storage
4. Still compatible with existing API

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
- Audio may still be generating
- Try refreshing
- Check file in `backend/audio/`

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
