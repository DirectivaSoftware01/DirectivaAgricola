"""
Vistas AJAX específicas para emisores
"""

import json
import base64
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from ..models import Emisor, Usuario


@login_required
@csrf_exempt
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        emisores = Emisor.objects.all().order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'serie': emisor.serie,
                'timbrado_prueba': emisor.timbrado_prueba,
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'password_pac': emisor.password_pac,
                'password_llave': emisor.password_llave,
                'archivo_certificado': emisor.archivo_certificado,
                'nombre_archivo_certificado': emisor.nombre_archivo_certificado,
                'archivo_llave': emisor.archivo_llave,
                'nombre_archivo_llave': emisor.nombre_archivo_llave,
                'activo': emisor.activo,
                'fecha_modificacion': emisor.fecha_modificacion.isoformat() if emisor.fecha_modificacion else None,
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener datos del formulario
        razon_social = request.POST.get('razon_social', '').strip()
        rfc = request.POST.get('rfc', '').strip()
        codigo_postal = request.POST.get('codigo_postal', '').strip()
        serie = request.POST.get('serie', 'A').strip()
        password_llave = request.POST.get('password_llave', '').strip()
        nombre_pac = request.POST.get('nombre_pac', 'PRODIGIA').strip()
        contrato = request.POST.get('contrato', '').strip()
        usuario_pac = request.POST.get('usuario_pac', '').strip()
        password_pac = request.POST.get('password_pac', '').strip()
        timbrado_prueba = request.POST.get('timbrado_prueba', 'true').lower() == 'true'
        regimen_fiscal = request.POST.get('regimen_fiscal', '626').strip()
        
        # Procesar archivos
        archivo_certificado = None
        archivo_llave = None
        nombre_certificado = None
        nombre_llave = None
        
        if 'archivo_certificado' in request.FILES:
            archivo_certificado = request.FILES['archivo_certificado']
            nombre_certificado = archivo_certificado.name
            if archivo_certificado.size > 10 * 1024 * 1024:  # 10MB límite
                return JsonResponse({'error': 'El archivo de certificado es demasiado grande (máximo 10MB)'}, status=400)
        
        if 'archivo_llave' in request.FILES:
            archivo_llave = request.FILES['archivo_llave']
            nombre_llave = archivo_llave.name
            if archivo_llave.size > 10 * 1024 * 1024:  # 10MB límite
                return JsonResponse({'error': 'El archivo de llave es demasiado grande (máximo 10MB)'}, status=400)
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        if not archivo_certificado:
            return JsonResponse({'error': 'El archivo de certificado (.cer) es requerido'}, status=400)
        if not archivo_llave:
            return JsonResponse({'error': 'El archivo de llave (.key) es requerido'}, status=400)
        
        # Validar formato del RFC
        if len(rfc) not in [12, 13]:
            return JsonResponse({'error': 'El RFC debe tener 12 o 13 caracteres'}, status=400)
        
        # Validar formato del código postal
        if not codigo_postal.isdigit() or len(codigo_postal) != 5:
            return JsonResponse({'error': 'El código postal debe tener 5 dígitos'}, status=400)
        
        # Verificar que no exista un emisor con el mismo RFC
        if Emisor.objects.filter(rfc=rfc.upper()).exists():
            return JsonResponse({'error': 'Ya existe un emisor con este RFC'}, status=400)
        
        # Convertir archivos a base64
        certificado_base64 = None
        llave_base64 = None
        
        try:
            if archivo_certificado:
                certificado_base64 = base64.b64encode(archivo_certificado.read()).decode('utf-8')
                archivo_certificado.seek(0)  # Resetear el puntero del archivo
            
            if archivo_llave:
                llave_base64 = base64.b64encode(archivo_llave.read()).decode('utf-8')
                archivo_llave.seek(0)  # Resetear el puntero del archivo
        except Exception as e:
            return JsonResponse({'error': f'Error procesando archivos: {str(e)}'}, status=400)
        
        # Crear el emisor
        with transaction.atomic():
            emisor = Emisor.objects.create(
                razon_social=razon_social,
                rfc=rfc.upper(),
                codigo_postal=codigo_postal,
                regimen_fiscal=regimen_fiscal,
                serie=serie,
                password_llave=password_llave,
                archivo_certificado=certificado_base64,
                nombre_archivo_certificado=nombre_certificado,
                archivo_llave=llave_base64,
                nombre_archivo_llave=nombre_llave,
                nombre_pac=nombre_pac,
                contrato=contrato,
                usuario_pac=usuario_pac,
                password_pac=password_pac,
                timbrado_prueba=timbrado_prueba,
                usuario_creacion=request.user,
                usuario_modificacion=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'serie': emisor.serie,
                'timbrado_prueba': emisor.timbrado_prueba,
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'password_pac': emisor.password_pac,
                'password_llave': emisor.password_llave,
                'archivo_certificado': emisor.archivo_certificado,
                'nombre_archivo_certificado': emisor.nombre_archivo_certificado,
                'archivo_llave': emisor.archivo_llave,
                'nombre_archivo_llave': emisor.nombre_archivo_llave,
                'activo': emisor.activo,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def obtener_emisor_ajax(request, codigo):
    """Vista AJAX para obtener datos de un emisor"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        return JsonResponse({
            'success': True,
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'serie': emisor.serie,
                'timbrado_prueba': emisor.timbrado_prueba,
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'password_pac': emisor.password_pac,
                'password_llave': emisor.password_llave,
                'archivo_certificado': emisor.archivo_certificado[:100] + '...' if emisor.archivo_certificado and len(emisor.archivo_certificado) > 100 else emisor.archivo_certificado,
                'nombre_archivo_certificado': emisor.nombre_archivo_certificado,
                'archivo_llave': emisor.archivo_llave[:100] + '...' if emisor.archivo_llave and len(emisor.archivo_llave) > 100 else emisor.archivo_llave,
                'nombre_archivo_llave': emisor.nombre_archivo_llave,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def validar_emisor_ajax(request, codigo):
    """Vista AJAX para validar certificado de un emisor"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Importar el servicio de certificados
        from ..services.certificado_service import CertificadoService
        
        # Validar certificado completo
        resultado = CertificadoService.validar_certificado_completo(emisor)
        
        return JsonResponse({
            'success': True,
            'validacion': resultado
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor (eliminación lógica)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Verificar si ya está inactivo
        if not emisor.activo:
            return JsonResponse({
                'success': False,
                'error': 'El emisor ya está inactivo'
            }, status=400)
        
        # Marcar como inactivo (eliminación lógica)
        razon_social = emisor.razon_social
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Emisor "{razon_social}" desactivado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def reactivar_emisor_ajax(request, codigo):
    """Vista AJAX para reactivar un emisor"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Verificar si ya está activo
        if emisor.activo:
            return JsonResponse({
                'success': False,
                'error': 'El emisor ya está activo'
            }, status=400)
        
        # Reactivar el emisor
        razon_social = emisor.razon_social
        emisor.activo = True
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Emisor "{razon_social}" reactivado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
