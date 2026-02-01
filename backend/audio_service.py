"""
Audio generation service using OpenAI TTS API.
Handles conversion of poem text to engaging audio files.
"""

import os
import hashlib
from pathlib import Path
from openai import OpenAI
from config import OPENAI_API_KEY


class AudioService:
    """Service for generating audio from poetry text."""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment or .env file")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.audio_dir = Path("audio")
        self.audio_dir.mkdir(exist_ok=True)
        
        # Voice options for engaging narration
        # These are the most engaging OpenAI voices
        self.voice_options = ["nova", "shimmer", "alloy", "echo", "fable", "onyx"]
        self.default_voice = "nova"  # Nova is warm and engaging
    
    def get_voice_for_route(self, route_id: str) -> str:
        """
        Select a consistent voice for a route based on its ID.
        This ensures the same route always gets the same voice.
        
        Args:
            route_id: The MARTA route identifier
            
        Returns:
            Voice name to use for this route
        """
        # Hash the route_id to get a consistent index
        hash_value = int(hashlib.md5(route_id.encode()).hexdigest(), 16)
        voice_index = hash_value % len(self.voice_options)
        return self.voice_options[voice_index]
    
    def _get_audio_path(self, poem_id: str, voice: str) -> Path:
        """Get the file path for storing audio."""
        filename = f"{poem_id}_{voice}.mp3"
        return self.audio_dir / filename
    
    def _generate_audio_filename(self, route_id: str, poem_hash: str) -> str:
        """Generate a unique identifier for audio based on route and poem content."""
        return f"{route_id}_{poem_hash[:8]}"
    
    def generate_audio(
        self, 
        poem_text: str, 
        route_id: str = "default",
        voice: str = None,
        speed: float = 0.9
    ) -> dict:
        """
        Generate audio from poem text and save it.
        
        Args:
            poem_text: The poem text to convert to audio
            route_id: The route this poem is for (used for consistent voice selection)
            voice: Optional specific voice to use. If None, selects based on route_id
            speed: Playback speed (0.25 to 4.0, default 1.0)
            
        Returns:
            Dictionary with audio_url and metadata
        """
        try:
            # Select voice if not provided
            if voice is None:
                voice = self.get_voice_for_route(route_id)
            
            # Validate voice
            if voice not in self.voice_options:
                voice = self.default_voice
            
            # Generate unique ID for this audio
            content_hash = hashlib.md5(poem_text.encode()).hexdigest()
            audio_id = self._generate_audio_filename(route_id, content_hash)
            audio_path = self._get_audio_path(audio_id, voice)
            
            # Check if audio already exists (cache)
            if audio_path.exists():
                return {
                    "success": True,
                    "audio_url": f"/api/audio/{audio_id}/{voice}",
                    "audio_file": str(audio_path),
                    "voice": voice,
                    "cached": True,
                    "duration_estimate": len(poem_text) / 150  # Rough estimate: ~150 chars per minute
                }
            
            # Generate audio using OpenAI TTS
            print(f"🎙️  Generating audio for {route_id} using voice: {voice}")
            
            response = self.client.audio.speech.create(
                model="tts-1-hd",  # High-definition model for better quality
                voice=voice,
                input=poem_text,
                speed=speed
            )
            
            # Save audio to file
            audio_path.write_bytes(response.content)
            print(f"✅ Audio saved to {audio_path}")
            
            # Calculate approximate duration
            duration_estimate = len(poem_text) / 150  # ~150 chars per minute
            
            return {
                "success": True,
                "audio_url": f"/api/audio/{audio_id}/{voice}",
                "audio_file": str(audio_path),
                "voice": voice,
                "cached": False,
                "duration_estimate": duration_estimate
            }
            
        except Exception as e:
            print(f"❌ Error generating audio: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_audio_file(self, poem_id: str, voice: str) -> Path:
        """
        Retrieve audio file path.
        
        Args:
            poem_id: The poem identifier
            voice: The voice used
            
        Returns:
            Path to audio file, or None if not found
        """
        audio_path = self._get_audio_path(poem_id, voice)
        if audio_path.exists():
            return audio_path
        return None
    
    def list_available_voices(self) -> list:
        """Return list of available voices."""
        return self.voice_options
    
    def delete_audio(self, poem_id: str, voice: str = None) -> dict:
        """
        Delete audio file(s) for a poem.
        
        Args:
            poem_id: The poem identifier
            voice: Optional specific voice. If None, deletes all voices for this poem
            
        Returns:
            Deletion status
        """
        try:
            if voice:
                audio_path = self._get_audio_path(poem_id, voice)
                if audio_path.exists():
                    audio_path.unlink()
                    return {"success": True, "deleted": 1}
            else:
                # Delete all voices for this poem
                count = 0
                for audio_file in self.audio_dir.glob(f"{poem_id}_*.mp3"):
                    audio_file.unlink()
                    count += 1
                return {"success": True, "deleted": count}
            
            return {"success": False, "error": "File not found"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
_audio_service = None


def get_audio_service() -> AudioService:
    """Get or create the audio service singleton."""
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service
