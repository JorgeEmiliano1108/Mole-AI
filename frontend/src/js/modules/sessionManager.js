// Session manager – tracks real user activity and enforces JWT expiry / inactivity
// ---------------------------------------------------------------
// This module is imported once (in main.js) so its side‑effects run globally.

import { getAuthToken, clearAuthToken } from './api/config.js';

// Helper: decode JWT payload (no verification) to read iat claim
function decodeJwtPayload(token) {
  if (!token) return null;
  const parts = token.split('.');
  if (parts.length < 2) return null;
  try {
    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch (e) {
    return null;
  }
}

// Simple debounce – execute fn after wait ms of no further calls
function debounce(fn, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), wait);
  };
}

// Timestamp of the last user interaction (ms since epoch)
let lastActivityTime = Date.now();

// Update activity timestamp – debounced to avoid flooding on fast events
const recordActivity = debounce(() => {
  lastActivityTime = Date.now();
}, 300);

// List of events that count as activity
['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach(ev => {
  window.addEventListener(ev, recordActivity, true);
});

// Configuration (in ms)
const INACTIVITY_LIMIT = 20 * 60 * 1000; // 20 minutes
const REFRESH_THRESHOLD = 15 * 60 * 1000; // 15 minutes token age
const CHECK_INTERVAL = 60 * 1000; // 1 minute

// Periodic check – runs even if the user is not interacting
const intervalId = setInterval(() => {
  const now = Date.now();

  // 1. Inactivity timeout -> log out immediately
  if (now - lastActivityTime >= INACTIVITY_LIMIT) {
    clearAuthToken();
    if (window.ApiService && typeof window.ApiService.clearToken === 'function') {
      window.ApiService.clearToken();
    }
    window.location.replace('/login.html');
    clearInterval(intervalId);
    return;
  }

  // 2. Token refresh - only if we have a token and it is >15 min old
  const token = getAuthToken();
  if (token) {
    const payload = decodeJwtPayload(token);
    if (payload && payload.iat) {
      const tokenAge = now - payload.iat * 1000;
      if (tokenAge >= REFRESH_THRESHOLD) {
        if (window.ApiService && typeof window.ApiService.post === 'function') {
          window.ApiService.post('auth/refresh/', {}, {})
            .then(resp => {
              if (resp && resp.token) {
                window.ApiService.setToken(resp.token);
              }
            })
            .catch(err => {
              console.warn('[SessionManager] token refresh failed', err);
            });
        }
      }
    }
  }
}, CHECK_INTERVAL);

// Optional export for testing
export { lastActivityTime };