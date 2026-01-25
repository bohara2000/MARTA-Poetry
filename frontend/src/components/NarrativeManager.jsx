import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const NarrativeManager = () => {
  const [narrativeStatus, setNarrativeStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeAction, setActiveAction] = useState(null);

  useEffect(() => {
    loadNarrativeStatus();
  }, []);

  const loadNarrativeStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/narrative/status`);
      const data = await response.json();
      setNarrativeStatus(data);
    } catch (err) {
      setError('Failed to load narrative status');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsCore = async (poemIds) => {
    try {
      const response = await fetch(`${API_BASE}/api/narrative/mark-core`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ poem_ids: poemIds })
      });
      
      if (response.ok) {
        await loadNarrativeStatus();
        setActiveAction(null);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (err) {
      alert('Failed to mark poems as core');
    }
  };

  const handleMarkAsExtension = async (poemIds) => {
    try {
      const response = await fetch(`${API_BASE}/api/narrative/mark-extension`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ poem_ids: poemIds })
      });
      
      if (response.ok) {
        await loadNarrativeStatus();
        setActiveAction(null);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (err) {
      alert('Failed to mark poems as extension');
    }
  };

  const handleRemovePoem = async (poemId) => {
    if (!confirm(`Are you sure you want to remove poem "${poemId}"?`)) return;
    
    try {
      const response = await fetch(`${API_BASE}/api/narrative/remove-poem/${poemId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        await loadNarrativeStatus();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (err) {
      alert('Failed to remove poem');
    }
  };

  const handleClearRole = async (poemId) => {
    try {
      const response = await fetch(`${API_BASE}/api/narrative/clear-role/${poemId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        await loadNarrativeStatus();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (err) {
      alert('Failed to clear narrative role');
    }
  };

  if (loading) return <div className="p-4">Loading narrative structure...</div>;
  if (error) return <div className="p-4 text-red-600">{error}</div>;

  return (
    <div className="space-y-6">
      {/* Status Overview */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          📊 Narrative Overview
        </h2>
        
        {narrativeStatus && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{narrativeStatus.summary?.core_poems || 0}</div>
              <div className="text-sm text-gray-600">Core Poems</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{narrativeStatus.summary?.extension_poems || 0}</div>
              <div className="text-sm text-gray-600">Extensions</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{narrativeStatus.summary?.route_generated_poems || 0}</div>
              <div className="text-sm text-gray-600">Route Generated</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-600">{narrativeStatus.summary?.total_poems || 0}</div>
              <div className="text-sm text-gray-600">Total Poems</div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          ⚡ Quick Actions
        </h2>
        
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => loadNarrativeStatus()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            🔄 Refresh Status
          </button>
          <button
            onClick={() => setActiveAction('bulk-core')}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            📖 Mark as Core
          </button>
          <button
            onClick={() => setActiveAction('bulk-extension')}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
          >
            🔗 Mark as Extension
          </button>
          <button
            onClick={() => setActiveAction('export')}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            📋 Export Report
          </button>
        </div>
      </div>

      {/* Poem Categories */}
      {narrativeStatus && Object.entries(narrativeStatus.poems_by_role || {}).map(([role, poems]) => (
        <div key={role} className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
            <span>
              {role === 'core' && '📖 Core Narrative'}
              {role === 'extension' && '🔗 Extensions'}
              {role === 'route_generated' && '🚌 Route Generated'}
              {role === 'variation' && '🎭 Variations'}
              {role === 'unassigned' && '❓ Unassigned'}
              <span className="ml-2 text-sm text-gray-500">({poems.length})</span>
            </span>
            
            {poems.length > 0 && (
              <div className="space-x-2">
                {role === 'unassigned' && (
                  <>
                    <button
                      onClick={() => handleMarkAsCore(poems.map(p => p.id))}
                      className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded"
                    >
                      Mark All as Core
                    </button>
                    <button
                      onClick={() => handleMarkAsExtension(poems.map(p => p.id))}
                      className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded"
                    >
                      Mark All as Extension
                    </button>
                  </>
                )}
              </div>
            )}
          </h3>
          
          <div className="space-y-3">
            {poems.map((poem) => (
              <div key={poem.id} className="border border-gray-100 rounded-md p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">
                      {poem.title || poem.id}
                    </h4>
                    <div className="text-sm text-gray-500 mt-1">
                      <span>Route: {poem.route_id}</span>
                      {poem.created_at && (
                        <span className="ml-3">Created: {new Date(poem.created_at).toLocaleDateString()}</span>
                      )}
                    </div>
                    {poem.content && (
                      <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                        {poem.content.substring(0, 150)}...
                      </p>
                    )}
                  </div>
                  
                  <div className="ml-4 space-x-2">
                    {role !== 'core' && (
                      <button
                        onClick={() => handleMarkAsCore([poem.id])}
                        className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                        title="Mark as Core"
                      >
                        📖
                      </button>
                    )}
                    {role !== 'extension' && (
                      <button
                        onClick={() => handleMarkAsExtension([poem.id])}
                        className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
                        title="Mark as Extension"
                      >
                        🔗
                      </button>
                    )}
                    {role !== 'unassigned' && (
                      <button
                        onClick={() => handleClearRole(poem.id)}
                        className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                        title="Clear Role"
                      >
                        🔄
                      </button>
                    )}
                    <button
                      onClick={() => handleRemovePoem(poem.id)}
                      className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                      title="Remove Poem"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))}
            
            {poems.length === 0 && (
              <p className="text-gray-500 text-sm italic">No poems in this category</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default NarrativeManager;