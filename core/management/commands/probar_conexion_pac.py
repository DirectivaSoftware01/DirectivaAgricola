from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.models import Emisor
from core.services.configuracion_entorno import ConfiguracionEntornoService
from core.services.pac_client import PACProdigiaClient
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Prueba la conexión con el PAC'

    def add_arguments(self, parser):
        parser.add_argument(
            '--emisor',
            type=int,
            help='ID del emisor específico para probar conexión (opcional)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada',
        )

    def handle(self, *args, **options):
        emisor_id = options['emisor']
        verbose = options['verbose']

        self.stdout.write(
            self.style.SUCCESS('=== PRUEBA DE CONEXIÓN PAC ===')
        )
        self.stdout.write(f"Fecha: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("")

        # Filtrar emisores
        if emisor_id:
            emisores = Emisor.objects.filter(codigo=emisor_id, activo=True)
        else:
            emisores = Emisor.objects.filter(activo=True)

        if not emisores.exists():
            self.stdout.write(
                self.style.ERROR("❌ No se encontraron emisores para probar conexión.")
            )
            return

        conexiones_exitosas = 0
        conexiones_fallidas = 0
        errores_configuracion = 0

        for emisor in emisores:
            self.stdout.write(f"--- Emisor: {emisor.razon_social} ({emisor.rfc}) ---")
            self.stdout.write(f"PAC: {emisor.nombre_pac}")
            self.stdout.write(f"Modo: {'Pruebas' if emisor.timbrado_prueba else 'Producción'}")

            try:
                # Verificar configuración del emisor
                validacion = ConfiguracionEntornoService.validar_configuracion_emisor(emisor)
                if not validacion['valido']:
                    errores_configuracion += 1
                    self.stdout.write(
                        self.style.ERROR("❌ Configuración incompleta:")
                    )
                    for error in validacion['errores']:
                        self.stdout.write(f"   - {error}")
                    self.stdout.write("")
                    continue

                # Probar conexión con el PAC
                inicio = time.time()
                
                # Obtener configuración del emisor
                configuracion = {
                    'url': ConfiguracionEntornoService.obtener_url_pac(emisor),
                    'credenciales': {
                        'usuario': emisor.usuario_pac,
                        'password': emisor.password_pac,
                        'contrato': emisor.contrato,
                    },
                    'timeout': 30,
                    'max_retries': 3,
                    'retry_delay': 1,
                    'backoff_factor': 2
                }
                
                # Crear cliente PAC
                pac_client = PACProdigiaClient(configuracion)
                resultado = pac_client.probar_conexion()
                tiempo_respuesta = round(time.time() - inicio, 2)

                if resultado['exito']:
                    conexiones_exitosas += 1
                    self.stdout.write(
                        self.style.SUCCESS("✅ Conexión exitosa")
                    )
                    self.stdout.write(f"   Tiempo de respuesta: {tiempo_respuesta} segundos")
                    self.stdout.write(f"   Mensaje: {resultado['mensaje']}")
                else:
                    conexiones_fallidas += 1
                    self.stdout.write(
                        self.style.ERROR("❌ Error de conexión")
                    )
                    self.stdout.write(f"   Código: {resultado.get('codigo_error', 'N/A')}")
                    self.stdout.write(f"   Mensaje: {resultado['error']}")
                    self.stdout.write(f"   Tiempo: {tiempo_respuesta} segundos")

                if verbose:
                    self.stdout.write(f"   Usuario PAC: {emisor.usuario_pac}")
                    self.stdout.write(f"   Contrato: {emisor.contrato or 'No configurado'}")

            except Exception as e:
                conexiones_fallidas += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Error inesperado: {str(e)}")
                )
                logger.error(f"Error probando conexión PAC del emisor {emisor.codigo}: {e}")

            self.stdout.write("")

        # Resumen
        self.stdout.write("=== RESUMEN ===")
        self.stdout.write(f"Conexiones exitosas: {conexiones_exitosas}")
        self.stdout.write(f"Conexiones fallidas: {conexiones_fallidas}")
        self.stdout.write(f"Errores de configuración: {errores_configuracion}")
        self.stdout.write(f"Total emisores: {emisores.count()}")

        if conexiones_fallidas > 0 or errores_configuracion > 0:
            self.stdout.write("")
            self.stdout.write(
                self.style.ERROR("❌ RECOMENDACIÓN: Revisar y corregir los errores encontrados")
            )
        else:
            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS("✅ Todas las conexiones fueron exitosas")
            )
