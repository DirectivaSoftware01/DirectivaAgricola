// JavaScript personalizado para Directiva Agrícola

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar popovers de Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Función para manejar la navegación del sidebar
    function initializeSidebar() {
        const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
        const accordionButtons = document.querySelectorAll('.sidebar .accordion-button');
        
        // Agregar eventos a los enlaces del sidebar
        sidebarLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                
                // Solo prevenir el comportamiento por defecto si el enlace es un hash (#) o está vacío
                if (href === '#' || href === '' || href === null) {
                    e.preventDefault();
                    showNotification('Navegando a: ' + this.textContent.trim());
                }
                
                // Remover clase activa de todos los enlaces
                sidebarLinks.forEach(l => l.classList.remove('active'));
                
                // Agregar clase activa al enlace clickeado
                this.classList.add('active');
                
                // Si es un enlace válido, permitir la navegación normal
                if (href && href !== '#' && href !== '') {
                    // La navegación se realizará normalmente
                    console.log('Navegando a:', href);
                }
            });
        });

        // Agregar eventos a los botones del accordion
        accordionButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Agregar efecto de ripple
                createRippleEffect(this, event);
            });
        });
    }

    // Función para crear efecto de ripple
    function createRippleEffect(element, event) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        element.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    // Función para mostrar notificaciones
    function showNotification(message, type = 'info', centered = false) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        
        // Detectar si es el popup de bienvenida
        const isWelcomeMessage = message.includes('Bienvenido a Directiva Agrícola');
        
        if (centered) {
            // Popup centrado en la pantalla
            notification.className += ' welcome-popup';
            notification.style.cssText = `
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 9999;
                min-width: 400px;
                max-width: 90vw;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                border: none;
                border-radius: 10px;
            `;
            notification.innerHTML = `
                <div class="d-flex align-items-center justify-content-center">
                    <i class="bi bi-check-circle-fill me-2" style="font-size: 1.5rem;"></i>
                    <span style="font-size: 1.1rem; font-weight: 500;">${message}</span>
                </div>
            `;
        } else {
            // Notificación normal en esquina inferior izquierda
            notification.className += ' notification-bottom-left';
            
            // Aplicar estilo especial si es el popup de bienvenida
            if (isWelcomeMessage) {
                notification.className += ' welcome-notification';
            }
            
            notification.style.cssText = `
                bottom: 20px;
                left: 20px;
                z-index: 9999;
                min-width: 250px;
                max-width: 300px;
                font-size: 0.875rem;
                padding: 0.5rem 0.75rem;
            `;
            
            // Ajustar estilos si es el popup de bienvenida
            if (isWelcomeMessage) {
                notification.style.cssText = `
                    bottom: 20px;
                    left: 20px;
                    z-index: 9999;
                    min-width: 300px;
                    max-width: 400px;
                    font-size: 1rem;
                    padding: 0.75rem 1rem;
                `;
            }
            
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
            `;
        }
        
        document.body.appendChild(notification);
        
        // Auto-remover después de 3 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                if (centered) {
                    // Animación de salida suave para popup centrado
                    notification.classList.add('fade-out');
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.remove();
                        }
                    }, 300); // Esperar a que termine la animación
                } else {
                    // Animación de salida suave para notificaciones normales
                    notification.classList.add('fade-out');
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.remove();
                        }
                    }, 300); // Esperar a que termine la animación
                }
            }
        }, 3000);
    }





    // Función para manejar la responsividad del sidebar
    function handleSidebarResponsiveness() {
        const sidebar = document.getElementById('sidebar');
        const main = document.querySelector('main');
        
        // En dispositivos móviles, colapsar sidebar por defecto
        if (window.innerWidth < 768) {
            sidebar.classList.remove('show');
        }
        
        // Agregar botón para toggle del sidebar en móviles
        if (!document.getElementById('sidebarToggle')) {
            const toggleButton = document.createElement('button');
            toggleButton.id = 'sidebarToggle';
            toggleButton.className = 'btn btn-primary d-md-none position-fixed';
            toggleButton.style.cssText = 'top: 70px; left: 10px; z-index: 1000;';
            toggleButton.innerHTML = '<i class="bi bi-list"></i>';
            toggleButton.addEventListener('click', toggleSidebar);
            
            document.body.appendChild(toggleButton);
        }
    }

    // Función para toggle del sidebar
    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('show');
    }

    // Función para inicializar las tarjetas del dashboard
    function initializeDashboardCards() {
        const cards = document.querySelectorAll('.card');
        
        cards.forEach((card, index) => {
            // Agregar delay de animación escalonado
            card.style.animationDelay = (index * 0.1) + 's';
            
            // Agregar efecto hover mejorado
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-8px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
    }

    // Función para manejar el estado de carga (mejorada)
    function handleLoadingStates() {
        // Solo aplicar loading a botones específicos, no a todos
        const loadingButtons = document.querySelectorAll('.btn[data-loading="true"]:not([type="submit"])');
        
        loadingButtons.forEach(button => {
            button.addEventListener('click', function() {
                if (!this.classList.contains('disabled')) {
                    this.classList.add('loading');
                    this.disabled = true;
                    
                    // Simular carga (remover en producción)
                    setTimeout(() => {
                        this.classList.remove('loading');
                        this.disabled = false;
                    }, 2000);
                }
            });
        });
    }

    // Función específica para manejar formularios
    function handleFormSubmissions() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitButton = this.querySelector('button[type="submit"]');
                
                if (submitButton && !submitButton.disabled) {
                    // Mostrar estado de carga en el botón de submit
                    submitButton.classList.add('loading');
                    submitButton.disabled = true;
                    
                    const originalText = submitButton.innerHTML;
                    submitButton.innerHTML = '<i class="spinner-border spinner-border-sm me-2"></i>Procesando...';
                    
                    // Re-habilitar el botón si hay errores de validación
                    setTimeout(() => {
                        if (this.querySelector('.alert-danger')) {
                            submitButton.classList.remove('loading');
                            submitButton.disabled = false;
                            submitButton.innerHTML = originalText;
                        }
                    }, 500);
                }
            });
        });
    }

    // Función para inicializar el timeline
    function initializeTimeline() {
        const timelineItems = document.querySelectorAll('.timeline-item');
        
        timelineItems.forEach((item, index) => {
            // Agregar animación de entrada
            item.style.opacity = '0';
            item.style.transform = 'translateX(-20px)';
            
            setTimeout(() => {
                item.style.transition = 'all 0.6s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateX(0)';
            }, index * 200);
        });
    }

    // Función para manejar el scroll suave
    function initializeSmoothScroll() {
        const links = document.querySelectorAll('a[href^="#"]');
        
        links.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // Función para inicializar el tema oscuro/claro
    function initializeThemeToggle() {
        const themeToggle = document.createElement('button');
        themeToggle.className = 'btn btn-outline-light btn-sm ms-2';
        themeToggle.innerHTML = '<i class="bi bi-moon"></i>';
        themeToggle.title = 'Cambiar tema';
        
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            const icon = this.querySelector('i');
            
            if (document.body.classList.contains('dark-theme')) {
                icon.className = 'bi bi-sun';
                localStorage.setItem('theme', 'dark');
            } else {
                icon.className = 'bi bi-moon';
                localStorage.setItem('theme', 'light');
            }
        });
        
        // Agregar al navbar
        const navbarNav = document.querySelector('.navbar-nav');
        if (navbarNav) {
            navbarNav.appendChild(themeToggle);
        }
        
        // Aplicar tema guardado
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
            themeToggle.querySelector('i').className = 'bi bi-sun';
        }
    }

    // Inicializar todas las funcionalidades
    function initializeApp() {
        initializeSidebar();
        handleSidebarResponsiveness();
        initializeDashboardCards();
        handleLoadingStates();
        handleFormSubmissions(); // Nueva función para formularios
        initializeTimeline();
        initializeSmoothScroll();
        initializeThemeToggle();
        
        // Mostrar mensaje de bienvenida centrado solo una vez por sesión y solo en el dashboard
        const isDashboard = document.body.classList.contains('dashboard-page');
        const welcomeShown = localStorage.getItem('welcomeShown');
        
        if (isDashboard && !welcomeShown) {
            setTimeout(() => {
                showNotification('¡Bienvenido a Directiva Agrícola!', 'success', false);
                localStorage.setItem('welcomeShown', 'true');
            }, 1000);
        }
    }

    // Función para manejar el logout
    function initializeLogout() {
        const logoutLink = document.getElementById('logout-link');
        if (logoutLink) {
            logoutLink.addEventListener('click', function() {
                // Limpiar el flag de bienvenida al hacer logout
                localStorage.removeItem('welcomeShown');
            });
        }
        
        // Limpiar el flag de bienvenida cuando se cierre la pestaña/ventana
        window.addEventListener('beforeunload', function() {
            localStorage.removeItem('welcomeShown');
        });
    }

    // Función de utilidad para resetear el popup de bienvenida (útil para testing)
    window.resetWelcomePopup = function() {
        localStorage.removeItem('welcomeShown');
        console.log('Popup de bienvenida reseteado. Recarga la página para verlo nuevamente.');
    };

    // Función de utilidad para probar notificaciones (útil para testing)
    window.testNotification = function(type = 'info') {
        const messages = {
            'success': '¡Operación exitosa!',
            'info': 'Información importante',
            'warning': 'Advertencia del sistema',
            'danger': 'Error crítico detectado',
            'welcome': '¡Bienvenido a Directiva Agrícola!'
        };
        showNotification(messages[type] || messages['info'], type);
        console.log(`Notificación de tipo '${type}' mostrada en esquina inferior izquierda.`);
    };

    // Ejecutar inicialización
    initializeApp();
    initializeLogout();

    // Manejar cambios de tamaño de ventana
    window.addEventListener('resize', handleSidebarResponsiveness);
});

// Agregar estilos CSS para efectos adicionales
const additionalStyles = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .sidebar .nav-link.active {
        background: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        transform: translateX(5px);
    }
    
    .dark-theme {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
    }
    
    .dark-theme .card {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
    }
    
    .dark-theme .navbar {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
    }
    
    .dark-theme .sidebar {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
    }
    
    /* Estilos para popup centrado de bienvenida */
    .welcome-popup {
        animation: welcomePopupIn 0.5s ease-out;
    }
    
    @keyframes welcomePopupIn {
        from {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.8);
        }
        to {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
        }
    }
    
    .welcome-popup.fade-out {
        animation: welcomePopupOut 0.3s ease-in forwards;
    }
    
    @keyframes welcomePopupOut {
        from {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
        }
        to {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.8);
        }
    }
    
    /* Estilos para notificaciones en esquina inferior izquierda */
    .notification-bottom-left {
        animation: slideInLeft 0.3s ease-out;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-radius: 6px;
        border-left: 4px solid;
    }
    
    /* Estilo especial para popup de bienvenida */
    .notification-bottom-left.welcome-notification {
        min-width: 300px;
        max-width: 400px;
        font-size: 1rem;
        padding: 0.75rem 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        border-left: 5px solid #198754;
        background: linear-gradient(135deg, #d1edff 0%, #e8f5e8 100%);
    }
    
    .notification-bottom-left.welcome-notification .btn-close {
        font-size: 0.8rem;
    }
    
    .notification-bottom-left.alert-success {
        border-left-color: #198754;
    }
    
    .notification-bottom-left.alert-info {
        border-left-color: #0dcaf0;
    }
    
    .notification-bottom-left.alert-warning {
        border-left-color: #ffc107;
    }
    
    .notification-bottom-left.alert-danger {
        border-left-color: #dc3545;
    }
    
    @keyframes slideInLeft {
        from {
            transform: translateX(-100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .notification-bottom-left.fade-out {
        animation: slideOutLeft 0.3s ease-in forwards;
    }
    
    @keyframes slideOutLeft {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(-100%);
            opacity: 0;
        }
    }
`;

// Insertar estilos adicionales
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);
