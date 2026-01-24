import React from 'react';

function PoetryDisplay({ poemData }) {
  if (!poemData) {
    return (
      <div className="mt-4 p-4 bg-white shadow rounded">
        <h2 className="text-xl font-bold mb-2">Generated Poem</h2>
        <p className="text-gray-500">Select a route and click Generate to create a poem.</p>
      </div>
    );
  }

  const { text, title, route_name, metadata, personality, context } = poemData;

  return (
    <div className="mt-4 space-y-4">
      {/* Main Poem Display */}
      <div className="p-6 bg-white shadow rounded-lg">
        <div className="mb-4">
          {title ? (
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-800 whitespace-pre-line">{title}</h2>
            </div>
          ) : (
            <h2 className="text-2xl font-bold text-gray-800">{route_name || 'Generated Poem'}</h2>
          )}
          {personality?.description && (
            <p className="text-sm text-gray-600 italic mt-2 text-center">{personality.description}</p>
          )}
        </div>
        <pre className="whitespace-pre-wrap text-lg leading-relaxed font-serif text-gray-900">
          {text}
        </pre>
      </div>

      {/* Metadata Display */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Themes & Emotions */}
        <div className="p-4 bg-white shadow rounded-lg">
          <h3 className="font-bold mb-3 text-green-700">Themes & Emotions</h3>
          
          {metadata?.themes?.length > 0 && (
            <div className="mb-3">
              <h4 className="font-medium text-sm text-gray-700">Themes:</h4>
              <div className="flex flex-wrap gap-1 mt-1">
                {metadata.themes.map((theme, index) => (
                  <span key={index} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                    {theme.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {metadata?.emotions?.length > 0 && (
            <div>
              <h4 className="font-medium text-sm text-gray-700">Emotions:</h4>
              <div className="flex flex-wrap gap-1 mt-1">
                {metadata.emotions.map((emotion, index) => (
                  <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    {emotion}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sound Devices & Structure */}
        <div className="p-4 bg-white shadow rounded-lg">
          <h3 className="font-bold mb-3 text-purple-700">Sound & Structure</h3>
          
          {metadata?.sound_devices?.length > 0 && (
            <div className="mb-3">
              <h4 className="font-medium text-sm text-gray-700">Sound Devices:</h4>
              <div className="flex flex-wrap gap-1 mt-1">
                {metadata.sound_devices.map((device, index) => (
                  <span key={index} className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                    {device.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {metadata?.structure_metadata?.line_count && (
            <div>
              <h4 className="font-medium text-sm text-gray-700">Structure:</h4>
              <p className="text-sm text-gray-600">
                {metadata.structure_metadata.line_count} lines, {metadata.structure_metadata.form || 'free verse'}
              </p>
              {metadata.sound_metadata?.alliteration_density && (
                <p className="text-sm text-gray-600">
                  Alliteration: {metadata.sound_metadata.alliteration_density}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Route Personality */}
        {personality && (
          <div className="p-4 bg-white shadow rounded-lg">
            <h3 className="font-bold mb-3 text-orange-700">Route Personality</h3>
            <div className="space-y-2">
              <div>
                <span className="text-sm font-medium text-gray-700">Canon Loyalty:</span>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    className="bg-orange-500 h-2 rounded-full" 
                    style={{ width: `${(personality.loyalty_to_canon || 0) * 100}%` }}
                  ></div>
                </div>
                <span className="text-xs text-gray-600">
                  {Math.round((personality.loyalty_to_canon || 0) * 100)}%
                </span>
              </div>
              
              {personality.rebellious_mode && (
                <div>
                  <span className="text-sm font-medium text-gray-700">Mode:</span>
                  <span className="ml-2 px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
                    {personality.rebellious_mode}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Generation Context */}
        {context && (
          <div className="p-4 bg-white shadow rounded-lg">
            <h3 className="font-bold mb-3 text-gray-700">Context</h3>
            <div className="space-y-1 text-sm">
              {context.time_of_day && (
                <p><span className="font-medium">Time:</span> {context.time_of_day.replace(/_/g, ' ')}</p>
              )}
              {context.passenger_count && (
                <p><span className="font-medium">Passenger Count:</span> {context.passenger_count}</p>
              )}
              {context.location && (
                <p><span className="font-medium">Location:</span> {context.location}</p>
              )}
              <p><span className="font-medium">Story Influence:</span> {Math.round(context.story_influence * 100)}%</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default PoetryDisplay;
