#!/bin/bash

# Script para sincronizar cambios del hosting con el proyecto local
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🔄 Sincronizando cambios del hosting con proyecto local..."

# Variables de configuración
SERVER_IP="89.116.51.217"
SERVER_USER="root"
SERVER_DIR="/var/www/directiva_agricola"

# Función para imprimir mensajes
print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_status "Descargando archivos modificados del hosting..."

# Descargar configuración de Django
print_status "Descargando settings_production.py..."
scp $SERVER_USER@$SERVER_IP:$SERVER_DIR/directiva_agricola/settings_production.py ./directiva_agricola/

# Descargar middleware
print_status "Descargando middleware.py..."
scp $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/middleware.py ./core/

# Descargar template con logs de depuración
print_status "Descargando presupuesto_list.html..."
scp $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/presupuesto_list.html ./templates/core/

print_status "✅ Archivos sincronizados exitosamente!"
print_status "📁 Archivos actualizados:"
echo "  - directiva_agricola/settings_production.py"
echo "  - core/middleware.py"
echo "  - templates/core/presupuesto_list.html"
print_status "🎯 Tu proyecto local ahora tiene la misma versión que el hosting"
