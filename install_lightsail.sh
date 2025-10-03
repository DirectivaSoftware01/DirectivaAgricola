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
    server_name 54.203.1.99 directiva-agricola.com www.directiva-agricola.com;
    
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
NGINX_EOF

# Habilitar sitio
sudo ln -sf /etc/nginx/sites-available/directiva-agricola /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl enable nginx

echo "✅ Instalación básica completada"
