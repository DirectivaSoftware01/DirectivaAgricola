#!/bin/bash

# Script de despliegue para AWS Lightsail - Versión económica
# Configuración básica
LIGHTSAIL_INSTANCE_NAME="directiva-agricola-prod"
LIGHTSAIL_BLUEPRINT="ubuntu_22_04"
LIGHTSAIL_BUNDLE_ID="nano_2_0"  # $5/mes - 512MB RAM, 1 vCPU
DOMAIN_NAME="agricola.directiva.mx"  # Subdominio correcto
EMAIL="admin@directiva.mx"  # Para SSL

echo "🚀 Iniciando despliegue en AWS Lightsail..."
echo "💰 Instancia: $LIGHTSAIL_BUNDLE_ID (~$5/mes)"
echo "🌐 Dominio: $DOMAIN_NAME"

# 1. Crear instancia Lightsail
echo "📦 Creando instancia Lightsail..."
aws lightsail create-instances \
    --instance-names $LIGHTSAIL_INSTANCE_NAME \
    --availability-zone us-west-2a \
    --blueprint-id $LIGHTSAIL_BLUEPRINT \
    --bundle-id $LIGHTSAIL_BUNDLE_ID \
    --user-data file://user_data_lightsail.sh

# Esperar a que la instancia esté lista
echo "⏳ Esperando a que la instancia esté lista..."
aws lightsail wait instance-running --instance-name $LIGHTSAIL_INSTANCE_NAME

# Obtener IP pública
PUBLIC_IP=$(aws lightsail get-instance --instance-name $LIGHTSAIL_INSTANCE_NAME --query 'instance.publicIpAddress' --output text)
echo "🌐 IP pública: $PUBLIC_IP"

# 2. Crear bucket S3 para archivos estáticos
echo "🪣 Creando bucket S3 para archivos estáticos..."
BUCKET_NAME="directiva-agricola-static-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME --region us-west-2

# Configurar bucket para hosting web
aws s3 website s3://$BUCKET_NAME --index-document index.html --error-document error.html

# Configurar política pública
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json

# 3. Crear base de datos PostgreSQL en Lightsail
echo "🗄️ Creando base de datos PostgreSQL..."
aws lightsail create-relational-database \
    --relational-database-name directiva-agricola-db \
    --relational-database-blueprint-id postgres_15 \
    --relational-database-bundle-id micro_1_0 \
    --master-username postgres \
    --master-user-password Directiva2024! \
    --preferred-backup-window 03:00-04:00 \
    --preferred-maintenance-window sun:04:00-sun:05:00

# Esperar a que la BD esté lista
echo "⏳ Esperando a que la base de datos esté lista..."
aws lightsail wait relational-database-available --relational-database-name directiva-agricola-db

# Obtener endpoint de la BD
DB_ENDPOINT=$(aws lightsail get-relational-database --relational-database-name directiva-agricola-db --query 'relationalDatabase.masterEndpoint.address' --output text)
echo "🗄️ Endpoint BD: $DB_ENDPOINT"

# 4. Configurar DNS (opcional - si tienes dominio)
echo "🌐 Configurando DNS..."
# Nota: Necesitarás configurar manualmente el DNS de tu dominio para apuntar a $PUBLIC_IP

# 5. Preparar archivos para despliegue
echo "📁 Preparando archivos para despliegue..."

# Crear archivo de configuración de producción para Lightsail
cat > directiva_agricola/settings_lightsail.py << EOF
"""
Configuración de producción para Lightsail
"""
import os
from .settings import *

# Configuración de base de datos PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'directiva_agricola',
        'USER': 'postgres',
        'PASSWORD': 'Directiva2024!',
        'HOST': '$DB_ENDPOINT',
        'PORT': '5432',
        'ATOMIC_REQUESTS': True,
    },
    'administracion': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'directiva_administracion',
        'USER': 'postgres',
        'PASSWORD': 'Directiva2024!',
        'HOST': '$DB_ENDPOINT',
        'PORT': '5432',
        'ATOMIC_REQUESTS': True,
    }
}

# Configuración de archivos estáticos con S3
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = '$BUCKET_NAME'
AWS_S3_REGION_NAME = 'us-west-2'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Configuración de archivos estáticos
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Configuración de archivos de media
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Configuración de seguridad
DEBUG = False
ALLOWED_HOSTS = [
    '$PUBLIC_IP',
    '$DOMAIN_NAME',
    'www.$DOMAIN_NAME',
    'localhost',
    '127.0.0.1',
]

# Configuración de seguridad adicional
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

# Configuración de middleware para producción
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'core.middleware.EmpresaDbMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.NoCacheMiddleware',
    'core.middleware.StaticFilesNoCacheMiddleware',
]
EOF

# Crear script de instalación para la instancia
cat > install_lightsail.sh << EOF
#!/bin/bash

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11 y dependencias
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
sudo apt install -y postgresql-client libpq-dev build-essential nginx git
sudo apt install -y certbot python3-certbot-nginx

# Crear directorio del proyecto
sudo mkdir -p /var/www/directiva_agricola
sudo chown ubuntu:ubuntu /var/www/directiva_agricola

# Crear directorio de logs
sudo mkdir -p /var/log/directiva_agricola
sudo chown ubuntu:ubuntu /var/log/directiva_agricola

# Configurar Nginx básico
sudo tee /etc/nginx/sites-available/directiva-agricola > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name $PUBLIC_IP $DOMAIN_NAME www.$DOMAIN_NAME;
    
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
NGINX_EOF

# Habilitar sitio
sudo ln -sf /etc/nginx/sites-available/directiva-agricola /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl enable nginx

echo "✅ Instalación básica completada"
EOF

# 6. Subir archivos a la instancia
echo "📤 Subiendo archivos a la instancia..."

# Usar la clave SSH ya creada en Lightsail
LIGHTSAIL_KEY_PATH="~/.ssh/directiva-lightsail-key"

# Esperar un poco para que la instancia esté completamente lista
sleep 30

# Subir archivos usando SCP
echo "📁 Subiendo archivos del proyecto..."
scp -i ~/.ssh/directiva-lightsail-key -o StrictHostKeyChecking=no -r \
    --exclude='venv/' --exclude='__pycache__/' --exclude='*.pyc' --exclude='.git/' \
    ./ ubuntu@$PUBLIC_IP:/var/www/directiva_agricola/

# Ejecutar instalación en la instancia
echo "🔧 Ejecutando instalación en la instancia..."
ssh -i ~/.ssh/directiva-lightsail-key -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP << EOF
    cd /var/www/directiva_agricola
    
    # Ejecutar script de instalación
    chmod +x install_lightsail.sh
    ./install_lightsail.sh
    
    # Crear entorno virtual
    python3.11 -m venv venv
    source venv/bin/activate
    
    # Instalar dependencias
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Configurar variables de entorno
    export AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID"
    export AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY"
    export SECRET_KEY="$(openssl rand -base64 32)"
    
    # Ejecutar migraciones
    python manage.py migrate --settings=directiva_agricola.settings_lightsail --database=administracion
    python manage.py migrate --settings=directiva_agricola.settings_lightsail --database=default
    
    # Recopilar archivos estáticos
    python manage.py collectstatic --noinput --settings=directiva_agricola.settings_lightsail
    
    # Crear servicio systemd para Gunicorn
    sudo tee /etc/systemd/system/directiva-agricola.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=Directiva Agricola Gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/directiva_agricola
Environment="PATH=/var/www/directiva_agricola/venv/bin"
Environment="AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"
Environment="AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"
Environment="SECRET_KEY=\$(openssl rand -base64 32)"
ExecStart=/var/www/directiva_agricola/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 2 directiva_agricola.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
SERVICE_EOF

    # Habilitar y iniciar servicio
    sudo systemctl daemon-reload
    sudo systemctl enable directiva-agricola
    sudo systemctl start directiva-agricola
    
    # Crear empresa de prueba
    python manage.py crear_empresa_postgresql \
        --razon-social="EMPRESA DEMOSTRACION" \
        --rfc="DEMO250901XXX" \
        --direccion="Dirección de prueba" \
        --telefono="555-1234" \
        --email="demo@directiva.com" \
        --ciclo-actual="2025" \
        --settings=directiva_agricola.settings_lightsail
EOF

# 7. Configurar SSL con Certbot
echo "🔒 Configurando SSL..."
ssh -i ~/.ssh/directiva-lightsail-key -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP << EOF
    # Configurar SSL (solo si tienes dominio configurado)
    if [ "$DOMAIN_NAME" != "directiva-agricola.com" ]; then
        sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --non-interactive --agree-tos --email $EMAIL
    fi
EOF

# Limpiar archivos temporales
rm -f bucket-policy.json

echo "✅ Despliegue en Lightsail completado!"
echo "🌐 Aplicación disponible en: http://$PUBLIC_IP"
echo "💰 Costo estimado: ~$15-20/mes (instancia + BD + S3)"
echo "📊 Estado del servicio: ssh -i ~/.ssh/directiva-lightsail-key ubuntu@$PUBLIC_IP 'sudo systemctl status directiva-agricola'"
echo "📝 Logs: ssh -i ~/.ssh/directiva-lightsail-key ubuntu@$PUBLIC_IP 'sudo journalctl -u directiva-agricola -f'"
echo "🔑 Usuario de prueba: supervisor"
echo "🔑 Contraseña: Directivasbmj1*"
echo ""
echo "📋 Próximos pasos:"
echo "1. Configurar DNS de tu dominio para apuntar a $PUBLIC_IP"
echo "2. Ejecutar: ssh -i ~/.ssh/directiva-lightsail-key ubuntu@$PUBLIC_IP 'sudo certbot --nginx -d $DOMAIN_NAME'"
echo "3. Verificar que la aplicación funcione correctamente"
