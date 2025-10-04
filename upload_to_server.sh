#!/bin/bash

# Script para subir archivos al servidor Hostinger VPS
# Ejecutar desde tu Mac

echo "📤 Subiendo archivos a Hostinger VPS..."

# Crear directorio temporal sin archivos innecesarios
echo "🗂️ Preparando archivos para subir..."
mkdir -p /tmp/directiva_upload
cp -r /Users/josemanuelbarba/Documents/Directiva\ Proyectos/DirectivaAgricola/* /tmp/directiva_upload/

# Remover archivos innecesarios
cd /tmp/directiva_upload
rm -rf venv/
rm -rf __pycache__/
rm -rf .git/
rm -rf *.pyc
rm -rf .DS_Store
rm -rf db.sqlite3
rm -rf staticfiles/
rm -rf media/debug_xml/

echo "📦 Archivos preparados en /tmp/directiva_upload"

# Subir archivos usando SCP
echo "🚀 Subiendo archivos al servidor..."
scp -i ~/.ssh/hostinger_key -r /tmp/directiva_upload/* root@89.116.51.217:/var/www/directiva_agricola/

# Limpiar archivos temporales
rm -rf /tmp/directiva_upload

echo "✅ Archivos subidos exitosamente!"
echo "🔗 Ahora conecta al servidor: ssh -i ~/.ssh/hostinger_key root@89.116.51.217"
