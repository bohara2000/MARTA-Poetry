/**
 * API utility functions
 * Dynamically constructs API URLs based on the current environment
 */

/**
 * Get the API base URL
 * In development: uses http://localhost:8000
 * In production: uses the current origin (same as frontend)
 */
export function getApiBaseUrl() {
  if (process.env.NODE_ENV === 'development') {
    // In development, connect to the backend running on port 8000
    return 'http://localhost:8000';
  } else {
    // In production, use the same origin as the frontend
    // This assumes the backend is served from the same domain
    return window.location.origin;
  }
}

/**
 * Construct a full API URL
 */
export function getApiUrl(endpoint) {
  const baseUrl = getApiBaseUrl();
  // Ensure endpoint starts with /
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${path}`;
}

/**
 * Fetch with automatic base URL
 */
export async function apiFetch(endpoint, options = {}) {
  const url = getApiUrl(endpoint);
  return fetch(url, options);
}
