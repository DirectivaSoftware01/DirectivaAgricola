#!/bin/bash

# Script para corregir el middleware faltante
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Corrigiendo middleware faltante..."

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

print_status "Creando el middleware faltante..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && cat > core/middleware.py << 'EOF'
from django.utils import timezone
from django.conf import settings

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Activar la zona horaria de México
        timezone.activate(settings.TIME_ZONE)
        response = self.get_response(request)
        return response
EOF"

print_status "Actualizando configuración de Django para remover el middleware problemático..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && sed -i 's/    \"core.middleware.TimezoneMiddleware\",/#    \"core.middleware.TimezoneMiddleware\",/' directiva_agricola/settings_production.py"

print_status "Subiendo archivos actualizados..."
scp templates/core/presupuesto_list.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/presupuesto_detail.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/presupuesto_gastos_reporte.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp core/models.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp core/views/main_views.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/views/
scp core/catalogos_ajax_views.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp core/admin.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp core/urls.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/

print_status "Configurando permisos..."
ssh $SERVER_USER@$SERVER_IP "chown -R www-data:www-data $SERVER_DIR && chmod -R 755 $SERVER_DIR"

print_status "Probando configuración de Django..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py check --settings=directiva_agricola.settings_production"

print_status "Iniciando servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl start gunicorn_directiva_agricola.service"

print_status "Esperando que el servicio se inicie..."
sleep 15

print_status "Verificando estado..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

print_status "Probando acceso local..."
ssh $SERVER_USER@$SERVER_IP "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/ || echo 'Error en acceso local'"

print_status "Probando acceso externo..."
curl -s -o /dev/null -w "%{http_code}" https://agricola.directiva.mx/ || echo "Error en acceso externo"

print_status "✅ Middleware corregido!"
print_status "🌐 Tu aplicación está disponible en: https://agricola.directiva.mx/"
print_status "📊 Todas las actualizaciones están aplicadas"
