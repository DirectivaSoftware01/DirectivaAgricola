#!/bin/bash

# Script para configurar SSH en el servidor
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🔑 Configurando SSH para Hostinger VPS..."

# Variables de configuración
SERVER_IP="89.116.51.217"
SERVER_USER="root"
PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBc1jznSeJSFWXQfpVw4euQkh9GX1tqnJcuRVTxZqTPH jm.barbasoto@outlook.com"

# Función para imprimir mensajes
print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

print_status "Tu clave pública SSH es:"
echo "$PUBLIC_KEY"
echo ""

print_warning "IMPORTANTE: Necesitas agregar esta clave al servidor"
print_warning "Opciones para agregar la clave:"
echo ""
echo "1. 📧 Panel de Hostinger:"
echo "   - Ve al panel de control de Hostinger"
echo "   - Busca la sección 'SSH Keys' o 'Claves SSH'"
echo "   - Agrega la clave pública mostrada arriba"
echo ""
echo "2. 🔑 Manualmente en el servidor:"
echo "   - Conecta al servidor por otro método (panel web, etc.)"
echo "   - Ejecuta: mkdir -p ~/.ssh"
echo "   - Ejecuta: echo '$PUBLIC_KEY' >> ~/.ssh/authorized_keys"
echo "   - Ejecuta: chmod 600 ~/.ssh/authorized_keys"
echo "   - Ejecuta: chmod 700 ~/.ssh"
echo ""
echo "3. 🚀 Una vez configurada la clave, ejecuta:"
echo "   ./deploy_simple.sh"
echo ""

print_status "¿Ya agregaste la clave al servidor? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    print_status "Probando conexión SSH..."
    ssh -o ConnectTimeout=10 -o BatchMode=yes $SERVER_USER@$SERVER_IP "echo 'Conexión SSH exitosa'" && {
        print_status "✅ Conexión SSH exitosa!"
        print_status "Ahora puedes ejecutar: ./deploy_simple.sh"
    } || {
        print_error "❌ La conexión SSH falló"
        print_warning "Verifica que hayas agregado la clave correctamente"
    }
else
    print_warning "Agrega la clave SSH al servidor y luego ejecuta: ./deploy_simple.sh"
fi
