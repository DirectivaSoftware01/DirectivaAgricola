#!/bin/bash

# Script de despliegue simplificado para AWS Elastic Beanstalk
# Uso: ./deploy_simple.sh

set -e

echo "🚀 Desplegando Directiva Agrícola en AWS Elastic Beanstalk"
echo ""

# Verificar que estemos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encontró manage.py. Ejecuta este script desde la raíz del proyecto."
    exit 1
fi

# Verificar que AWS CLI esté configurado
if ! python -m awscli sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS CLI no está configurado"
    echo "🔧 Configura AWS CLI primero con: ./configure_aws.sh"
    exit 1
fi

echo "✅ AWS CLI configurado correctamente"

# Verificar que EB CLI esté instalado
if ! command -v eb &> /dev/null; then
    echo "❌ Error: EB CLI no está instalado"
    echo "📥 Instala EB CLI con: pip install awsebcli"
    exit 1
fi

echo "✅ EB CLI instalado correctamente"

# Inicializar aplicación EB si no existe
if [ ! -d ".elasticbeanstalk" ]; then
    echo "📦 Inicializando aplicación Elastic Beanstalk..."
    eb init directiva-agricola --region us-west-2 --platform "Python 3.11"
fi

# Crear entorno si no existe
echo "🏗️  Verificando entorno..."
if ! eb list | grep -q "directiva-agricola-prod"; then
    echo "🌱 Creando entorno de producción..."
    eb create directiva-agricola-prod --instance-type t3.small --min-size 1 --max-size 3
else
    echo "🔄 Desplegando en entorno existente..."
    eb deploy directiva-agricola-prod
fi

echo ""
echo "✅ ¡Despliegue completado!"
echo "🌐 URL: $(eb status | grep CNAME | awk '{print $2}')"
echo ""
echo "📊 Para monitorear la aplicación:"
echo "   eb health"
echo "   eb logs"
echo ""
echo "🔧 Para abrir la aplicación:"
echo "   eb open"
