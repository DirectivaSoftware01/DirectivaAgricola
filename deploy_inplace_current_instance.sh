#!/bin/bash

set -euo pipefail

# Despliegue in-place sobre la instancia actual con IP pública 54.212.80.37
# Requiere acceso SSH via PEM local.

REGION="us-west-2"
PUBLIC_IP="54.212.80.37"
KEY_PATH="/Users/josemanuelbarba/Documents/Directiva Proyectos/DirectivaAgricola/directiva-agricola-key.pem"
APP_DIR="/var/www/directiva_agricola"
LOCAL_PROVISION="/Users/josemanuelbarba/Documents/Directiva Proyectos/DirectivaAgricola/scripts/provision_al2023_arm64_pyenv.sh"

DOMAIN_ROOT="agricola.directiva.mx"
DOMAIN_WWW="www.agricola.directiva.mx"

export DS_DB_NAME="directiva_agricola"
export RDS_ADMIN_DB_NAME="directiva_administracion"
export RDS_USERNAME="postgres"
export RDS_PASSWORD="Directiva2024!"
export RDS_HOSTNAME="directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com"
export RDS_PORT="5432"

[ -f "$KEY_PATH" ] || { echo "No existe PEM en $KEY_PATH"; exit 1; }
[ -f "$LOCAL_PROVISION" ] || { echo "No existe $LOCAL_PROVISION"; exit 1; }

echo "==> Copiando provisionador..."
scp -o StrictHostKeyChecking=no -i "$KEY_PATH" "$LOCAL_PROVISION" ec2-user@"$PUBLIC_IP":/home/ec2-user/

echo "==> Ejecutando provisionador..."
ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@"$PUBLIC_IP" "chmod +x provision_al2023_arm64_pyenv.sh && sudo ./provision_al2023_arm64_pyenv.sh"

echo "==> Configurando servicios y HTTPS..."
ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@"$PUBLIC_IP" 'bash -lc "
set -e
cd '"$APP_DIR"'

sudo tee /etc/systemd/system/directiva-agricola.service > /dev/null <<EOL
[Unit]
Description=Directiva Agricola Gunicorn daemon
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory='"$APP_DIR"'
Environment=PATH='"$APP_DIR"'/venv/bin
Environment=DS_DB_NAME='"$DS_DB_NAME"'
Environment=RDS_ADMIN_DB_NAME='"$RDS_ADMIN_DB_NAME"'
Environment=RDS_USERNAME='"$RDS_USERNAME"'
Environment=RDS_PASSWORD='"$RDS_PASSWORD"'
Environment=RDS_HOSTNAME='"$RDS_HOSTNAME"'
Environment=RDS_PORT='"$RDS_PORT"'
Environment=SECRET_KEY=directiva-secret-key-2024-production
ExecStart='"$APP_DIR"'/venv/bin/gunicorn --config gunicorn.conf.py directiva_agricola.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL

if [ ! -f gunicorn.conf.py ]; then
  cat > gunicorn.conf.py <<GCONF
bind = \"127.0.0.1:8000\"
workers = 3
worker_class = \"sync\"
timeout = 30
keepalive = 2
preload_app = True
GCONF
fi

cat > directiva_agricola/settings_production.py <<'PY'
import os
from .settings import *
DEBUG = False
ALLOWED_HOSTS = ['"$PUBLIC_IP"', '"$DOMAIN_ROOT"', '"$DOMAIN_WWW"']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DS_DB_NAME', 'directiva_agricola'),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', ''),
        'HOST': os.environ.get('RDS_HOSTNAME', ''),
        'PORT': os.environ.get('RDS_PORT', '5432'),
        'ATOMIC_REQUESTS': True,
        'TIME_ZONE': 'America/Mexico_City',
    },
    'administracion': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('RDS_ADMIN_DB_NAME', 'directiva_administracion'),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', ''),
        'HOST': os.environ.get('RDS_HOSTNAME', ''),
        'PORT': os.environ.get('RDS_PORT', '5432'),
        'ATOMIC_REQUESTS': True,
        'TIME_ZONE': 'America/Mexico_City',
    }
}
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
SECRET_KEY = os.environ.get('SECRET_KEY', 'directiva-secret-key-2024-production')
PY

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate --settings=directiva_agricola.settings_production --database=administracion
python manage.py migrate --settings=directiva_agricola.settings_production --database=default
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production

sudo dnf install -y snapd || sudo yum install -y snapd || true
sudo systemctl enable --now snapd.socket || true
sudo ln -s /var/lib/snapd/snap /snap || true
sudo snap install core || true; sudo snap refresh core || true
sudo snap install --classic certbot || true
sudo ln -sf /snap/bin/certbot /usr/bin/certbot || true

sudo mkdir -p /var/www/letsencrypt
sudo chown ec2-user:ec2-user /var/www/letsencrypt

sudo tee /etc/nginx/conf.d/directiva-agricola.conf > /dev/null <<NGHTTP
server {
    listen 80;
    server_name '"$DOMAIN_ROOT"' '"$DOMAIN_WWW"' '"$PUBLIC_IP"';
    client_max_body_size 100M;
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }
    location /static/ {
        alias '"$APP_DIR"'/staticfiles/;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }
    location /media/ {
        alias '"$APP_DIR"'/media/;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGHTTP

sudo nginx -t && sudo systemctl reload nginx

sudo certbot certonly --webroot -w /var/www/letsencrypt -d '"$DOMAIN_ROOT"' -d '"$DOMAIN_WWW"' --agree-tos -m admin@'"$DOMAIN_ROOT"' --non-interactive --no-eff-email || true

sudo tee /etc/nginx/conf.d/directiva-agricola-ssl.conf > /dev/null <<NGSSL
server {
    listen 80;
    server_name '"$DOMAIN_ROOT"' '"$DOMAIN_WWW"' '"$PUBLIC_IP"';
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name '"$DOMAIN_ROOT"' '"$DOMAIN_WWW"';
    ssl_certificate /etc/letsencrypt/live/'"$DOMAIN_ROOT"'/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/'"$DOMAIN_ROOT"'/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    client_max_body_size 100M;
    location /static/ {
        alias '"$APP_DIR"'/staticfiles/;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }
    location /media/ {
        alias '"$APP_DIR"'/media/;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGSSL

sudo nginx -t && sudo systemctl reload nginx

sudo systemctl daemon-reload
sudo systemctl enable --now directiva-agricola
sudo systemctl restart nginx
"'

echo "==> Verificación http/https:"
curl -I --max-time 5 "http://$PUBLIC_IP" || true
curl -I --max-time 5 "https://$DOMAIN_ROOT" || true

echo "==> Despliegue in-place terminado."


