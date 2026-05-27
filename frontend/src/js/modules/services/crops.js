// ==========================================================
// 7. FUNCIONES PARA NUEVOS USUARIOS Y MODAL DE CULTIVOS [BACKEND ESTRICTO]
// ==========================================================

/**
 * ESTADO VAC O: Limpia el dashboard para usuarios sin cultivos.
 */
export function setEmptyDashboardState() {
    // Ponemos los sensores en espera
    document.getElementById('txt-hum').innerText = '--%';
    document.getElementById('txt-temp').innerText = '--\u00b0C';
    document.getElementById('txt-ph').innerText = '--';
    document.getElementById('txt-uv').innerText = 'N/A';
    
    // Alerta de sin se al en el tag superior
    const plantTag = document.getElementById('plant-tag');
    if (plantTag) {
        plantTag.innerText = 'SIN SE\u00d1AL';
        plantTag.classList.add('text-red-500', 'animate-pulse');
        plantTag.classList.remove('text-[#00e5ff]');
    }
    
    // Deshabilitar bot n de an lisis
    const btnAnalysis = document.getElementById('btn-analysis');
    if(btnAnalysis) {
        btnAnalysis.innerText = 'ESPERANDO DATOS...';
        btnAnalysis.disabled = true;
        btnAnalysis.classList.add('opacity-50', 'cursor-not-allowed');
    }
    
    // Manejo visual de la c mara (Imagen vs No Se al)
    const mainImgContainer = document.getElementById('main-img');
    if (mainImgContainer) {
        const parentContainer = mainImgContainer.parentElement;
        mainImgContainer.style.display = 'none';
        
        let noSignal = document.getElementById('no-signal-container');
        if (!noSignal) {
            noSignal = document.createElement('div');
            noSignal.id = 'no-signal-container';
            noSignal.className = "text-[#00e5ff] opacity-50 flex flex-col items-center justify-center w-full h-full min-h-[250px] border border-dashed border-[#00e5ff]/30";
            const svgNS = "http://www.w3.org/2000/svg";
            const svg = document.createElementNS(svgNS, "svg");
            svg.setAttribute("class", "w-16 h-16 mx-auto mb-4");
            svg.setAttribute("fill", "none");
            svg.setAttribute("stroke", "currentColor");
            svg.setAttribute("viewBox", "0 0 24 24");
            const path = document.createElementNS(svgNS, "path");
            path.setAttribute("stroke-linecap", "round");
            path.setAttribute("stroke-linejoin", "round");
            path.setAttribute("stroke-width", "1");
            path.setAttribute("d", "M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z");
            svg.appendChild(path);
            
            const p = document.createElement('p');
            p.className = "text-xs tracking-widest text-center";
            p.appendChild(document.createTextNode("> VINCULE UN CULTIVO "));
            p.appendChild(document.createElement("br"));
            p.appendChild(document.createTextNode(" PARA INICIAR MONITOREO"));
            
            noSignal.appendChild(svg);
            noSignal.appendChild(p);
            parentContainer.appendChild(noSignal);
        } else {
            noSignal.style.display = 'flex';
        }
    }
}

export function openAddPlantModal() {
    const modal = document.getElementById('add-plant-modal');
    if (modal) modal.classList.remove('hidden');
}

export function closeAddPlantModal() {
    const modal = document.getElementById('add-plant-modal');
    if (modal) modal.classList.add('hidden');
    // Limpiar campos al cerrar
    document.getElementById('new-plant-name').value = '';
    document.getElementById('new-plant-type').value = '';
}

/**
 * REGISTRO: Env a el nuevo cultivo al backend estrictamente.
 */
async function registerNewPlant() {
    const plantNameInput = document.getElementById('new-plant-name');
    const plantTypeInput = document.getElementById('new-plant-type');
    
    const plantName = plantNameInput ? plantNameInput.value.trim() : '';
    const plantType = plantTypeInput ? plantTypeInput.value.trim() : '';
    const currentUser = localStorage.getItem('moleia_current_user');

    if(!plantName) {
        alert("ERROR: El esp\u00e9cimen requiere un identificador.");
        return;
    }

    const safePlantName = plantName.toLowerCase();
    console.log(`> Iniciando secuencia de registro en servidor para: ${safePlantName}...`);

    const newPlantData = {
        nickname: safePlantName,
        species_id: null // To be linked later via UI
    };

    try {
        const token = window.getAuthToken();
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/user-plants/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(newPlantData)
        });

        if (response.ok) {
            console.log(`> [ OK ] ${safePlantName.toUpperCase()} a\u00f1adido a la base de datos central.`);
            closeAddPlantModal();
            
            // Forzamos la sincronizaci n con el backend para descargar el inventario actualizado
            if (typeof syncUserPlants === 'function') {
                await syncUserPlants();
            }
            
            // Recargamos o actualizamos la interfaz con los datos que mand  el servidor
            if (typeof updatePlant === 'function') {
                updatePlant(safePlantName);
            } else {
                location.reload(); 
            }
        } else {
            throw new Error("El servidor rechaz\u00f3 el nuevo esp\u00e9cimen. C\u00f3digo de error: " + response.status);
        }
    } catch (error) {
        console.error("> [ ERROR CR\u00cdTICO ] Fallo de comunicaci\u00f3n con el backend:", error);
        alert("ERROR: No se pudo conectar con el servidor central. El registro fue abortado.");
    }
}

/**
 * PARCHE DE ACTUALIZACI N: Restaura la UI cuando hay datos.
 */
export const originalUpdatePlant = typeof updatePlant !== 'undefined' ? updatePlant : () => {};

/**
 * Actualiza la vista de la planta seleccionada
 * Exportada para estar disponible en window.updatePlant
 */
export function updatePlant(name) {
    const mainImg = document.getElementById('main-img');
    const noSignal = document.getElementById('no-signal-container');
    
    if (mainImg) mainImg.style.display = 'block';
    if (noSignal) noSignal.style.display = 'none';
    
    const btnAnalysis = document.getElementById('btn-analysis');
    if(btnAnalysis) {
        btnAnalysis.innerText = '[ AN\u00c1LISIS DETALLADO ]';
        btnAnalysis.disabled = false;
        btnAnalysis.classList.remove('opacity-50', 'cursor-not-allowed');
    }

    const plantTag = document.getElementById('plant-tag');
    if (plantTag) {
        plantTag.classList.remove('text-red-500', 'animate-pulse');
        plantTag.classList.add('text-[#00e5ff]');
    }

    // Ejecutamos la l gica original
    originalUpdatePlant(name);
}