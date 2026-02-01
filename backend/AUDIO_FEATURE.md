# Audio Generation Feature

## Overview
This feature generates engaging audio narration of poetry using OpenAI's Text-to-Speech (TTS) API. Each generated poem can be converted to audio with different voice options.

## Features
- **Multiple Engaging Voices**: 6 voice options (nova, shimmer, alloy, echo, fable, onyx)
- **Consistent Route Voices**: Each route gets assigned a consistent voice based on its ID
- **Audio Caching**: Generated audio is cached to avoid regenerating the same poem
- **Playback Controls**: Play, pause/resume, stop, and progress tracking in the frontend
- **Download Support**: Users can download MP3 audio files
- **Voice Selection**: Users can choose different voices via dropdown
- **Speed Control**: Supports playback speeds from 0.25x to 4.0x

## Setup

### Backend Requirements
The audio service uses OpenAI's TTS API. Ensure you have:
1. `OPENAI_API_KEY` environment variable set in `.env`
2. Python dependencies installed: `pip install -r requirements.txt`

### Environment Configuration
Add to `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## API Endpoints

### Generate Audio
**POST** `/api/audio/generate`

Generate audio from poem text.

**Request Body (JSON):**
```json
{
  "route": "5",
  "poem_text": "Your poem text here",
  "voice": "nova",
  "speed": 0.9
}
```

**Parameters:**
- `route` (required): Route identifier (e.g., "5", "MARTA_5")
- `poem_text` (required): The poem text to convert to audio
- `voice` (optional): Specific voice to use (nova, shimmer, alloy, echo, fable, onyx)
- `speed` (optional): Playback speed (0.25-4.0, default 0.9)

**Response:**
```json
{
  "success": true,
  "audio_url": "/api/audio/MARTA_5_abc123de/nova",
  "voice": "nova",
  "cached": false,
  "duration_estimate": 2.5
}
```

### Get Audio File
**GET** `/api/audio/{poem_id}/{voice}`

Retrieve the generated audio file in MP3 format.

**Parameters:**
- `poem_id`: The poem identifier
- `voice`: The voice used for generation

### List Available Voices
**GET** `/api/audio/voices`

Get list of available voices and default settings.

**Response:**
```json
{
  "voices": ["nova", "shimmer", "alloy", "echo", "fable", "onyx"],
  "default": "nova",
  "description": "Select engaging voices for poetry narration"
}
```

### Delete Audio
**DELETE** `/api/audio/{poem_id}`

Delete audio file(s) for a poem.

**Query Parameters:**
- `voice` (optional): Specific voice to delete. If omitted, deletes all voices.

## Integrated Poetry Generation

The `/api/poetry` endpoint now supports an optional `include_audio` parameter:

**GET** `/api/poetry?route=5&story_influence=0.7&include_audio=true`

When `include_audio=true`, the response will include an `audio` object with generation details.

## Frontend Integration

### AudioControls Component
The AudioControls component now provides:
- Voice selection dropdown
- Play/Pause/Stop buttons
- Download MP3 button
- Progress bar with time display
- Error handling
- Loading states

### Usage in App
```jsx
<AudioControls 
  poemText={poemData?.poem}
  routeId={selectedRoute}
/>
```

## Voice Characteristics

Each voice has distinct qualities:
- **nova**: Warm, engaging, professional (recommended default)
- **shimmer**: Bright, cheerful, energetic
- **alloy**: Neutral, clear, reliable
- **echo**: Deep, resonant, dramatic
- **fable**: Narrative, storytelling quality
- **onyx**: Smooth, sophisticated

## Caching Strategy

Audio files are cached based on:
1. Route ID
2. Voice used
3. Poem content (MD5 hash)

Example: `MARTA_5_abc123de_nova.mp3`

Generated audio is stored in `backend/audio/` directory. To clear cache:
```bash
rm backend/audio/*.mp3
```

## Future Enhancements

### Easy Migration to ElevenLabs
To upgrade to ElevenLabs for even better quality:
1. Create `elevenlabs_service.py` following the same interface
2. Update imports in `app.py`
3. No frontend changes needed

### Potential Improvements
- Batch audio generation for multiple poems
- Streaming audio generation for long poems
- SSML support for more expressive narration
- Custom voice cloning (with ElevenLabs)
- Audio storage in Azure Blob Storage
- Transcription support (using Whisper API)

## Troubleshooting

### "Audio generation failed"
- Check OPENAI_API_KEY is set correctly
- Verify OpenAI account has TTS API access
- Check token limits on OpenAI account

### "Audio file not found"
- Audio may still be generating, try again
- Check `backend/audio/` directory exists
- Delete corrupted audio: `DELETE /api/audio/{poem_id}`

### Slow audio generation
- TTS generation takes ~1-2 seconds per 100 characters
- Long poems may take 10-30 seconds
- Generation is asynchronous, check browser console for progress

### "Generated poem is empty" errors
- Occasionally Azure OpenAI returns empty content with `finish_reason=length`
- Retry logic automatically handles this
- If persistent, check prompt length and token limits

### Frontend receives HTML instead of JSON
- Ensure Vite proxy is configured in `vite.config.js`
- Proxy should forward `/api/` to `http://localhost:8000`
- Restart dev server after proxy changes

## Cost Estimation
OpenAI TTS pricing (as of Jan 2026):
- ~$0.015 per 1,000 characters
- Average poem (500 chars) = $0.0075
- 1,000 poems/month ≈ $7.50

## Testing
```bash
# Generate audio for a poem
curl -X POST "http://localhost:8000/api/audio/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "route": "5",
    "poem_text": "The train arrives with a gentle sway...",
    "voice": "nova"
  }'

# Get available voices
curl http://localhost:8000/api/audio/voices

# Play generated audio
curl http://localhost:8000/api/audio/MARTA_5_abc123de/nova -o poem.mp3
```
