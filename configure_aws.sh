#!/bin/bash

# Script simplificado para configurar AWS CLI
# Uso: ./configure_aws.sh

echo "🔧 Configurando AWS CLI para Directiva Agrícola"
echo ""

# Verificar si ya está configurado
if python -m awscli sts get-caller-identity &> /dev/null; then
    echo "✅ AWS CLI ya está configurado"
    python -m awscli sts get-caller-identity
    echo ""
    echo "¿Quieres continuar con la creación de recursos? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo "❌ Configuración cancelada"
        exit 0
    fi
else
    echo "❌ AWS CLI no está configurado"
    echo ""
    echo "📋 Necesitas configurar tus credenciales de AWS:"
    echo "   1. Ve a AWS Console → IAM → Users → Tu usuario → Security credentials"
    echo "   2. Crea un Access Key si no tienes una"
    echo "   3. Ejecuta estos comandos con tus credenciales:"
    echo ""
    echo "   python -m awscli configure set aws_access_key_id TU_ACCESS_KEY_ID"
    echo "   python -m awscli configure set aws_secret_access_key TU_SECRET_ACCESS_KEY"
    echo "   python -m awscli configure set default.region us-west-2"
    echo "   python -m awscli configure set default.output json"
    echo ""
    echo "   Luego ejecuta: ./configure_aws.sh"
    exit 1
fi

echo "🚀 Creando recursos AWS..."
./setup_aws_resources.sh
