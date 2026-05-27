// ==========================================================
// 11. FLUJO DE DESCARGA DE REPORTES Y MEN S [BACKEND ESTRICTO]
// ==========================================================

export async function downloadReportPDF(reportId, btnElement) {
    if (!btnElement) return;

    // 1. Cambiamos el estado del bot n a "descargando" y lo bloqueamos
    const originalText = btnElement.innerText;
    btnElement.innerText = "[ DESCARGANDO... ]";
    btnElement.classList.add('animate-pulse', 'bg-[#00e5ff]/20', 'cursor-not-allowed');
    btnElement.disabled = true;

    const currentUser = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
    const token = window.getAuthToken();

    try {
        if (!token) throw new Error("Acceso denegado: Se requiere Token de Autenticaci\u00f3n para descargas.");

        // ========================================================
        //   CONEXI N AL BACKEND: Pedir el PDF generado por la IA
        // ========================================================
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/diagnostics/${reportId}/download/`, {
            method: 'GET',
            headers: { 
                'Authorization': `Bearer ${token}` 
            }
        });
        
        if (!response.ok) throw new Error(`El servidor rechaz\u00f3 la solicitud. C\u00f3digo: ${response.status}`);
        
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

        // Feedback visual de  xito (Se pone verde)
        btnElement.innerText = "[ \u00c9XITO ]";
        btnElement.classList.replace('text-[#00e5ff]', 'text-[#00e5ff]');
        btnElement.classList.replace('border-[#00e5ff]', 'border-[#00e5ff]');

    } catch (error) {
        console.error("> [ ERROR CR\u00cdTICO ] Fallo en descarga de reporte:", error);
        alert(`[!] ERROR: No se pudo verificar la autorizaci\u00f3n o establecer conexi\u00f3n para el reporte ${reportId}.`);
        
        // Feedback visual de error (Se pone rojo)
        btnElement.innerText = "[ FALLO ]";
        btnElement.classList.replace('text-[#00e5ff]', 'text-red-500');
        btnElement.classList.replace('border-[#00e5ff]', 'border-red-500');
    } finally {
        // 4. Regresamos el bot n a la normalidad despu s de 2 segundos
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
// MEN  DESPLEGABLE DE CULTIVOS (DROPDOWN)
// ==========================================================
export function toggleCultivosMenu() {
    const dropdown = document.getElementById('dropdown-cultivos');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

// Cierra el men  si das clic en cualquier otro lado de la pantalla
window.addEventListener('click', function(e) {
    const dropdown = document.getElementById('dropdown-cultivos');
    
    // Si el men  no existe o ya est  oculto, no hacemos nada
    if (!dropdown || dropdown.classList.contains('hidden')) return;

    //  El usuario hizo clic en el bot n que abre el men ?
    const isClickInsideBtn = e.target.closest('button[data-action="menu:toggle-cultivos"]');
    
    // MEJORA:  El usuario hizo clic ADENTRO del men ? (Para que no se cierre mientras lo usa)
    const isClickInsideMenu = e.target.closest('#dropdown-cultivos');
    
    // Si no hizo clic ni en el bot n ni dentro del men , lo cerramos
    if (!isClickInsideBtn && !isClickInsideMenu) {
        dropdown.classList.add('hidden');
    }
});