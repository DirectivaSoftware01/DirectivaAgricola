#!/bin/bash

# Script para actualización sin backup
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Actualización de Directiva Agrícola (sin backup)..."

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

print_status "Deteniendo servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl stop gunicorn_directiva_agricola.service"

print_status "Subiendo archivos de la aplicación..."

# Subir core completo
print_status "Subiendo core/..."
scp -r core/ $SERVER_USER@$SERVER_IP:$SERVER_DIR/

# Subir templates completos
print_status "Subiendo templates/..."
scp -r templates/ $SERVER_USER@$SERVER_IP:$SERVER_DIR/

# Subir archivos de configuración
print_status "Subiendo archivos de configuración..."
scp requirements.txt $SERVER_USER@$SERVER_IP:$SERVER_DIR/
scp manage.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/
scp -r directiva_agricola/ $SERVER_USER@$SERVER_IP:$SERVER_DIR/

# Subir archivos estáticos
print_status "Subiendo archivos estáticos..."
scp -r static/ $SERVER_USER@$SERVER_IP:$SERVER_DIR/

print_status "Configurando permisos..."
ssh $SERVER_USER@$SERVER_IP "chown -R www-data:www-data $SERVER_DIR && chmod -R 755 $SERVER_DIR"

print_status "Actualizando dependencias..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

print_status "Creando migraciones..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py makemigrations --settings=directiva_agricola.settings_production"

print_status "Ejecutando migraciones..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py migrate --settings=directiva_agricola.settings_production"

print_status "Recopilando archivos estáticos..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production"

print_status "Iniciando servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl start gunicorn_directiva_agricola.service"

print_status "Verificando estado..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

print_status "✅ Actualización completada!"
print_status "🌐 Tu aplicación está disponible en: https://agricola.directiva.mx/"
