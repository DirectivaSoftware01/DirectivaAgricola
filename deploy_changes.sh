#!/bin/bash

# Script para desplegar solo los cambios específicos
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Desplegando cambios específicos a Hostinger VPS..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables de configuración (CAMBIAR ESTAS VARIABLES)
SERVER_IP="89.116.51.217"  # Cambiar por tu IP del VPS
SERVER_USER="root"  # Cambiar por tu usuario del servidor
SERVER_DIR="/var/www/directiva_agricola"

# Función para imprimir mensajes
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
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

print_status "✅ Despliegue de cambios completado!"
print_status "🌐 Tu aplicación actualizada está disponible en: http://$SERVER_IP"
print_status "📊 Para verificar: ssh $SERVER_USER@$SERVER_IP 'systemctl status directiva-agricola'"

echo ""
print_warning "IMPORTANTE:"
print_warning "1. Verifica que la aplicación funcione correctamente"
print_warning "2. Revisa los logs si hay algún problema"
print_warning "3. Los cambios incluyen nuevos modelos y migraciones"
