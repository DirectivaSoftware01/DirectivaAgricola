from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.services.sat_catalog_service import SATCatalogService
from core.models import ConfiguracionSistema
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Actualiza los catálogos SAT'

    def add_arguments(self, parser):
        parser.add_argument(
            '--catalogo',
            type=str,
            help='Nombre del catálogo específico a actualizar (opcional)',
        )
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Forzar actualización incluso si el catálogo está actualizado',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada',
        )

    def handle(self, *args, **options):
        catalogo = options['catalogo']
        forzar = options['forzar']
        verbose = options['verbose']

        self.stdout.write(
            self.style.SUCCESS('=== ACTUALIZACIÓN DE CATÁLOGOS SAT ===')
        )
        self.stdout.write(f"Fecha: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"Forzar actualización: {'Sí' if forzar else 'No'}")
        self.stdout.write("")

        # Inicializar servicio de catálogos
        catalog_service = SATCatalogService()

        # Determinar qué catálogos actualizar
        if catalogo:
            if catalogo not in catalog_service.CATALOG_FILES:
                raise CommandError(f"Catálogo '{catalogo}' no soportado. Catálogos disponibles: {', '.join(catalog_service.CATALOG_FILES.keys())}")
            catalogos_a_actualizar = [catalogo]
        else:
            catalogos_a_actualizar = list(catalog_service.CATALOG_FILES.keys())

        catalogos_actualizados = 0
        catalogos_con_error = 0

        for cat in catalogos_a_actualizar:
            self.stdout.write(f"--- Actualizando catálogo: {cat} ---")

            try:
                resultado = catalog_service.actualizar_catalogo(cat, forzar=forzar)

                if resultado['actualizado']:
                    catalogos_actualizados += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ {resultado['mensaje']}")
                    )
                    if 'registros' in resultado:
                        self.stdout.write(f"   Registros: {resultado['registros']}")
                    if verbose and 'fecha_actualizacion' in resultado:
                        self.stdout.write(f"   Fecha: {resultado['fecha_actualizacion']}")
                else:
                    self.stdout.write(
                        self.style.WARNING(f"ℹ️  {resultado['mensaje']}")
                    )

            except Exception as e:
                catalogos_con_error += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Error: {str(e)}")
                )
                logger.error(f"Error actualizando catálogo {cat}: {e}")

            self.stdout.write("")

        # Actualizar fecha de última actualización
        try:
            config, created = ConfiguracionSistema.objects.get_or_create(
                defaults={'ultima_actualizacion_catalogos': timezone.now()}
            )
            if not created:
                config.ultima_actualizacion_catalogos = timezone.now()
                config.save()
            
            self.stdout.write(
                self.style.SUCCESS("✅ Fecha de última actualización actualizada")
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Advertencia: No se pudo actualizar la fecha de última actualización: {e}")
            )

        # Resumen
        self.stdout.write("=== RESUMEN ===")
        self.stdout.write(f"Catálogos actualizados: {catalogos_actualizados}")
        self.stdout.write(f"Catálogos con error: {catalogos_con_error}")
        self.stdout.write(f"Total procesados: {len(catalogos_a_actualizar)}")

        if catalogos_con_error > 0:
            self.stdout.write("")
            self.stdout.write(
                self.style.ERROR("❌ RECOMENDACIÓN: Revisar los errores y reintentar la actualización")
            )
        else:
            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS("✅ Todos los catálogos se actualizaron correctamente")
            )

        # Mostrar estadísticas si es verbose
        if verbose:
            self.stdout.write("")
            self.stdout.write("=== ESTADÍSTICAS DE CATÁLOGOS ===")
            try:
                stats = catalog_service.obtener_estadisticas_catalogos()
                self.stdout.write(f"Total de catálogos: {stats['total_catalogos']}")
                self.stdout.write(f"En cache: {stats['catalogos_en_cache']}")
                self.stdout.write(f"Actualizados: {stats['catalogos_actualizados']}")
                self.stdout.write(f"Desactualizados: {stats['catalogos_desactualizados']}")
            except Exception as e:
                self.stdout.write(f"Error obteniendo estadísticas: {e}")