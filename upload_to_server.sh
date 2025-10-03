#!/bin/bash

# Script para subir archivos al servidor EC2
# Uso: ./upload_to_server.sh

set -e

SERVER_IP="35.94.62.23"
KEY_FILE="directiva-key.pem"
USER="ubuntu"

echo "🚀 Subiendo archivos al servidor EC2..."

# Verificar que la clave SSH existe
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Error: No se encontró el archivo de clave SSH: $KEY_FILE"
    exit 1
fi

# Crear directorio en el servidor
echo "📁 Creando directorio en el servidor..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "$USER@$SERVER_IP" "mkdir -p ~/directiva-agricola"

# Subir archivos del proyecto
echo "📤 Subiendo archivos del proyecto..."
scp -i "$KEY_FILE" -o StrictHostKeyChecking=no -r \
    . "$USER@$SERVER_IP:~/directiva-agricola/"

# Hacer ejecutables los scripts
echo "🔧 Configurando permisos de scripts..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "$USER@$SERVER_IP" "
    cd ~/directiva-agricola
    chmod +x deploy_ec2.sh setup_ssl.sh
"

echo "✅ Archivos subidos exitosamente!"
echo ""
echo "🌐 Servidor: $SERVER_IP"
echo "📁 Directorio: ~/directiva-agricola"
echo ""
echo "🔧 Para conectarte al servidor:"
echo "   ssh -i $KEY_FILE $USER@$SERVER_IP"
echo ""
echo "🚀 Para desplegar la aplicación:"
echo "   ssh -i $KEY_FILE $USER@$SERVER_IP 'cd ~/directiva-agricola && ./deploy_ec2.sh'"
echo ""
