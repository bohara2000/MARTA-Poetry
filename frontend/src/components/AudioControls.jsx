import React, { useState, useRef, useEffect } from 'react';
import { apiFetch, getApiUrl } from '../utils/api';

function AudioControls({ poemText, routeId, onStop }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);

  // Fetch available voices on component mount
  useEffect(() => {
    const fetchVoices = async () => {
      try {
        const response = await apiFetch('/api/audio/voices');
        console.log('Voices response status:', response.status);
        console.log('Voices response headers:', response.headers);
        
        const text = await response.text();
        console.log('Voices response text:', text);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = JSON.parse(text);
        setAvailableVoices(data.voices);
        setSelectedVoice(data.default);
      } catch (err) {
        console.error('Failed to fetch available voices:', err);
        // Fallback to default voices
        setAvailableVoices(['nova', 'shimmer', 'alloy', 'echo', 'fable', 'onyx']);
        setSelectedVoice('nova');
      }
    };
    fetchVoices();
  }, []);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setAudioUrl(null);
    setError(null);
  }, [poemText, routeId]);

  useEffect(() => {
    if (!audioUrl) return;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setAudioUrl(null);
  }, [selectedVoice]);

  // Update time display
  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
  };

  const generateAndPlayAudio = async () => {
    if (!poemText || !routeId) {
      setError('Missing poem text or route ID');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Generate audio
      const generateResponse = await apiFetch('/api/audio/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          route: routeId,
          poem_text: poemText,
          voice: selectedVoice,
        }),
      });

      if (!generateResponse.ok) {
        throw new Error('Failed to generate audio');
      }

      const audioData = await generateResponse.json();

      if (!audioData.success) {
        throw new Error(audioData.error || 'Audio generation failed');
      }

      // Play the generated audio
      if (audioRef.current) {
        // audio_url is a relative path like /api/audio/{id}/{voice} — make it absolute
        const fullAudioUrl = getApiUrl(audioData.audio_url);
        audioRef.current.src = fullAudioUrl;
        setAudioUrl(fullAudioUrl);
        audioRef.current.play();
        setIsPlaying(true);
      }
    } catch (err) {
      setError(err.message);
      console.error('Audio generation error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePauseResume = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  const handleStop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlaying(false);
    setCurrentTime(0);
    if (typeof onStop === 'function') {
      onStop();
    }
  };

  const handleDownload = () => {
    if (audioUrl) {
      const link = document.createElement('a');
      link.href = audioUrl;
      link.download = `poem-${routeId}-${selectedVoice}.mp3`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleProgressClick = (e) => {
    if (audioRef.current && duration) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const percentage = x / rect.width;
      audioRef.current.currentTime = percentage * duration;
    }
  };

  return (
    <div className="mt-6 p-3 sm:p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
      <audio
        ref={audioRef}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
      />

      <div className="space-y-3">
        {/* Voice Selection */}
        {availableVoices.length > 0 && (
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
            <label className="text-sm font-semibold text-gray-700">Voice:</label>
            <select
              value={selectedVoice || ''}
              onChange={(e) => setSelectedVoice(e.target.value)}
              className="w-full sm:w-auto px-3 py-1 text-sm border border-gray-300 rounded bg-white hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {availableVoices.map((voice) => (
                <option key={voice} value={voice}>
                  {voice.charAt(0).toUpperCase() + voice.slice(1)}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Progress Bar */}
        {isPlaying && (
          <div className="space-y-1">
            <div
              className="w-full h-2 bg-gray-300 rounded cursor-pointer hover:bg-gray-400 transition"
              onClick={handleProgressClick}
            >
              <div
                className="h-full bg-blue-500 rounded transition-all"
                style={{
                  width: duration ? `${(currentTime / duration) * 100}%` : '0%',
                }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-600">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-2">
          {!audioUrl ? (
            <button
              onClick={generateAndPlayAudio}
              disabled={isLoading}
              className={`flex-1 px-4 py-2 rounded font-semibold text-white transition text-sm sm:text-base ${
                isLoading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-500 hover:bg-blue-600 active:bg-blue-700'
              }`}
              aria-label="Generate audio"
            >
              {isLoading ? '⏳ Generating...' : '▶️ Play Audio'}
            </button>
          ) : (
            <>
              <button
                onClick={handlePauseResume}
                disabled={!audioUrl}
                className="flex-1 px-4 py-2 rounded font-semibold text-white transition bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-sm sm:text-base"
                aria-label={isPlaying ? 'Pause audio' : 'Resume audio'}
              >
                {isPlaying ? '⏸️ Pause' : '▶️ Resume'}
              </button>
              <button
                onClick={handleStop}
                className="flex-1 sm:flex-none px-4 py-2 rounded font-semibold text-white transition bg-red-500 hover:bg-red-600 active:bg-red-700 text-sm sm:text-base"
                aria-label="Stop audio playback"
              >
                ⏹️ Stop
              </button>
              <button
                onClick={handleDownload}
                className="flex-1 sm:flex-none px-4 py-2 rounded font-semibold text-white transition bg-green-500 hover:bg-green-600 active:bg-green-700 text-sm sm:text-base"
                aria-label="Download audio file"
                title="Download MP3"
              >
                ⬇️ Download
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default AudioControls;
