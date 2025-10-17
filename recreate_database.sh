#!/bin/bash

# Script para recrear la base de datos y desplegar
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Recreando base de datos y desplegando aplicación..."

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

print_status "Eliminando base de datos actual..."
ssh $SERVER_USER@$SERVER_IP "mysql -u root -e 'DROP DATABASE IF EXISTS directiva_agricola;'"

print_status "Creando nueva base de datos..."
ssh $SERVER_USER@$SERVER_IP "mysql -u root -e 'CREATE DATABASE directiva_agricola CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'"

print_status "Creando usuario de base de datos..."
ssh $SERVER_USER@$SERVER_IP "mysql -u root -e 'CREATE USER IF NOT EXISTS \"directiva_user\"@\"localhost\" IDENTIFIED BY \"Directiva2024!\";'"
ssh $SERVER_USER@$SERVER_IP "mysql -u root -e 'GRANT ALL PRIVILEGES ON directiva_agricola.* TO \"directiva_user\"@\"localhost\";'"
ssh $SERVER_USER@$SERVER_IP "mysql -u root -e 'FLUSH PRIVILEGES;'"

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

print_status "Creando migraciones iniciales..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py makemigrations --settings=directiva_agricola.settings_production"

print_status "Ejecutando migraciones..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py migrate --settings=directiva_agricola.settings_production"

print_status "Creando superusuario..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && echo 'from core.models import Usuario; Usuario.objects.create_superuser(\"admin\", \"admin@directiva.mx\", \"admin123\")' | python manage.py shell --settings=directiva_agricola.settings_production"

print_status "Recopilando archivos estáticos..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production"

print_status "Iniciando servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl start gunicorn_directiva_agricola.service"

print_status "Esperando que el servicio se inicie..."
sleep 10

print_status "Verificando estado..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

print_status "Probando acceso local..."
ssh $SERVER_USER@$SERVER_IP "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/ || echo 'Error en acceso local'"

print_status "✅ Base de datos recreada y aplicación desplegada!"
print_status "🌐 Tu aplicación está disponible en: https://agricola.directiva.mx/"
print_status "👤 Usuario: admin / Contraseña: admin123"
print_status "📊 Todas las actualizaciones están aplicadas"
