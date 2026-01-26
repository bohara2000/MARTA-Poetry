import React, { useState, useEffect } from 'react';
import './NarrativeAdherenceTest.css';
import { getApiUrl } from '../utils/api';

const NarrativeAdherenceTest = () => {
  const [routeId, setRouteId] = useState('');
  const [availableRoutes, setAvailableRoutes] = useState([]);
  const [loadingRoutes, setLoadingRoutes] = useState(true);
  const [storyInfluence, setStoryInfluence] = useState(0.5);
  const [testType, setTestType] = useState('single'); // 'single' or 'comprehensive'
  const [testResults, setTestResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch available routes on component mount
  useEffect(() => {
    fetchAvailableRoutes();
  }, []);

  const fetchAvailableRoutes = async () => {
    setLoadingRoutes(true);
    setError('');
    try {
      console.log('Fetching routes from /api/available-routes');
      const url = getApiUrl('/api/available-routes');
      console.log('Fetch URL:', url);
      const response = await fetch(url);
      console.log('Response status:', response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Routes data:', data);
      // Convert from object format to array
      const routesArray = Object.entries(data.routes || {}).map(([routeId, routeInfo]) => ({
        route_id: routeId,
        friendly_name: routeInfo.name || routeId,
        ...routeInfo
      }));
      console.log('Routes array:', routesArray);
      setAvailableRoutes(routesArray);
      
      // Auto-select first route if none selected
      if (routesArray && routesArray.length > 0 && !routeId) {
        console.log('Auto-selecting first route:', routesArray[0].route_id);
        setRouteId(routesArray[0].route_id);
      }
    } catch (err) {
      console.error('Error fetching routes:', err);
      setError(`Failed to load available routes: ${err.message}`);
    } finally {
      setLoadingRoutes(false);
    }
  };

  const handleRunTest = async () => {
    if (!routeId) {
      setError('Please select a route');
      return;
    }

    setLoading(true);
    setError('');
    setTestResults(null);

    try {
      const requestData = {
        route_id: routeId,
        comprehensive: testType === 'comprehensive'
      };

      if (testType === 'single') {
        requestData.story_influence = storyInfluence;
      }

      const response = await fetch(getApiUrl('/api/narrative/test-adherence'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setTestResults(data.results);
    } catch (err) {
      console.error('Error running adherence test:', err);
      setError(err.message || 'Failed to run narrative adherence test');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!routeId) {
      setError('Please select a route');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(getApiUrl('/api/narrative/generate-adherence-report'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ route_id: routeId })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      alert(`Report generated successfully: ${data.message}`);
    } catch (err) {
      console.error('Error generating report:', err);
      setError(err.message || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const getAdherenceColor = (score) => {
    if (score >= 0.8) return '#4CAF50'; // Green
    if (score >= 0.6) return '#FF9800'; // Orange
    if (score >= 0.4) return '#F44336'; // Red
    return '#9C27B0'; // Purple for very low
  };

  const getResultBadgeClass = (result) => {
    switch (result) {
      case 'HIGH_ADHERENCE': return 'badge-success';
      case 'MODERATE_ADHERENCE': return 'badge-warning';
      case 'LOW_ADHERENCE': return 'badge-danger';
      case 'POOR_ADHERENCE': return 'badge-critical';
      case 'NO_POEMS': return 'badge-info';
      default: return 'badge-secondary';
    }
  };

  const renderSingleTestResults = (results) => (
    <div className="test-results">
      <div className="result-header">
        <h4>Test Results for Route {results.route_id}</h4>
        <div className="result-badges">
          <span className={`badge ${getResultBadgeClass(results.test_result)}`}>
            {results.test_result.replace('_', ' ')}
          </span>
          <span className="adherence-score" style={{ color: getAdherenceColor(results.avg_adherence_score || 0) }}>
            {((results.avg_adherence_score || 0) * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      <div className="test-details">
        <div className="detail-grid">
          <div className="detail-item">
            <label>Story Influence:</label>
            <span>{results.story_influence?.toFixed(1)}</span>
          </div>
          <div className="detail-item">
            <label>Expected Stance:</label>
            <span className="stance">{results.expected_stance?.toUpperCase()}</span>
          </div>
          <div className="detail-item">
            <label>Poems Analyzed:</label>
            <span>{results.poems_analyzed}</span>
          </div>
          <div className="detail-item">
            <label>Adherence Score:</label>
            <span style={{ color: getAdherenceColor(results.avg_adherence_score || 0) }}>
              {((results.avg_adherence_score || 0) * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {results.detailed_analysis && results.detailed_analysis.length > 0 && (
        <div className="poem-analysis">
          <h5>Individual Poem Analysis</h5>
          <div className="poems-list">
            {results.detailed_analysis.slice(0, 5).map((poem, index) => (
              <div key={index} className="poem-item">
                <div className="poem-title">{poem.title}</div>
                <div className="poem-score">
                  <span className="score-label">Adherence:</span>
                  <span 
                    className="score-value" 
                    style={{ color: getAdherenceColor(poem.adherence_score) }}
                  >
                    {(poem.adherence_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
            {results.detailed_analysis.length > 5 && (
              <div className="more-poems">
                +{results.detailed_analysis.length - 5} more poems...
              </div>
            )}
          </div>
        </div>
      )}

      {results.narrative_data && (
        <div className="narrative-details">
          <h5>Narrative Expectations</h5>
          <div className="narrative-info">
            <div className="motifs-section">
              <strong>Emphasized Motifs:</strong>
              <ul>
                {results.narrative_data.emphasized_motifs?.map((motif, index) => (
                  <li key={index}>{motif}</li>
                ))}
              </ul>
            </div>
            {results.narrative_data.rejected_motifs?.length > 0 && (
              <div className="motifs-section rejected">
                <strong>Rejected Motifs:</strong>
                <ul>
                  {results.narrative_data.rejected_motifs.map((motif, index) => (
                    <li key={index}>{motif}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderComprehensiveResults = (results) => (
    <div className="test-results comprehensive">
      <div className="result-header">
        <h4>Comprehensive Test Results for Route {results.route_id}</h4>
        <div className="summary-stats">
          <span className="stat">
            <label>Overall Average:</label>
            <span style={{ color: getAdherenceColor(results.summary?.avg_adherence_across_all || 0) }}>
              {((results.summary?.avg_adherence_across_all || 0) * 100).toFixed(1)}%
            </span>
          </span>
        </div>
      </div>

      <div className="influence-tests">
        {results.test_results?.map((test, index) => (
          <div key={index} className="influence-test-card">
            <div className="test-card-header">
              <div className="influence-info">
                <span className="influence-level">
                  Story Influence: {test.story_influence?.toFixed(1)}
                </span>
                <span className={`stance stance-${test.expected_stance}`}>
                  {test.expected_stance?.toUpperCase()}
                </span>
              </div>
              <div className="test-result-info">
                <span className={`badge ${getResultBadgeClass(test.test_result)}`}>
                  {test.test_result?.replace('_', ' ')}
                </span>
                <span className="adherence-score" style={{ color: getAdherenceColor(test.avg_adherence_score || 0) }}>
                  {((test.avg_adherence_score || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            
            {test.poems_analyzed !== undefined && (
              <div className="poems-count">
                {test.poems_analyzed} poems analyzed
              </div>
            )}
          </div>
        ))}
      </div>

      {results.summary && (
        <div className="summary-section">
          <h5>Summary</h5>
          <div className="best-worst">
            <div className="performance-item best">
              <strong>Best Performance:</strong>
              <div>
                Story Influence {results.summary.best_adherence?.story_influence?.toFixed(1)} 
                ({results.summary.best_adherence?.expected_stance}) - 
                <span style={{ color: getAdherenceColor(results.summary.best_adherence?.avg_adherence_score || 0) }}>
                  {((results.summary.best_adherence?.avg_adherence_score || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            <div className="performance-item worst">
              <strong>Worst Performance:</strong>
              <div>
                Story Influence {results.summary.worst_adherence?.story_influence?.toFixed(1)} 
                ({results.summary.worst_adherence?.expected_stance}) - 
                <span style={{ color: getAdherenceColor(results.summary.worst_adherence?.avg_adherence_score || 0) }}>
                  {((results.summary.worst_adherence?.avg_adherence_score || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="narrative-adherence-test">
      <div className="test-header">
        <h3>🧪 Narrative Adherence Testing</h3>
        <p>Test how well a route's poems adhere to their expected narrative stance based on story influence.</p>
      </div>

      <div className="test-controls">
        <div className="control-row">
          <div className="control-group">
            <label htmlFor="routeId">Route:</label>
            {loadingRoutes ? (
              <div className="loading-routes">Loading routes...</div>
            ) : (
              <select
                id="routeId"
                value={routeId}
                onChange={(e) => setRouteId(e.target.value)}
                disabled={loading}
              >
                <option value="">Select a route...</option>
                {availableRoutes.map((route) => (
                  <option key={route.route_id} value={route.route_id}>
                    {route.friendly_name}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="control-group">
            <label htmlFor="testType">Test Type:</label>
            <select
              id="testType"
              value={testType}
              onChange={(e) => setTestType(e.target.value)}
              disabled={loading}
            >
              <option value="single">Single Story Influence</option>
              <option value="comprehensive">Comprehensive (Multiple Levels)</option>
            </select>
          </div>
        </div>

        {testType === 'single' && (
          <div className="control-row">
            <div className="control-group">
              <label htmlFor="storyInfluence">Story Influence: {storyInfluence.toFixed(1)}</label>
              <input
                type="range"
                id="storyInfluence"
                min="0"
                max="1"
                step="0.1"
                value={storyInfluence}
                onChange={(e) => setStoryInfluence(parseFloat(e.target.value))}
                disabled={loading}
              />
              <div className="range-labels">
                <span>Opposing (0.0)</span>
                <span>Ambivalent (0.5)</span>
                <span>Supporting (1.0)</span>
              </div>
            </div>
          </div>
        )}

        <div className="action-buttons">
          <button 
            className="btn btn-primary" 
            onClick={handleRunTest}
            disabled={loading}
          >
            {loading ? 'Running Test...' : 'Run Adherence Test'}
          </button>
          
          <button 
            className="btn btn-secondary" 
            onClick={handleGenerateReport}
            disabled={loading}
          >
            {loading ? 'Generating...' : 'Generate Full Report'}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {testResults && (
        <div className="results-section">
          {testResults.test_results ? 
            renderComprehensiveResults(testResults) : 
            renderSingleTestResults(testResults)
          }
        </div>
      )}

      <div className="help-section">
        <h4>How Narrative Adherence Testing Works</h4>
        <div className="help-content">
          <div className="help-item">
            <strong>Story Influence Levels:</strong>
            <ul>
              <li><strong>0.0-0.3 (Opposing):</strong> Route should reject surveillance themes, emphasize freedom/escape</li>
              <li><strong>0.3-0.7 (Ambivalent):</strong> Route should show mixed relationship to canonical themes</li>
              <li><strong>0.7-1.0 (Supporting):</strong> Route should embrace urban observation and canonical motifs</li>
            </ul>
          </div>
          <div className="help-item">
            <strong>Adherence Scoring:</strong>
            <ul>
              <li><strong>80%+ (High):</strong> Strong alignment with expected narrative stance</li>
              <li><strong>60-80% (Moderate):</strong> Reasonable alignment with some deviations</li>
              <li><strong>40-60% (Low):</strong> Weak alignment, significant mismatches</li>
              <li><strong>&lt;40% (Poor):</strong> Very little adherence to expected patterns</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NarrativeAdherenceTest;