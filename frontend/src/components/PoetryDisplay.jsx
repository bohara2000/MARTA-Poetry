import React from 'react';

function PoetryDisplay({ poem }) {
  return (
    <div className="mt-4 p-4 bg-white shadow rounded">
      <h2 className="text-xl font-bold mb-2">Generated Poem</h2>
      <pre className="whitespace-pre-wrap">{poem || 'Select a route and click Generate to create a poem.'}</pre>
    </div>
  );
}

export default PoetryDisplay;
