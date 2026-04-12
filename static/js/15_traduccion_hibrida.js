// ==========================================================
// 15. MÓDULO I18N: TRADUCCIÓN DINÁMICA [BACKEND ESTRICTO]
// ==========================================================

var API_BASE_URL = window.API_BASE_URL || 'https://tu-backend-real.com';

// Memoria volátil para no descargar el mismo idioma dos veces en la misma sesión (ahorra red)
let loadedTranslations = {};

// 1. INICIALIZACIÓN AL CARGAR EL DOM
document.addEventListener("DOMContentLoaded", () => {
    initLanguageProtocol();
});

async function initLanguageProtocol() {
    // Revisamos si el usuario ya tenía un idioma asignado localmente
    let savedLang = localStorage.getItem('moleia_system_lang');

    if (!savedLang) {
        // Detectamos la firma de idioma de su navegador
        const browserLang = navigator.language || navigator.userLanguage;
        savedLang = browserLang.split('-')[0]; // Extrae 'es' de 'es-MX'
    }

    // Iniciamos la descarga y aplicación del idioma desde el servidor
    await applyLanguage(savedLang);
}

// 2. MOTOR DE DESCARGA Y TRADUCCIÓN (100% DEPENDIENTE DEL BACKEND)
async function applyLanguage(lang) {
    console.log(`> Solicitando paquete de idioma [${lang.toUpperCase()}] al servidor central...`);

    // Si no tenemos el idioma en la memoria temporal, lo descargamos del Backend
    if (!loadedTranslations[lang]) {
        try {
            // Petición GET al servidor para traer el diccionario JSON de ese idioma
            const response = await fetch(`${API_BASE_URL}/api/i18n/paquete/${lang}`);
            
            if (!response.ok) throw new Error(`El servidor no encontró el idioma: ${lang}`);
            
            // Guardamos el diccionario descargado en la memoria RAM
            loadedTranslations[lang] = await response.json();
            console.log(`> [ OK ] Paquete [${lang.toUpperCase()}] descargado con éxito.`);

        } catch (error) {
            console.error("> [ ERROR CRÍTICO ] Fallo al descargar idioma desde el backend:", error);
            
            // Si el backend falla y no hay nada en memoria, abortamos la traducción
            if (!loadedTranslations['es']) {
                console.warn("> La interfaz quedará con los textos por defecto del HTML.");
                return;
            } else {
                // Fallback al español si ya estaba descargado
                lang = 'es'; 
            }
        }
    }

    const dict = loadedTranslations[lang];
    
    // Guardamos la configuración activa
    localStorage.setItem('moleia_system_lang', lang);

    // Escaneamos el DOM buscando nodos con la etiqueta data-i18n
    const elementsToTranslate = document.querySelectorAll('[data-i18n]');
    
    elementsToTranslate.forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            // Efecto visual de transición (Glitch/Fade)
            el.style.transition = "opacity 0.15s ease-in-out";
            el.style.opacity = 0;
            
            setTimeout(() => {
                el.innerText = dict[key];
                el.style.opacity = 1;
            }, 150);
        }
    });

    // Actualizamos el display del selector de idioma (si existe en la UI)
    const langSelector = document.getElementById('current-lang-display');
    if (langSelector) langSelector.innerText = lang.toUpperCase();
}

// 3. CAMBIO MANUAL Y SINCRONIZACIÓN ESTRICTA CON BACKEND
async function switchLanguage(newLang) {
    // 1. Descargamos y aplicamos el nuevo idioma desde la base de datos
    await applyLanguage(newLang);

    // 2. Sincronizamos con el servidor para que se guarde en el perfil del Operador
    const currentUser = localStorage.getItem('moleia_current_user');
    const token = localStorage.getItem('moleia_token');

    if (currentUser && token) {
        try {
            console.log("> Sincronizando preferencia de idioma con el perfil central...");
            const response = await fetch(`${API_BASE_URL}/api/usuarios/preferencias`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    usuario: currentUser,
                    idioma: newLang
                })
            });
            
            if (!response.ok) throw new Error("Rechazado por el servidor.");
            
            console.log("> [ OK ] Preferencia de idioma sincronizada con el servidor central.");
        } catch (error) {
            console.error("> [ ERROR CRÍTICO ] No se pudo guardar el idioma en el perfil del Operador:", error);
        }
    }
}   