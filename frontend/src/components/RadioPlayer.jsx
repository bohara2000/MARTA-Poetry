import { useState, useEffect, useRef } from 'react';
import { getApiUrl } from '../utils/api.js';

const POLL_INTERVAL_MS = 5 * 60 * 1000; // re-check status every 5 minutes

function formatDuration(sec) {
  if (!sec) return null;
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function formatDate(iso) {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return null;
  }
}

export default function RadioPlayer() {
  const [status, setStatus]     = useState(null);   // null | { status, url, duration_sec, poem_count, generated_at }
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const audioRef                = useRef(null);

  const fetchStatus = () => {
    setLoading(true);
    fetch(getApiUrl('/api/radio/status'))
      .then(r => r.json())
      .then(d => { setStatus(d); setError(null); })
      .catch(() => setError('Could not reach the radio API.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchStatus();
    const id = setInterval(fetchStatus, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, []);

  const streamUrl = getApiUrl('/api/radio/stream');

  const isOnline = status?.status === 'online';

  return (
    <div className="mb-6 p-4 rounded-xl border-2 border-green-700 bg-green-50 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span
            className={`inline-block w-2.5 h-2.5 rounded-full ${
              isOnline ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
            }`}
          />
          <span className="font-bold text-green-900 text-sm sm:text-base tracking-wide uppercase">
            📻 MARTA Poetry Radio
          </span>
        </div>

        <button
          onClick={fetchStatus}
          className="text-xs text-green-700 hover:text-green-900 underline"
          title="Refresh status"
        >
          ↻ refresh
        </button>
      </div>

      {/* Status line */}
      {loading && !status && (
        <p className="text-sm text-gray-500 italic">Checking broadcast status…</p>
      )}
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
      {status && !isOnline && !error && (
        <p className="text-sm text-gray-500 italic">
          No broadcast available yet. Check back soon.
        </p>
      )}

      {isOnline && (
        <>
          {/* Metadata line */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-green-800 mb-3">
            {status.poem_count && (
              <span>🎵 {status.poem_count} poem{status.poem_count !== 1 ? 's' : ''}</span>
            )}
            {status.duration_sec && (
              <span>⏱ {formatDuration(status.duration_sec)}</span>
            )}
            {status.generated_at && (
              <span>🕐 Generated {formatDate(status.generated_at)}</span>
            )}
            {status.seed && (
              <span className="opacity-60">seed {status.seed}</span>
            )}
          </div>

          {/* Player */}
          <audio
            ref={audioRef}
            controls
            preload="none"
            className="w-full rounded"
            src={streamUrl}
          >
            Your browser does not support the audio element.
          </audio>

          <p className="mt-2 text-xs text-green-700 opacity-80">
            AI poems from MARTA bus &amp; train routes, with generative music. Loop friendly.
          </p>
        </>
      )}
    </div>
  );
}
