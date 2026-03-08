import { useState } from 'react';
import RouteSelector from './components/RouteSelector.jsx';
import StorySlider from './components/StorySlider.jsx';
import PoetryDisplay from './components/PoetryDisplay.jsx';
import AudioControls from './components/AudioControls.jsx';
import AdminPanel from './components/AdminPanel.jsx';
import RadioPlayer from './components/RadioPlayer.jsx';
import { getApiUrl } from './utils/api.js';

function App() {
  const [selectedRoute, setSelectedRoute] = useState('');
  const [storyInfluence, setStoryInfluence] = useState(0.7);
  const [poemData, setPoemData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [routeType, setRouteType] = useState('bus'); // 'bus' or 'train'
  const [showAdmin, setShowAdmin] = useState(false);
  
  // Additional context parameters
  const [timeOfDay, setTimeOfDay] = useState('');
  const [passengerCount, setPassengerCount] = useState('');
  const [location, setLocation] = useState('');

  const generatePoem = () => {
    if (!selectedRoute) {
      alert('Please select a route!');
      return;
    }

    setLoading(true);
    
    // Build query parameters
    const params = new URLSearchParams({
      route: selectedRoute,
      story_influence: storyInfluence,
      route_type: routeType
    });
    
    if (timeOfDay) params.append('time_of_day', timeOfDay);
    if (passengerCount) params.append('passenger_count', passengerCount);
    if (location) params.append('location', location);

    fetch(getApiUrl(`/api/poetry?${params.toString()}`))
      .then(res => res.json())
      .then(data => {
        if (data.text) {
          setPoemData(data);
        } else if (data.detail) {
          alert(`Error: ${data.detail}`);
        } else {
          alert('Failed to generate poem');
        }
      })
      .catch(err => {
        console.error('Error fetching poem:', err);
        alert('Failed to generate poem');
      })
      .finally(() => setLoading(false));
  };

  // Show admin interface if toggled
  if (showAdmin) {
    return <AdminPanel onClose={() => setShowAdmin(false)} />;
  }

  return (
    <div className="min-h-screen p-2 sm:p-4 bg-gray-100">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-2 sm:gap-0">
        <h1 className="text-2xl sm:text-3xl font-bold">MARTA Poetry Project</h1>
        <button
          onClick={() => setShowAdmin(true)}
          className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm w-full sm:w-auto"
        >
          🔧 Admin Panel
        </button>
      </div>

      <RadioPlayer />

      <div className="mb-4">
        <label className="mr-2 sm:mr-4 font-semibold text-sm sm:text-base">Type:</label>
        <select value={routeType} onChange={e => setRouteType(e.target.value)} className="border p-2 rounded text-sm sm:text-base">
          <option value="bus">Bus</option>
          <option value="train">Train</option>
        </select>
      </div>

      <RouteSelector onSelectRoute={setSelectedRoute} routeType={routeType} />
      <StorySlider storyInfluence={storyInfluence} setStoryInfluence={setStoryInfluence} />
      
      {/* New Context Controls */}
      <div className="mb-4 p-3 sm:p-4 border rounded-lg bg-white">
        <h3 className="font-semibold mb-2 text-sm sm:text-base">Context (Optional)</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1">Time of Day:</label>
            <select 
              value={timeOfDay} 
              onChange={e => setTimeOfDay(e.target.value)}
              className="w-full border p-2 rounded text-sm"
            >
              <option value="">-- Any Time --</option>
              <option value="morning_rush">Morning Rush</option>
              <option value="afternoon">Afternoon</option>
              <option value="evening_rush">Evening Rush</option>
              <option value="late_night">Late Night</option>
            </select>
          </div>
          
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1">Passenger Count:</label>
            <select 
              value={passengerCount} 
              onChange={e => setPassengerCount(e.target.value)}
              className="w-full border p-2 rounded text-sm"
            >
              <option value="">-- Any Count --</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1">Location:</label>
            <input
              type="text"
              value={location}
              onChange={e => setLocation(e.target.value)}
              placeholder="e.g., Downtown, Midtown"
              className="w-full border p-2 rounded text-sm"
            />
          </div>
        </div>
      </div>

      <button
        onClick={generatePoem}
        className="bg-green-700 hover:bg-green-900 text-white font-bold py-3 px-6 rounded-lg border-2 border-white shadow-lg w-full sm:w-auto"
      >
        {loading ? 'Generating...' : 'Generate Poem'}
      </button>

      <PoetryDisplay poemData={poemData} />
      <AudioControls 
        poemText={poemData?.poem || poemData?.text}
        routeId={selectedRoute}
      />
    </div>
  );
}

export default App;
