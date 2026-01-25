import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const PoemManager = () => {
  const [poems, setPoems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPoem, setSelectedPoem] = useState(null);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [newTheme, setNewTheme] = useState('');
  const [addingTheme, setAddingTheme] = useState(false);
  const [selectedPoems, setSelectedPoems] = useState([]);
  const [batchMode, setBatchMode] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => {
    loadPoems();
  }, []);

  const loadPoems = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/poems/`);
      const data = await response.json();
      setPoems(data.poems || []);
    } catch (err) {
      setError('Failed to load poems');
    } finally {
      setLoading(false);
    }
  };

  const filteredPoems = poems.filter(poem => {
    const matchesFilter = filter === 'all' || poem.narrative_role === filter;
    const matchesSearch = !searchTerm || 
      poem.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      poem.route_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      poem.content?.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesFilter && matchesSearch;
  });

  const getPoemRelationships = async (poemId) => {
    try {
      const response = await fetch(`${API_BASE}/api/poems/${poemId}/relationships`);
      return await response.json();
    } catch (err) {
      console.error('Failed to load relationships:', err);
      return null;
    }
  };

  const handlePoemClick = async (poem) => {
    setSelectedPoem({ ...poem, relationships: null });
    const relationships = await getPoemRelationships(poem.id);
    setSelectedPoem({ ...poem, relationships });
  };

  const generateNewPoem = async (routeId) => {
    try {
      const response = await fetch(`${API_BASE}/api/poetry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          route: routeId,
          story_influence: 0.7
        })
      });
      
      if (response.ok) {
        await loadPoems();
      } else {
        const error = await response.json();
        alert(`Error generating poem: ${error.detail}`);
      }
    } catch (err) {
      alert('Failed to generate poem');
    }
  };

  const addThemeToPoem = async (poemId, themes) => {
    try {
      setAddingTheme(true);
      const response = await fetch(`${API_BASE}/api/poems/${poemId}/add-themes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ themes })
      });
      
      if (response.ok) {
        const result = await response.json();
        // Refresh the selected poem's relationships
        const relationships = await getPoemRelationships(poemId);
        setSelectedPoem(prev => ({ ...prev, relationships }));
        setNewTheme('');
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to add themes');
      }
    } catch (err) {
      alert(`Error adding themes: ${err.message}`);
    } finally {
      setAddingTheme(false);
    }
  };

  const removeThemeFromPoem = async (poemId, themeName) => {
    try {
      const response = await fetch(`${API_BASE}/api/poems/${poemId}/remove-theme/${encodeURIComponent(themeName)}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        // Refresh the selected poem's relationships
        const relationships = await getPoemRelationships(poemId);
        setSelectedPoem(prev => ({ ...prev, relationships }));
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to remove theme');
      }
    } catch (err) {
      alert(`Error removing theme: ${err.message}`);
    }
  };

  const handleAddThemes = async () => {
    if (!newTheme.trim() || !selectedPoem) return;
    
    const themes = newTheme.split(',').map(t => t.trim()).filter(t => t.length > 0);
    if (themes.length > 0) {
      await addThemeToPoem(selectedPoem.id, themes);
    }
  };

  const togglePoemSelection = (poemId) => {
    setSelectedPoems(prev => {
      if (prev.includes(poemId)) {
        return prev.filter(id => id !== poemId);
      } else {
        return [...prev, poemId];
      }
    });
  };

  const batchMarkAsCore = async () => {
    if (selectedPoems.length === 0) return;
    
    try {
      const response = await fetch(`${API_BASE}/api/narrative/mark-core`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ poem_ids: selectedPoems })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Marked ${result.success_count} poems as core narrative`);
        await loadPoems(); // Refresh the list
        setSelectedPoems([]);
        setBatchMode(false);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (err) {
      alert('Failed to mark poems as core');
    }
  };

  const batchMarkAsExtension = async () => {
    if (selectedPoems.length === 0) return;
    
    try {
      const response = await fetch(`${API_BASE}/api/narrative/mark-extension`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ poem_ids: selectedPoems })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Marked ${result.success_count} poems as extensions`);
        await loadPoems(); // Refresh the list
        setSelectedPoems([]);
        setBatchMode(false);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (err) {
      alert('Failed to mark poems as extensions');
    }
  };

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;
    
    setUploading(true);
    try {
      const formData = new FormData();
      Array.from(files).forEach(file => {
        formData.append('files', file);
      });
      
      const response = await fetch(`${API_BASE}/api/system/upload-poems`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Successfully uploaded ${result.uploaded_count} poems!`);
        if (result.skipped_count > 0) {
          alert(`Note: ${result.skipped_count} files were skipped (see console for details)`);
          console.log('Skipped files:', result.skipped_poems);
        }
        await loadPoems(); // Refresh the list
      } else {
        const error = await response.json();
        alert(`Error uploading poems: ${error.detail}`);
      }
    } catch (err) {
      alert('Failed to upload poems');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files).filter(file => 
      file.name.endsWith('.txt')
    );
    
    if (files.length === 0) {
      alert('Please drop .txt files only');
      return;
    }
    
    handleFileUpload(files);
  };

  if (loading) return <div className="p-4">Loading poems...</div>;
  if (error) return <div className="p-4 text-red-600">{error}</div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Poem List Panel */}
      <div className="lg:col-span-2 space-y-4">
        
        {/* File Upload Area */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-3">Upload Poems</h3>
          
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
              dragOver 
                ? 'border-blue-400 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {uploading ? (
              <div className="text-blue-600">
                <svg className="mx-auto h-8 w-8 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p className="mt-2">Uploading poems...</p>
              </div>
            ) : (
              <>
                <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <div className="mt-4">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Click to upload</span> or drag and drop
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    .txt files only. Multiple files supported.
                  </p>
                </div>
                <input
                  type="file"
                  multiple
                  accept=".txt"
                  onChange={(e) => handleFileUpload(e.target.files)}
                  className="hidden"
                  id="poem-upload"
                />
                <label
                  htmlFor="poem-upload"
                  className="mt-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 cursor-pointer"
                >
                  Choose Files
                </label>
              </>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search poems, routes, or content..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="all">All Poems</option>
                <option value="core">Core Narrative</option>
                <option value="extension">Extensions</option>
                <option value="route_generated">Route Generated</option>
                <option value="variation">Variations</option>
                <option value="unassigned">Unassigned</option>
              </select>
            </div>
            <div>
              <button
                onClick={() => {
                  setBatchMode(!batchMode);
                  setSelectedPoems([]);
                }}
                className={`px-4 py-2 text-sm rounded ${
                  batchMode 
                    ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                    : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }`}
              >
                {batchMode ? 'Cancel Batch' : 'Batch Select'}
              </button>
            </div>
          </div>
          
          {/* Batch Actions */}
          {batchMode && (
            <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded">
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-700">
                  Selected: {selectedPoems.length} poems
                </span>
                {selectedPoems.length > 0 && (
                  <div className="flex space-x-2">
                    <button
                      onClick={batchMarkAsCore}
                      className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                    >
                      Mark as Core
                    </button>
                    <button
                      onClick={batchMarkAsExtension}
                      className="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700"
                    >
                      Mark as Extension
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
          
          <div className="mt-3 text-sm text-gray-500">
            Showing {filteredPoems.length} of {poems.length} poems
          </div>
        </div>

        {/* Poem Grid */}
        <div className="space-y-3">
          {filteredPoems.map((poem) => (
            <div
              key={poem.id}
              className={`bg-white border rounded-lg p-4 hover:shadow-md transition-shadow ${
                selectedPoem?.id === poem.id ? 'ring-2 ring-blue-500' : 'border-gray-200'
              } ${
                batchMode && selectedPoems.includes(poem.id) ? 'ring-2 ring-purple-400' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {/* Batch Mode Checkbox */}
                  {batchMode && (
                    <input
                      type="checkbox"
                      checked={selectedPoems.includes(poem.id)}
                      onChange={() => togglePoemSelection(poem.id)}
                      className="mt-1 rounded border-gray-300 text-purple-600"
                    />
                  )}
                  
                  <div 
                    className="flex-1 cursor-pointer" 
                    onClick={() => !batchMode && handlePoemClick(poem)}
                  >
                  <div className="flex items-center space-x-2">
                    <h3 className="font-medium text-gray-900">
                      {poem.title || `Poem ${poem.id.slice(-8)}`}
                    </h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      poem.narrative_role === 'core' ? 'bg-green-100 text-green-800' :
                      poem.narrative_role === 'extension' ? 'bg-purple-100 text-purple-800' :
                      poem.narrative_role === 'route_generated' ? 'bg-blue-100 text-blue-800' :
                      poem.narrative_role === 'variation' ? 'bg-orange-100 text-orange-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {poem.narrative_role || 'unassigned'}
                    </span>
                  </div>
                  
                  <div className="mt-1 text-sm text-gray-500">
                    <span>Route: {poem.route_id}</span>
                    {poem.created_at && (
                      <span className="ml-3">
                        {new Date(poem.created_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  
                  {poem.content && (
                    <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                      {poem.content.substring(0, 120)}...
                    </p>
                  )}
                  </div>
                </div>
                
                <div className="ml-4">
                  <button 
                    className="text-gray-400 hover:text-gray-600"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (!batchMode) handlePoemClick(poem);
                    }}
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
          
          {filteredPoems.length === 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
              <p className="text-gray-500">No poems found matching your criteria.</p>
            </div>
          )}
        </div>
      </div>

      {/* Poem Detail Panel */}
      <div className="lg:col-span-1">
        <div className="bg-white border border-gray-200 rounded-lg p-6 sticky top-4">
          {selectedPoem ? (
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  {selectedPoem.title || 'Untitled Poem'}
                </h2>
                <p className="text-sm text-gray-500">
                  {selectedPoem.id}
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Route:</span>
                  <span className="text-sm text-gray-900">{selectedPoem.route_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Role:</span>
                  <span className={`text-sm px-2 py-1 rounded ${
                    selectedPoem.narrative_role === 'core' ? 'bg-green-100 text-green-800' :
                    selectedPoem.narrative_role === 'extension' ? 'bg-purple-100 text-purple-800' :
                    selectedPoem.narrative_role === 'route_generated' ? 'bg-blue-100 text-blue-800' :
                    selectedPoem.narrative_role === 'variation' ? 'bg-orange-100 text-orange-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {selectedPoem.narrative_role || 'unassigned'}
                  </span>
                </div>
                {selectedPoem.created_at && (
                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-500">Created:</span>
                    <span className="text-sm text-gray-900">
                      {new Date(selectedPoem.created_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>

              {selectedPoem.content && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Content:</h3>
                  <div className="bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap max-h-64 overflow-y-auto">
                    {selectedPoem.content}
                  </div>
                </div>
              )}

              {selectedPoem.relationships && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Relationships:</h3>
                  <div className="space-y-2">
                    {selectedPoem.relationships.themes?.length > 0 && (
                      <div>
                        <span className="text-xs font-medium text-gray-400">Themes:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {selectedPoem.relationships.themes.map(theme => (
                            <span key={theme} className="group relative px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded flex items-center">
                              {theme}
                              <button
                                onClick={() => removeThemeFromPoem(selectedPoem.id, theme)}
                                className="ml-1 opacity-0 group-hover:opacity-100 text-blue-600 hover:text-red-600 transition-opacity"
                                title="Remove theme"
                              >
                                ×
                              </button>
                            </span>
                          ))}
                        </div>
                        
                        {/* Add Theme Input */}
                        <div className="mt-2 flex gap-2">
                          <input
                            type="text"
                            placeholder="Add themes (comma-separated)"
                            value={newTheme}
                            onChange={(e) => setNewTheme(e.target.value)}
                            className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded"
                            onKeyPress={(e) => e.key === 'Enter' && handleAddThemes()}
                          />
                          <button
                            onClick={handleAddThemes}
                            disabled={!newTheme.trim() || addingTheme}
                            className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                          >
                            {addingTheme ? '...' : '+'}
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {/* Add Theme Section for poems without themes */}
                    {(!selectedPoem.relationships.themes || selectedPoem.relationships.themes.length === 0) && (
                      <div>
                        <span className="text-xs font-medium text-gray-400">Add Themes:</span>
                        <div className="mt-1 flex gap-2">
                          <input
                            type="text"
                            placeholder="Enter themes (comma-separated)"
                            value={newTheme}
                            onChange={(e) => setNewTheme(e.target.value)}
                            className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded"
                            onKeyPress={(e) => e.key === 'Enter' && handleAddThemes()}
                          />
                          <button
                            onClick={handleAddThemes}
                            disabled={!newTheme.trim() || addingTheme}
                            className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                          >
                            {addingTheme ? '...' : 'Add'}
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {selectedPoem.relationships.emotions?.length > 0 && (
                      <div>
                        <span className="text-xs font-medium text-gray-400">Emotions:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {selectedPoem.relationships.emotions.map(emotion => (
                            <span key={emotion} className="px-2 py-1 text-xs bg-pink-100 text-pink-800 rounded">
                              {emotion}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="pt-4 border-t border-gray-200 space-y-2">
                <button
                  onClick={() => generateNewPoem(selectedPoem.route_id)}
                  className="w-full px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                >
                  Generate Similar Poem
                </button>
                <button
                  onClick={() => setSelectedPoem(null)}
                  className="w-full px-3 py-2 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
                >
                  Close
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500">
              <p className="mb-4">Select a poem to view details</p>
              <button
                onClick={loadPoems}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
              >
                Refresh Poems
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PoemManager;