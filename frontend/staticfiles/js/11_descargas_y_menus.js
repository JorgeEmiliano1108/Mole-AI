// ==========================================================
// 11. FLUJO DE DESCARGA DE REPORTES Y MENÚS [BACKEND ESTRICTO]
// ==========================================================

async function downloadReportPDF(reportId, btnElement) {
    if (!btnElement) return;

    // 1. Cambiamos el estado del botón a "descargando" y lo bloqueamos
    const originalText = btnElement.innerText;
    btnElement.innerText = "[ DESCARGANDO... ]";
    btnElement.classList.add('animate-pulse', 'bg-[#00e5ff]/20', 'cursor-not-allowed');
    btnElement.disabled = true;

    const currentUser = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
    const token = window.getAuthToken();

    try {
        if (!token) throw new Error("Acceso denegado: Se requiere Token de Autenticación para descargas.");

        // ========================================================
        // 🚀 CONEXIÓN AL BACKEND: Pedir el PDF generado por la IA
        // ========================================================
        const response = await fetch(`http://localhost:3000/api/reportes/descargar/${reportId}?user=${currentUser}`, {
            method: 'GET',
            headers: { 
                'Authorization': `Bearer ${token}` 
            }
        });
        
        if (!response.ok) throw new Error(`El servidor rechazó la solicitud. Código: ${response.status}`);
        
        // Recibimos el archivo binario real (Blob) desde tu servidor
        const blob = await response.blob();

        // 2. MAGIA DE FRONTEND: Crear enlace invisible y forzar descarga
        const url = window.URL.createObjectURL(blob); 
        const a = document.createElement('a');        
        a.style.display = 'none';
        a.href = url;
        a.download = `MOLE_IA_REPORTE_${reportId}.pdf`; 
        
        document.body.appendChild(a);
        a.click(); 
        
        // 3. Limpieza de memoria
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        // Feedback visual de éxito (Se pone verde)
        btnElement.innerText = "[ ÉXITO ]";
        btnElement.classList.replace('text-[#00e5ff]', 'text-[#00e5ff]');
        btnElement.classList.replace('border-[#00e5ff]', 'border-[#00e5ff]');

    } catch (error) {
        console.error("> [ ERROR CRÍTICO ] Fallo en descarga de reporte:", error);
        alert(`[!] ERROR: No se pudo verificar la autorización o establecer conexión para el reporte ${reportId}.`);
        
        // Feedback visual de error (Se pone rojo)
        btnElement.innerText = "[ FALLO ]";
        btnElement.classList.replace('text-[#00e5ff]', 'text-red-500');
        btnElement.classList.replace('border-[#00e5ff]', 'border-red-500');
    } finally {
        // 4. Regresamos el botón a la normalidad después de 2 segundos
        setTimeout(() => {
            btnElement.innerText = originalText;
            btnElement.classList.remove('animate-pulse', 'bg-[#00e5ff]/20', 'cursor-not-allowed');
            
            // Restauramos los colores originales por si cambiaron a verde o rojo
            btnElement.classList.replace('text-[#00e5ff]', 'text-[#00e5ff]');
            btnElement.classList.replace('border-[#00e5ff]', 'border-[#00e5ff]');
            btnElement.classList.replace('text-red-500', 'text-[#00e5ff]');
            btnElement.classList.replace('border-red-500', 'border-[#00e5ff]');
            
            btnElement.disabled = false;
        }, 2000);
    }
}

// ==========================================================
// MENÚ DESPLEGABLE DE CULTIVOS (DROPDOWN)
// ==========================================================
function toggleCultivosMenu() {
    const dropdown = document.getElementById('dropdown-cultivos');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

// Cierra el menú si das clic en cualquier otro lado de la pantalla
window.addEventListener('click', function(e) {
    const dropdown = document.getElementById('dropdown-cultivos');
    
    // Si el menú no existe o ya está oculto, no hacemos nada
    if (!dropdown || dropdown.classList.contains('hidden')) return;

    // ¿El usuario hizo clic en el botón que abre el menú?
    const isClickInsideBtn = e.target.closest('button[data-action="menu:toggle-cultivos"]');
    
    // MEJORA: ¿El usuario hizo clic ADENTRO del menú? (Para que no se cierre mientras lo usa)
    const isClickInsideMenu = e.target.closest('#dropdown-cultivos');
    
    // Si no hizo clic ni en el botón ni dentro del menú, lo cerramos
    if (!isClickInsideBtn && !isClickInsideMenu) {
        dropdown.classList.add('hidden');
    }
});