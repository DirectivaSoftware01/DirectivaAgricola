#!/bin/bash

# Script para desplegar directamente sin Git
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Desplegando cambios directamente a Hostinger VPS..."

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

print_status "Ejecutando migraciones en el servidor..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py migrate --settings=directiva_agricola.settings_production"

print_status "Recopilando archivos estáticos en el servidor..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production"

print_status "Reiniciando aplicación en el servidor..."
ssh $SERVER_USER@$SERVER_IP "systemctl restart directiva-agricola"

print_status "Verificando estado del servidor..."
ssh $SERVER_USER@$SERVER_IP "systemctl status directiva-agricola --no-pager -l"

print_status "✅ Despliegue completado exitosamente!"
print_status "🌐 Tu aplicación actualizada está disponible en: http://$SERVER_IP"
print_status "📊 Para verificar: ssh $SERVER_USER@$SERVER_IP 'systemctl status directiva-agricola'"
