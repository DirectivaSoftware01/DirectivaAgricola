#!/bin/bash

# Script para corregir configuración de archivos estáticos
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Corrigiendo configuración de archivos estáticos..."

# Variables de configuración
SERVER_IP="89.116.51.217"
SERVER_USER="root"
SERVER_DIR="/var/www/directiva_agricola"

# Función para imprimir mensajes
print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_status "Haciendo backup de la configuración..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && cp directiva_agricola/settings_production.py directiva_agricola/settings_production.py.backup"

print_status "Corrigiendo configuración de archivos estáticos..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && sed -i 's/STATICFILES_DIRS = \[os.path.join(BASE_DIR, \"static\")\]/# STATICFILES_DIRS = [os.path.join(BASE_DIR, \"static\")]/' directiva_agricola/settings_production.py"

print_status "Verificando configuración corregida..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && grep -n 'STATICFILES_DIRS' directiva_agricola/settings_production.py"

print_status "Probando configuración de Django..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py check --settings=directiva_agricola.settings_production"

print_status "Iniciando servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl start gunicorn_directiva_agricola.service"

print_status "Verificando estado..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

print_status "✅ Configuración corregida!"
print_status "🌐 Tu aplicación está disponible en: https://agricola.directiva.mx/"
