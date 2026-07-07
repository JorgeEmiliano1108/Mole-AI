// =============================================================================
// Copyright (C) 2024-2026 Mole.AI - All Rights Reserved.
// =============================================================================
// index-boot.js - Bootstrap configuration for index.html (Landing Page)
// Extracted from inline <script> for CSP/SoC compliance.
// =============================================================================

// API Base URL configuration (must load before ApiService.js)
window.AppConfig = {
    API_BASE_URL: '/api/v1/'  // Trailing slash required: baseUrl + endpoint concatenation in apiService._buildUrl
};

// Theme Toggle Function
function toggleTheme() {
    const body = document.body;
    body.classList.toggle('light-mode');
    localStorage.setItem('mole_theme', body.classList.contains('light-mode') ? 'solar' : 'pipboy');
}
// Expose globally for event delegation
window.toggleTheme = toggleTheme;

// Apply saved theme on load (IIFE)
(function() {
    const savedTheme = localStorage.getItem('mole_theme');
    if (savedTheme === 'solar') {
        document.body.classList.add('light-mode');
    }
})();

// BFCache Guard for index.html
window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        console.warn('[Index] P\u00e1gina restaurada de BFCache, re-validando...');
        // El index no requiere auth, pero limpiamos cualquier estado residual
    }
});

// Event Delegation for index.html interactive elements
document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action="toggle-theme"]');
    if (btn) {
        toggleTheme();
    }
});
