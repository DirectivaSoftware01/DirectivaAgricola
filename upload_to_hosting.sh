#!/bin/bash

# Script para subir archivos al servidor de Hostinger
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "📤 Subiendo archivos a Hostinger VPS..."

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

# Verificar que rsync esté instalado
if ! command -v rsync &> /dev/null; then
    print_error "rsync no está instalado. Instálalo con: brew install rsync"
    exit 1
fi

print_status "Sincronizando archivos con el servidor..."
print_warning "Asegúrate de que el servidor esté accesible y las credenciales sean correctas"

# Sincronizar archivos (excluyendo archivos innecesarios)
rsync -avz --progress \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='db.sqlite3' \
    --exclude='media/' \
    --exclude='staticfiles/' \
    --exclude='.env' \
    --exclude='*.log' \
    --exclude='backup_*.sql' \
    ./ $SERVER_USER@$SERVER_IP:$SERVER_DIR/

print_status "Subiendo script de actualización..."
scp update_hosting.sh $SERVER_USER@$SERVER_IP:$SERVER_DIR/

print_status "Ejecutando actualización en el servidor..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && chmod +x update_hosting.sh && sudo ./update_hosting.sh"

print_status "✅ Actualización completada!"
print_status "🌐 Tu aplicación está disponible en: http://$SERVER_IP"
print_status "📊 Para verificar el estado: ssh $SERVER_USER@$SERVER_IP 'systemctl status directiva-agricola'"

echo ""
print_warning "IMPORTANTE:"
print_warning "1. Verifica que la aplicación funcione correctamente"
print_warning "2. Revisa los logs si hay algún problema"
print_warning "3. Configura tu dominio DNS si es necesario"
