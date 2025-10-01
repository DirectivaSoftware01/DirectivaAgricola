#!/bin/bash

# Script para verificar conectividad con AWS EC2

EC2_IP="54.212.80.37"
KEY_FILE="directiva-agricola-key.pem"

echo "🔍 Verificando conectividad con AWS EC2..."
echo "📍 IP: $EC2_IP"
echo "🔑 Clave: $KEY_FILE"

# Verificar que la clave existe
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ No se encontró el archivo de clave: $KEY_FILE"
    exit 1
fi

# Verificar permisos de la clave
chmod 600 "$KEY_FILE"
echo "✅ Permisos de clave configurados"

# Verificar conectividad SSH
echo "🔐 Probando conexión SSH..."
if ssh -i "$KEY_FILE" -o ConnectTimeout=10 -o StrictHostKeyChecking=no ubuntu@$EC2_IP 'echo "Conexión SSH exitosa"' 2>/dev/null; then
    echo "✅ Conexión SSH exitosa"
else
    echo "❌ Error de conexión SSH"
    echo "💡 Posibles soluciones:"
    echo "   1. Verificar que la instancia EC2 esté ejecutándose"
    echo "   2. Verificar que el Security Group permita SSH (puerto 22)"
    echo "   3. Verificar que la clave SSH sea correcta"
    echo "   4. Verificar que el usuario sea 'ubuntu'"
    exit 1
fi

# Verificar conectividad HTTP
echo "🌐 Probando conectividad HTTP..."
if curl -s --connect-timeout 10 http://$EC2_IP > /dev/null; then
    echo "✅ Conectividad HTTP exitosa"
else
    echo "ℹ️  HTTP no disponible (normal si la aplicación no está desplegada)"
fi

# Verificar conectividad RDS
echo "🗄️ Probando conectividad RDS..."
if nc -z directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com 5432 2>/dev/null; then
    echo "✅ Conectividad RDS exitosa"
else
    echo "❌ Error de conectividad RDS"
    echo "💡 Verificar Security Groups de RDS"
fi

echo ""
echo "🎯 Verificación completada"
echo "📋 Para proceder con el despliegue:"
echo "   ssh -i $KEY_FILE ubuntu@$EC2_IP"
echo "   curl -s https://raw.githubusercontent.com/DirectivaSoftware01/DirectivaAgricola/main/deploy_ec2_direct.sh | bash"
