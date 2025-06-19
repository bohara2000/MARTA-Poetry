import React, { useEffect, useState } from 'react';

function RouteSelector({ onSelectRoute, routeType = 'bus' }) {
  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`http://localhost:8000/api/routes?type=${routeType}`)
      .then(res => res.json())
      .then(data => {
        setRoutes(data.routes || []);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load routes');
        setLoading(false);
      });
  }, [routeType]);

  return (
    <div className="mb-4">
      <label htmlFor="route" className="block font-semibold">Select Route:</label>
      {loading ? (
        <div>Loading routes...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : (
        <select id="route" onChange={(e) => onSelectRoute(e.target.value)} className="border p-2 rounded">
          <option value="">-- Choose a Route --</option>
          {routes.map((route) => (
            <option key={route.route_id} value={route.route_id}>
              {route.route_short_name || route.route_id} - {route.route_long_name}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}

export default RouteSelector;
