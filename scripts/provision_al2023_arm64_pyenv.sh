#!/bin/bash

set -euo pipefail

# Este script prepara una instancia Amazon Linux 2023 ARM64 (t4g.micro - Free Tier)
# Instalando pyenv, Python 3.13.7, y dependencias del proyecto Django.
# Úsalo como user-data o ejecutándolo manualmente como ec2-user.

PYTHON_VERSION="3.13.7"
APP_DIR="/var/www/directiva_agricola"

echo "📦 Actualizando sistema..."
sudo dnf update -y

echo "🛠️  Instalando dependencias de compilación y runtime..."
sudo dnf install -y git curl gcc gcc-c++ make patch zlib-devel bzip2 bzip2-devel \
  readline-devel sqlite sqlite-devel openssl openssl-devel tk tk-devel libffi-devel \
  xz xz-devel findutils tar nginx || true

# PostgreSQL dev headers (AL2023 suele usar postgresql15/libpq-devel)
sudo dnf install -y postgresql15 postgresql15-devel libpq-devel || \
sudo dnf install -y postgresql postgresql-devel || true

echo "👤 Instalando pyenv para ec2-user..."
if [ ! -d "/home/ec2-user/.pyenv" ]; then
  sudo -u ec2-user bash -lc "git clone https://github.com/pyenv/pyenv.git ~/.pyenv"
fi

echo "🐍 Instalando Python ${PYTHON_VERSION} con pyenv (ruta absoluta)..."
sudo -u ec2-user bash -lc "~/.pyenv/bin/pyenv install -s ${PYTHON_VERSION} && ~/.pyenv/bin/pyenv global ${PYTHON_VERSION} && ~/.pyenv/bin/pyenv rehash"

echo "📂 Creando directorio de la app: ${APP_DIR}"
sudo mkdir -p "${APP_DIR}"
sudo chown ec2-user:ec2-user "${APP_DIR}"

echo "📥 Clonando repositorio (ajusta si ya está copiado)..."
sudo -u ec2-user bash -lc "cd ${APP_DIR} && if [ ! -d .git ]; then git clone https://github.com/DirectivaSoftware01/DirectivaAgricola.git .; fi"

echo "📦 Creando y activando venv con Python ${PYTHON_VERSION}"
sudo -u ec2-user bash -lc "cd ${APP_DIR} && ~/.pyenv/versions/${PYTHON_VERSION}/bin/python -m venv venv && source venv/bin/activate && pip install --upgrade pip wheel setuptools"

echo "📚 Instalando dependencias del proyecto"
sudo -u ec2-user bash -lc "cd ${APP_DIR} && source venv/bin/activate && pip install -r requirements.txt"

echo "⚙️  Configurando permisos y Nginx básico"
sudo mkdir -p /var/log/directiva_agricola
sudo chown ec2-user:ec2-user /var/log/directiva_agricola

sudo tee /etc/nginx/conf.d/directiva-agricola.conf > /dev/null <<'NGINX'
server {
    listen 80;
    server_name _;
    client_max_body_size 50M;
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

sudo systemctl enable --now nginx

echo "✅ Provisioning completado. Siguiente paso: configurar Gunicorn y variables de entorno."


