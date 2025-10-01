#!/bin/bash

# Script de despliegue para AWS EC2
# Configuración de credenciales AWS
export AWS_ACCESS_KEY_ID="AKIAQDYWGM2KDAQWS544"
export AWS_SECRET_ACCESS_KEY="XSDybPa3iEaRoSIjKX01Rd+OHe3xpeyq2GieBhLxt"

# Configuración de base de datos RDS
export DS_DB_NAME="directiva_agricola"
export RDS_ADMIN_DB_NAME="directiva_administracion"
export RDS_USERNAME="postgres"
export RDS_PASSWORD="Directiva2024!"
export RDS_HOSTNAME="directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com"
export RDS_PORT="5432"

# IP de la instancia EC2
EC2_IP="54.212.80.37"

echo "🚀 Iniciando despliegue en AWS EC2..."

# 1. Conectar a la instancia EC2 y actualizar el sistema
echo "📦 Actualizando sistema en EC2..."
ssh -i ~/.ssh/your-key.pem ubuntu@$EC2_IP << 'EOF'
    sudo apt update
    sudo apt upgrade -y
    
    # Instalar Python 3.13.7
    sudo apt install -y software-properties-common
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install -y python3.13 python3.13-venv python3.13-dev
    
    # Instalar dependencias del sistema
    sudo apt install -y postgresql-client libpq-dev build-essential nginx git
    
    # Crear directorio del proyecto
    sudo mkdir -p /var/www/directiva_agricola
    sudo chown ubuntu:ubuntu /var/www/directiva_agricola
EOF

# 2. Subir archivos del proyecto
echo "📁 Subiendo archivos del proyecto..."
rsync -avz --exclude 'venv/' --exclude '__pycache__/' --exclude '*.pyc' --exclude '.git/' \
    -e "ssh -i ~/.ssh/your-key.pem" \
    ./ ubuntu@$EC2_IP:/var/www/directiva_agricola/

# 3. Configurar entorno virtual y dependencias
echo "🐍 Configurando entorno virtual..."
ssh -i ~/.ssh/your-key.pem ubuntu@$EC2_IP << 'EOF'
    cd /var/www/directiva_agricola
    
    # Eliminar entorno virtual existente si existe
    rm -rf venv
    
    # Crear nuevo entorno virtual con Python 3.13
    python3.13 -m venv venv
    source venv/bin/activate
    
    # Actualizar pip
    pip install --upgrade pip
    
    # Instalar dependencias
    pip install -r requirements.txt
    
    # Instalar dependencias adicionales para producción
    pip install gunicorn psycopg2-binary
EOF

# 4. Configurar base de datos PostgreSQL
echo "🗄️ Configurando base de datos PostgreSQL..."
ssh -i ~/.ssh/your-key.pem ubuntu@$EC2_IP << 'EOF'
    cd /var/www/directiva_agricola
    source venv/bin/activate
    
    # Crear archivo de configuración de producción
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
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
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

    # Crear directorio de logs
    sudo mkdir -p /var/log/directiva_agricola
    sudo chown ubuntu:ubuntu /var/log/directiva_agricola
EOF

# 5. Configurar y ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
ssh -i ~/.ssh/your-key.pem ubuntu@$EC2_IP << 'EOF'
    cd /var/www/directiva_agricola
    source venv/bin/activate
    
    # Configurar variables de entorno
    export DS_DB_NAME="directiva_agricola"
    export RDS_ADMIN_DB_NAME="directiva_administracion"
    export RDS_USERNAME="postgres"
    export RDS_PASSWORD="Directiva2024!"
    export RDS_HOSTNAME="directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com"
    export RDS_PORT="5432"
    export SECRET_KEY="your-secret-key-here"
    
    # Ejecutar migraciones para base de datos de administración
    python manage.py migrate --settings=directiva_agricola.settings_production --database=administracion
    
    # Ejecutar migraciones para base de datos principal
    python manage.py migrate --settings=directiva_agricola.settings_production --database=default
    
    # Recopilar archivos estáticos
    python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production
EOF

# 6. Configurar Gunicorn
echo "🔧 Configurando Gunicorn..."
ssh -i ~/.ssh/your-key.pem ubuntu@$EC2_IP << 'EOF'
    cd /var/www/directiva_agricola
    
    # Crear archivo de configuración de Gunicorn
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

    # Crear servicio systemd para Gunicorn
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
Environment="SECRET_KEY=your-secret-key-here"
ExecStart=/var/www/directiva_agricola/venv/bin/gunicorn --config gunicorn.conf.py directiva_agricola.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL

    # Recargar systemd y habilitar servicio
    sudo systemctl daemon-reload
    sudo systemctl enable directiva-agricola
    sudo systemctl start directiva-agricola
EOF

# 7. Configurar Nginx
echo "🌐 Configurando Nginx..."
ssh -i ~/.ssh/your-key.pem ubuntu@$EC2_IP << 'EOF'
    # Crear configuración de Nginx
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

    # Habilitar sitio y reiniciar Nginx
    sudo ln -sf /etc/nginx/sites-available/directiva-agricola /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl restart nginx
    sudo systemctl enable nginx
EOF

echo "✅ Despliegue completado!"
echo "🌐 Aplicación disponible en: http://54.212.80.37"
echo "📊 Estado del servicio: sudo systemctl status directiva-agricola"
echo "📝 Logs: sudo journalctl -u directiva-agricola -f"
