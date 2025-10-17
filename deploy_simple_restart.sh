#!/bin/bash

# Script simple para reiniciar servicios
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Reiniciando servicios y verificando actualización..."

# Variables de configuración
SERVER_IP="89.116.51.217"
SERVER_USER="root"
SERVER_DIR="/var/www/directiva_agricola"

# Función para imprimir mensajes
print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_status "Subiendo archivos específicos de Presupuestos..."

# Subir solo los archivos de presupuestos que necesitan actualización
scp templates/core/presupuesto_list.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/presupuesto_detail.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/presupuesto_gastos_reporte.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/

print_status "Subiendo modelos y vistas actualizados..."
scp core/models.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp core/views/main_views.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/views/
scp core/catalogos_ajax_views.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp core/admin.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp core/urls.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/

print_status "Configurando permisos..."
ssh $SERVER_USER@$SERVER_IP "chown -R www-data:www-data $SERVER_DIR && chmod -R 755 $SERVER_DIR"

print_status "Reiniciando servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl restart gunicorn_directiva_agricola.service"

print_status "Esperando que el servicio se inicie..."
sleep 5

print_status "Verificando estado del servicio..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

print_status "Verificando que los archivos estén actualizados..."
ssh $SERVER_USER@$SERVER_IP "grep -n 'color: #ffffff' $SERVER_DIR/templates/core/presupuesto_list.html || echo 'Archivo no encontrado o no actualizado'"

print_status "✅ Actualización completada!"
print_status "🌐 Tu aplicación está disponible en: https://agricola.directiva.mx/"
print_status "📊 Verifica que los cambios en Presupuestos estén funcionando"
