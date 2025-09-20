"""
Vistas AJAX para catálogos SAT
"""

import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .services.sat_catalog_service import SATCatalogService


@login_required
def obtener_usos_cfdi_ajax(request):
    """Vista AJAX para obtener el catálogo completo de usos CFDI"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
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
