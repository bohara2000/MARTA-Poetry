"""
Audio generation service using OpenAI TTS API.
Handles conversion of poem text to engaging audio files.
Audio is stored in Azure Blob Storage when configured, with a local filesystem fallback.
"""

import os
import hashlib
from pathlib import Path
from openai import OpenAI
from config import OPENAI_API_KEY, STORAGE_CONNECTION_STRING, AUDIO_CONTAINER_NAME, STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY

# Azure Blob Storage (optional — falls back to local if not configured)
try:
    from azure.storage.blob import BlobServiceClient, ContentSettings
    BLOB_AVAILABLE = True
except ImportError:
    BLOB_AVAILABLE = False


class AudioService:
    """Service for generating audio from poetry text."""

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment or .env file")

        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.audio_container = AUDIO_CONTAINER_NAME or "audio"

        # Set up Azure Blob Storage client if connection string is available
        self._blob_service: BlobServiceClient | None = None
        if BLOB_AVAILABLE and STORAGE_CONNECTION_STRING:
            try:
                self._blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
                # Ensure container exists
                container_client = self._blob_service.get_container_client(self.audio_container)
                if not container_client.exists():
                    container_client.create_container(public_access="blob")
                print(f"✅ Audio service using Azure Blob Storage via connection string (container: {self.audio_container})")
            except Exception as e:
                print(f"⚠️  Connection string init failed ({e}), trying account name+key...")
                self._blob_service = None

        # Fallback: try STORAGE_ACCOUNT_NAME + STORAGE_ACCOUNT_KEY
        if BLOB_AVAILABLE and self._blob_service is None:
            if STORAGE_ACCOUNT_NAME and STORAGE_ACCOUNT_KEY:
                try:
                    from azure.storage.blob import StorageSharedKeyCredential
                    credential = StorageSharedKeyCredential(STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY)
                    account_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
                    self._blob_service = BlobServiceClient(account_url=account_url, credential=credential)
                    container_client = self._blob_service.get_container_client(self.audio_container)
                    if not container_client.exists():
                        container_client.create_container(public_access="blob")
                    print(f"✅ Audio service using Azure Blob Storage via account key (container: {self.audio_container})")
                except Exception as e:
                    print(f"⚠️  Account key init failed ({e}), falling back to local")
                    self._blob_service = None
            else:
                print("⚠️  No STORAGE_CONNECTION_STRING or STORAGE_ACCOUNT_KEY — audio will use local filesystem")

        # Local fallback directory
        self.audio_dir = Path("audio")
        self.audio_dir.mkdir(exist_ok=True)

        # Voice options for engaging narration
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

    def _generate_audio_id(self, route_id: str, poem_hash: str) -> str:
        """Generate a unique identifier for audio based on route and poem content."""
        return f"{route_id}_{poem_hash[:8]}"

    def _blob_name(self, audio_id: str, voice: str) -> str:
        return f"{audio_id}_{voice}.mp3"

    def _local_path(self, audio_id: str, voice: str) -> Path:
        return self.audio_dir / self._blob_name(audio_id, voice)
    
    def generate_audio(
        self, 
        poem_text: str, 
        route_id: str = "default",
        voice: str = None,
        speed: float = 0.9
    ) -> dict:
        """
        Generate audio from poem text and persist it.

        In production (STORAGE_CONNECTION_STRING set): uploads to Azure Blob Storage
        and returns a public blob URL.
        In development (no connection string): saves to local audio/ directory and
        returns a /api/audio/{id}/{voice} URL served by the API.

        Args:
            poem_text: The poem text to convert to audio
            route_id: The route this poem is for (used for consistent voice selection)
            voice: Optional specific voice to use. If None, selects based on route_id
            speed: Playback speed (0.25 to 4.0, default 1.0)

        Returns:
            Dictionary with audio_url and metadata
        """
        try:
            if voice is None:
                voice = self.get_voice_for_route(route_id)
            if voice not in self.voice_options:
                voice = self.default_voice

            content_hash = hashlib.md5(poem_text.encode()).hexdigest()
            audio_id = self._generate_audio_id(route_id, content_hash)
            blob_name = self._blob_name(audio_id, voice)
            duration_estimate = len(poem_text) / 150

            # --- Azure Blob Storage path ---
            if self._blob_service:
                container_client = self._blob_service.get_container_client(self.audio_container)
                blob_client = container_client.get_blob_client(blob_name)

                if blob_client.exists():
                    print(f"✅ Audio cache hit (blob): {blob_name}")
                    return {
                        "success": True,
                        "audio_url": blob_client.url,
                        "voice": voice,
                        "cached": True,
                        "duration_estimate": duration_estimate,
                    }

                print(f"🎙️  Generating audio for {route_id} using voice: {voice}")
                response = self.client.audio.speech.create(
                    model="tts-1-hd",
                    voice=voice,
                    input=poem_text,
                    speed=speed
                )
                blob_client.upload_blob(
                    response.content,
                    overwrite=True,
                    content_settings=ContentSettings(content_type="audio/mpeg")
                )
                print(f"✅ Audio uploaded to blob: {blob_name}")
                return {
                    "success": True,
                    "audio_url": blob_client.url,
                    "voice": voice,
                    "cached": False,
                    "duration_estimate": duration_estimate,
                }

            # --- Local filesystem fallback ---
            local_path = self._local_path(audio_id, voice)
            if local_path.exists():
                print(f"✅ Audio cache hit (local): {local_path}")
                return {
                    "success": True,
                    "audio_url": f"/api/audio/{audio_id}/{voice}",
                    "audio_file": str(local_path),
                    "voice": voice,
                    "cached": True,
                    "duration_estimate": duration_estimate,
                }

            print(f"🎙️  Generating audio (local) for {route_id} using voice: {voice}")
            response = self.client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=poem_text,
                speed=speed
            )
            local_path.write_bytes(response.content)
            print(f"✅ Audio saved locally: {local_path}")
            return {
                "success": True,
                "audio_url": f"/api/audio/{audio_id}/{voice}",
                "audio_file": str(local_path),
                "voice": voice,
                "cached": False,
                "duration_estimate": duration_estimate,
            }

        except Exception as e:
            print(f"❌ Error generating audio: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_audio_file(self, audio_id: str, voice: str) -> Path | None:
        """
        Retrieve local audio file path (used only for local-fallback serving).
        Returns None when using blob storage (the URL is served directly).
        """
        local_path = self._local_path(audio_id, voice)
        return local_path if local_path.exists() else None
    
    def list_available_voices(self) -> list:
        """Return list of available voices."""
        return self.voice_options
    
    def delete_audio(self, audio_id: str, voice: str = None) -> dict:
        """
        Delete audio file(s) for a poem from blob storage or local filesystem.

        Args:
            audio_id: The audio identifier
            voice: Optional specific voice. If None, deletes all voices for this id

        Returns:
            Deletion status
        """
        try:
            count = 0
            voices_to_delete = [voice] if voice else self.voice_options

            if self._blob_service:
                container_client = self._blob_service.get_container_client(self.audio_container)
                for v in voices_to_delete:
                    blob_client = container_client.get_blob_client(self._blob_name(audio_id, v))
                    if blob_client.exists():
                        blob_client.delete_blob()
                        count += 1
            else:
                for v in voices_to_delete:
                    local_path = self._local_path(audio_id, v)
                    if local_path.exists():
                        local_path.unlink()
                        count += 1

            if count == 0 and voice:
                return {"success": False, "error": "File not found"}
            return {"success": True, "deleted": count}

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
