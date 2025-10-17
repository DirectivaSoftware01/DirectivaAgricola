#!/bin/bash

# Script para ejecutar solo migraciones
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Ejecutando solo migraciones y reiniciando servicios..."

# Variables de configuración
SERVER_IP="89.116.51.217"
SERVER_USER="root"
SERVER_DIR="/var/www/directiva_agricola"

# Función para imprimir mensajes
print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_status "Deteniendo servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl stop gunicorn_directiva_agricola.service"

print_status "Ejecutando migraciones (ignorando errores de configuración)..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py migrate --settings=directiva_agricola.settings_production --run-syncdb"

print_status "Iniciando servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl start gunicorn_directiva_agricola.service"

print_status "Verificando estado..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

print_status "✅ Migraciones ejecutadas!"
print_status "🌐 Tu aplicación está disponible en: https://agricola.directiva.mx/"
