#!/bin/bash

# Script de despliegue para Hostinger VPS
# Ejecutar en el servidor VPS de Hostinger

set -e  # Salir si hay algún error

echo "🚀 Iniciando despliegue de Directiva Agrícola en Hostinger VPS..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables de configuración
PROJECT_NAME="directiva_agricola"
PROJECT_DIR="/var/www/$PROJECT_NAME"
VENV_DIR="/var/www/$PROJECT_NAME/venv"
REPO_URL="https://github.com/tu-usuario/DirectivaAgricola.git"  # Cambiar por tu repositorio
DOMAIN="89.116.51.217"  # IP del VPS de Hostinger

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

print_status "Actualizando sistema..."
apt update && apt upgrade -y

print_status "Instalando dependencias del sistema..."
apt install -y python3 python3-pip python3-venv python3-dev \
    nginx mysql-server mysql-client \
    git curl wget unzip \
    libmysqlclient-dev pkg-config \
    redis-server supervisor \
    certbot python3-certbot-nginx

print_status "Configurando MySQL..."
mysql -e "CREATE DATABASE IF NOT EXISTS directiva_agricola CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS 'directiva_user'@'localhost' IDENTIFIED BY 'tu_password_seguro';"
mysql -e "GRANT ALL PRIVILEGES ON directiva_agricola.* TO 'directiva_user'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

print_status "Configurando Redis..."
systemctl enable redis-server
systemctl start redis-server

print_status "Creando directorio del proyecto..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Si es la primera vez, clonar el repositorio
if [ ! -d ".git" ]; then
    print_status "Clonando repositorio..."
    git clone $REPO_URL .
else
    print_status "Actualizando código desde Git..."
    git pull origin main
fi

print_status "Creando entorno virtual..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

print_status "Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn mysqlclient

print_status "Configurando variables de entorno..."
cat > .env << EOF
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
DB_NAME=directiva_agricola
DB_USER=directiva_user
DB_PASSWORD=tu_password_seguro
DB_HOST=localhost
DB_PORT=3306
EMAIL_HOST=smtp.hostinger.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu_email@tu-dominio.com
EMAIL_HOST_PASSWORD=tu_password_email
DEFAULT_FROM_EMAIL=noreply@$DOMAIN
EOF

print_status "Ejecutando migraciones de base de datos..."
python manage.py migrate --settings=directiva_agricola.settings_production

print_status "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production

print_status "Creando superusuario..."
python manage.py createsuperuser --settings=directiva_agricola.settings_production || true

print_status "Configurando permisos..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

print_status "Configurando Gunicorn..."
cat > /etc/systemd/system/directiva-agricola.service << EOF
[Unit]
Description=Directiva Agrícola Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:$PROJECT_DIR/directiva_agricola.sock directiva_agricola.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

print_status "Configurando Nginx..."
cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root $PROJECT_DIR;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        root $PROJECT_DIR;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/directiva_agricola.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Habilitar el sitio
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

print_status "Probando configuración de Nginx..."
nginx -t

print_status "Iniciando servicios..."
systemctl daemon-reload
systemctl enable directiva-agricola
systemctl start directiva-agricola
systemctl restart nginx

print_status "Configurando SSL con Let's Encrypt..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

print_status "Configurando logrotate..."
cat > /etc/logrotate.d/directiva-agricola << EOF
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload directiva-agricola
    endscript
}
EOF

print_status "✅ Despliegue completado exitosamente!"
print_status "🌐 Tu aplicación está disponible en: https://$DOMAIN"
print_status "📊 Para monitorear: systemctl status directiva-agricola"
print_status "📝 Para ver logs: journalctl -u directiva-agricola -f"

echo ""
print_warning "IMPORTANTE:"
print_warning "1. Cambia las contraseñas en el archivo .env"
print_warning "2. Configura tu dominio DNS para apuntar a esta IP"
print_warning "3. Actualiza la URL del repositorio en este script"
print_warning "4. Revisa la configuración de email"
