import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const SystemStatus = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    loadSystemStatus();
    const interval = setInterval(loadSystemStatus, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadSystemStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/system/status`);
      const data = await response.json();
      setStatus(data);
      
      // Add a log entry for successful status check
      setLogs(prev => [
        { time: new Date(), type: 'info', message: 'System status updated' },
        ...prev.slice(0, 49) // Keep last 50 logs
      ]);
    } catch (err) {
      setError('Failed to load system status');
      setLogs(prev => [
        { time: new Date(), type: 'error', message: `Failed to connect: ${err.message}` },
        ...prev.slice(0, 49)
      ]);
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (service) => {
    try {
      const response = await fetch(`${API_BASE}/api/system/test/${service}`);
      const result = await response.json();
      
      setLogs(prev => [
        { 
          time: new Date(), 
          type: result.status === 'ok' ? 'success' : 'error', 
          message: `${service} test: ${result.message}` 
        },
        ...prev.slice(0, 49)
      ]);
    } catch (err) {
      setLogs(prev => [
        { time: new Date(), type: 'error', message: `${service} test failed: ${err.message}` },
        ...prev.slice(0, 49)
      ]);
    }
  };

  const clearCache = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/system/clear-cache`, { method: 'POST' });
      const result = await response.json();
      
      setLogs(prev => [
        { time: new Date(), type: 'success', message: 'Cache cleared successfully' },
        ...prev.slice(0, 49)
      ]);
      
      await loadSystemStatus();
    } catch (err) {
      setLogs(prev => [
        { time: new Date(), type: 'error', message: `Cache clear failed: ${err.message}` },
        ...prev.slice(0, 49)
      ]);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return '❓';
    }
  };

  return (
    <div className="space-y-6">
      {/* System Overview */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          ⚙️ System Overview
          <button
            onClick={loadSystemStatus}
            className="ml-auto px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
            disabled={loading}
          >
            {loading ? '🔄 Refreshing...' : '🔄 Refresh'}
          </button>
        </h2>
        
        {status && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">Backend API</span>
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(status.api_status || 'healthy')}`}>
                  {getStatusIcon(status.api_status || 'healthy')} {status.api_status || 'Healthy'}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">FastAPI Server</p>
            </div>
            
            <div className="p-4 border rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">Poetry Graph</span>
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(status.graph_status || 'healthy')}`}>
                  {getStatusIcon(status.graph_status || 'healthy')} {status.graph_status || 'Loaded'}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">{status.total_poems || 0} poems loaded</p>
            </div>
            
            <div className="p-4 border rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">Azure OpenAI</span>
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(status.ai_status || 'unknown')}`}>
                  {getStatusIcon(status.ai_status || 'unknown')} {status.ai_status || 'Unknown'}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">GPT-4 Model</p>
            </div>
          </div>
        )}
      </div>

      {/* System Statistics */}
      {status && status.statistics && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">📊 Statistics</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{status.statistics.total_poems || 0}</div>
              <div className="text-sm text-gray-600">Total Poems</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{status.statistics.unique_routes || 0}</div>
              <div className="text-sm text-gray-600">Routes</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{status.statistics.narrative_connections || 0}</div>
              <div className="text-sm text-gray-600">Connections</div>
            </div>
            <div className="text-center p-3 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{status.statistics.total_themes || 0}</div>
              <div className="text-sm text-gray-600">Themes</div>
            </div>
          </div>
        </div>
      )}

      {/* System Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">🔧 System Actions</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <button
            onClick={() => testConnection('database')}
            className="p-3 border border-blue-200 rounded-lg hover:bg-blue-50 text-left"
          >
            <div className="font-medium text-blue-600">Test Database</div>
            <div className="text-sm text-gray-500">Check graph connectivity</div>
          </button>
          
          <button
            onClick={() => testConnection('ai')}
            className="p-3 border border-green-200 rounded-lg hover:bg-green-50 text-left"
          >
            <div className="font-medium text-green-600">Test AI Connection</div>
            <div className="text-sm text-gray-500">Verify Azure OpenAI</div>
          </button>
          
          <button
            onClick={clearCache}
            className="p-3 border border-orange-200 rounded-lg hover:bg-orange-50 text-left"
          >
            <div className="font-medium text-orange-600">Clear Cache</div>
            <div className="text-sm text-gray-500">Reset system caches</div>
          </button>
        </div>
      </div>

      {/* System Logs */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center justify-between">
          📝 System Logs
          <button
            onClick={() => setLogs([])}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
          >
            Clear Logs
          </button>
        </h2>
        
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {logs.length > 0 ? logs.map((log, index) => (
            <div key={index} className={`p-2 rounded text-sm ${
              log.type === 'error' ? 'bg-red-50 text-red-700' :
              log.type === 'success' ? 'bg-green-50 text-green-700' :
              log.type === 'warning' ? 'bg-yellow-50 text-yellow-700' :
              'bg-gray-50 text-gray-700'
            }`}>
              <span className="text-xs text-gray-500">
                {log.time.toLocaleTimeString()}
              </span>
              <span className="ml-3">{log.message}</span>
            </div>
          )) : (
            <p className="text-gray-500 text-sm italic">No logs yet</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;