#!/bin/bash

# Script para iniciar el servidor Django con el entorno virtual activado
# Uso: ./start_server.sh

echo "🚀 Iniciando servidor Django de Directiva Agrícola..."

# Navegar al directorio del proyecto
cd "$(dirname "$0")"

# Activar el entorno virtual
echo "📦 Activando entorno virtual..."
source venv/bin/activate

# Verificar que el entorno virtual esté activado
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Entorno virtual activado: $VIRTUAL_ENV"
else
    echo "❌ Error: No se pudo activar el entorno virtual"
    exit 1
fi

# Verificar que las dependencias estén instaladas
echo "🔍 Verificando dependencias..."
pip list | grep -q qrcode
if [ $? -eq 0 ]; then
    echo "✅ Dependencia qrcode encontrada"
else
    echo "⚠️  Instalando dependencias faltantes..."
    pip install -r requirements.txt
fi

# Iniciar el servidor Django
echo "🌐 Iniciando servidor Django en http://localhost:8000"
echo "💡 Presiona Ctrl+C para detener el servidor"
echo ""

python manage.py runserver
