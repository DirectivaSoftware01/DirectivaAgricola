#!/bin/bash

# Script simple para desplegar con clave SSH
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Desplegando cambios a Hostinger VPS..."

# Variables de configuración
SERVER_IP="89.116.51.217"
SERVER_USER="root"
SERVER_DIR="/var/www/directiva_agricola"

# Función para imprimir mensajes
print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

print_status "Subiendo archivos modificados..."

# Subir archivos específicos modificados
print_status "Subiendo templates..."
scp templates/core/presupuesto_list.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/presupuesto_detail.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/presupuesto_gastos_reporte.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/remision_liquidacion.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/remision_detail.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/remision_form.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/remision_imprimir.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/

print_status "Subiendo modelos y vistas..."
scp core/models.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp core/views/main_views.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/views/
scp core/catalogos_ajax_views.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp core/admin.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp core/urls.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/

print_status "Subiendo archivos de configuración..."
scp requirements.txt $SERVER_USER@$SERVER_IP:$SERVER_DIR/
scp quick_update.sh $SERVER_USER@$SERVER_IP:$SERVER_DIR/

print_status "Ejecutando actualización en el servidor..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && chmod +x quick_update.sh && sudo ./quick_update.sh"

print_status "Verificando estado del servidor..."
ssh $SERVER_USER@$SERVER_IP "systemctl status directiva-agricola --no-pager -l"

print_status "✅ Despliegue completado exitosamente!"
print_status "🌐 Tu aplicación actualizada está disponible en: http://$SERVER_IP"
