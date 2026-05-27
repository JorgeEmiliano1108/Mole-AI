/**
 * Sistema de Bloqueo y Feedback Visual (Spinner) para operaciones as ncronas.
 * Previene el doble-env o de formularios y brinda feedback claro al operador.
 * CUMPLE REQ-NF-SEC-02: Cero innerHTML - usa DOM API exclusivamente.
 */

export class SpinnerService {
    constructor() {
        this.activeButtons = new Map();
    }

    /**
     * Muestra un spinner o texto de carga en un bot n y lo deshabilita.
     * @param {HTMLElement|string} button - Elemento DOM o ID del bot n.
     * @param {string} loadingText - Texto opcional a mostrar durante la carga.
     */
    show(button, loadingText = '[ PROCESANDO... ]') {
        const btn = typeof button === 'string' ? document.getElementById(button) : button;
        if (!btn) return;

        // Guardar el estado original del bot n (sin innerHTML)
        if (!this.activeButtons.has(btn)) {
            this.activeButtons.set(btn, {
                originalChildren: Array.from(btn.childNodes),
                originalDisabled: btn.disabled,
                originalClasses: btn.className
            });
        }

        btn.disabled = true;
        btn.classList.add('cursor-not-allowed', 'opacity-50');

        // Efecto Cyberpunk de carga - usando DOM API segura
        btn.textContent = '';
        btn.classList.remove('opacity-50');

        const spanLoading = document.createElement('span');
        spanLoading.className = 'animate-pulse';
        spanLoading.textContent = loadingText;
        btn.appendChild(spanLoading);

        const spinnerEl = document.createElement('span');
        spinnerEl.className = 'inline-block w-4 h-4 ml-2 border-2 border-t-transparent border-[#00e5ff] rounded-full animate-spin';
        btn.appendChild(spinnerEl);
    }

    /**
     * Restaura el bot n a su estado original.
     * @param {HTMLElement|string} button - Elemento DOM o ID del bot n.
     */
    hide(button) {
        const btn = typeof button === 'string' ? document.getElementById(button) : button;
        if (!btn || !this.activeButtons.has(btn)) return;

        const state = this.activeButtons.get(btn);

        // Limpiar hijos actuales
        while (btn.firstChild) {
            btn.removeChild(btn.firstChild);
        }

        // Restaurar hijos originales
        state.originalChildren.forEach(child => {
            btn.appendChild(child);
        });

        btn.disabled = state.originalDisabled;
        btn.className = state.originalClasses;

        this.activeButtons.delete(btn);
    }

    /**
     * Bloqueo Global de UI (para transiciones completas)
     */
    showGlobal() {
        let overlay = document.getElementById('global-spinner-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'global-spinner-overlay';
            overlay.className = 'fixed inset-0 bg-black/80 z-[9999] flex flex-col items-center justify-center';

            // Spinner circle
            const spinnerDiv = document.createElement('div');
            spinnerDiv.className = 'w-16 h-16 border-4 border-[#00e5ff]/20 border-t-[#00e5ff] rounded-full animate-spin';
            overlay.appendChild(spinnerDiv);

            // Loading text
            const textDiv = document.createElement('div');
            textDiv.className = 'mt-4 text-[#00e5ff] font-mono tracking-widest animate-pulse';
            textDiv.textContent = '> SINCRONIZANDO...';
            overlay.appendChild(textDiv);

            document.body.appendChild(overlay);
        }
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
    }

    hideGlobal() {
        const overlay = document.getElementById('global-spinner-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
            overlay.classList.remove('flex');
        }
    }
}

export const spinner = new SpinnerService();
window.Spinner = spinner;