#!/bin/bash

# Script para corregir el error de humanize
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Corrigiendo error de humanize..."

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

print_status "Agregando humanize a INSTALLED_APPS..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && sed -i \"s/'django.contrib.staticfiles',/'django.contrib.staticfiles',\n    'django.contrib.humanize',/\" directiva_agricola/settings_production.py"

print_status "Verificando configuración..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && grep -A 5 -B 5 'humanize' directiva_agricola/settings_production.py"

print_status "Probando configuración de Django..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py check --settings=directiva_agricola.settings_production"

print_status "Iniciando servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl start gunicorn_directiva_agricola.service"

print_status "Esperando que el servicio se inicie..."
sleep 10

print_status "Verificando estado..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

print_status "Probando acceso local..."
ssh $SERVER_USER@$SERVER_IP "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/ || echo 'Error en acceso local'"

print_status "Probando acceso externo..."
curl -s -o /dev/null -w "%{http_code}" https://agricola.directiva.mx/ || echo "Error en acceso externo"

print_status "✅ Error de humanize corregido!"
print_status "🌐 Tu aplicación está disponible en: https://agricola.directiva.mx/"
