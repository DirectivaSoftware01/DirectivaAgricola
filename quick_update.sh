#!/bin/bash

# Script de actualización rápida para Hostinger VPS
# Solo actualiza archivos y reinicia la aplicación

set -e  # Salir si hay algún error

echo "⚡ Actualización rápida de Directiva Agrícola..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables de configuración
PROJECT_DIR="/var/www/directiva_agricola"
VENV_DIR="/var/www/directiva_agricola/venv"

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

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    print_error "Este script debe ejecutarse como root (sudo)"
    exit 1
fi

print_status "Actualizando código desde Git..."
cd $PROJECT_DIR
git pull origin main

print_status "Activando entorno virtual..."
source $VENV_DIR/bin/activate

print_status "Ejecutando migraciones de base de datos..."
python manage.py migrate --settings=directiva_agricola.settings_production

print_status "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production

print_status "Reiniciando aplicación..."
systemctl restart directiva-agricola

print_status "Verificando estado..."
systemctl status directiva-agricola --no-pager -l

print_status "✅ Actualización rápida completada!"
print_status "🌐 Tu aplicación está actualizada y funcionando"
