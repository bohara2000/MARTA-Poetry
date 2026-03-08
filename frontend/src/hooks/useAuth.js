import { useState, useEffect } from 'react';

/**
 * Fetches the current user from Azure Static Web Apps' built-in auth endpoint.
 * Returns { user, loading } where user is null when unauthenticated.
 *
 * user shape: { userId, userDetails, identityProvider, userRoles, claims }
 */
export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/.auth/me')
      .then(res => res.json())
      .then(data => {
        const principal = data?.clientPrincipal ?? null;
        setUser(principal);
      })
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  return { user, loading };
}

export function logout() {
  window.location.href = '/.auth/logout?post_logout_redirect_uri=/';
}
