from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.models import Emisor
from core.services.configuracion_entorno import ConfiguracionEntornoService
from core.services.certificado_service import CertificadoService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verifica el estado de los certificados de los emisores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--emisor',
            type=int,
            help='ID del emisor específico a verificar (opcional)',
        )
        parser.add_argument(
            '--dias-advertencia',
            type=int,
            default=30,
            help='Días de advertencia para certificados próximos a vencer (default: 30)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada',
        )

    def handle(self, *args, **options):
        emisor_id = options['emisor']
        dias_advertencia = options['dias_advertencia']
        verbose = options['verbose']

        self.stdout.write(
            self.style.SUCCESS('=== VERIFICACIÓN DE CERTIFICADOS ===')
        )
        self.stdout.write(f"Fecha: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"Días de advertencia: {dias_advertencia}")
        self.stdout.write("")

        # Filtrar emisores
        if emisor_id:
            emisores = Emisor.objects.filter(codigo=emisor_id, activo=True)
        else:
            emisores = Emisor.objects.filter(activo=True)

        if not emisores.exists():
            self.stdout.write(
                self.style.ERROR("❌ No se encontraron emisores para verificar.")
            )
            return

        certificados_verificados = 0
        certificados_vigentes = 0
        certificados_por_vencer = 0
        certificados_vencidos = 0
        certificados_fiel = 0
        errores = 0

        for emisor in emisores:
            self.stdout.write(f"--- Emisor: {emisor.razon_social} ({emisor.rfc}) ---")

            try:
                # Verificar configuración básica
                validacion = ConfiguracionEntornoService.validar_configuracion_emisor(emisor)
                if not validacion['valido']:
                    self.stdout.write(
                        self.style.ERROR("❌ Configuración incompleta:")
                    )
                    for error in validacion['errores']:
                        self.stdout.write(f"   - {error}")
                    errores += 1
                    continue

                # Extraer datos del certificado
                cert_data = CertificadoService.extraer_datos_certificado(emisor)
                certificados_verificados += 1

                # Verificar vigencia
                if cert_data['vigente']:
                    certificados_vigentes += 1
                    self.stdout.write(
                        self.style.SUCCESS("✅ Certificado vigente")
                    )

                    # Verificar si está por vencer
                    fecha_fin = cert_data['fecha_fin']
                    if isinstance(fecha_fin, str):
                        from datetime import datetime
                        fecha_fin_date = datetime.fromisoformat(fecha_fin).date()
                    elif hasattr(fecha_fin, 'date'):
                        fecha_fin_date = fecha_fin.date()
                    else:
                        fecha_fin_date = fecha_fin
                    dias_restantes = (fecha_fin_date - timezone.now().date()).days

                    if dias_restantes <= dias_advertencia:
                        certificados_por_vencer += 1
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  Advertencia: Certificado vence en {dias_restantes} días")
                        )
                        self.stdout.write(f"   Fecha de vencimiento: {fecha_fin_date}")
                    else:
                        self.stdout.write(f"   Vence el: {fecha_fin_date} ({dias_restantes} días restantes)")
                else:
                    certificados_vencidos += 1
                    self.stdout.write(
                        self.style.ERROR("❌ Certificado vencido")
                    )
                    fecha_inicio = cert_data['fecha_inicio']
                    fecha_fin = cert_data['fecha_fin']
                    if hasattr(fecha_inicio, 'date'):
                        fecha_inicio_date = fecha_inicio.date()
                    else:
                        fecha_inicio_date = fecha_inicio
                    if hasattr(fecha_fin, 'date'):
                        fecha_fin_date = fecha_fin.date()
                    else:
                        fecha_fin_date = fecha_fin
                    self.stdout.write(f"   Vigencia: {fecha_inicio_date} - {fecha_fin_date}")

                # Verificar si es FIEL
                if cert_data['es_fiel']:
                    certificados_fiel += 1
                    self.stdout.write(
                        self.style.WARNING("⚠️  Advertencia: Este es un certificado FIEL, se requiere un CSD para facturación")
                    )

                # Mostrar número de certificado
                self.stdout.write(f"   No. Certificado: {cert_data['no_certificado']}")

                if verbose:
                    self.stdout.write(f"   Fecha de inicio: {cert_data['fecha_inicio']}")
                    self.stdout.write(f"   Fecha de fin: {cert_data['fecha_fin']}")

            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Error al verificar certificado: {str(e)}")
                )
                logger.error(f"Error verificando certificado del emisor {emisor.codigo}: {e}")

            self.stdout.write("")

        # Resumen
        self.stdout.write("=== RESUMEN ===")
        self.stdout.write(f"Certificados verificados: {certificados_verificados}")
        self.stdout.write(f"Vigentes: {certificados_vigentes}")
        self.stdout.write(f"Por vencer (≤{dias_advertencia} días): {certificados_por_vencer}")
        self.stdout.write(f"Vencidos: {certificados_vencidos}")
        self.stdout.write(f"FIEL (no válidos para facturación): {certificados_fiel}")
        self.stdout.write(f"Errores: {errores}")

        if certificados_por_vencer > 0:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING("⚠️  RECOMENDACIÓN: Renovar certificados próximos a vencer")
            )

        if certificados_fiel > 0:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING("⚠️  RECOMENDACIÓN: Obtener CSD para facturación (no FIEL)")
            )

        if errores > 0:
            self.stdout.write("")
            self.stdout.write(
                self.style.ERROR("❌ RECOMENDACIÓN: Revisar y corregir los errores encontrados")
            )