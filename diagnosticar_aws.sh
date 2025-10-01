#!/bin/bash

# Script para diagnosticar problemas de conectividad con AWS EC2

EC2_IP="54.212.80.37"
KEY_FILE="directiva-agricola-key.pem"

echo "🔍 Diagnosticando problemas de conectividad con AWS EC2..."
echo "📍 IP: $EC2_IP"
echo "🔑 Clave: $KEY_FILE"
echo ""

# Verificar que la clave existe
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ No se encontró el archivo de clave: $KEY_FILE"
    exit 1
fi

# Verificar permisos de la clave
chmod 600 "$KEY_FILE"
echo "✅ Permisos de clave configurados"

# Verificar formato de la clave
echo "🔍 Verificando formato de la clave SSH..."
if head -1 "$KEY_FILE" | grep -q "BEGIN.*PRIVATE KEY"; then
    echo "✅ Formato de clave SSH válido"
else
    echo "❌ Formato de clave SSH inválido"
    echo "💡 La clave debe comenzar con '-----BEGIN PRIVATE KEY-----'"
    exit 1
fi

# Verificar conectividad de red
echo "🌐 Verificando conectividad de red..."
if ping -c 3 $EC2_IP > /dev/null 2>&1; then
    echo "✅ La instancia responde a ping"
else
    echo "❌ La instancia no responde a ping"
    echo "💡 Posibles causas:"
    echo "   - La instancia no está ejecutándose"
    echo "   - El Security Group bloquea ICMP"
    echo "   - La IP ha cambiado"
fi

# Verificar puerto SSH
echo "🔐 Verificando puerto SSH (22)..."
if nc -z $EC2_IP 22 2>/dev/null; then
    echo "✅ Puerto SSH (22) está abierto"
else
    echo "❌ Puerto SSH (22) está cerrado o filtrado"
    echo "💡 Verificar Security Groups en AWS Console"
fi

# Verificar puerto HTTP
echo "🌐 Verificando puerto HTTP (80)..."
if nc -z $EC2_IP 80 2>/dev/null; then
    echo "✅ Puerto HTTP (80) está abierto"
else
    echo "ℹ️  Puerto HTTP (80) está cerrado (normal si no hay aplicación desplegada)"
fi

# Intentar conexión SSH con más detalles
echo "🔐 Intentando conexión SSH con detalles..."
ssh -i "$KEY_FILE" -o ConnectTimeout=10 -o StrictHostKeyChecking=no -v ubuntu@$EC2_IP 'echo "Conexión SSH exitosa"' 2>&1 | head -20

echo ""
echo "📋 Resumen del diagnóstico:"
echo "   1. Verificar en AWS Console que la instancia esté en estado 'running'"
echo "   2. Verificar Security Groups:"
echo "      - SSH (puerto 22) desde 0.0.0.0/0"
echo "      - HTTP (puerto 80) desde 0.0.0.0/0"
echo "      - RDS (puerto 5432) desde la instancia EC2"
echo "   3. Verificar que la clave SSH sea la correcta para esta instancia"
echo "   4. Verificar que el usuario sea 'ubuntu' (para Ubuntu) o 'ec2-user' (para Amazon Linux)"
