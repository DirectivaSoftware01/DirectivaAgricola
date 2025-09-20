"""
Vistas para herramientas de mantenimiento
"""

import subprocess
import json
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.utils import timezone
from .models import Emisor
from .services.certificado_service import CertificadoService
from .services.configuracion_entorno import ConfiguracionEntornoService


@login_required
@staff_member_required
def herramientas_mantenimiento(request):
    """Vista para herramientas de mantenimiento"""
    context = {
        'title': 'Herramientas de Mantenimiento',
        'emisores': Emisor.objects.filter(activo=True),
    }
    return render(request, 'core/herramientas_mantenimiento.html', context)


@login_required
@staff_member_required
def verificar_certificados_ajax(request):
    """Vista AJAX para verificar certificados"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        emisor_id = request.POST.get('emisor_id')
        dias_advertencia = int(request.POST.get('dias_advertencia', 30))
        
        # Ejecutar comando de verificación
        cmd = ['python', 'manage.py', 'verificar_certificados']
        
        if emisor_id:
            cmd.extend(['--emisor-id', emisor_id])
        
        cmd.extend(['--dias-advertencia', str(dias_advertencia)])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=settings.BASE_DIR
        )
        
        return JsonResponse({
            'success': True,
            'output': result.stdout,
            'error': result.stderr,
            'return_code': result.returncode
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error ejecutando verificación: {str(e)}'
        }, status=500)


@login_required
@staff_member_required
def actualizar_catalogos_ajax(request):
    """Vista AJAX para actualizar catálogos SAT"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        catalogo = request.POST.get('catalogo', '')
        forzar = request.POST.get('forzar') == 'true'
        
        # Ejecutar comando de actualización
        cmd = ['python', 'manage.py', 'actualizar_catalogos_sat']
        
        if catalogo:
            cmd.extend(['--catalogo', catalogo])
        
        if forzar:
            cmd.append('--forzar')
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=settings.BASE_DIR
        )
        
        return JsonResponse({
            'success': True,
            'output': result.stdout,
            'error': result.stderr,
            'return_code': result.returncode
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error ejecutando actualización: {str(e)}'
        }, status=500)


@login_required
@staff_member_required
def probar_conexion_pac_ajax(request):
    """Vista AJAX para probar conexión con PAC"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        emisor_id = request.POST.get('emisor_id')
        
        if not emisor_id:
            return JsonResponse({
                'success': False,
                'error': 'ID de emisor requerido'
            })
        
        emisor = Emisor.objects.get(codigo=emisor_id)
        
        # Validar configuración
        config_validacion = ConfiguracionEntornoService.validar_configuracion_emisor(emisor)
        
        if not config_validacion['valido']:
            return JsonResponse({
                'success': False,
                'error': 'Configuración del emisor inválida',
                'detalles': config_validacion['errores']
            })
        
        # Probar conexión
        from .services.facturacion_service import FacturacionService
        resultado = FacturacionService.probar_conexion_pac(emisor_id)
        
        return JsonResponse(resultado)
        
    except Emisor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Emisor no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error probando conexión: {str(e)}'
        }, status=500)


@login_required
@staff_member_required
def estado_sistema_ajax(request):
    """Vista AJAX para obtener estado del sistema"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Verificar emisores
        emisores_activos = Emisor.objects.filter(activo=True).count()
        emisores_con_problemas = 0
        
        for emisor in Emisor.objects.filter(activo=True):
            config_validacion = ConfiguracionEntornoService.validar_configuracion_emisor(emisor)
            if not config_validacion['valido']:
                emisores_con_problemas += 1
                continue
            
            cert_validacion = CertificadoService.validar_certificado_completo(emisor)
            if not cert_validacion['valido']:
                emisores_con_problemas += 1
        
        # Verificar catálogos SAT
        directorio_catalogos = os.path.join(settings.BASE_DIR, 'static', 'catalogos_sat')
        catalogos_actualizados = 0
        catalogos_desactualizados = 0
        
        if os.path.exists(directorio_catalogos):
            for archivo in os.listdir(directorio_catalogos):
                if archivo.endswith('.json'):
                    archivo_path = os.path.join(directorio_catalogos, archivo)
                    fecha_modificacion = os.path.getmtime(archivo_path)
                    dias_desde_modificacion = (timezone.now().timestamp() - fecha_modificacion) / (24 * 3600)
                    
                    if dias_desde_modificacion < 7:
                        catalogos_actualizados += 1
                    else:
                        catalogos_desactualizados += 1
        
        return JsonResponse({
            'success': True,
            'emisores': {
                'total': emisores_activos,
                'con_problemas': emisores_con_problemas,
                'validos': emisores_activos - emisores_con_problemas
            },
            'catalogos': {
                'actualizados': catalogos_actualizados,
                'desactualizados': catalogos_desactualizados
            },
            'fecha_verificacion': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error obteniendo estado: {str(e)}'
        }, status=500)
