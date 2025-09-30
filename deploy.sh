#!/bin/bash

# Script de despliegue para AWS Elastic Beanstalk
# Uso: ./deploy.sh [environment-name]

set -e

# Configuración
APPLICATION_NAME="directiva-agricola"
REGION="us-west-2"
PLATFORM="Python 3.11"
ENVIRONMENT_NAME=${1:-"directiva-agricola-prod"}

echo "🚀 Iniciando despliegue de Directiva Agrícola en AWS Elastic Beanstalk"
echo "📋 Aplicación: $APPLICATION_NAME"
echo "🌍 Región: $REGION"
echo "🐍 Plataforma: $PLATFORM"
echo "🏗️  Entorno: $ENVIRONMENT_NAME"

# Verificar que EB CLI esté instalado
if ! command -v eb &> /dev/null; then
    echo "❌ Error: EB CLI no está instalado"
    echo "📥 Instala EB CLI con: pip install awsebcli"
    exit 1
fi

# Verificar que estemos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encontró manage.py. Ejecuta este script desde la raíz del proyecto."
    exit 1
fi

# Crear aplicación si no existe
echo "🔍 Verificando aplicación..."
if ! eb list 2>/dev/null | grep -q "$APPLICATION_NAME"; then
    echo "📦 Creando aplicación $APPLICATION_NAME..."
    eb init $APPLICATION_NAME --region $REGION --platform $PLATFORM
fi

# Crear entorno si no existe
echo "🏗️  Verificando entorno $ENVIRONMENT_NAME..."
if ! eb list | grep -q "$ENVIRONMENT_NAME"; then
    echo "🌱 Creando entorno $ENVIRONMENT_NAME..."
    eb create $ENVIRONMENT_NAME --instance-type t3.small --min-size 1 --max-size 3
else
    echo "🔄 Desplegando en entorno existente $ENVIRONMENT_NAME..."
    eb deploy $ENVIRONMENT_NAME
fi

echo "✅ Despliegue completado!"
echo "🌐 URL: $(eb status | grep CNAME | awk '{print $2}')"
echo "📊 Monitoreo: https://console.aws.amazon.com/elasticbeanstalk/home?region=$REGION#/applications"
