#!/bin/bash

# User data script para Lightsail
# Este script se ejecuta automáticamente cuando se crea la instancia

# Actualizar sistema
apt update && apt upgrade -y

# Instalar dependencias básicas
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
apt install -y postgresql-client libpq-dev build-essential nginx git
apt install -y certbot python3-certbot-nginx curl wget

# Crear usuario para la aplicación
useradd -m -s /bin/bash directiva
usermod -aG www-data directiva

# Crear directorios necesarios
mkdir -p /var/www/directiva_agricola
mkdir -p /var/log/directiva_agricola
chown -R directiva:www-data /var/www/directiva_agricola
chown -R directiva:www-data /var/log/directiva_agricola

# Configurar firewall básico
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configurar Nginx básico
cat > /etc/nginx/sites-available/directiva-agricola << 'EOF'
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
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
EOF

# Habilitar sitio
ln -sf /etc/nginx/sites-available/directiva-agricola /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
systemctl enable nginx

# Crear script de despliegue
cat > /home/ubuntu/deploy_app.sh << 'EOF'
#!/bin/bash

cd /var/www/directiva_agricola

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
cat > /tmp/directiva-agricola.service << 'SERVICE_EOF'
[Unit]
Description=Directiva Agricola Gunicorn daemon
After=network.target

[Service]
User=directiva
Group=www-data
WorkingDirectory=/var/www/directiva_agricola
Environment="PATH=/var/www/directiva_agricola/venv/bin"
Environment="AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"
Environment="AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"
Environment="SECRET_KEY=$(openssl rand -base64 32)"
ExecStart=/var/www/directiva_agricola/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 2 directiva_agricola.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
SERVICE_EOF

sudo mv /tmp/directiva-agricola.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable directiva-agricola
sudo systemctl start directiva-agricola

echo "✅ Aplicación desplegada correctamente"
EOF

chmod +x /home/ubuntu/deploy_app.sh

# Log de finalización
echo "✅ User data script completado" >> /var/log/user-data.log
date >> /var/log/user-data.log
