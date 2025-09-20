import json
from django.core.management.base import BaseCommand, CommandError
from core.models import Factura, FacturaDetalle

class Command(BaseCommand):
    help = 'Debug del proceso de guardado de facturas'

    def handle(self, *args, **kwargs):
        # Obtener la última factura creada
        try:
            factura = Factura.objects.latest('fecha_creacion')
        except Factura.DoesNotExist:
            self.stdout.write(self.style.WARNING("No hay facturas en la base de datos"))
            return

        self.stdout.write(self.style.SUCCESS(f"=== DEBUG FACTURA {factura.serie}-{factura.folio:06d} ==="))
        
        # Información básica
        self.stdout.write(f"\n--- Información Básica ---")
        self.stdout.write(f"Serie: {factura.serie}")
        self.stdout.write(f"Folio: {factura.folio}")
        self.stdout.write(f"Fecha Creación: {factura.fecha_creacion}")
        self.stdout.write(f"Subtotal: {factura.subtotal}")
        self.stdout.write(f"Impuesto: {factura.impuesto}")
        self.stdout.write(f"Total: {factura.total}")
        
        # Detalles
        detalles = FacturaDetalle.objects.filter(factura=factura)
        self.stdout.write(f"\n--- Detalles ({len(detalles)} encontrados) ---")
        
        if detalles.exists():
            for i, detalle in enumerate(detalles, 1):
                self.stdout.write(f"Detalle {i}:")
                self.stdout.write(f"  ID: {detalle.id}")
                self.stdout.write(f"  Producto: {detalle.producto_servicio.descripcion}")
                self.stdout.write(f"  Cantidad: {detalle.cantidad}")
                self.stdout.write(f"  Precio: {detalle.precio}")
                self.stdout.write(f"  Importe: {detalle.importe}")
                self.stdout.write(f"  Impuesto: {detalle.impuesto_concepto}")
                self.stdout.write(f"  Concepto: {detalle.concepto}")
                self.stdout.write(f"  Clave Prod/Serv: {detalle.clave_prod_serv}")
                self.stdout.write(f"  Unidad: {detalle.unidad}")
                self.stdout.write(f"  Objeto Impuesto: {detalle.objeto_impuesto}")
        else:
            self.stdout.write(self.style.ERROR("❌ No se encontraron detalles para esta factura"))
        
        # Verificar si hay facturas con detalles
        facturas_con_detalles = Factura.objects.filter(detalles__isnull=False).distinct()
        self.stdout.write(f"\n--- Estadísticas ---")
        self.stdout.write(f"Total facturas: {Factura.objects.count()}")
        self.stdout.write(f"Facturas con detalles: {facturas_con_detalles.count()}")
        self.stdout.write(f"Total detalles: {FacturaDetalle.objects.count()}")
        
        self.stdout.write(f"\n=== FIN DEL DEBUG ===")
