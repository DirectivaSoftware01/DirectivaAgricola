#!/bin/bash

# Script para agregar logs de depuración al modal
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Agregando logs de depuración al modal..."

# Variables de configuración
SERVER_IP="89.116.51.217"
SERVER_USER="root"
SERVER_DIR="/var/www/directiva_agricola"

# Función para imprimir mensajes
print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_status "Agregando logs de depuración al template..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && cp templates/core/presupuesto_list.html templates/core/presupuesto_list.html.backup"

# Crear un parche para agregar logs de depuración
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && cat > debug_patch.py << 'EOF'
import re

# Leer el archivo
with open('templates/core/presupuesto_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Agregar logs de depuración a la función loadClasificacionesGastos
old_function = '''    function loadClasificacionesGastos() {
        const clasificacionSelect = document.getElementById('clasificacion_gasto');
        if (clasificacionSelect && presupuestoActual) {
            clasificacionSelect.innerHTML = '<option value=\"\">Seleccionar clasificación...</option>';
            
            fetch(\`/ajax/presupuestos/\${presupuestoActual}/clasificaciones/\`)'''

new_function = '''    function loadClasificacionesGastos() {
        console.log('DEBUG: loadClasificacionesGastos llamada');
        console.log('DEBUG: presupuestoActual =', presupuestoActual);
        const clasificacionSelect = document.getElementById('clasificacion_gasto');
        console.log('DEBUG: clasificacionSelect encontrado:', !!clasificacionSelect);
        if (clasificacionSelect && presupuestoActual) {
            console.log('DEBUG: Cargando clasificaciones para presupuesto:', presupuestoActual);
            clasificacionSelect.innerHTML = '<option value=\"\">Seleccionar clasificación...</option>';
            
            fetch(\`/ajax/presupuestos/\${presupuestoActual}/clasificaciones/\`)'''

# Aplicar el parche
content = content.replace(old_function, new_function)

# Agregar logs al evento del modal
old_modal_event = '''    gastoModal.addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        presupuestoActual = button.getAttribute('data-presupuesto-id');
        const presupuestoDesc = button.getAttribute('data-presupuesto-desc');'''

new_modal_event = '''    gastoModal.addEventListener('show.bs.modal', function(event) {
        console.log('DEBUG: Modal de gastos abierto');
        const button = event.relatedTarget;
        presupuestoActual = button.getAttribute('data-presupuesto-id');
        console.log('DEBUG: presupuestoActual establecido a:', presupuestoActual);
        const presupuestoDesc = button.getAttribute('data-presupuesto-desc');'''

content = content.replace(old_modal_event, new_modal_event)

# Escribir el archivo modificado
with open('templates/core/presupuesto_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Logs de depuración agregados')
EOF"

ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && python debug_patch.py"

print_status "Configurando permisos..."
ssh $SERVER_USER@$SERVER_IP "chown -R www-data:www-data $SERVER_DIR && chmod -R 755 $SERVER_DIR"

print_status "Reiniciando servicios..."
ssh $SERVER_USER@$SERVER_IP "systemctl restart gunicorn_directiva_agricola.service"

print_status "Esperando que el servicio se inicie..."
sleep 10

print_status "Verificando estado..."
ssh $SERVER_USER@$SERVER_IP "systemctl status gunicorn_directiva_agricola.service --no-pager -l"

print_status "✅ Logs de depuración agregados!"
print_status "🌐 Abre la consola del navegador (F12) y verifica los logs cuando abras el modal"
