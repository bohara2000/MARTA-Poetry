import React from 'react';

function StorySlider({ storyInfluence, setStoryInfluence }) {
  return (
    <div className="mb-4">
      <label htmlFor="storyInfluence" className="block font-semibold">
        Story Influence: {storyInfluence}
      </label>
      <input
        type="range"
        id="storyInfluence"
        min="0"
        max="1"
        step="0.01"
        value={storyInfluence}
        onChange={(e) => setStoryInfluence(parseFloat(e.target.value))}
        className="w-full"
      />
    </div>
  );
}

export default StorySlider;
