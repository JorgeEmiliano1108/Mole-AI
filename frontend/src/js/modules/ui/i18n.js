// ==========================================================
// 15. M DULO I18N: TRADUCCI N DIN MICA [BACKEND ESTRICTO]
// ==========================================================

import { getAuthToken } from '../api/config.js';

// Use centralized AppConfig for API base URL (see static/js/config.js)
// Avoid redeclaring API_BASE_URL in multiple modules.
// Access via: window.AppConfig.API_BASE_URL

// Memoria vol til para no descargar el mismo idioma dos veces en la misma sesi n (ahorra red)
export let loadedTranslations = {};

// 1. INICIALIZACI N AL CARGAR EL DOM
document.addEventListener("DOMContentLoaded", () => {
    initLanguageProtocol();
});

async function initLanguageProtocol() {
    // Revisamos si el usuario ya ten a un idioma asignado localmente
    let savedLang = localStorage.getItem('moleia_system_lang');

    if (!savedLang) {
        // Detectamos la firma de idioma de su navegador
        const browserLang = navigator.language || navigator.userLanguage;
        savedLang = browserLang.split('-')[0]; // Extrae 'es' de 'es-MX'
    }

    // Iniciamos la descarga y aplicaci n del idioma desde el servidor
    await applyLanguage(savedLang);
}

// 2. MOTOR DE DESCARGA Y TRADUCCI N (100% DEPENDIENTE DEL BACKEND)
async function applyLanguage(lang) {
    console.log(`> Solicitando paquete de idioma [${lang.toUpperCase()}] al servidor central...`);

    // Si no tenemos el idioma en la memoria temporal, lo descargamos del Backend
    if (!loadedTranslations[lang]) {
        try {
            // Petici n GET al servidor para traer el diccionario JSON de ese idioma
            // Vite serves static/ files from root, so use /lang/
            const response = await fetch(`/lang/${lang}.json`);
            
            if (!response.ok) throw new Error(`El servidor no encontr\u00f3 el idioma: ${lang}`);
            
            // Guardamos el diccionario descargado en la memoria RAM
            loadedTranslations[lang] = await response.json();
            console.log(`> [ OK ] Paquete [${lang.toUpperCase()}] descargado con \u00e9xito.`);

        } catch (error) {
            console.error("> [ ERROR CR\u00cdTICO ] Fallo al descargar idioma desde el backend:", error);
            
            // Si el backend falla y no hay nada en memoria, abortamos la traducci n
            if (!loadedTranslations['es']) {
                console.warn("> La interfaz quedar\u00e1 con los textos por defecto del HTML.");
                return;
            } else {
                // Fallback al espa ol si ya estaba descargado
                lang = 'es'; 
            }
        }
    }

    const dict = loadedTranslations[lang];
    
    // Guardamos la configuraci n activa
    localStorage.setItem('moleia_system_lang', lang);

    // Escaneamos el DOM buscando nodos con la etiqueta data-i18n
    const elementsToTranslate = document.querySelectorAll('[data-i18n]');
    
    elementsToTranslate.forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            // Efecto visual de transici n (Glitch/Fade)
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

// 3. CAMBIO MANUAL Y SINCRONIZACI N ESTRICTA CON BACKEND
async function switchLanguage(newLang) {
    // 1. Descargamos y aplicamos el nuevo idioma desde la base de datos
    await applyLanguage(newLang);

    // 2. Sincronizamos con el servidor para que se guarde en el perfil del Operador
    const currentUser = localStorage.getItem('moleia_current_user');
    const token = getAuthToken();

    if (currentUser && token) {
        try {
            console.log("> Sincronizando preferencia de idioma con el perfil central...");
            const response = await fetch(`${window.AppConfig.API_BASE_URL}/users/preferences`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify({
                    usuario: currentUser,
                    idioma: newLang
                })
            });
            
            if (!response.ok) throw new Error("Rechazado por el servidor.");
            
            console.log("> [ OK ] Preferencia de idioma sincronizada con el servidor central.");
        } catch (error) {
            console.error("> [ ERROR CR\u00cdTICO ] No se pudo guardar el idioma en el perfil del Operador:", error);
        }
    }
}   