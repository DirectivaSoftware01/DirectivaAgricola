"""
Vistas AJAX para catálogos SAT
"""

import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .services.sat_catalog_service import SATCatalogService
from .models import AutorizoGasto


@login_required
def obtener_usos_cfdi_ajax(request):
    """Vista AJAX para obtener el catálogo completo de usos CFDI"""
    # Permitir a usuarios autenticados consultar catálogos
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        resultado = SATCatalogService.obtener_usos_cfdi()
        
        if resultado['exito']:
            return JsonResponse({
                'success': True,
                'usos_cfdi': resultado['usos_cfdi'],
                'total': resultado['total']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': resultado.get('error', 'Error obteniendo catálogo de usos CFDI')
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def obtener_autorizo_gastos_ajax(request):
    """Vista AJAX para obtener la lista de personas que autorizan gastos"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        autorizos = AutorizoGasto.objects.filter(activo=True).order_by('nombre')
        autorizos_list = [{'id': autorizo.id, 'nombre': autorizo.nombre} for autorizo in autorizos]
        
        return JsonResponse({
            'success': True,
            'autorizos': autorizos_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def crear_autorizo_gasto_ajax(request):
    """Vista AJAX para crear una nueva persona que autoriza gastos"""
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip()
        
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        # Verificar si ya existe
        if AutorizoGasto.objects.filter(nombre__iexact=nombre).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una persona con ese nombre'
            }, status=400)
        
        # Crear nuevo autorizo
        autorizo = AutorizoGasto.objects.create(nombre=nombre)
        
        return JsonResponse({
            'success': True,
            'autorizo': {
                'id': autorizo.id,
                'nombre': autorizo.nombre
            },
            'message': 'Persona agregada exitosamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
