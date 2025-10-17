#!/bin/bash

set -euo pipefail

# Provisioning limpio para Amazon Linux 2023 (ARM64/x86_64)
# - Usa Python del sistema (python3.11 en AL2023)
# - Instala dependencias del sistema, crea venv, instala requerimientos
# - Configura Nginx básico

APP_DIR="/var/www/directiva_agricola"

echo "📦 Actualizando sistema..."
sudo dnf -y update || true

echo "🛠️  Instalando dependencias del sistema..."
sudo dnf -y install --allowerasing git curl gcc gcc-c++ make patch \
  zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel \
  openssl openssl-devel tk tk-devel libffi-devel xz xz-devel \
  findutils tar nginx || true

# Postgres client headers (para psycopg2 si se compila)
sudo dnf -y install --allowerasing libpq-devel postgresql15 || true

echo "📁 Preparando directorio de la app"
sudo mkdir -p "$APP_DIR"
sudo chown ec2-user:ec2-user "$APP_DIR"

echo "📥 Clonando repositorio si no existe..."
sudo -u ec2-user bash -lc "cd $APP_DIR && if [ ! -d .git ]; then git clone https://github.com/DirectivaSoftware01/DirectivaAgricola.git .; fi"

echo "🐍 Creando entorno virtual con Python del sistema"
sudo dnf -y install python3 python3-pip python3-devel || true
sudo -u ec2-user bash -lc "cd $APP_DIR && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip wheel setuptools"

echo "📚 Instalando requerimientos"
sudo -u ec2-user bash -lc "cd $APP_DIR && source venv/bin/activate && pip install -r requirements.txt"

echo "🌐 Configurando Nginx básico (HTTP)"
sudo tee /etc/nginx/conf.d/directiva-agricola.conf > /dev/null <<'NGINX'
server {
    listen 80;
    server_name _;
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
    }
}
NGINX

sudo systemctl enable --now nginx || true
echo "✅ Provisioning base completado"


