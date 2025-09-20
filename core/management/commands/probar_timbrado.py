from django.core.management.base import BaseCommand, CommandError
from core.models import Factura
from core.services.facturacion_service import FacturacionService

class Command(BaseCommand):
    help = 'Prueba el timbrado de una factura específica'

    def add_arguments(self, parser):
        parser.add_argument('--folio', type=int, required=True, help='Folio de la factura a timbrar.')

    def handle(self, *args, **kwargs):
        folio = kwargs['folio']
        
        try:
            factura = Factura.objects.get(folio=folio)
        except Factura.DoesNotExist:
            raise CommandError(f'Factura con folio {folio} no encontrada.')

        self.stdout.write(self.style.SUCCESS(f"=== PROBANDO TIMBRADO DE FACTURA {factura.serie}-{factura.folio:06d} ==="))
        
        # Verificar estado actual
        self.stdout.write(f"Estado actual: {factura.estado_timbrado}")
        self.stdout.write(f"UUID: {factura.uuid or 'No timbrada'}")
        
        # Intentar timbrado
        self.stdout.write(f"\n--- Iniciando timbrado ---")
        try:
            resultado = FacturacionService.timbrar_factura(factura.folio)
            
            if resultado['exito']:
                self.stdout.write(self.style.SUCCESS("✅ Timbrado exitoso"))
                self.stdout.write(f"UUID: {resultado.get('uuid', 'N/A')}")
                self.stdout.write(f"Fecha Timbrado: {resultado.get('fecha_timbrado', 'N/A')}")
            else:
                self.stdout.write(self.style.ERROR("❌ Error en timbrado"))
                self.stdout.write(f"Error: {resultado.get('error', 'Error desconocido')}")
                if 'detalles' in resultado:
                    for detalle in resultado['detalles']:
                        self.stdout.write(f"  - {detalle}")
                        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Excepción durante timbrado: {str(e)}"))
        
        self.stdout.write(f"\n=== FIN DE PRUEBA ===")
