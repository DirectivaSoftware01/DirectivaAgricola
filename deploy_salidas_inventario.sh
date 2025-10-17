#!/bin/bash

# Script para desplegar funcionalidad de Salidas de Inventario
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Desplegando Salidas de Inventario a Hostinger VPS..."

# Variables de configuración
SERVER_IP="89.116.51.217"
SERVER_USER="root"
SERVER_DIR="/var/www/directiva_agricola"

# Función para imprimir mensajes
print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

print_status "Deteniendo servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl stop gunicorn_directiva_agricola.service"

print_status "Haciendo backup de la base de datos..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && mysqldump -u root -p'-kNuHf@9G&94BR/d&eA6' directiva_agricola > backup_$(date +%Y%m%d_%H%M%S).sql"

print_status "Subiendo archivos nuevos de Salidas de Inventario..."

# Subir nuevos archivos de modelos y vistas
print_status "Subiendo modelos actualizados..."
scp core/models.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/

print_status "Subiendo nuevas vistas de salidas..."
scp core/salida_views.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/
scp core/salida_forms.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/

print_status "Subiendo URLs actualizadas..."
scp core/urls.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/

print_status "Subiendo nuevas migraciones..."
scp core/migrations/0068_add_clasificacion_gasto_to_producto_servicio.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/migrations/
scp core/migrations/0069_tiposalida_salidainventario_salidainventariodetalle.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/migrations/
scp core/migrations/0070_make_proveedor_optional_in_gastodetalle.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/migrations/

print_status "Subiendo templates de salidas de inventario..."
scp templates/core/salida_inventario_*.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/

print_status "Subiendo templates actualizados..."
scp templates/core/existencias_list.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/kardex_list.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/kardex_producto.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/producto_servicio_form.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/core/producto_servicio_detail.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/core/
scp templates/base.html $SERVER_USER@$SERVER_IP:$SERVER_DIR/templates/

print_status "Subiendo comando de gestión..."
scp core/management/commands/crear_tipos_salida.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/core/management/commands/

print_status "Configurando permisos..."
ssh $SERVER_USER@$SERVER_IP "chown -R www-data:www-data $SERVER_DIR && chmod -R 755 $SERVER_DIR"

print_status "Activando entorno virtual..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && pip install --upgrade pip"

print_status "Ejecutando migraciones..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py migrate --settings=directiva_agricola.settings_production"

print_status "Recopilando archivos estáticos..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production"

print_status "Iniciando servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl start gunicorn_directiva_agricola.service"

print_status "Verificando estado de los servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

print_status "✅ Despliegue de Salidas de Inventario completado!"
print_status "🌐 Tu aplicación actualizada está disponible en: https://agricola.directiva.mx/"
print_status "📊 Para verificar: ssh $SERVER_USER@$SERVER_IP 'systemctl status gunicorn_directiva_agricola.service'"

echo ""
print_status "Nuevas funcionalidades desplegadas:"
echo "  ✅ Salidas de Inventario (master-detail)"
echo "  ✅ Integración automática con Presupuestos"
echo "  ✅ Validación de existencias en tiempo real"
echo "  ✅ Formato de impresión profesional"
echo "  ✅ Campo clasificación de gastos en productos"
echo "  ✅ Botones de acción mejorados"
echo "  ✅ Nuevas migraciones aplicadas"
