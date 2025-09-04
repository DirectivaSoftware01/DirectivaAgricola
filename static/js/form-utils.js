// Utilidades para manejo de formularios - Directiva Agrícola
// Este archivo contiene funciones reutilizables para formularios

/**
 * Configuración global para formularios
 */
const FormConfig = {
    // Selectores seguros que no interfieren con formularios
    loadingButtonSelector: '.btn[data-loading="true"]:not([type="submit"])',
    
    // Mensajes por defecto
    messages: {
        processing: 'Procesando...',
        saving: 'Guardando...',
        loading: 'Cargando...',
        updating: 'Actualizando...'
    },
    
    // Configuración de timeouts
    timeouts: {
        validation: 500,
        loading: 2000
    }
};

/**
 * Clase para manejar formularios de forma segura
 */
class FormHandler {
    constructor(form) {
        this.form = form;
        this.submitButton = form.querySelector('button[type="submit"]');
        this.originalButtonText = this.submitButton ? this.submitButton.innerHTML : '';
        this.isSubmitting = false;
        
        this.init();
    }
    
    init() {
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
    }
    
    handleSubmit(e) {
        if (this.isSubmitting) {
            e.preventDefault();
            return false;
        }
        
        // Validar formulario antes del envío
        if (!this.validateForm()) {
            e.preventDefault();
            return false;
        }
        
        // Mostrar estado de carga
        this.showLoading();
        
        // Marcar como enviándose
        this.isSubmitting = true;
        
        // Re-habilitar si hay errores después del envío
        this.setupErrorRecovery();
    }
    
    validateForm() {
        const requiredFields = this.form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, 'Este campo es requerido');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });
        
        return isValid;
    }
    
    showLoading(message = null) {
        if (!this.submitButton) return;
        
        this.submitButton.disabled = true;
        this.submitButton.classList.add('loading');
        
        const loadingMessage = message || this.getLoadingMessage();
        this.submitButton.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            ${loadingMessage}
        `;
    }
    
    hideLoading() {
        if (!this.submitButton) return;
        
        this.submitButton.disabled = false;
        this.submitButton.classList.remove('loading');
        this.submitButton.innerHTML = this.originalButtonText;
        this.isSubmitting = false;
    }
    
    getLoadingMessage() {
        const buttonText = this.originalButtonText.toLowerCase();
        
        if (buttonText.includes('crear')) return FormConfig.messages.saving;
        if (buttonText.includes('actualizar')) return FormConfig.messages.updating;
        if (buttonText.includes('guardar')) return FormConfig.messages.saving;
        
        return FormConfig.messages.processing;
    }
    
    showFieldError(field, message) {
        // Remover errores anteriores
        this.clearFieldError(field);
        
        // Agregar clase de error
        field.classList.add('is-invalid');
        
        // Crear elemento de error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        // Insertar después del campo
        field.parentNode.insertBefore(errorDiv, field.nextSibling);
    }
    
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
    
    setupErrorRecovery() {
        // Si después de un tiempo hay errores visibles, rehabilitar el botón
        setTimeout(() => {
            if (this.form.querySelector('.alert-danger, .invalid-feedback')) {
                this.hideLoading();
            }
        }, FormConfig.timeouts.validation);
    }
}

/**
 * Función para inicializar todos los formularios en la página
 */
function initializeForms() {
    const forms = document.querySelectorAll('form');
    const formHandlers = [];
    
    forms.forEach(form => {
        // Solo inicializar formularios que no tengan el atributo data-no-auto-handle
        if (!form.hasAttribute('data-no-auto-handle')) {
            formHandlers.push(new FormHandler(form));
        }
    });
    
    return formHandlers;
}

/**
 * Función para manejar botones con loading manual
 */
function initializeLoadingButtons() {
    const loadingButtons = document.querySelectorAll(FormConfig.loadingButtonSelector);
    
    loadingButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                const originalText = this.innerHTML;
                
                this.disabled = true;
                this.classList.add('loading');
                this.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                    ${FormConfig.messages.loading}
                `;
                
                // Auto-restaurar después del timeout configurado
                setTimeout(() => {
                    this.disabled = false;
                    this.classList.remove('loading');
                    this.innerHTML = originalText;
                }, FormConfig.timeouts.loading);
            }
        });
    });
}

/**
 * Función para validar un formulario específico
 */
function validateForm(form) {
    const handler = new FormHandler(form);
    return handler.validateForm();
}

/**
 * Función para mostrar/ocultar loading en un botón específico
 */
function toggleButtonLoading(button, show = true, message = null) {
    if (show) {
        const originalText = button.getAttribute('data-original-text') || button.innerHTML;
        button.setAttribute('data-original-text', originalText);
        
        button.disabled = true;
        button.classList.add('loading');
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            ${message || FormConfig.messages.processing}
        `;
    } else {
        const originalText = button.getAttribute('data-original-text') || 'Procesar';
        
        button.disabled = false;
        button.classList.remove('loading');
        button.innerHTML = originalText;
        button.removeAttribute('data-original-text');
    }
}

// Exportar para uso global
window.FormUtils = {
    FormHandler,
    initializeForms,
    initializeLoadingButtons,
    validateForm,
    toggleButtonLoading,
    FormConfig
};

// Auto-inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeForms();
    initializeLoadingButtons();
});
