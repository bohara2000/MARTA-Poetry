/**
 * API utility functions
 * Dynamically constructs API URLs based on the current environment
 */

/**
 * Get the API base URL
 * 
 * Supports three scenarios:
 * 1. Environment variable VITE_API_URL (set by build/deploy process)
 * 2. Development: http://localhost:8000
 * 3. Production: same origin as frontend (if backend served from same domain)
 */
export function getApiBaseUrl() {
  // Check for explicit environment variable (set during build)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  if (import.meta.env.DEV) {
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
