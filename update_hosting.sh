#!/bin/bash

# Script de actualización para Hostinger VPS
# Ejecutar en el servidor VPS para actualizar la aplicación

set -e  # Salir si hay algún error

echo "🔄 Iniciando actualización de Directiva Agrícola en Hostinger VPS..."

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

# Verificar que el directorio del proyecto existe
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "El directorio del proyecto no existe: $PROJECT_DIR"
    print_error "Ejecuta primero el script de despliegue inicial"
    exit 1
fi

print_status "Deteniendo servicios..."
systemctl stop directiva-agricola

print_status "Haciendo backup de la base de datos..."
cd $PROJECT_DIR
mysqldump -u directiva_user -p directiva_agricola > backup_$(date +%Y%m%d_%H%M%S).sql

print_status "Actualizando código desde Git..."
cd $PROJECT_DIR
git fetch origin
git reset --hard origin/main

print_status "Activando entorno virtual..."
source $VENV_DIR/bin/activate

print_status "Actualizando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

print_status "Ejecutando migraciones de base de datos..."
python manage.py migrate --settings=directiva_agricola.settings_production

print_status "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production

print_status "Configurando permisos..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

print_status "Iniciando servicios..."
systemctl start directiva-agricola
systemctl reload nginx

print_status "Verificando estado de los servicios..."
systemctl status directiva-agricola --no-pager
systemctl status nginx --no-pager

print_status "✅ Actualización completada exitosamente!"
print_status "🌐 Tu aplicación actualizada está disponible"
print_status "📊 Para monitorear: systemctl status directiva-agricola"
print_status "📝 Para ver logs: journalctl -u directiva-agricola -f"

echo ""
print_warning "IMPORTANTE:"
print_warning "1. Verifica que la aplicación funcione correctamente"
print_warning "2. Revisa los logs si hay algún problema"
print_warning "3. El backup de la base de datos se guardó en: $PROJECT_DIR/backup_*.sql"
