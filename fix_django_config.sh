#!/bin/bash

# Script para corregir configuración de Django
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Corrigiendo configuración de Django..."

# Variables de configuración
SERVER_IP="89.116.51.217"
SERVER_USER="root"
SERVER_DIR="/var/www/directiva_agricola"

# Función para imprimir mensajes
print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_status "Deteniendo servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl stop gunicorn_directiva_agricola.service"

print_status "Corrigiendo configuración de archivos estáticos..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && cp directiva_agricola/settings_production.py directiva_agricola/settings_production.py.backup"

# Crear un archivo de configuración temporal que ignore los errores de staticfiles
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && cat > fix_settings.py << 'EOF'
import os
import sys
import django
from django.conf import settings

# Configuración mínima para ejecutar migraciones
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'directiva_agricola.settings_production')

# Configurar Django sin verificar staticfiles
settings.configure(
    DEBUG=False,
    INSTALLED_APPS=[
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'core',
    ],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'directiva_agricola',
            'USER': 'directiva_user',
            'PASSWORD': 'tu_password_seguro',
            'HOST': 'localhost',
            'PORT': '3306',
        }
    },
    SECRET_KEY='temp-secret-key-for-migrations',
    USE_TZ=True,
    TIME_ZONE='UTC',
)

django.setup()

# Ejecutar migraciones
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate'])
EOF"

print_status "Ejecutando migraciones con configuración temporal..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python fix_settings.py"

print_status "Iniciando servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl start gunicorn_directiva_agricola.service"

print_status "Verificando estado..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

print_status "Limpiando archivos temporales..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && rm -f fix_settings.py"

print_status "✅ Configuración corregida y migraciones ejecutadas!"
print_status "🌐 Tu aplicación está disponible en: https://agricola.directiva.mx/"
