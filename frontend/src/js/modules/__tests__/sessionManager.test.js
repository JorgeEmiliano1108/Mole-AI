import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock localStorage
const localStore = {};
Object.defineProperty(globalThis, 'localStorage', {
  value: {
    getItem: (key) => localStore[key] ?? null,
    setItem: (key, value) => { localStore[key] = String(value); },
    removeItem: (key) => { delete localStore[key]; },
    clear: () => { Object.keys(localStore).forEach(k => delete localStore[k]); },
    get length() { return Object.keys(localStore).length; },
    key: (i) => Object.keys(localStore)[i] ?? null,
  },
  writable: true,
  configurable: true,
});

// Mock api/config
vi.mock('../api/config.js', () => ({
  getAuthToken: vi.fn(),
  clearAuthToken: vi.fn(),
}));

// Mock BroadcastChannel
globalThis.BroadcastChannel = vi.fn(() => ({
  postMessage: vi.fn(),
  addEventListener: vi.fn(),
  close: vi.fn(),
}));

describe('sessionManager', () => {
  let getAuthToken, clearAuthToken;

  beforeEach(async () => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    Object.keys(localStore).forEach(k => delete localStore[k]);
    vi.resetModules();
    const config = await import('../api/config.js');
    getAuthToken = config.getAuthToken;
    clearAuthToken = config.clearAuthToken;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('exports sessionLogout function', async () => {
    const mod = await import('../auth/sessionManager.js');
    expect(mod.sessionLogout).toBeDefined();
    expect(typeof mod.sessionLogout).toBe('function');
  });

  it('exports lastActivityTime', async () => {
    const mod = await import('../auth/sessionManager.js');
    expect(mod.lastActivityTime).toBeDefined();
    expect(typeof mod.lastActivityTime).toBe('number');
  });

  it('calls clearAuthToken on cleanupSession (via sessionLogout)', async () => {
    const mod = await import('../auth/sessionManager.js');

    const replace = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { replace },
      writable: true,
    });

    mod.sessionLogout();

    expect(clearAuthToken).toHaveBeenCalled();
  });

  it('forces logout on inactivity', async () => {
    const replace = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { replace },
      writable: true,
    });

    await import('../auth/sessionManager.js');

    vi.advanceTimersByTime(20 * 60 * 1000 + 1000);

    await vi.runAllTimersAsync();

    expect(replace).toHaveBeenCalledWith('/login.html');
  });

  it('attempts token refresh when token is old', async () => {
    const replace = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { replace },
      writable: true,
    });

    // Dynamically import apiService AFTER resetModules() to get a fresh instance,
    // set mocks on it, THEN import sessionManager.js (which shares the same instance)
    const { apiService } = await import('../api/ApiService.js');
    const postMock = vi.fn().mockResolvedValue({ token: 'new-token' });
    apiService.post = postMock;

    const oldIat = Math.floor((Date.now() - 16 * 60 * 1000) / 1000);
    const payload = btoa(JSON.stringify({ iat: oldIat }));
    getAuthToken.mockReturnValue(`header.${payload}.signature`);

    await import('../auth/sessionManager.js');

    vi.advanceTimersByTime(60 * 1000);

    expect(postMock).toHaveBeenCalledWith('auth/refresh/', {}, {});
  });

  it('clears moleia_chat_history_data on logout', async () => {
    const replace = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { replace },
      writable: true,
    });

    localStorage.setItem('moleia_chat_history_data', 'some data');

    const mod = await import('../auth/sessionManager.js');
    mod.sessionLogout();

    expect(localStorage.getItem('moleia_chat_history_data')).toBeNull();
  });
});
