// ==========================================================
// 9. FLUJO DE MI HUERTO (HISTORIAL Y FAVORITOS) [BACKEND ESTRICTO]
// ==========================================================

// Variable para recordar qu  pesta a estamos viendo
export let currentTab = 'history'; 

export function openHistoryModal() {
    const modal = document.getElementById('history-modal');
    if (modal) modal.classList.remove('hidden');
    // Solicitamos los datos reales al servidor
    fetchAndRenderHuerto(currentTab);
}

export function closeHistoryModal() {
    const modal = document.getElementById('history-modal');
    if (modal) modal.classList.add('hidden');
}

export function switchHistoryTab(tab) {
    currentTab = tab;
    
    // Estilos visuales de las pesta as
    const btnHist = document.getElementById('tab-history');
    const btnFav = document.getElementById('tab-favorites');
    
    if (tab === 'history') {
        if(btnHist) btnHist.className = "text-[#00e5ff] border-b-2 border-[#00e5ff] px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
        if(btnFav) btnFav.className = "text-[#00e5ff]/40 hover:text-[#00e5ff] border-b-2 border-transparent px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
    } else {
        if(btnFav) btnFav.className = "text-[#FBBF24] border-b-2 border-[#FBBF24] px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
        if(btnHist) btnHist.className = "text-[#00e5ff]/40 hover:text-[#00e5ff] border-b-2 border-transparent px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
    }
    
    fetchAndRenderHuerto(tab);
}

/**
 * LECTURA DESDE EL BACKEND (GET) - ESTRICTO
 */
async function fetchAndRenderHuerto(tab) {
    const container = document.getElementById('history-list-container');
    if(!container) return;

    container.textContent = '';
    const syncing = createNode('div', 'text-center text-[#00e5ff] animate-pulse mt-10 text-xs tracking-widest', '> SINCRONIZANDO CON BASE DE DATOS CENTRAL...');
    container.appendChild(syncing);

    const currentUser = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
    const token = window.getAuthToken();
    let dataToRender = [];

    try {
        if (!token) throw new Error("Acceso denegado: Se requiere Token.");

        // ========================================================
        //   PETICI N AL SERVIDOR (HISTORIAL O FAVORITOS)
        // ========================================================
        const endpoint = tab === 'history' 
            ? `${window.AppConfig.API_BASE_URL}/users/${currentUser}/history/`
            : `${window.AppConfig.API_BASE_URL}/users/${currentUser}/favorites/`;

        const response = await fetch(endpoint, {
            method: 'GET',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error("El servidor rechaz\u00f3 la conexi\u00f3n o no hay datos.");
        
        dataToRender = await response.json();

    } catch (error) {
        console.error("> [ ERROR CR\u00cdTICO ] Fallo al obtener base de datos:", error);
        // Mostrar error en pantalla en lugar de usar datos locales
        container.textContent = '';
        const err = createNode('div', 'text-center text-red-500 mt-10 text-xs font-bold tracking-widest', '> ERROR DE RED: NO SE PUDO CONECTAR AL SERVIDOR CENTRAL.');
        container.appendChild(err);
        return;
    }

    // 2. RENDERIZADO DE LAS CARDS
    if (!dataToRender || dataToRender.length === 0) {
        container.textContent = '';
        const none = createNode('div', 'text-center text-white/50 mt-10 text-xs tracking-widest', '> NO HAY REGISTROS EN ESTA CATEGOR\u00cdA.');
        container.appendChild(none);
        return;
    }

    // Arreglo de clases de Tailwind
    const themeClasses = tab === 'history' 
        ? { border: 'border-[#00e5ff]/30', bgHover: 'hover:bg-[#00e5ff]/10', text: 'text-[#00e5ff]' }
        : { border: 'border-[#FBBF24]/30', bgHover: 'hover:bg-[#FBBF24]/10', text: 'text-[#FBBF24]' };

    container.textContent = '';
    dataToRender.forEach(item => {
        const card = createNode('div', `border ${themeClasses.border} bg-black p-4 flex flex-col md:flex-row justify-between md:items-center gap-4 ${themeClasses.bgHover} transition-colors`);

        const left = createNode('div');
        const idSpan = createNode('span', 'text-[10px] text-white/50 border border-white/20 px-1', `${item.id || 'N/A'} | ${item.date}`);
        left.appendChild(idSpan);

        const title = createNode('h3', `${themeClasses.text} font-bold mt-1 text-sm md:text-base uppercase`, item.species || 'Sin nombre');
        left.appendChild(title);

        const statusClass = (item.status && item.status.toLowerCase().includes('\u00f3ptimo')) ? 'text-[#00e5ff]' : 'text-red-400';
        const statusP = createNode('p', 'text-xs text-white/80', `Estado: `);
        const statusSpan = createNode('span', statusClass, item.status || 'Desconocido');
        statusP.appendChild(statusSpan);
        statusP.appendChild(document.createTextNode(` | pH: ${item.ph || 'N/A'}`));
        left.appendChild(statusP);

        const right = createNode('div', 'flex gap-2 shrink-0');
        const btn = createNode('button', 'border border-[#00e5ff] text-[#00e5ff] px-3 py-1 text-[10px] uppercase font-bold hover:bg-[#00e5ff] hover:text-black transition-colors', '[ PDF ]', { 'data-report-id': item.id });
        btn.setAttribute('data-action', 'report:download');
        right.appendChild(btn);

        card.appendChild(left);
        card.appendChild(right);
        container.appendChild(card);
    });
}

// ----------------------------------------------------
// GUARDAR EN FAVORITOS (POST AL BACKEND) - ESTRICTO
// ----------------------------------------------------
async function saveToFavorites(event) {
    const btn = event.target || event.currentTarget;
    if(!btn) return;

    btn.innerText = "[ ENVIANDO... ]";
    btn.classList.add('animate-pulse');

    const currentUser = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
    const token = window.getAuthToken();

    // Tomamos los datos de la UI del diagn stico. El backend deber  asignar el ID real.
    const newFavorite = {
        usuario: currentUser,
        date: new Date().toLocaleDateString('en-GB'),
        species: document.getElementById('diag-species')?.innerText || "Desconocida",
        status: document.getElementById('diag-status')?.innerText || "Desconocido",
        ph: document.getElementById('diag-ph')?.innerText || "N/A"
    };

    try {
        if (!token) throw new Error("Acceso denegado: Se requiere Token.");

        // ========================================================
        //   ENVIAR FAVORITO AL SERVIDOR
        // ========================================================
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/favorites/save/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(newFavorite)
        });

        if (!response.ok) throw new Error("Rechazado por el servidor");

        btn.innerText = "[ GUARDADO EN FAVORITOS ]";
        btn.classList.remove('animate-pulse', 'border-[#FBBF24]', 'text-[#FBBF24]', 'hover:bg-[#FBBF24]');
        btn.classList.add('border-green-500', 'text-green-500', 'hover:bg-green-500', 'cursor-not-allowed');
        btn.disabled = true; // Evitar multiples clicks
        
    } catch (error) {
        console.error("> [ ERROR CR\u00cdTICO ] Error al guardar favorito:", error);
        btn.innerText = "[ ERROR DE CONEXI\u00d3N ]";
        btn.classList.remove('animate-pulse');
        btn.classList.add('text-red-500', 'border-red-500');
        
        // Permitimos intentar de nuevo tras 2 segundos
        setTimeout(() => {
            btn.innerText = "[ GUARDAR DIAGN\u00d3STICO ]";
            btn.classList.remove('text-red-500', 'border-red-500');
        }, 2000);
    }
}