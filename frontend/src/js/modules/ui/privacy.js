/**
 * Módulo de Privacidad (LFPDPPP)
 * Controla la visualización del Aviso de Privacidad la primera vez que se accede a la app.
 */

export class PrivacyBanner {
    constructor() {
        this.storageKey = 'consent_lfpdppp';
        this.init();
    }

    init() {
        // Verificar si ya existe el consentimiento en localStorage
        if (localStorage.getItem(this.storageKey) === 'true') {
            return;
        }

        // Si no existe, renderizamos el banner
        this.renderBanner();
    }

    renderBanner() {
        const bannerId = 'privacy-banner-lfpdppp';
        if (document.getElementById(bannerId)) return;

        const banner = document.createElement('div');
        banner.id = bannerId;
        banner.className = 'fixed bottom-0 left-0 w-full bg-[#001105] border-t-2 border-[#00e5ff] p-4 md:p-6 z-[10000] shadow-[0_-5px_20px_rgba(0,255,170,0.2)] flex flex-col md:flex-row items-center justify-between gap-4 font-mono';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'text-[#00e5ff] text-xs md:text-sm tracking-wide text-justify flex-1';
        
        const strong = document.createElement('strong');
        strong.textContent = 'AVISO DE PRIVACIDAD (LFPDPPP):';
        contentDiv.appendChild(strong);
        
        const textNode = document.createTextNode(' Mole.AI recopila y procesa datos telemétricos e imágenes exclusivamente con fines de diagnóstico y monitoreo agrícola. Sus datos están protegidos bajo estándares de cifrado (Zero-Trust) y no serán compartidos con terceros sin consentimiento explícito. Al continuar usando esta plataforma, acepta nuestras políticas de privacidad y manejo de datos.');
        contentDiv.appendChild(textNode);
        
        const btn = document.createElement('button');
        btn.id = 'btn-accept-privacy';
        btn.className = 'border border-[#00e5ff] px-6 py-2 hover:bg-[#00e5ff] hover:text-black font-bold tracking-widest text-sm transition-colors text-[#00e5ff] whitespace-nowrap';
        btn.textContent = '[ ACEPTAR Y CONTINUAR ]';
        
        banner.appendChild(contentDiv);
        banner.appendChild(btn);
        document.body.appendChild(banner);

        document.getElementById('btn-accept-privacy').addEventListener('click', () => {
            this.acceptPrivacy();
        });
    }

    acceptPrivacy() {
        localStorage.setItem(this.storageKey, 'true');
        const banner = document.getElementById('privacy-banner-lfpdppp');
        if (banner) {
            banner.remove();
        }
    }
}

// Inicializar automáticamente al cargar el script
export const privacyBanner = new PrivacyBanner();
