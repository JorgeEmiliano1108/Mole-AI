// ==========================================================
// 9. FLUJO DE MI HUERTO (HISTORIAL Y FAVORITOS) [BACKEND ESTRICTO]
// ==========================================================

// Variable para recordar qué pestaña estamos viendo
let currentTab = 'history'; 

function openHistoryModal() {
    const modal = document.getElementById('history-modal');
    if (modal) modal.classList.remove('hidden');
    // Solicitamos los datos reales al servidor
    fetchAndRenderHuerto(currentTab);
}

function closeHistoryModal() {
    const modal = document.getElementById('history-modal');
    if (modal) modal.classList.add('hidden');
}

function switchHistoryTab(tab) {
    currentTab = tab;
    
    // Estilos visuales de las pestañas
    const btnHist = document.getElementById('tab-history');
    const btnFav = document.getElementById('tab-favorites');
    
    if (tab === 'history') {
        if(btnHist) btnHist.className = "text-[#00ffaa] border-b-2 border-[#00ffaa] px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
        if(btnFav) btnFav.className = "text-[#00ffaa]/40 hover:text-[#00ffaa] border-b-2 border-transparent px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
    } else {
        if(btnFav) btnFav.className = "text-[#f97316] border-b-2 border-[#f97316] px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
        if(btnHist) btnHist.className = "text-[#00ffaa]/40 hover:text-[#00ffaa] border-b-2 border-transparent px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
    }
    
    fetchAndRenderHuerto(tab);
}

/**
 * LECTURA DESDE EL BACKEND (GET) - ESTRICTO
 */
async function fetchAndRenderHuerto(tab) {
    const container = document.getElementById('history-list-container');
    if(!container) return;

    container.innerHTML = `<div class="text-center text-[#00ffaa] animate-pulse mt-10 text-xs tracking-widest">> SINCRONIZANDO CON BASE DE DATOS CENTRAL...</div>`;

    const currentUser = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
    const token = localStorage.getItem('moleia_token');
    let dataToRender = [];

    try {
        if (!token) throw new Error("Acceso denegado: Se requiere Token.");

        // ========================================================
        // 🚀 PETICIÓN AL SERVIDOR (HISTORIAL O FAVORITOS)
        // ========================================================
        const endpoint = tab === 'history' 
            ? `http://localhost:3000/api/usuarios/${currentUser}/historial`
            : `http://localhost:3000/api/usuarios/${currentUser}/favoritos`;

        const response = await fetch(endpoint, {
            method: 'GET',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error("El servidor rechazó la conexión o no hay datos.");
        
        dataToRender = await response.json();

    } catch (error) {
        console.error("> [ ERROR CRÍTICO ] Fallo al obtener base de datos:", error);
        // Mostrar error en pantalla en lugar de usar datos locales
        container.innerHTML = `<div class="text-center text-red-500 mt-10 text-xs font-bold tracking-widest">> ERROR DE RED: NO SE PUDO CONECTAR AL SERVIDOR CENTRAL.</div>`;
        return;
    }

    // 2. RENDERIZADO DE LAS CARDS
    if (!dataToRender || dataToRender.length === 0) {
        container.innerHTML = `<div class="text-center text-white/50 mt-10 text-xs tracking-widest">> NO HAY REGISTROS EN ESTA CATEGORÍA.</div>`;
        return;
    }

    // Arreglo de clases de Tailwind
    const themeClasses = tab === 'history' 
        ? { border: 'border-[#00ffaa]/30', bgHover: 'hover:bg-[#00ffaa]/10', text: 'text-[#00ffaa]' }
        : { border: 'border-[#f97316]/30', bgHover: 'hover:bg-[#f97316]/10', text: 'text-[#f97316]' };

    container.innerHTML = dataToRender.map(item => `
        <div class="border ${themeClasses.border} bg-black p-4 flex flex-col md:flex-row justify-between md:items-center gap-4 ${themeClasses.bgHover} transition-colors">
            <div>
                <span class="text-[10px] text-white/50 border border-white/20 px-1">${item.id || 'N/A'} | ${item.date}</span>
                <h3 class="${themeClasses.text} font-bold mt-1 text-sm md:text-base uppercase">${item.species}</h3>
                <p class="text-xs text-white/80">Estado: <span class="${(item.status && item.status.toLowerCase().includes('óptimo')) ? 'text-[#00ffaa]' : 'text-red-400'}">${item.status}</span> | pH: ${item.ph}</p>
            </div>
            <div class="flex gap-2 shrink-0">
                <button onclick="downloadReportPDF('${item.id}', this)" class="border border-[#00e5ff] text-[#00e5ff] px-3 py-1 text-[10px] uppercase font-bold hover:bg-[#00e5ff] hover:text-black transition-colors">
                    [ PDF ]
                </button>
            </div>
        </div>
    `).join('');
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
    const token = localStorage.getItem('moleia_token');

    // Tomamos los datos de la UI del diagnóstico. El backend deberá asignar el ID real.
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
        // 🚀 ENVIAR FAVORITO AL SERVIDOR
        // ========================================================
        const response = await fetch('http://localhost:3000/api/favoritos/guardar', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(newFavorite)
        });

        if (!response.ok) throw new Error("Rechazado por el servidor");

        btn.innerText = "[ GUARDADO EN FAVORITOS ]";
        btn.classList.remove('animate-pulse', 'border-[#f97316]', 'text-[#f97316]', 'hover:bg-[#f97316]');
        btn.classList.add('border-green-500', 'text-green-500', 'hover:bg-green-500', 'cursor-not-allowed');
        btn.disabled = true; // Evitar multiples clicks
        
    } catch (error) {
        console.error("> [ ERROR CRÍTICO ] Error al guardar favorito:", error);
        btn.innerText = "[ ERROR DE CONEXIÓN ]";
        btn.classList.remove('animate-pulse');
        btn.classList.add('text-red-500', 'border-red-500');
        
        // Permitimos intentar de nuevo tras 2 segundos
        setTimeout(() => {
            btn.innerText = "[ GUARDAR DIAGNÓSTICO ]";
            btn.classList.remove('text-red-500', 'border-red-500');
        }, 2000);
    }
}