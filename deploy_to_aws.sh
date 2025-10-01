#!/bin/bash

# Script para desplegar en AWS EC2
# IP de la instancia EC2
EC2_IP="54.212.80.37"

echo "🚀 Iniciando despliegue en AWS EC2..."

# Verificar que tenemos acceso SSH
echo "🔐 Verificando acceso SSH..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes ubuntu@$EC2_IP exit 2>/dev/null; then
    echo "❌ No se puede conectar a la instancia EC2"
    echo "💡 Asegúrate de que:"
    echo "   1. La instancia esté ejecutándose"
    echo "   2. Tengas configurada la clave SSH"
    echo "   3. El Security Group permita conexiones SSH (puerto 22)"
    echo "   4. El Security Group permita conexiones HTTP (puerto 80)"
    echo "   5. El Security Group permita conexiones a RDS (puerto 5432)"
    exit 1
fi

echo "✅ Conexión SSH exitosa"

# Ejecutar script de despliegue en la instancia
echo "📥 Ejecutando despliegue en EC2..."
ssh ubuntu@$EC2_IP << 'EOF'
    # Descargar y ejecutar script de despliegue
    curl -s https://raw.githubusercontent.com/DirectivaSoftware01/DirectivaAgricola/main/deploy_ec2_direct.sh | bash
EOF

echo "✅ Despliegue completado!"
echo "🌐 Aplicación disponible en: http://54.212.80.37"
echo "🔑 Usuario administrador: admin / Directiva2024!"
echo "🔑 Usuario supervisor: supervisor / Directivasbmj1*"
echo ""
echo "📋 Comandos útiles:"
echo "   ssh ubuntu@54.212.80.37"
echo "   sudo systemctl status directiva-agricola"
echo "   sudo journalctl -u directiva-agricola -f"
