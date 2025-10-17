#!/bin/bash

echo "=== Probando captura de gasto con forma de pago y autorizó ==="

# Crear un gasto de prueba con forma de pago y autorizó
ssh root@89.116.51.217 "cd /var/www/directiva_agricola && source venv/bin/activate && python manage.py shell --settings=directiva_agricola.settings_production -c \"
from core.models import Gasto, GastoDetalle, Proveedor, ClasificacionGasto, AutorizoGasto, Presupuesto, Usuario
from decimal import Decimal

# Obtener objetos necesarios
proveedor = Proveedor.objects.filter(activo=True).first()
clasificacion = ClasificacionGasto.objects.filter(activo=True).first()
autorizo = AutorizoGasto.objects.filter(activo=True).first()
presupuesto = Presupuesto.objects.filter(activo=True).first()
usuario = Usuario.objects.filter(is_active=True).first()

if not all([proveedor, clasificacion, autorizo, presupuesto, usuario]):
    print('Faltan datos necesarios para crear el gasto de prueba')
    exit()

# Crear gasto
from datetime import date
gasto = Gasto.objects.create(
    presupuesto=presupuesto,
    ciclo='2025-2026',
    fecha_gasto=date.today(),
    usuario_creacion=usuario
)

# Crear detalle con forma de pago y autorizó
detalle = GastoDetalle.objects.create(
    gasto=gasto,
    proveedor=proveedor,
    factura='TEST-001',
    clasificacion_gasto=clasificacion,
    concepto='PRUEBA DE FILTROS',
    forma_pago='02',  # Cheque nominativo
    autorizo=autorizo,
    importe=Decimal('100.00'),
    usuario_creacion=usuario
)

print(f'Gasto creado: {gasto.codigo}')
print(f'Detalle creado: {detalle.factura}')
print(f'Forma de pago: {detalle.forma_pago}')
print(f'Autorizó: {detalle.autorizo.nombre}')
\""

echo ""
echo "=== Verificando que se guardó correctamente ==="

# Verificar que se guardó
ssh root@89.116.51.217 "cd /var/www/directiva_agricola && source venv/bin/activate && python manage.py shell --settings=directiva_agricola.settings_production -c \"
from core.models import GastoDetalle
detalles = GastoDetalle.objects.filter(activo=True, factura='TEST-001')
print(f'Detalles encontrados: {detalles.count()}')
for d in detalles:
    print(f'- Factura: {d.factura}')
    print(f'- Forma pago: {d.forma_pago}')
    print(f'- Autorizó: {d.autorizo.nombre if d.autorizo else \"Sin autorizador\"}')
    print(f'- Concepto: {d.concepto}')
\""

echo ""
echo "=== Prueba completada ==="
