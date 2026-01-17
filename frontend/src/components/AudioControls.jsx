import React from 'react';

function AudioControls({ onStop }) {
  const handleStop = () => {
    if (typeof onStop === 'function') {
      onStop();
    }
  };

  return (
    <div className="mt-4">
      <button 
        className="bg-blue-500 text-white px-4 py-2 rounded mr-2"
        aria-label="Play audio"
      >
        Play
      </button>
      <button
        className="bg-red-500 text-white px-4 py-2 rounded"
        onClick={handleStop}
        aria-label="Stop audio playback"
      >
        Stop
      </button>
    </div>
  );
}

export default AudioControls;
