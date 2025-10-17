#!/bin/bash

# Script para agregar datos de prueba
# Ejecutar desde tu máquina local

set -e  # Salir si hay algún error

echo "🚀 Agregando datos de prueba para el modal..."

# Variables de configuración
SERVER_IP="89.116.51.217"
SERVER_USER="root"
SERVER_DIR="/var/www/directiva_agricola"

# Función para imprimir mensajes
print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_status "Agregando datos de prueba a la base de datos..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py shell --settings=directiva_agricola.settings_production << 'EOF'
from core.models import Presupuesto, PresupuestoDetalle, ClasificacionGasto, CentroCosto

# Obtener el primer presupuesto
presupuesto = Presupuesto.objects.first()
print(f'Presupuesto encontrado: {presupuesto.codigo}')

# Obtener la clasificación de gasto
clasificacion = ClasificacionGasto.objects.first()
print(f'Clasificación encontrada: {clasificacion.descripcion}')

# Obtener el centro de costo del presupuesto
centro_costo = presupuesto.centro_costo
print(f'Centro de costo: {centro_costo.descripcion}')

# Crear un detalle de presupuesto
detalle, created = PresupuestoDetalle.objects.get_or_create(
    presupuesto=presupuesto,
    clasificacion_gasto=clasificacion,
    defaults={
        'monto_presupuestado': 10000.00,
        'monto_ejecutado': 0.00,
        'activo': True
    }
)

if created:
    print(f'Detalle de presupuesto creado: {detalle.clasificacion_gasto.descripcion}')
else:
    print(f'Detalle de presupuesto ya existía: {detalle.clasificacion_gasto.descripcion}')

print('Datos de prueba agregados exitosamente')
EOF"

print_status "Verificando que los datos se agregaron..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_DIR && source venv/bin/activate && python manage.py shell --settings=directiva_agricola.settings_production -c \"from core.models import Presupuesto, PresupuestoDetalle; presupuesto = Presupuesto.objects.first(); detalles = presupuesto.detalles.filter(activo=True); print(f'Detalles activos: {detalles.count()}'); [print(f'- Clasificación: {d.clasificacion_gasto.descripcion}') for d in detalles]\""

print_status "Probando la URL AJAX..."
ssh $SERVER_USER@$SERVER_IP "curl -s 'http://localhost:8000/ajax/presupuestos/1/clasificaciones/' | python -m json.tool || echo 'Error en la URL AJAX'"

print_status "✅ Datos de prueba agregados!"
print_status "🌐 Ahora el modal debería mostrar las clasificaciones de gasto"
