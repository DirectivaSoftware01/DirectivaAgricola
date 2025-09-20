from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.models import Emisor, ConfiguracionSistema
from core.services.configuracion_entorno import ConfiguracionEntornoService
from core.services.sat_catalog_service import SATCatalogService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Muestra el estado general del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']

        self.stdout.write(
            self.style.SUCCESS('=== ESTADO DEL SISTEMA ===')
        )
        self.stdout.write(f"Fecha: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("")

        # Estado de emisores
        self.stdout.write("--- EMISORES ---")
        emisores_total = Emisor.objects.filter(activo=True).count()
        emisores_validos = 0
        emisores_con_problemas = 0

        for emisor in Emisor.objects.filter(activo=True):
            validacion = ConfiguracionEntornoService.validar_configuracion_emisor(emisor)
            if validacion['valido']:
                emisores_validos += 1
            else:
                emisores_con_problemas += 1

        self.stdout.write(f"Total: {emisores_total}")
        self.stdout.write(f"Válidos: {emisores_validos}")
        self.stdout.write(f"Con problemas: {emisores_con_problemas}")

        if verbose and emisores_con_problemas > 0:
            self.stdout.write("")
            self.stdout.write("Emisores con problemas:")
            for emisor in Emisor.objects.filter(activo=True):
                validacion = ConfiguracionEntornoService.validar_configuracion_emisor(emisor)
                if not validacion['valido']:
                    self.stdout.write(f"  - {emisor.razon_social} ({emisor.rfc})")
                    for error in validacion['errores']:
                        self.stdout.write(f"    * {error}")

        # Estado de catálogos SAT
        self.stdout.write("")
        self.stdout.write("--- CATÁLOGOS SAT ---")
        
        try:
            catalog_service = SATCatalogService()
            stats = catalog_service.obtener_estadisticas_catalogos()
            
            self.stdout.write(f"Total de catálogos: {stats['total_catalogos']}")
            self.stdout.write(f"En cache: {stats['catalogos_en_cache']}")
            self.stdout.write(f"Actualizados: {stats['catalogos_actualizados']}")
            self.stdout.write(f"Desactualizados: {stats['catalogos_desactualizados']}")

            if verbose:
                self.stdout.write("")
                self.stdout.write("Detalle de catálogos:")
                for nombre, detalle in stats['detalle'].items():
                    estado = "✅" if detalle['actualizado'] else "❌"
                    self.stdout.write(f"  {estado} {nombre}: {detalle['registros']} registros")
                    if detalle['dias_desde_actualizacion'] is not None:
                        self.stdout.write(f"    Última actualización: hace {detalle['dias_desde_actualizacion']} días")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error obteniendo estadísticas de catálogos: {e}")
            )

        # Estado de configuración del sistema
        self.stdout.write("")
        self.stdout.write("--- CONFIGURACIÓN DEL SISTEMA ---")
        
        try:
            config = ConfiguracionSistema.objects.first()
            if config and config.ultima_actualizacion_catalogos:
                ultima_actualizacion = config.ultima_actualizacion_catalogos
                if hasattr(ultima_actualizacion, 'date'):
                    # Si es datetime, convertir a date
                    ultima_actualizacion = ultima_actualizacion.date()
                dias_desde_actualizacion = (timezone.now().date() - ultima_actualizacion).days
                self.stdout.write(f"Última actualización de catálogos: {config.ultima_actualizacion_catalogos.strftime('%Y-%m-%d %H:%M:%S')}")
                self.stdout.write(f"Días desde actualización: {dias_desde_actualizacion}")
                
                if dias_desde_actualizacion > 7:
                    self.stdout.write(
                        self.style.WARNING("⚠️  Los catálogos están desactualizados (más de 7 días)")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✅ Los catálogos están actualizados")
                    )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️  No hay registro de actualización de catálogos")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error obteniendo configuración del sistema: {e}")
            )

        # Resumen general
        self.stdout.write("")
        self.stdout.write("=== RESUMEN GENERAL ===")
        
        if emisores_con_problemas == 0 and stats['catalogos_desactualizados'] == 0:
            self.stdout.write(
                self.style.SUCCESS("✅ Sistema en buen estado")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠️  Sistema requiere atención")
            )
            
            if emisores_con_problemas > 0:
                self.stdout.write(f"  - {emisores_con_problemas} emisor(es) con problemas de configuración")
            if stats['catalogos_desactualizados'] > 0:
                self.stdout.write(f"  - {stats['catalogos_desactualizados']} catálogo(s) desactualizado(s)")

        # Recomendaciones
        self.stdout.write("")
        self.stdout.write("=== RECOMENDACIONES ===")
        
        if emisores_con_problemas > 0:
            self.stdout.write("• Ejecutar: python manage.py verificar_certificados")
        
        if stats['catalogos_desactualizados'] > 0:
            self.stdout.write("• Ejecutar: python manage.py actualizar_catalogos_sat")
        
        if emisores_validos > 0:
            self.stdout.write("• Ejecutar: python manage.py probar_conexion_pac")
