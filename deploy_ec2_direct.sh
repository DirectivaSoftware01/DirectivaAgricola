#!/bin/bash

# Script de despliegue directo en EC2
# Este script se ejecuta directamente en la instancia EC2

echo "🚀 Iniciando despliegue directo en EC2..."

# Configuración de base de datos RDS
export DS_DB_NAME="directiva_agricola"
export RDS_ADMIN_DB_NAME="directiva_administracion"
export RDS_USERNAME="postgres"
export RDS_PASSWORD="Directiva2024!"
export RDS_HOSTNAME="directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com"
export RDS_PORT="5432"
export SECRET_KEY="directiva-secret-key-2024-production"

# 1. Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update
sudo apt upgrade -y

# 2. Instalar Python 3.13.7
echo "🐍 Instalando Python 3.13.7..."
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3.13-dev

# 3. Instalar dependencias del sistema
echo "📚 Instalando dependencias del sistema..."
sudo apt install -y postgresql-client libpq-dev build-essential nginx git

# 4. Crear directorio del proyecto
echo "📁 Creando directorio del proyecto..."
sudo mkdir -p /var/www/directiva_agricola
sudo chown ubuntu:ubuntu /var/www/directiva_agricola

# 5. Clonar repositorio
echo "📥 Clonando repositorio..."
cd /var/www
sudo rm -rf directiva_agricola
sudo git clone https://github.com/DirectivaSoftware01/DirectivaAgricola.git directiva_agricola
sudo chown -R ubuntu:ubuntu /var/www/directiva_agricola
cd /var/www/directiva_agricola

# 6. Crear entorno virtual
echo "🔧 Creando entorno virtual..."
python3.13 -m venv venv
source venv/bin/activate

# 7. Instalar dependencias
echo "📦 Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt

# 8. Crear configuración de producción
echo "⚙️ Creando configuración de producción..."
cat > directiva_agricola/settings_production.py << 'EOL'
import os
from pathlib import Path
from .settings import *

# Configuración de producción
DEBUG = False
ALLOWED_HOSTS = ['54.212.80.37', 'directiva-agricola.com', 'www.directiva-agricola.com']

# Configuración de base de datos PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DS_DB_NAME', 'directiva_agricola'),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', 'Directiva2024!'),
        'HOST': os.environ.get('RDS_HOSTNAME', 'directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com'),
        'PORT': os.environ.get('RDS_PORT', '5432'),
        'ATOMIC_REQUESTS': True,
        'TIME_ZONE': 'America/Mexico_City',
        'OPTIONS': {},
        'CONN_MAX_AGE': 0,
        'AUTOCOMMIT': True,
        'CONN_HEALTH_CHECKS': False,
        'TEST': {
            'CHARSET': None,
            'COLLATION': None,
            'MIGRATE': True,
            'MIRROR': None,
            'NAME': None
        },
    },
    'administracion': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('RDS_ADMIN_DB_NAME', 'directiva_administracion'),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', 'Directiva2024!'),
        'HOST': os.environ.get('RDS_HOSTNAME', 'directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com'),
        'PORT': os.environ.get('RDS_PORT', '5432'),
        'ATOMIC_REQUESTS': True,
        'TIME_ZONE': 'America/Mexico_City',
        'OPTIONS': {},
        'CONN_MAX_AGE': 0,
        'AUTOCOMMIT': True,
        'CONN_HEALTH_CHECKS': False,
        'TEST': {
            'CHARSET': None,
            'COLLATION': None,
            'MIGRATE': True,
            'MIRROR': None,
            'NAME': None
        },
    }
}

# Configuración de archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configuración de archivos multimedia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuración de seguridad
SECRET_KEY = os.environ.get('SECRET_KEY', 'directiva-secret-key-2024-production')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/directiva_agricola/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
EOL

# 9. Crear directorio de logs
echo "📝 Creando directorio de logs..."
sudo mkdir -p /var/log/directiva_agricola
sudo chown ubuntu:ubuntu /var/log/directiva_agricola

# 10. Configurar variables de entorno
echo "🔧 Configurando variables de entorno..."
export DS_DB_NAME="directiva_agricola"
export RDS_ADMIN_DB_NAME="directiva_administracion"
export RDS_USERNAME="postgres"
export RDS_PASSWORD="Directiva2024!"
export RDS_HOSTNAME="directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com"
export RDS_PORT="5432"
export SECRET_KEY="directiva-secret-key-2024-production"

# 11. Crear bases de datos RDS
echo "🗄️ Creando bases de datos RDS..."
python3.13 -c "
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Conectar a PostgreSQL como superusuario
conn = psycopg2.connect(
    host='directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com',
    port=5432,
    user='postgres',
    password='Directiva2024!',
    database='postgres'
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

# Crear base de datos de administración
try:
    cursor.execute('CREATE DATABASE directiva_administracion')
    print('✅ Base de datos directiva_administracion creada')
except:
    print('ℹ️  Base de datos directiva_administracion ya existe')

# Crear base de datos principal
try:
    cursor.execute('CREATE DATABASE directiva_agricola')
    print('✅ Base de datos directiva_agricola creada')
except:
    print('ℹ️  Base de datos directiva_agricola ya existe')

cursor.close()
conn.close()
"

# 12. Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py migrate --settings=directiva_agricola.settings_production --database=administracion
python manage.py migrate --settings=directiva_agricola.settings_production --database=default

# 13. Recopilar archivos estáticos
echo "📦 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production

# 14. Crear usuario administrador
echo "👤 Creando usuario administrador..."
python manage.py shell --settings=directiva_agricola.settings_production << 'EOF'
from django.contrib.auth import get_user_model
from administracion.models import UsuarioAdministracion

User = get_user_model()

# Crear usuario administrador en base de administración
admin_user, created = UsuarioAdministracion.objects.using('administracion').get_or_create(
    username='admin',
    defaults={
        'first_name': 'Administrador',
        'last_name': 'Sistema',
        'email': 'admin@directiva.com',
        'is_staff': True,
        'is_active': True
    }
)
if created:
    admin_user.set_password('Directiva2024!')
    admin_user.save()
    print('✅ Usuario administrador creado')
else:
    print('ℹ️  Usuario administrador ya existe')

# Crear usuario supervisor en base principal
supervisor_user, created = User.objects.using('default').get_or_create(
    username='supervisor',
    defaults={
        'first_name': 'Supervisor',
        'last_name': 'Sistema',
        'email': 'supervisor@directiva.com',
        'is_superuser': True,
        'is_staff': True,
        'is_active': True
    }
)
if created:
    supervisor_user.set_password('Directivasbmj1*')
    supervisor_user.save()
    print('✅ Usuario supervisor creado')
else:
    print('ℹ️  Usuario supervisor ya existe')
EOF

# 15. Configurar Gunicorn
echo "🔧 Configurando Gunicorn..."
cat > gunicorn.conf.py << 'EOL'
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOL

# 16. Crear servicio systemd para Gunicorn
echo "🔧 Creando servicio systemd..."
sudo tee /etc/systemd/system/directiva-agricola.service > /dev/null << 'EOL'
[Unit]
Description=Directiva Agricola Gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/directiva_agricola
Environment="PATH=/var/www/directiva_agricola/venv/bin"
Environment="DS_DB_NAME=directiva_agricola"
Environment="RDS_ADMIN_DB_NAME=directiva_administracion"
Environment="RDS_USERNAME=postgres"
Environment="RDS_PASSWORD=Directiva2024!"
Environment="RDS_HOSTNAME=directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com"
Environment="RDS_PORT=5432"
Environment="SECRET_KEY=directiva-secret-key-2024-production"
ExecStart=/var/www/directiva_agricola/venv/bin/gunicorn --config gunicorn.conf.py directiva_agricola.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL

# 17. Habilitar y iniciar servicio
echo "🚀 Iniciando servicio..."
sudo systemctl daemon-reload
sudo systemctl enable directiva-agricola
sudo systemctl start directiva-agricola

# 18. Configurar Nginx
echo "🌐 Configurando Nginx..."
sudo tee /etc/nginx/sites-available/directiva-agricola > /dev/null << 'EOL'
server {
    listen 80;
    server_name 54.212.80.37 directiva-agricola.com www.directiva-agricola.com;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias /var/www/directiva_agricola/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/directiva_agricola/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
EOL

# 19. Habilitar sitio y reiniciar Nginx
echo "🌐 Configurando Nginx..."
sudo ln -sf /etc/nginx/sites-available/directiva-agricola /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# 20. Crear empresa de prueba
echo "🏢 Creando empresa de prueba..."
python manage.py crear_empresa_postgresql \
    --razon-social="EMPRESA DEMOSTRACION" \
    --rfc="DEMO250901XXX" \
    --direccion="Dirección de prueba" \
    --telefono="555-1234" \
    --email="demo@directiva.com" \
    --ciclo-actual="2025" \
    --settings=directiva_agricola.settings_production

echo "✅ Despliegue completado!"
echo "🌐 Aplicación disponible en: http://54.212.80.37"
echo "📊 Estado del servicio: sudo systemctl status directiva-agricola"
echo "📝 Logs: sudo journalctl -u directiva-agricola -f"
echo "🔑 Usuario administrador: admin / Directiva2024!"
echo "🔑 Usuario supervisor: supervisor / Directivasbmj1*"
