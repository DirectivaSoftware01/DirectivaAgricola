#!/bin/bash

# Script para probar con servidor de desarrollo de Django
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Probando con servidor de desarrollo de Django..."

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

print_status "Probando con servidor de desarrollo de Django..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py runserver 0.0.0.0:8000 --settings=directiva_agricola.settings_production" &

print_status "Esperando que el servidor se inicie..."
sleep 10

print_status "Probando acceso local..."
ssh $SERVER_USER@$SERVER_IP "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/ || echo 'Error en acceso local'"

print_status "Probando acceso externo..."
curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP:8000/ || echo "Error en acceso externo"

print_status "Deteniendo servidor de desarrollo..."
ssh $SERVER_USER@$SERVER_IP "pkill -f 'python manage.py runserver' || echo 'Servidor detenido'"

print_status "Iniciando Gunicorn nuevamente..."
ssh $SERVER_USER@$SERVER_IP "systemctl start gunicorn_directiva_agricola.service"

print_status "Esperando que Gunicorn se inicie..."
sleep 10

print_status "Verificando estado de Gunicorn..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

print_status "✅ Prueba completada!"
print_status "🌐 Tu aplicación está disponible en: https://agricola.directiva.mx/"
print_status "📊 Los archivos han sido actualizados, verifica los cambios en Presupuestos"
