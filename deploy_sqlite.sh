#!/bin/bash

echo "🚀 Desplegando Directiva Agrícola con SQLite (Desarrollo)"

# Verificar que EB CLI esté instalado
if ! command -v eb &> /dev/null; then
    echo "❌ EB CLI no está instalado. Instalando..."
    pip install awsebcli
fi

# Inicializar EB si no existe
if [ ! -d ".elasticbeanstalk" ]; then
    echo "📦 Inicializando Elastic Beanstalk..."
    eb init directiva-agricola --platform python-3.11 --region us-west-2
fi

# Crear ambiente si no existe
if ! eb list | grep -q "directiva-agricola-env"; then
    echo "🌍 Creando ambiente de producción..."
    eb create directiva-agricola-env --instance-type t3.micro --single-instance
else
    echo "✅ Ambiente ya existe"
fi

# Desplegar aplicación
echo "🚀 Desplegando aplicación..."
eb deploy

echo "✅ Despliegue completado!"
echo "🌐 URL de la aplicación:"
eb status | grep "CNAME"


