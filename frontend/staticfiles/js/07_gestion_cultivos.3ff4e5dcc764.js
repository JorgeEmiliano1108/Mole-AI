// ==========================================================
// 7. FUNCIONES PARA NUEVOS USUARIOS Y MODAL DE CULTIVOS [BACKEND ESTRICTO]
// ==========================================================

/**
 * ESTADO VACÍO: Limpia el dashboard para usuarios sin cultivos.
 */
function setEmptyDashboardState() {
    // Ponemos los sensores en espera
    document.getElementById('txt-hum').innerText = '--%';
    document.getElementById('txt-temp').innerText = '--°C';
    document.getElementById('txt-ph').innerText = '--';
    document.getElementById('txt-uv').innerText = 'N/A';
    
    // Alerta de sin señal en el tag superior
    const plantTag = document.getElementById('plant-tag');
    if (plantTag) {
        plantTag.innerText = 'SIN SEÑAL';
        plantTag.classList.add('text-red-500', 'animate-pulse');
        plantTag.classList.remove('text-[#00ffaa]');
    }
    
    // Deshabilitar botón de análisis
    const btnAnalysis = document.getElementById('btn-analysis');
    if(btnAnalysis) {
        btnAnalysis.innerText = 'ESPERANDO DATOS...';
        btnAnalysis.disabled = true;
        btnAnalysis.classList.add('opacity-50', 'cursor-not-allowed');
    }
    
    // Manejo visual de la cámara (Imagen vs No Señal)
    const mainImgContainer = document.getElementById('main-img');
    if (mainImgContainer) {
        const parentContainer = mainImgContainer.parentElement;
        mainImgContainer.style.display = 'none';
        
        let noSignal = document.getElementById('no-signal-container');
        if (!noSignal) {
            noSignal = document.createElement('div');
            noSignal.id = 'no-signal-container';
            noSignal.className = "text-[#00ffaa] opacity-50 flex flex-col items-center justify-center w-full h-full min-h-[250px] border border-dashed border-[#00ffaa]/30";
            noSignal.innerHTML = `
                <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
                <p class="text-xs tracking-widest text-center">> VINCULE UN CULTIVO <br> PARA INICIAR MONITOREO</p>
            `;
            parentContainer.appendChild(noSignal);
        } else {
            noSignal.style.display = 'flex';
        }
    }
}

function openAddPlantModal() {
    const modal = document.getElementById('add-plant-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeAddPlantModal() {
    const modal = document.getElementById('add-plant-modal');
    if (modal) modal.classList.add('hidden');
    // Limpiar campos al cerrar
    document.getElementById('new-plant-name').value = '';
    document.getElementById('new-plant-type').value = '';
}

/**
 * REGISTRO: Envía el nuevo cultivo al backend estrictamente.
 */
async function registerNewPlant() {
    const plantNameInput = document.getElementById('new-plant-name');
    const plantTypeInput = document.getElementById('new-plant-type');
    
    const plantName = plantNameInput ? plantNameInput.value.trim() : '';
    const plantType = plantTypeInput ? plantTypeInput.value.trim() : '';
    const currentUser = localStorage.getItem('moleia_current_user');

    if(!plantName) {
        alert("ERROR: El espécimen requiere un identificador.");
        return;
    }

    const safePlantName = plantName.toLowerCase();
    console.log(`> Iniciando secuencia de registro en servidor para: ${safePlantName}...`);

    const newPlantData = {
        usuario: currentUser,
        nombre: safePlantName,
        tipo: plantType,
        timestamp: Date.now()
    };

    try {
        const token = window.getAuthToken();
        const response = await fetch('http://TU-BACKEND-REAL.com/api/plantas/registro', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(newPlantData)
        });

        if (response.ok) {
            console.log(`> [ OK ] ${safePlantName.toUpperCase()} añadido a la base de datos central.`);
            closeAddPlantModal();
            
            // Forzamos la sincronización con el backend para descargar el inventario actualizado
            if (typeof syncUserPlants === 'function') {
                await syncUserPlants();
            }
            
            // Recargamos o actualizamos la interfaz con los datos que mandó el servidor
            if (typeof updatePlant === 'function') {
                updatePlant(safePlantName);
            } else {
                location.reload(); 
            }
        } else {
            throw new Error("El servidor rechazó el nuevo espécimen. Código de error: " + response.status);
        }
    } catch (error) {
        console.error("> [ ERROR CRÍTICO ] Fallo de comunicación con el backend:", error);
        alert("ERROR: No se pudo conectar con el servidor central. El registro fue abortado.");
    }
}

/**
 * PARCHE DE ACTUALIZACIÓN: Restaura la UI cuando hay datos.
 */
const originalUpdatePlant = typeof updatePlant !== 'undefined' ? updatePlant : () => {};

updatePlant = function(name) {
    const mainImg = document.getElementById('main-img');
    const noSignal = document.getElementById('no-signal-container');
    
    if (mainImg) mainImg.style.display = 'block';
    if (noSignal) noSignal.style.display = 'none';
    
    const btnAnalysis = document.getElementById('btn-analysis');
    if(btnAnalysis) {
        btnAnalysis.innerText = '[ ANÁLISIS DETALLADO ]';
        btnAnalysis.disabled = false;
        btnAnalysis.classList.remove('opacity-50', 'cursor-not-allowed');
    }

    const plantTag = document.getElementById('plant-tag');
    if (plantTag) {
        plantTag.classList.remove('text-red-500', 'animate-pulse');
        plantTag.classList.add('text-[#00ffaa]');
    }

    // Ejecutamos la lógica original
    originalUpdatePlant(name);
};