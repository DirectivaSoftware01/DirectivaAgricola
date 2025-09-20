import json
from django.core.management.base import BaseCommand, CommandError
from core.models import Factura, FacturaDetalle
from core.validators.cfdi_validator import CFDIValidator

class Command(BaseCommand):
    help = 'Diagnostica problemas de validación CFDI en una factura específica'

    def add_arguments(self, parser):
        parser.add_argument('--folio', type=int, required=True, help='Folio de la factura a diagnosticar.')

    def handle(self, *args, **kwargs):
        folio = kwargs['folio']
        
        try:
            factura = Factura.objects.get(folio=folio)
        except Factura.DoesNotExist:
            raise CommandError(f'Factura con folio {folio} no encontrada.')

        self.stdout.write(self.style.SUCCESS(f"=== DIAGNÓSTICO DE FACTURA {factura.serie}-{factura.folio:06d} ==="))
        
        # Obtener detalles
        detalles = FacturaDetalle.objects.filter(factura=factura)
        
        self.stdout.write(f"\n--- Información Básica ---")
        self.stdout.write(f"Serie: {factura.serie}")
        self.stdout.write(f"Folio: {factura.folio}")
        self.stdout.write(f"Fecha Emisión: {factura.fecha_emision}")
        self.stdout.write(f"Lugar Expedición: {factura.lugar_expedicion}")
        self.stdout.write(f"Subtotal: {factura.subtotal}")
        self.stdout.write(f"Impuesto: {factura.impuesto}")
        self.stdout.write(f"Total: {factura.total}")
        
        self.stdout.write(f"\n--- Emisor ---")
        self.stdout.write(f"RFC: {factura.emisor.rfc}")
        self.stdout.write(f"Razón Social: {factura.emisor.razon_social}")
        self.stdout.write(f"Régimen Fiscal: {factura.emisor.regimen_fiscal}")
        
        self.stdout.write(f"\n--- Receptor ---")
        self.stdout.write(f"RFC: {factura.receptor.rfc}")
        self.stdout.write(f"Razón Social: {factura.receptor.razon_social}")
        self.stdout.write(f"Régimen Fiscal: {factura.receptor.regimen_fiscal}")
        self.stdout.write(f"Código Postal: {factura.receptor.codigo_postal}")
        
        self.stdout.write(f"\n--- Detalles ({len(detalles)} conceptos) ---")
        for i, detalle in enumerate(detalles, 1):
            self.stdout.write(f"Concepto {i}:")
            self.stdout.write(f"  Producto: {detalle.producto_servicio.descripcion}")
            self.stdout.write(f"  Cantidad: {detalle.cantidad}")
            self.stdout.write(f"  Precio: {detalle.precio}")
            self.stdout.write(f"  Importe: {detalle.importe}")
            self.stdout.write(f"  Clave Prod/Serv: {detalle.clave_prod_serv}")
            self.stdout.write(f"  Unidad: {detalle.unidad}")
            self.stdout.write(f"  Objeto Impuesto: {detalle.objeto_impuesto}")
        
        # Ejecutar validación
        self.stdout.write(f"\n--- Validación CFDI ---")
        resultado = CFDIValidator.validar_factura_completa(factura, list(detalles))
        
        if resultado['valido']:
            self.stdout.write(self.style.SUCCESS("✅ La factura es válida"))
        else:
            self.stdout.write(self.style.ERROR("❌ La factura tiene errores de validación:"))
            for error in resultado['errores']:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
        
        if resultado['advertencias']:
            self.stdout.write(self.style.WARNING("⚠️  Advertencias:"))
            for advertencia in resultado['advertencias']:
                self.stdout.write(self.style.WARNING(f"  - {advertencia}"))
        
        self.stdout.write(f"\n=== FIN DEL DIAGNÓSTICO ===")
