import { useState } from 'react';
import RouteSelector from './components/RouteSelector.jsx';
import StorySlider from './components/StorySlider.jsx';
import PoetryDisplay from './components/PoetryDisplay.jsx';
import AudioControls from './components/AudioControls.jsx';

function App() {
  const [selectedRoute, setSelectedRoute] = useState('');
  const [storyInfluence, setStoryInfluence] = useState(0.7);
  const [poem, setPoem] = useState('');
  const [loading, setLoading] = useState(false);
  const [routeType, setRouteType] = useState('bus'); // 'bus' or 'train'

  const generatePoem = () => {
    if (!selectedRoute) {
      alert('Please select a route!');
      return;
    }

    setLoading(true);
    fetch(`http://localhost:8000/api/poetry?route=${selectedRoute}&story_influence=${storyInfluence}&route_type=${routeType}`)
      .then(res => res.json())
      .then(data => setPoem(data.poem))
      .catch(err => console.error('Error fetching poem:', err))
      .finally(() => setLoading(false));
  };

  return (
    <div className="min-h-screen p-4 bg-gray-100">
      <h1 className="text-3xl font-bold mb-4">MARTA Poetry Project</h1>

      <div className="mb-4">
        <label className="mr-4 font-semibold">Type:</label>
        <select value={routeType} onChange={e => setRouteType(e.target.value)} className="border p-2 rounded">
          <option value="bus">Bus</option>
          <option value="train">Train</option>
        </select>
      </div>

      <RouteSelector onSelectRoute={setSelectedRoute} routeType={routeType} />
      <StorySlider storyInfluence={storyInfluence} setStoryInfluence={setStoryInfluence} />

      <button
        onClick={generatePoem}
        className="bg-green-700 hover:bg-green-900 text-white font-bold py-3 px-6 rounded-lg border-2 border-white shadow-lg"
      >
        {loading ? 'Generating...' : 'Generate Poem'}
      </button>

      <PoetryDisplay poem={poem} />
      <AudioControls />
    </div>
  );
}

export default App;
