#!/bin/bash

# Script de despliegue para Directiva Agrícola
# Este script se ejecuta en el servidor EC2

set -e

echo "🚀 Iniciando despliegue de Directiva Agrícola..."

# Variables de entorno
APP_DIR="/opt/directiva-agricola"
BACKUP_DIR="/opt/backups/directiva-agricola"
LOG_FILE="/var/log/directiva-agricola/deploy.log"

# Crear directorio de logs si no existe
sudo mkdir -p /var/log/directiva-agricola
sudo chown ec2-user:ec2-user /var/log/directiva-agricola

# Función para logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "Iniciando proceso de despliegue"

# 1. Crear backup del código actual
log "Creando backup del código actual..."
sudo mkdir -p $BACKUP_DIR
sudo cp -r $APP_DIR $BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S)

# 2. Detener servicios
log "Deteniendo servicios..."
sudo systemctl stop directiva || true

# 3. Actualizar código
log "Actualizando código desde GitHub..."
cd /tmp
rm -rf directiva-agricola
git clone https://github.com/$GITHUB_REPOSITORY.git directiva-agricola

# 4. Verificar que el código se descargó correctamente
if [ ! -d "directiva-agricola" ]; then
    log "ERROR: No se pudo descargar el código desde GitHub"
    exit 1
fi

# 5. Actualizar archivos de la aplicación
log "Actualizando archivos de la aplicación..."
sudo cp -r /tmp/directiva-agricola/* $APP_DIR/
sudo chown -R directiva:directiva $APP_DIR/

# 6. Instalar dependencias
log "Instalando dependencias de Python..."
cd $APP_DIR
sudo pip3 install -r requirements.txt

# 7. Ejecutar migraciones
log "Ejecutando migraciones de la base de datos principal..."
sudo -u directiva RDS_HOSTNAME=$RDS_HOSTNAME \
    RDS_DB_NAME=$RDS_DB_NAME \
    RDS_ADMIN_DB_NAME=$RDS_ADMIN_DB_NAME \
    RDS_USERNAME=$RDS_USERNAME \
    RDS_PASSWORD=$RDS_PASSWORD \
    RDS_PORT=$RDS_PORT \
    python3 manage.py migrate --settings=directiva_agricola.settings_simple

log "Ejecutando migraciones de la base de datos de administración..."
sudo -u directiva RDS_HOSTNAME=$RDS_HOSTNAME \
    RDS_DB_NAME=$RDS_DB_NAME \
    RDS_ADMIN_DB_NAME=$RDS_ADMIN_DB_NAME \
    RDS_USERNAME=$RDS_USERNAME \
    RDS_PASSWORD=$RDS_PASSWORD \
    RDS_PORT=$RDS_PORT \
    python3 manage.py migrate --database=administracion --settings=directiva_agricola.settings_simple

# 8. Recopilar archivos estáticos
log "Recopilando archivos estáticos..."
sudo -u directiva python3 manage.py collectstatic --noinput --settings=directiva_agricola.settings_simple

# 9. Reiniciar servicios
log "Reiniciando servicios..."
sudo systemctl start directiva
sudo systemctl reload nginx

# 10. Verificar estado de los servicios
log "Verificando estado de los servicios..."
if sudo systemctl is-active --quiet directiva; then
    log "✅ Servicio directiva está activo"
else
    log "❌ ERROR: Servicio directiva no está activo"
    sudo systemctl status directiva
    exit 1
fi

if sudo systemctl is-active --quiet nginx; then
    log "✅ Servicio nginx está activo"
else
    log "❌ ERROR: Servicio nginx no está activo"
    sudo systemctl status nginx
    exit 1
fi

# 11. Verificar que la aplicación responde
log "Verificando que la aplicación responde..."
sleep 5
if curl -f -s http://localhost:8000 > /dev/null; then
    log "✅ Aplicación responde correctamente"
else
    log "❌ ERROR: La aplicación no responde"
    exit 1
fi

log "🎉 Despliegue completado exitosamente"

# 12. Limpiar backups antiguos (mantener solo los últimos 5)
log "Limpiando backups antiguos..."
cd $BACKUP_DIR
ls -t | tail -n +6 | xargs -r rm -rf

log "Despliegue finalizado"
