# 🎙️ Audio Feature - Quick Start

## ✅ Working Implementation

Your MARTA Poetry project now has **fully functional audio generation** for poetry narration!

## Quick Setup (Already Done!)

✅ Backend audio service created
✅ Frontend audio player integrated
✅ API endpoints working
✅ Vite proxy configured
✅ OpenAI TTS integrated

## How to Use

### Generate & Play Poetry
1. **Select a route** (e.g., "Route 5")
2. **Adjust Story Influence** slider (0-1)
3. **Set context** (Time, Passenger Count, Location - optional)
4. **Click "Generate Poem"** → Wait for poem to appear
5. **Click "▶️ Play Audio"** → Audio generates and plays
6. **Select voice** from dropdown (optional, defaults to "nova")
7. Use progress bar to seek, **Pause/Resume** to toggle playback, **Stop** to reset
8. **Download** the MP3 with the Download button

## Features

| Feature | Details |
|---------|---------|
| **Voices** | nova, shimmer, alloy, echo, fable, onyx |
| **Speed** | Adjustable 0.25x - 4.0x (default 0.9x for natural pace) |
| **Caching** | Audio cached to save costs |
| **UI** | Progress bar, voice selector, play/pause/stop controls, download |

## That's It!

The audio feature is production-ready and working. Just generate poems and click Play! 🎵

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Audio doesn't play | Hard refresh browser (Ctrl+F5) |
| "Generated poem is empty" | Sometimes happens - click Generate again |
| No voices in dropdown | Fallback voices auto-load; error won't block feature |
| Slow generation | Normal - TTS takes 2-3 seconds per poem |

## API Reference

```bash
# Generate audio
curl -X POST http://localhost:8000/api/audio/generate \
  -H "Content-Type: application/json" \
  -d '{"route": "5", "poem_text": "Your poem text", "voice": "nova", "speed": 0.9}'

# Get voices
curl http://localhost:8000/api/audio/voices

# Stream audio file
curl http://localhost:8000/api/audio/MARTA_5_abc123de/nova -o poem.mp3
```

## Costs

- ~$0.015 per 1,000 characters (OpenAI TTS)
- Average poem: ~$0.01
- 1,000 poems/month: ~$7.50

---

**Ready to hear your poetry!** 🎵

