/**
 * Route Personality Manager - React Component
 * 
 * UI for viewing and editing route personalities.
 * Place this in: frontend/src/components/PersonalityManager.jsx
 */

import React, { useState, useEffect } from 'react';
import './PersonalityManager.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const PersonalityManager = () => {
  const [personalities, setPersonalities] = useState({});
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [editing, setEditing] = useState(null);
  const [soundDeviceOptions, setSoundDeviceOptions] = useState([]);
  const [themeOptions, setThemeOptions] = useState([]);
  const [rebelliousModeOptions, setRebelliousModeOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null);

  // Load personalities and options on mount
  useEffect(() => {
    loadPersonalities();
    loadOptions();
  }, []);

  const loadPersonalities = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/personalities/`);
      const data = await response.json();
      setPersonalities(data.personalities);
      setLoading(false);
    } catch (err) {
      setError('Failed to load personalities');
      setLoading(false);
    }
  };

  const loadOptions = async () => {
    try {
      const [sounds, themes, modes] = await Promise.all([
        fetch(`${API_BASE}/api/personalities/options/sound-devices`).then(r => r.json()),
        fetch(`${API_BASE}/api/personalities/options/themes`).then(r => r.json()),
        fetch(`${API_BASE}/api/personalities/options/rebellious-modes`).then(r => r.json())
      ]);

      setSoundDeviceOptions(sounds.sound_devices);
      setThemeOptions(themes.themes);
      setRebelliousModeOptions(modes.modes);
    } catch (err) {
      console.error('Failed to load options:', err);
    }
  };

  const handleEdit = (routeId) => {
    setEditing({ ...personalities[routeId] });
    setSelectedRoute(routeId);
  };

  const handleSave = async (routeId) => {
    try {
      const response = await fetch(`${API_BASE}/api/personalities/${routeId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ personality: editing })
      });

      if (response.ok) {
        setPersonalities({
          ...personalities,
          [routeId]: editing
        });
        setEditing(null);
        setSelectedRoute(null);
        setSaveStatus({ type: 'success', message: 'Saved successfully!' });
        setTimeout(() => setSaveStatus(null), 3000);
      } else {
        setSaveStatus({ type: 'error', message: 'Failed to save' });
      }
    } catch (err) {
      setSaveStatus({ type: 'error', message: 'Error saving' });
    }
  };

  const handleCancel = () => {
    setEditing(null);
    setSelectedRoute(null);
  };

  const handleCreateNew = () => {
    const newRouteId = prompt('Enter route ID (e.g., MARTA_99):');
    if (!newRouteId) return;

    if (personalities[newRouteId]) {
      alert('Route already exists!');
      return;
    }

    setEditing({
      name: `Route ${newRouteId}`,
      description: 'New route description',
      loyalty_to_canon: 0.5,
      rebellious_mode: null,
      sound_preferences: {},
      theme_affinities: {}
    });
    setSelectedRoute(newRouteId);
  };

  const updateEditing = (field, value) => {
    setEditing({ ...editing, [field]: value });
  };

  const updatePreference = (category, key, value) => {
    setEditing({
      ...editing,
      [category]: {
        ...editing[category],
        [key]: parseFloat(value)
      }
    });
  };

  const removePreference = (category, key) => {
    const updated = { ...editing[category] };
    delete updated[key];
    setEditing({ ...editing, [category]: updated });
  };

  const addPreference = (category) => {
    const options = category === 'sound_preferences' ? soundDeviceOptions : themeOptions;
    const existing = Object.keys(editing[category]);
    const available = options.filter(opt => !existing.includes(opt));

    if (available.length === 0) {
      alert('All options already added!');
      return;
    }

    const selection = prompt(`Choose from: ${available.join(', ')}`);
    if (!selection || !available.includes(selection)) return;

    updatePreference(category, selection, 0.5);
  };

  const getPersonalityType = (personality) => {
    if (personality.loyalty_to_canon > 0.8) return 'Traditionalist';
    if (personality.rebellious_mode === 'invert') return 'Contrarian';
    if (personality.rebellious_mode === 'ignore') return 'Explorer';
    if (personality.rebellious_mode === 'create_new') return 'Pioneer';
    return 'Balanced';
  };

  const getLoyaltyLabel = (value) => {
    if (value > 0.8) return 'Very High (Traditionalist)';
    if (value > 0.6) return 'High (Loyal)';
    if (value > 0.4) return 'Moderate (Balanced)';
    if (value > 0.2) return 'Low (Rebellious)';
    return 'Very Low (Extreme Rebel)';
  };

  if (loading) return <div className="personality-manager loading">Loading...</div>;
  if (error) return <div className="personality-manager error">{error}</div>;

  return (
    <div className="personality-manager">
      <div className="header">
        <h1>Route Personality Manager</h1>
        <button onClick={handleCreateNew} className="btn-create">
          + Create New Route
        </button>
      </div>

      {saveStatus && (
        <div className={`save-status ${saveStatus.type}`}>
          {saveStatus.message}
        </div>
      )}

      <div className="content">
        {/* Route List */}
        <div className="route-list">
          <h2>Routes ({Object.keys(personalities).length})</h2>
          {Object.entries(personalities).map(([routeId, personality]) => (
            <div
              key={routeId}
              className={`route-card ${selectedRoute === routeId ? 'selected' : ''}`}
              onClick={() => !editing && setSelectedRoute(routeId)}
            >
              <div className="route-header">
                <h3>{personality.name}</h3>
                <span className={`type-badge type-${getPersonalityType(personality).toLowerCase()}`}>
                  {getPersonalityType(personality)}
                </span>
              </div>
              <p className="route-description">{personality.description}</p>
              <div className="route-stats">
                <div className="stat">
                  <span className="stat-label">Loyalty:</span>
                  <span className="stat-value">{(personality.loyalty_to_canon * 100).toFixed(0)}%</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Mode:</span>
                  <span className="stat-value">{personality.rebellious_mode || 'None'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Editor Panel */}
        <div className="editor-panel">
          {selectedRoute && !editing && (
            <div className="view-mode">
              <h2>{personalities[selectedRoute].name}</h2>
              <p className="description">{personalities[selectedRoute].description}</p>

              <div className="detail-section">
                <h3>Loyalty to Canon</h3>
                <div className="loyalty-display">
                  <div className="loyalty-bar">
                    <div
                      className="loyalty-fill"
                      style={{ width: `${personalities[selectedRoute].loyalty_to_canon * 100}%` }}
                    />
                  </div>
                  <span className="loyalty-value">
                    {(personalities[selectedRoute].loyalty_to_canon * 100).toFixed(0)}% - {getLoyaltyLabel(personalities[selectedRoute].loyalty_to_canon)}
                  </span>
                </div>
              </div>

              <div className="detail-section">
                <h3>Rebellious Mode</h3>
                <p>{personalities[selectedRoute].rebellious_mode || 'None (Balanced)'}</p>
              </div>

              <div className="detail-section">
                <h3>Sound Preferences</h3>
                <div className="preferences-list">
                  {Object.entries(personalities[selectedRoute].sound_preferences).map(([sound, value]) => (
                    <div key={sound} className="preference-item">
                      <span>{sound}</span>
                      <span>{(value * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="detail-section">
                <h3>Theme Affinities</h3>
                <div className="preferences-list">
                  {Object.entries(personalities[selectedRoute].theme_affinities).map(([theme, value]) => (
                    <div key={theme} className="preference-item">
                      <span>{theme}</span>
                      <span>{(value * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>

              <button onClick={() => handleEdit(selectedRoute)} className="btn-edit">
                Edit Personality
              </button>
            </div>
          )}

          {editing && (
            <div className="edit-mode">
              <h2>Editing: {selectedRoute}</h2>

              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={editing.name}
                  onChange={(e) => updateEditing('name', e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={editing.description}
                  onChange={(e) => updateEditing('description', e.target.value)}
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label>Loyalty to Canon: {(editing.loyalty_to_canon * 100).toFixed(0)}%</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={editing.loyalty_to_canon}
                  onChange={(e) => updateEditing('loyalty_to_canon', parseFloat(e.target.value))}
                />
                <small>{getLoyaltyLabel(editing.loyalty_to_canon)}</small>
              </div>

              <div className="form-group">
                <label>Rebellious Mode</label>
                <select
                  value={editing.rebellious_mode || ''}
                  onChange={(e) => updateEditing('rebellious_mode', e.target.value || null)}
                >
                  {rebelliousModeOptions.map(mode => (
                    <option key={mode.value || 'null'} value={mode.value || ''}>
                      {mode.label} - {mode.description}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>
                  Sound Preferences
                  <button onClick={() => addPreference('sound_preferences')} className="btn-add-small">+</button>
                </label>
                <div className="preferences-edit">
                  {Object.entries(editing.sound_preferences).map(([sound, value]) => (
                    <div key={sound} className="preference-edit-item">
                      <span>{sound}</span>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={value}
                        onChange={(e) => updatePreference('sound_preferences', sound, e.target.value)}
                      />
                      <span>{(value * 100).toFixed(0)}%</span>
                      <button onClick={() => removePreference('sound_preferences', sound)}>×</button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>
                  Theme Affinities
                  <button onClick={() => addPreference('theme_affinities')} className="btn-add-small">+</button>
                </label>
                <div className="preferences-edit">
                  {Object.entries(editing.theme_affinities).map(([theme, value]) => (
                    <div key={theme} className="preference-edit-item">
                      <span>{theme}</span>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={value}
                        onChange={(e) => updatePreference('theme_affinities', theme, e.target.value)}
                      />
                      <span>{(value * 100).toFixed(0)}%</span>
                      <button onClick={() => removePreference('theme_affinities', theme)}>×</button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="button-group">
                <button onClick={() => handleSave(selectedRoute)} className="btn-save">
                  Save Changes
                </button>
                <button onClick={handleCancel} className="btn-cancel">
                  Cancel
                </button>
              </div>
            </div>
          )}

          {!selectedRoute && (
            <div className="empty-state">
              <p>Select a route to view or edit its personality</p>
              <p>or</p>
              <button onClick={handleCreateNew} className="btn-create-large">
                Create New Route Personality
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PersonalityManager;
