import json
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from ..models import Emisor, ConfiguracionSistema
from ..services.configuracion_entorno import ConfiguracionEntornoService
from ..services.certificado_service import CertificadoService
from ..services.pac_client import PACProdigiaClient
from ..services.sat_catalog_service import SATCatalogService
import logging

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET"])
def estado_sistema(request):
    """
    Vista AJAX para verificar el estado general del sistema.
    """
    try:
        # Estado de emisores
        emisores_total = Emisor.objects.filter(activo=True).count()
        emisores_validos = 0
        emisores_con_problemas = 0
        
        for emisor in Emisor.objects.filter(activo=True):
            validacion = ConfiguracionEntornoService.validar_configuracion_emisor(emisor)
            if validacion['valido']:
                emisores_validos += 1
            else:
                emisores_con_problemas += 1
        
        # Estado de catálogos SAT
        catalogos_actualizados = 0
        catalogos_desactualizados = 0
        
        try:
            # Verificar si los catálogos están actualizados
            config = ConfiguracionSistema.objects.first()
            if config and config.ultima_actualizacion_catalogos:
                # Considerar desactualizado si tiene más de 7 días
                ultima_actualizacion = config.ultima_actualizacion_catalogos
                if hasattr(ultima_actualizacion, 'date'):
                    # Si es datetime, convertir a date
                    ultima_actualizacion = ultima_actualizacion.date()
                dias_desde_actualizacion = (timezone.now().date() - ultima_actualizacion).days
                if dias_desde_actualizacion <= 7:
                    catalogos_actualizados = 1
                else:
                    catalogos_desactualizados = 1
            else:
                catalogos_desactualizados = 1
        except Exception as e:
            logger.error(f"Error verificando estado de catálogos: {e}")
            catalogos_desactualizados = 1
        
        return JsonResponse({
            'success': True,
            'emisores': {
                'total': emisores_total,
                'validos': emisores_validos,
                'con_problemas': emisores_con_problemas
            },
            'catalogos': {
                'actualizados': catalogos_actualizados,
                'desactualizados': catalogos_desactualizados
            },
            'fecha_verificacion': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en estado_sistema: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def verificar_certificados(request):
    """
    Vista AJAX para verificar el estado de los certificados.
    """
    try:
        emisor_id = request.POST.get('emisor_id')
        dias_advertencia = int(request.POST.get('dias_advertencia', 30))
        
        output_lines = []
        output_lines.append("=== VERIFICACIÓN DE CERTIFICADOS ===")
        output_lines.append(f"Fecha: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"Días de advertencia: {dias_advertencia}")
        output_lines.append("")
        
        # Filtrar emisores
        if emisor_id:
            emisores = Emisor.objects.filter(codigo=emisor_id, activo=True)
        else:
            emisores = Emisor.objects.filter(activo=True)
        
        if not emisores.exists():
            output_lines.append("❌ No se encontraron emisores para verificar.")
            return JsonResponse({
                'success': True,
                'output': '\n'.join(output_lines)
            })
        
        certificados_verificados = 0
        certificados_vigentes = 0
        certificados_por_vencer = 0
        certificados_vencidos = 0
        certificados_fiel = 0
        errores = 0
        
        for emisor in emisores:
            output_lines.append(f"--- Emisor: {emisor.razon_social} ({emisor.rfc}) ---")
            
            try:
                # Verificar configuración básica
                validacion = ConfiguracionEntornoService.validar_configuracion_emisor(emisor)
                if not validacion['valido']:
                    output_lines.append("❌ Configuración incompleta:")
                    for error in validacion['errores']:
                        output_lines.append(f"   - {error}")
                    errores += 1
                    continue
                
                # Extraer datos del certificado
                cert_data = CertificadoService.extraer_datos_certificado(emisor)
                certificados_verificados += 1
                
                # Verificar vigencia
                if cert_data['vigente']:
                    certificados_vigentes += 1
                    output_lines.append("✅ Certificado vigente")
                    
                    # Verificar si está por vencer
                    fecha_fin = cert_data['fecha_fin']
                    dias_restantes = (fecha_fin - timezone.now().date()).days
                    
                    if dias_restantes <= dias_advertencia:
                        certificados_por_vencer += 1
                        output_lines.append(f"⚠️  Advertencia: Certificado vence en {dias_restantes} días")
                        output_lines.append(f"   Fecha de vencimiento: {fecha_fin.strftime('%Y-%m-%d')}")
                    else:
                        output_lines.append(f"   Vence el: {fecha_fin.strftime('%Y-%m-%d')} ({dias_restantes} días restantes)")
                else:
                    certificados_vencidos += 1
                    output_lines.append("❌ Certificado vencido")
                    output_lines.append(f"   Vigencia: {cert_data['fecha_inicio'].strftime('%Y-%m-%d')} - {cert_data['fecha_fin'].strftime('%Y-%m-%d')}")
                
                # Verificar si es FIEL
                if cert_data['es_fiel']:
                    certificados_fiel += 1
                    output_lines.append("⚠️  Advertencia: Este es un certificado FIEL, se requiere un CSD para facturación")
                
                # Mostrar número de certificado
                output_lines.append(f"   No. Certificado: {cert_data['no_certificado']}")
                
            except Exception as e:
                errores += 1
                output_lines.append(f"❌ Error al verificar certificado: {str(e)}")
                logger.error(f"Error verificando certificado del emisor {emisor.codigo}: {e}")
            
            output_lines.append("")
        
        # Resumen
        output_lines.append("=== RESUMEN ===")
        output_lines.append(f"Certificados verificados: {certificados_verificados}")
        output_lines.append(f"Vigentes: {certificados_vigentes}")
        output_lines.append(f"Por vencer (≤{dias_advertencia} días): {certificados_por_vencer}")
        output_lines.append(f"Vencidos: {certificados_vencidos}")
        output_lines.append(f"FIEL (no válidos para facturación): {certificados_fiel}")
        output_lines.append(f"Errores: {errores}")
        
        if certificados_por_vencer > 0:
            output_lines.append("")
            output_lines.append("⚠️  RECOMENDACIÓN: Renovar certificados próximos a vencer")
        
        if certificados_fiel > 0:
            output_lines.append("")
            output_lines.append("⚠️  RECOMENDACIÓN: Obtener CSD para facturación (no FIEL)")
        
        return JsonResponse({
            'success': True,
            'output': '\n'.join(output_lines)
        })
        
    except Exception as e:
        logger.error(f"Error en verificar_certificados: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def actualizar_catalogos(request):
    """
    Vista AJAX para actualizar los catálogos SAT.
    """
    try:
        catalogo = request.POST.get('catalogo', '')
        forzar = request.POST.get('forzar', 'false').lower() == 'true'
        
        output_lines = []
        output_lines.append("=== ACTUALIZACIÓN DE CATÁLOGOS SAT ===")
        output_lines.append(f"Fecha: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"Forzar actualización: {'Sí' if forzar else 'No'}")
        output_lines.append("")
        
        # Inicializar servicio de catálogos
        catalog_service = SATCatalogService()
        
        # Determinar qué catálogos actualizar
        if catalogo:
            catalogos_a_actualizar = [catalogo]
        else:
            catalogos_a_actualizar = [
                'regimenes', 'usos-cfdi', 'formas-pago', 'metodos-pago',
                'monedas', 'tipos-comprobante', 'objeto-impuesto', 'exportacion'
            ]
        
        catalogos_actualizados = 0
        catalogos_con_error = 0
        
        for cat in catalogos_a_actualizar:
            output_lines.append(f"--- Actualizando catálogo: {cat} ---")
            
            try:
                resultado = catalog_service.actualizar_catalogo(cat, forzar=forzar)
                
                if resultado['actualizado']:
                    catalogos_actualizados += 1
                    output_lines.append(f"✅ {resultado['mensaje']}")
                    if 'registros' in resultado:
                        output_lines.append(f"   Registros: {resultado['registros']}")
                else:
                    output_lines.append(f"ℹ️  {resultado['mensaje']}")
                
            except Exception as e:
                catalogos_con_error += 1
                output_lines.append(f"❌ Error: {str(e)}")
                logger.error(f"Error actualizando catálogo {cat}: {e}")
            
            output_lines.append("")
        
        # Actualizar fecha de última actualización
        try:
            config, created = ConfiguracionSistema.objects.get_or_create(
                defaults={'ultima_actualizacion_catalogos': timezone.now()}
            )
            if not created:
                config.ultima_actualizacion_catalogos = timezone.now()
                config.save()
        except Exception as e:
            output_lines.append(f"⚠️  Advertencia: No se pudo actualizar la fecha de última actualización: {e}")
        
        # Resumen
        output_lines.append("=== RESUMEN ===")
        output_lines.append(f"Catálogos actualizados: {catalogos_actualizados}")
        output_lines.append(f"Catálogos con error: {catalogos_con_error}")
        output_lines.append(f"Total procesados: {len(catalogos_a_actualizar)}")
        
        if catalogos_con_error > 0:
            output_lines.append("")
            output_lines.append("⚠️  RECOMENDACIÓN: Revisar los errores y reintentar la actualización")
        
        return JsonResponse({
            'success': True,
            'output': '\n'.join(output_lines)
        })
        
    except Exception as e:
        logger.error(f"Error en actualizar_catalogos: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def probar_conexion_pac(request):
    """
    Vista AJAX para probar la conexión con el PAC.
    """
    try:
        emisor_id = request.POST.get('emisor_id')
        
        if not emisor_id:
            return JsonResponse({
                'exito': False,
                'error': 'ID de emisor requerido',
                'codigo_error': 'MISSING_EMISOR_ID'
            })
        
        try:
            emisor = Emisor.objects.get(codigo=emisor_id, activo=True)
        except Emisor.DoesNotExist:
            return JsonResponse({
                'exito': False,
                'error': 'Emisor no encontrado',
                'codigo_error': 'EMISOR_NOT_FOUND'
            })
        
        # Verificar configuración del emisor
        validacion = ConfiguracionEntornoService.validar_configuracion_emisor(emisor)
        if not validacion['valido']:
            return JsonResponse({
                'exito': False,
                'error': f"Configuración del emisor incompleta: {'; '.join(validacion['errores'])}",
                'codigo_error': 'INVALID_EMISOR_CONFIG'
            })
        
        # Probar conexión con el PAC
        inicio = time.time()
        resultado = PACProdigiaClient.probar_conexion(emisor)
        tiempo_respuesta = round(time.time() - inicio, 2)
        
        if resultado['exito']:
            return JsonResponse({
                'exito': True,
                'mensaje': resultado['mensaje'],
                'tiempo_respuesta': tiempo_respuesta,
                'emisor': {
                    'razon_social': emisor.razon_social,
                    'rfc': emisor.rfc,
                    'pac': emisor.nombre_pac,
                    'modo': 'Pruebas' if emisor.timbrado_prueba else 'Producción'
                }
            })
        else:
            return JsonResponse({
                'exito': False,
                'error': resultado['error'],
                'codigo_error': resultado.get('codigo_error', 'PAC_CONNECTION_FAILED'),
                'tiempo_respuesta': tiempo_respuesta
            })
        
    except Exception as e:
        logger.error(f"Error en probar_conexion_pac: {e}")
        return JsonResponse({
            'exito': False,
            'error': str(e),
            'codigo_error': 'UNKNOWN_ERROR'
        })
