// Theme toggle logic extracted from dashboard.html
export function toggleTheme() {
    const body = document.body;
    const iconSun = document.getElementById('icon-sun');
    const iconMoon = document.getElementById('icon-moon');
    body.classList.toggle('light-mode');
    if (body.classList.contains('light-mode')) {
        if (iconSun) iconSun.classList.remove('hidden');
        if (iconMoon) iconMoon.classList.add('hidden');
        localStorage.setItem('mole_theme', 'solar');
    } else {
        if (iconSun) iconSun.classList.add('hidden');
        if (iconMoon) iconMoon.classList.remove('hidden');
        localStorage.setItem('mole_theme', 'pipboy');
    }
}

// Apply saved theme on load (self invoking)
(function() {
    const savedTheme = localStorage.getItem('mole_theme');
    if (savedTheme === 'solar') {
        document.body.classList.add('light-mode');
        window.addEventListener('DOMContentLoaded', function() {
            const iconSun = document.getElementById('icon-sun');
            const iconMoon = document.getElementById('icon-moon');
            if (iconSun) iconSun.classList.remove('hidden');
            if (iconMoon) iconMoon.classList.add('hidden');
        });
    }
})();

