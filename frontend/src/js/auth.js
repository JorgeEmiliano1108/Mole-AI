// 1. Guardi n de Sesi n Inicial (Inmediato)
(function checkInitialSession() {
    const token = localStorage.getItem('mole_jwt') || localStorage.getItem('moleia_token');
    if (token && window.location.pathname.includes('login.html')) {
        window.location.replace('/dashboard.html');
    }
})();

// 2. DOM Listeners (On Load)
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (!loginForm) return; // Salir si no estamos en login.html

    // Submit delegation
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        document.querySelector('[data-action="auth:login"]')?.click();
    });

    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            document.querySelector('[data-action="auth:register"]')?.click();
        });
    }

    // Password Toggle UX
    document.querySelectorAll('.toggle-pass-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = btn.closest('.relative').querySelector('input');
            if (input) {
                const isHidden = (input.type === 'password');
                input.type = isHidden ? 'text' : 'password';
                btn.setAttribute('aria-label', isHidden ? 'Ocultar' : 'Mostrar');
                btn.querySelector('.eye-open').classList.toggle('hidden', !isHidden);
                btn.querySelector('.eye-closed').classList.toggle('hidden', isHidden);
            }
        });
    });
});

// 3. BFCache Guard (Restauraci n desde historial)
window.addEventListener('pageshow', (event) => {
    if (event.persisted && window.location.pathname.includes('login.html')) {
        ['user-input', 'pass-input', 'reg-username', 'reg-email', 'reg-password', 'reg-pass-confirm'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        
        const token = localStorage.getItem('mole_jwt') || localStorage.getItem('moleia_token');
        if (token) window.location.replace('/dashboard.html');
    }
});

// 4. Password Recovery (migrado de mlops.js en FE-DT14 por cohesión semántica)
export async function forgotPassword() {
    const user = prompt("Ingrese su usuario o correo para recuperar la credencial:");
    if (!user) return;

    try {
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/auth/password-reset/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier: user })
        });

        if (response.ok) {
            alert("> PROTOCOLO DE RECUPERACI\u00d3N INICIADO. Revise su terminal (correo).");
        } else {
            alert("> [ ERROR ] Credencial no encontrada o sistema bloqueado.");
        }
    } catch (e) {
        alert("> [ ERROR CR\u00cdTICO ] No se pudo contactar al servidor central.");
    }
}
