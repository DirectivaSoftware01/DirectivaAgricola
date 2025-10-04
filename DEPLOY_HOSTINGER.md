# 🚀 Despliegue en Hostinger VPS

Esta guía te ayudará a desplegar **Directiva Agrícola** en un VPS de Hostinger.

## 📋 Requisitos Previos

1. **VPS de Hostinger** con Ubuntu 20.04/22.04
2. **Dominio** configurado (opcional, pero recomendado)
3. **Acceso SSH** al servidor
4. **Repositorio Git** con tu código

## 💰 Costos Estimados en Hostinger

| Plan VPS | CPU | RAM | Almacenamiento | Precio/mes |
|----------|-----|-----|----------------|------------|
| VPS 1 | 1 vCPU | 1 GB | 20 GB SSD | ~$3.99 |
| VPS 2 | 1 vCPU | 2 GB | 40 GB SSD | ~$5.99 |
| VPS 3 | 2 vCPU | 4 GB | 80 GB SSD | ~$9.99 |

**Recomendación:** VPS 2 o VPS 3 para tu aplicación Django.

## 🛠️ Pasos de Despliegue

### 1. Preparar el Repositorio

```bash
# En tu máquina local
git add .
git commit -m "Preparar para despliegue en Hostinger"
git push origin main
```

### 2. Conectar al VPS

```bash
# Conectar por SSH
ssh root@tu-ip-del-vps

# O si tienes usuario específico
ssh usuario@tu-ip-del-vps
```

### 3. Ejecutar Script de Despliegue

```bash
# Descargar y ejecutar el script
wget https://raw.githubusercontent.com/tu-usuario/DirectivaAgricola/main/deploy_hostinger.sh
chmod +x deploy_hostinger.sh
sudo ./deploy_hostinger.sh
```

### 4. Configuración Manual (si es necesario)

Si el script automático no funciona, sigue estos pasos:

#### Instalar Dependencias

```bash
# Actualizar sistema
apt update && apt upgrade -y

# Instalar Python y dependencias
apt install -y python3 python3-pip python3-venv python3-dev
apt install -y nginx mysql-server mysql-client
apt install -y git curl wget unzip
apt install -y libmysqlclient-dev pkg-config
apt install -y redis-server supervisor
apt install -y certbot python3-certbot-nginx
```

#### Configurar Base de Datos

```bash
# Configurar MySQL
mysql_secure_installation

# Crear base de datos
mysql -u root -p
```

```sql
CREATE DATABASE directiva_agricola CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'directiva_user'@'localhost' IDENTIFIED BY 'tu_password_seguro';
GRANT ALL PRIVILEGES ON directiva_agricola.* TO 'directiva_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### Configurar la Aplicación

```bash
# Crear directorio
mkdir -p /var/www/directiva_agricola
cd /var/www/directiva_agricola

# Clonar repositorio
git clone https://github.com/tu-usuario/DirectivaAgricola.git .

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install gunicorn mysqlclient

# Configurar variables de entorno
cp .env.example .env
nano .env
```

#### Configurar Gunicorn

```bash
# Crear servicio systemd
nano /etc/systemd/system/directiva-agricola.service
```

Contenido del archivo:
```ini
[Unit]
Description=Directiva Agrícola Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/directiva_agricola
Environment="PATH=/var/www/directiva_agricola/venv/bin"
ExecStart=/var/www/directiva_agricola/venv/bin/gunicorn --workers 3 --bind unix:/var/www/directiva_agricola/directiva_agricola.sock directiva_agricola.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### Configurar Nginx

```bash
# Crear configuración de sitio
nano /etc/nginx/sites-available/directiva_agricola
```

Usar el contenido del archivo `nginx_config.conf` incluido en el proyecto.

```bash
# Habilitar sitio
ln -s /etc/nginx/sites-available/directiva_agricola /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# Probar configuración
nginx -t

# Reiniciar servicios
systemctl daemon-reload
systemctl enable directiva-agricola
systemctl start directiva-agricola
systemctl restart nginx
```

#### Configurar SSL

```bash
# Instalar certificado SSL
certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

## 🔧 Comandos Útiles

### Gestión de Servicios

```bash
# Ver estado de la aplicación
systemctl status directiva-agricola

# Ver logs de la aplicación
journalctl -u directiva-agricola -f

# Reiniciar aplicación
systemctl restart directiva-agricola

# Ver estado de Nginx
systemctl status nginx

# Reiniciar Nginx
systemctl restart nginx
```

### Gestión de la Aplicación

```bash
# Activar entorno virtual
cd /var/www/directiva_agricola
source venv/bin/activate

# Ejecutar migraciones
python manage.py migrate --settings=directiva_agricola.settings_production

# Recopilar archivos estáticos
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production

# Crear superusuario
python manage.py createsuperuser --settings=directiva_agricola.settings_production
```

### Actualización de Código

```bash
# Actualizar desde Git
cd /var/www/directiva_agricola
git pull origin main

# Activar entorno virtual
source venv/bin/activate

# Instalar nuevas dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate --settings=directiva_agricola.settings_production

# Recopilar archivos estáticos
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production

# Reiniciar aplicación
systemctl restart directiva-agricola
```

## 🔒 Configuración de Seguridad

### Firewall

```bash
# Configurar UFW
ufw allow ssh
ufw allow 'Nginx Full'
ufw enable
```

### Variables de Entorno

Asegúrate de configurar estas variables en `/var/www/directiva_agricola/.env`:

```bash
SECRET_KEY=tu_secret_key_muy_seguro
DEBUG=False
DB_NAME=directiva_agricola
DB_USER=directiva_user
DB_PASSWORD=tu_password_muy_seguro
DB_HOST=localhost
DB_PORT=3306
```

## 📊 Monitoreo

### Logs

```bash
# Logs de la aplicación
tail -f /var/log/directiva_agricola/django.log

# Logs de Nginx
tail -f /var/log/nginx/directiva_agricola_access.log
tail -f /var/log/nginx/directiva_agricola_error.log

# Logs de Gunicorn
tail -f /var/log/directiva_agricola/gunicorn_access.log
tail -f /var/log/directiva_agricola/gunicorn_error.log
```

### Recursos del Sistema

```bash
# Uso de CPU y memoria
htop

# Espacio en disco
df -h

# Uso de memoria
free -h
```

## 🆘 Solución de Problemas

### Error 502 Bad Gateway

```bash
# Verificar que Gunicorn esté ejecutándose
systemctl status directiva-agricola

# Verificar permisos del socket
ls -la /var/www/directiva_agricola/directiva_agricola.sock

# Reiniciar servicios
systemctl restart directiva-agricola
systemctl restart nginx
```

### Error de Base de Datos

```bash
# Verificar conexión a MySQL
mysql -u directiva_user -p directiva_agricola

# Verificar configuración de Django
cd /var/www/directiva_agricola
source venv/bin/activate
python manage.py dbshell --settings=directiva_agricola.settings_production
```

### Error de Archivos Estáticos

```bash
# Recopilar archivos estáticos
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production

# Verificar permisos
chown -R www-data:www-data /var/www/directiva_agricola/static/
```

## 📞 Soporte

Si tienes problemas con el despliegue:

1. Revisa los logs de error
2. Verifica la configuración de servicios
3. Consulta la documentación de Hostinger
4. Contacta al soporte técnico

## 🎉 ¡Listo!

Una vez completado el despliegue, tu aplicación estará disponible en:
- **HTTP:** http://tu-ip-del-vps
- **HTTPS:** https://tu-dominio.com (si configuraste SSL)

¡Felicidades! Tu aplicación Django está ahora ejecutándose en producción. 🚀
