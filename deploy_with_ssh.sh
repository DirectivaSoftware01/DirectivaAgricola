#!/bin/bash

# Script para desplegar con clave SSH específica
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Desplegando con clave SSH a Hostinger VPS..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables de configuración
SERVER_IP="89.116.51.217"
SERVER_USER="root"
SERVER_DIR="/var/www/directiva_agricola"
SSH_KEY="~/.ssh/id_ed25519"  # Ajustar si es necesario

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

print_status "Verificando conexión SSH..."
ssh -o ConnectTimeout=10 -o BatchMode=yes $SERVER_USER@$SERVER_IP "echo 'Conexión SSH exitosa'" || {
    print_error "No se puede conectar al servidor SSH"
    print_warning "Asegúrate de que:"
    print_warning "1. La clave SSH esté en ~/.ssh/id_ed25519"
    print_warning "2. El servidor esté accesible"
    print_warning "3. El usuario tenga permisos SSH"
    exit 1
}

print_status "Subiendo archivos modificados..."

# Subir archivos específicos modificados
print_status "Subiendo templates..."
scp -i $SSH_KEY templates/core/presupuesto_list.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp -i $SSH_KEY templates/core/presupuesto_detail.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp -i $SSH_KEY templates/core/presupuesto_gastos_reporte.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp -i $SSH_KEY templates/core/remision_liquidacion.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp -i $SSH_KEY templates/core/remision_detail.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp -i $SSH_KEY templates/core/remision_form.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp -i $SSH_KEY templates/core/remision_imprimir.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/

print_status "Subiendo modelos y vistas..."
scp -i $SSH_KEY core/models.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp -i $SSH_KEY core/views/main_views.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/views/
scp -i $SSH_KEY core/catalogos_ajax_views.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp -i $SSH_KEY core/admin.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp -i $SSH_KEY core/urls.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/

print_status "Subiendo archivos de configuración..."
scp -i $SSH_KEY requirements.txt $SERVER_USER@$SERVER_IP:$SERVER_DIR/
scp -i $SSH_KEY quick_update.sh $SERVER_USER@$SERVER_IP:$SERVER_DIR/

print_status "Ejecutando actualización en el servidor..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && chmod +x quick_update.sh && sudo ./quick_update.sh"

print_status "Verificando estado del servidor..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "systemctl status directiva-agricola --no-pager -l"

print_status "✅ Despliegue completado exitosamente!"
print_status "🌐 Tu aplicación actualizada está disponible en: http://$SERVER_IP"
print_status "📊 Para verificar: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'systemctl status directiva-agricola'"

echo ""
print_warning "IMPORTANTE:"
print_warning "1. Verifica que la aplicación funcione correctamente"
print_warning "2. Revisa los logs si hay algún problema"
print_warning "3. Los cambios incluyen nuevos modelos y migraciones"
