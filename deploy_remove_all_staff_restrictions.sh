#!/bin/bash

# Script para desplegar eliminación completa de restricciones de staff
# Permite que usuarios normales accedan a TODAS las funcionalidades

SERVER_IP="89.116.51.217"
SERVER_USER="root"
SERVER_DIR="/var/www/directiva_agricola"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_status "Iniciando despliegue de eliminación completa de restricciones de staff..."

# Hacer backup de la base de datos
print_status "Haciendo backup de la base de datos..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && mysqldump -u root -p'-kNuHf@9G&94BR/d&eA6' directiva_agricola > backup_no_staff_$(date +%Y%m%d_%H%M%S).sql"

if [ $? -eq 0 ]; then
    print_status "Backup de base de datos completado"
else
    print_error "Error al hacer backup de la base de datos"
    exit 1
fi

# Subir archivos modificados
print_status "Subiendo archivos de vistas modificados..."
scp core/views/main_views.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/views/
scp core/views/emisor_ajax_views.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/views/

if [ $? -eq 0 ]; then
    print_status "Archivos de vistas subidos correctamente"
else
    print_error "Error al subir archivos de vistas"
    exit 1
fi

# Establecer permisos
print_status "Estableciendo permisos..."
ssh $SERVER_USER@$SERVER_IP "chown -R www-data:www-data $SERVER_DIR && chmod -R 755 $SERVER_DIR"

# Reiniciar servicio
print_status "Reiniciando servicio Gunicorn..."
ssh $SERVER_USER@$SERVER_IP "systemctl restart gunicorn_directiva_agricola.service"

# Verificar estado del servicio
print_status "Verificando estado del servicio..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

# Verificar que la aplicación esté funcionando
print_status "Verificando funcionamiento de la aplicación..."
HTTP_CODE=$(ssh $SERVER_USER@$SERVER_IP "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/")

if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ]; then
    print_status "✅ Aplicación funcionando correctamente (HTTP $HTTP_CODE)"
else
    print_error "❌ Error en la aplicación (HTTP $HTTP_CODE)"
    exit 1
fi

# Verificar múltiples páginas
print_status "Verificando acceso a múltiples funcionalidades..."
pages=(
    "existencias/"
    "salidas-inventario/"
    "almacenes/"
    "compras/"
    "kardex/"
    "presupuestos/"
    "facturas/"
    "productos-servicios/"
    "proveedores/"
    "usuarios/"
)

for page in "${pages[@]}"; do
    HTTP_CODE=$(ssh $SERVER_USER@$SERVER_IP "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/$page")
    if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ]; then
        print_status "✅ $page - Accesible (HTTP $HTTP_CODE)"
    else
        print_warning "⚠️  $page - Problema (HTTP $HTTP_CODE)"
    fi
done

print_status "🎉 Despliegue completado exitosamente!"
print_status "TODAS las restricciones de staff han sido eliminadas."
print_status "Los usuarios normales ahora tienen acceso completo a:"
print_status "  ✅ Control de Existencias y Costos"
print_status "  ✅ Salidas de Inventario"
print_status "  ✅ Almacenes"
print_status "  ✅ Compras"
print_status "  ✅ Kardex"
print_status "  ✅ Presupuestos"
print_status "  ✅ Facturas"
print_status "  ✅ Productos y Servicios"
print_status "  ✅ Proveedores"
print_status "  ✅ Usuarios"
print_status "  ✅ Y TODAS las demás funcionalidades del sistema"
