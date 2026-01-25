import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ThemeManager = () => {
  const [themes, setThemes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTheme, setSelectedTheme] = useState(null);
  const [mergeMode, setMergeMode] = useState(false);
  const [selectedThemesToMerge, setSelectedThemesToMerge] = useState([]);
  const [newThemeName, setNewThemeName] = useState('');

  useEffect(() => {
    loadThemes();
  }, []);

  const loadThemes = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/themes/`);
      const data = await response.json();
      setThemes(data.themes || []);
    } catch (err) {
      setError('Failed to load themes');
    } finally {
      setLoading(false);
    }
  };

  const mergeThemes = async () => {
    if (selectedThemesToMerge.length < 2 || !newThemeName.trim()) {
      alert('Please select at least 2 themes and provide a target theme name');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/themes/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_themes: selectedThemesToMerge,
          target_theme: newThemeName.trim()
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(result.message);
        await loadThemes();
        setMergeMode(false);
        setSelectedThemesToMerge([]);
        setNewThemeName('');
      } else {
        const error = await response.json();
        alert(`Error merging themes: ${error.detail}`);
      }
    } catch (err) {
      alert('Failed to merge themes');
    }
  };

  const toggleThemeForMerge = (themeName) => {
    setSelectedThemesToMerge(prev => {
      if (prev.includes(themeName)) {
        return prev.filter(name => name !== themeName);
      } else {
        return [...prev, themeName];
      }
    });
  };

  if (loading) return <div className="p-4">Loading themes...</div>;
  if (error) return <div className="p-4 text-red-600">{error}</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Theme Management</h2>
            <p className="text-sm text-gray-600 mt-1">
              Manage themes across all poems in your collection
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => {
                setMergeMode(!mergeMode);
                setSelectedThemesToMerge([]);
              }}
              className={`px-4 py-2 text-sm rounded ${
                mergeMode 
                  ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
              }`}
            >
              {mergeMode ? 'Cancel Merge' : 'Merge Themes'}
            </button>
            <button
              onClick={loadThemes}
              className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Merge Mode Panel */}
      {mergeMode && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-medium text-yellow-800 mb-3">Merge Themes</h3>
          <p className="text-sm text-yellow-700 mb-4">
            Select themes to merge and provide a target theme name. All poems will be updated to use the target theme.
          </p>
          
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target theme name:
              </label>
              <input
                type="text"
                value={newThemeName}
                onChange={(e) => setNewThemeName(e.target.value)}
                placeholder="Enter the name for the merged theme"
                className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Selected: {selectedThemesToMerge.length} themes
              </span>
              {selectedThemesToMerge.length >= 2 && newThemeName.trim() && (
                <button
                  onClick={mergeThemes}
                  className="px-4 py-2 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700"
                >
                  Merge Selected Themes
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-2xl font-bold text-blue-600">{themes.length}</div>
          <div className="text-sm text-gray-600">Total Themes</div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-2xl font-bold text-green-600">
            {themes.reduce((sum, theme) => sum + theme.usage_count, 0)}
          </div>
          <div className="text-sm text-gray-600">Theme Connections</div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-2xl font-bold text-purple-600">
            {themes.filter(theme => theme.usage_count > 1).length}
          </div>
          <div className="text-sm text-gray-600">Shared Themes</div>
        </div>
      </div>

      {/* Themes Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {themes.map((theme) => (
          <div
            key={theme.id}
            className={`bg-white border rounded-lg p-4 transition-all ${
              mergeMode && selectedThemesToMerge.includes(theme.name)
                ? 'ring-2 ring-yellow-400 bg-yellow-50'
                : 'border-gray-200 hover:shadow-md'
            } ${
              selectedTheme?.id === theme.id ? 'ring-2 ring-blue-500' : ''
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  {mergeMode && (
                    <input
                      type="checkbox"
                      checked={selectedThemesToMerge.includes(theme.name)}
                      onChange={() => toggleThemeForMerge(theme.name)}
                      className="rounded border-gray-300 text-yellow-600"
                    />
                  )}
                  <h3 className="font-medium text-gray-900">
                    {theme.name}
                  </h3>
                  <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                    {theme.usage_count} poems
                  </span>
                </div>
                
                <p className="mt-1 text-xs text-gray-500">
                  ID: {theme.id}
                </p>
                
                {theme.connected_poems && theme.connected_poems.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-gray-500 mb-2">Used in poems:</p>
                    <div className="space-y-1 max-h-20 overflow-y-auto">
                      {theme.connected_poems.slice(0, 3).map((poem) => (
                        <div key={poem.id} className="text-xs text-gray-600">
                          {poem.title || poem.id.slice(-8)}
                        </div>
                      ))}
                      {theme.connected_poems.length > 3 && (
                        <div className="text-xs text-gray-500">
                          +{theme.connected_poems.length - 3} more...
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
              
              <button
                onClick={() => setSelectedTheme(selectedTheme?.id === theme.id ? null : theme)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        ))}
        
        {themes.length === 0 && (
          <div className="col-span-full bg-white border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-500">No themes found. Import some poems to see themes.</p>
          </div>
        )}
      </div>

      {/* Selected Theme Detail */}
      {selectedTheme && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Theme: "{selectedTheme.name}"
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-2">Details</h4>
              <dl className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Usage Count:</dt>
                  <dd className="text-gray-900">{selectedTheme.usage_count}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Theme ID:</dt>
                  <dd className="text-gray-900 font-mono text-xs">{selectedTheme.id}</dd>
                </div>
                {selectedTheme.created_at && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Created:</dt>
                    <dd className="text-gray-900">
                      {new Date(selectedTheme.created_at).toLocaleDateString()}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-2">
                Connected Poems ({selectedTheme.connected_poems?.length || 0})
              </h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {selectedTheme.connected_poems?.map((poem) => (
                  <div key={poem.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-900">
                      {poem.title || `Poem ${poem.id.slice(-8)}`}
                    </span>
                    <span className="text-xs text-gray-500 font-mono">
                      {poem.id.slice(-8)}
                    </span>
                  </div>
                ))}
                {(!selectedTheme.connected_poems || selectedTheme.connected_poems.length === 0) && (
                  <p className="text-sm text-gray-500">No poems connected to this theme.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThemeManager;