/**
 * Cache Buster para Directiva Agrícola
 * Evita problemas de cache en navegadores
 */

(function() {
    'use strict';
    
    // Función para agregar timestamp a URLs
    function addTimestampToUrl(url) {
        const separator = url.includes('?') ? '&' : '?';
        return `${url}${separator}_t=${Date.now()}`;
    }
    
    // Función para forzar recarga de recursos
    function forceReloadResource(selector, attribute) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            if (element[attribute]) {
                element[attribute] = addTimestampToUrl(element[attribute]);
            }
        });
    }
    
    // Función para limpiar cache del navegador
    function clearBrowserCache() {
        // Claves a preservar en localStorage
        const PRESERVE_KEYS = ['loginRFC'];
        let preserved = {};
        
        // Limpiar cache de localStorage preservando claves necesarias
        if (typeof(Storage) !== "undefined") {
            try {
                PRESERVE_KEYS.forEach(k => {
                    const val = localStorage.getItem(k);
                    if (val !== null) preserved[k] = val;
                });
                localStorage.clear();
                Object.keys(preserved).forEach(k => localStorage.setItem(k, preserved[k]));
            } catch (e) {
                // ignorar errores de almacenamiento
            }
        }
        
        // Limpiar cache de sessionStorage (no preservamos nada allí)
        if (typeof(Storage) !== "undefined") {
            try { sessionStorage.clear(); } catch (e) {}
        }
        
        // Limpiar cache de IndexedDB si está disponible
        if ('indexedDB' in window) {
            try {
                indexedDB.databases().then(databases => {
                    databases.forEach(db => {
                        indexedDB.deleteDatabase(db.name);
                    });
                }).catch(function(){ /* noop */ });
            } catch (e) { /* noop */ }
        }
    }
    
    // Función para manejar formularios y evitar cache
    function handleFormSubmission() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                // Agregar timestamp al formulario
                const timestamp = document.createElement('input');
                timestamp.type = 'hidden';
                timestamp.name = '_timestamp';
                timestamp.value = Date.now();
                form.appendChild(timestamp);
                
                // Limpiar cache antes del envío
                clearBrowserCache();
            });
        });
    }
    
    // Función para manejar enlaces y evitar cache
    function handleLinks() {
        // Deshabilitado temporalmente para evitar problemas de navegación
        // const links = document.querySelectorAll('a[href]');
        // links.forEach(link => {
        //     // Solo para enlaces internos
        //     if (link.href.includes(window.location.hostname)) {
        //         link.addEventListener('click', function(e) {
        //             // Solo agregar timestamp si no tiene uno ya
        //             if (!this.href.includes('_t=')) {
        //                 const originalHref = this.href;
        //                 this.href = addTimestampToUrl(originalHref);
        //             }
        //         });
        //     }
        // });
    }
    
    // Función para verificar y actualizar recursos
    function updateResources() {
        // Actualizar imágenes
        forceReloadResource('img[src]', 'src');
        
        // Actualizar CSS
        forceReloadResource('link[rel="stylesheet"]', 'href');
        
        // Actualizar JavaScript
        forceReloadResource('script[src]', 'src');
    }
    
    // Función para detectar cambios en el servidor
    function checkForUpdates() {
        const lastCheck = localStorage.getItem('lastUpdateCheck');
        const now = Date.now();
        
        // Verificar cada 5 minutos
        if (!lastCheck || (now - parseInt(lastCheck)) > 300000) {
            fetch('/api/version/?_t=' + now)
                .then(response => response.json())
                .then(data => {
                    const currentVersion = localStorage.getItem('appVersion');
                    if (currentVersion && currentVersion !== data.version) {
                        // Nueva versión disponible, recargar página
                        window.location.reload(true);
                    }
                    localStorage.setItem('appVersion', data.version);
                    localStorage.setItem('lastUpdateCheck', now.toString());
                })
                .catch(() => {
                    // Si no hay API de versión, solo actualizar timestamp
                    localStorage.setItem('lastUpdateCheck', now.toString());
                });
        }
    }
    
    // Función para manejar el evento beforeunload
    function handleBeforeUnload() {
        window.addEventListener('beforeunload', function() {
            // Limpiar cache al salir preservando claves whitelisted
            clearBrowserCache();
        });
    }
    
    // Función para manejar el evento online/offline
    function handleConnectionStatus() {
        window.addEventListener('online', function() {
            // Cuando se reconecta, verificar actualizaciones
            checkForUpdates();
        });
    }
    
    // Inicializar cuando el DOM esté listo
    function init() {
        // Manejar formularios
        handleFormSubmission();
        
        // Manejar enlaces - DESHABILITADO para evitar problemas de navegación
        // handleLinks();
        
        // Verificar actualizaciones
        checkForUpdates();
        
        // Manejar eventos del navegador
        handleBeforeUnload();
        handleConnectionStatus();
        
        // Actualizar recursos si es necesario
        if (localStorage.getItem('forceReload') === 'true') {
            updateResources();
            localStorage.removeItem('forceReload');
        }
        
        console.log('Cache Buster inicializado correctamente');
    }
    
    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Exponer funciones globalmente para uso manual
    window.CacheBuster = {
        clearCache: clearBrowserCache,
        updateResources: updateResources,
        addTimestamp: addTimestampToUrl,
        forceReload: function() {
            localStorage.setItem('forceReload', 'true');
            window.location.reload(true);
        }
    };
    
})();

