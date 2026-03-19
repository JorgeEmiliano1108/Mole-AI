// =============================================================================
// config.js — Zero Trust Configuration
// Supabase credentials injected server-side via Django template data-* attributes.
// API_URL derived dynamically from current origin (works in dev + prod).
// =============================================================================

(function () {
    'use strict';

    const body = document.body;

    window.APP_CONFIG = {
        // Zero Trust: derive API gateway URL from current origin
        API_URL: window.location.origin + '/api/v1/',

        // Supabase config injected by Django via data-* attributes on <body>
        SUPABASE: {
            URL: body.dataset.supabaseUrl || '',
            ANON_KEY: body.dataset.supabaseKey || ''
        },

        // Timeout configuration (ms)
        TIMEOUTS: {
            DEFAULT: 30000,   // 30s for standard requests
            AI: 120000        // 120s for AI/LLM endpoints
        },

        // Retry configuration
        RETRY: {
            MAX_ATTEMPTS: 3,
            BASE_DELAY: 1000  // 1s base, exponential backoff
        }
    };

    // Backward compatibility
    window.SUPABASE_CONFIG = window.APP_CONFIG.SUPABASE;
})();