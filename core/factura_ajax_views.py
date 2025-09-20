"""
Vistas AJAX adicionales para facturación
"""

import json
from datetime import datetime
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Emisor, Cliente, ProductoServicio, Factura, FacturaDetalle


@login_required
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
                'archivo_certificado': emisor.archivo_certificado[:100] + '...' if emisor.archivo_certificado and len(emisor.archivo_certificado) > 100 else emisor.archivo_certificado,
                'archivo_llave': emisor.archivo_llave[:100] + '...' if emisor.archivo_llave and len(emisor.archivo_llave) > 100 else emisor.archivo_llave,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def obtener_cliente_ajax(request, codigo):
    """Vista AJAX para obtener datos de un cliente"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        cliente = get_object_or_404(Cliente, codigo=codigo)
        
        return JsonResponse({
            'success': True,
            'cliente': {
                'codigo': cliente.codigo,
                'nombre': cliente.razon_social,
                'rfc': cliente.rfc,
                'codigo_postal': cliente.codigo_postal,
                'regimen_fiscal': cliente.regimen_fiscal,
                'regimen_fiscal_display': cliente.get_regimen_fiscal_display(),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def obtener_producto_ajax(request, codigo):
    """Vista AJAX para obtener datos de un producto/servicio"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        producto = get_object_or_404(ProductoServicio, codigo=codigo)
        
        return JsonResponse({
            'success': True,
            'producto': {
                'codigo': producto.codigo,
                'nombre': producto.descripcion,
                'clave_prod_serv': producto.clave_sat,
                'unidad_medida': producto.unidad_medida,
                'descripcion': producto.descripcion,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def guardar_factura_ajax(request):
    """Vista AJAX para guardar una factura"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener datos del formulario
        serie = request.POST.get('serie')
        fecha_emision = request.POST.get('fecha_emision')
        emisor_id = request.POST.get('emisor_id')
        lugar_expedicion = request.POST.get('lugar_expedicion')
        receptor_id = request.POST.get('receptor_id')
        uso_cfdi = request.POST.get('uso_cfdi')
        exportacion = request.POST.get('exportacion')
        metodo_pago = request.POST.get('metodo_pago')
        moneda = request.POST.get('moneda')
        forma_pago = request.POST.get('forma_pago')
        tipo_cambio = request.POST.get('tipo_cambio')
        detalles_json = request.POST.get('detalles')
        
        # Validar datos obligatorios
        if not all([serie, fecha_emision, emisor_id, lugar_expedicion, receptor_id, uso_cfdi]):
            return JsonResponse({
                'success': False,
                'error': 'Faltan datos obligatorios'
            })
        
        # Obtener objetos relacionados
        emisor = get_object_or_404(Emisor, codigo=emisor_id)
        receptor = get_object_or_404(Cliente, codigo=receptor_id)
        
        # Obtener campos de información global (solo para RFC XAXX010101000)
        periodicidad = request.POST.get('periodicidad')
        meses = request.POST.get('meses')
        año_informacion_global = request.POST.get('año_informacion_global')
        
        # Crear factura con valores iniciales para subtotal y total
        factura_data = {
            'serie': serie,
            'fecha_emision': datetime.fromisoformat(fecha_emision.replace('Z', '+00:00')),
            'emisor': emisor,
            'lugar_expedicion': lugar_expedicion,
            'receptor': receptor,
            'uso_cfdi': uso_cfdi,
            'exportacion': exportacion,
            'metodo_pago': metodo_pago,
            'moneda': moneda,
            'forma_pago': forma_pago,
            'tipo_cambio': Decimal(str(tipo_cambio)) if tipo_cambio else Decimal('1.0'),
            'subtotal': Decimal('0.0000'),  # Valor inicial
            'total': Decimal('0.0000'),     # Valor inicial
            'usuario_creacion': request.user
        }
        
        # Agregar campos de información global si están presentes
        if periodicidad:
            factura_data['periodicidad'] = periodicidad
        if meses:
            factura_data['meses'] = meses
        if año_informacion_global:
            factura_data['año_informacion_global'] = int(año_informacion_global)
        
        factura = Factura.objects.create(**factura_data)
        
        # Procesar detalles
        detalles = json.loads(detalles_json) if detalles_json else []
        subtotal = Decimal('0.00')
        impuesto = Decimal('0.00')
        
        print(f"DEBUG: Procesando {len(detalles)} detalles")
        
        for i, detalle_data in enumerate(detalles):
            print(f"DEBUG: Procesando detalle {i+1}: {detalle_data}")
            
            producto = get_object_or_404(ProductoServicio, codigo=detalle_data['producto_id'])
            
            # Convertir a Decimal para evitar errores de tipo
            cantidad = Decimal(str(detalle_data['cantidad']))
            precio = Decimal(str(detalle_data['precio']))
            
            # Calcular importe e impuesto
            importe = cantidad * precio
            from core.utils.tax_utils import calcular_impuesto_concepto
            impuesto_concepto = calcular_impuesto_concepto(
                importe, 
                producto.impuesto, 
                detalle_data['objeto_impuesto']
            )
            
            print(f"DEBUG: Cálculos - cantidad: {cantidad}, precio: {precio}, importe: {importe}, impuesto_concepto: {impuesto_concepto}")
            
            detalle = FacturaDetalle.objects.create(
                factura=factura,
                producto_servicio=producto,
                no_identificacion=detalle_data.get('no_identificacion', ''),
                concepto=detalle_data['concepto'],
                cantidad=cantidad,
                precio=precio,
                importe=importe,
                clave_prod_serv=detalle_data['clave_prod_serv'],
                unidad=detalle_data['unidad'],
                objeto_impuesto=detalle_data['objeto_impuesto'],
                impuesto_concepto=impuesto_concepto
            )
            
            subtotal += importe
            impuesto += impuesto_concepto
            
            print(f"DEBUG: Acumulados - subtotal: {subtotal}, impuesto: {impuesto}")
        
        # Actualizar totales con precisión de 4 decimales
        from decimal import ROUND_HALF_UP
        factura.subtotal = subtotal.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        factura.impuesto = impuesto.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        factura.total = (subtotal + impuesto).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        
        print(f"DEBUG: Totales finales - subtotal: {factura.subtotal}, impuesto: {factura.impuesto}, total: {factura.total}")
        
        # Verificar que los valores no sean None o nulos
        if factura.subtotal is None:
            print("ERROR: subtotal es None, estableciendo a 0.0000")
            factura.subtotal = Decimal('0.0000')
        if factura.total is None:
            print("ERROR: total es None, estableciendo a 0.0000")
            factura.total = Decimal('0.0000')
        if factura.impuesto is None:
            print("ERROR: impuesto es None, estableciendo a 0.0000")
            factura.impuesto = Decimal('0.0000')
        
        try:
            factura.save()
            print(f"DEBUG: Factura guardada con folio: {factura.folio}")
            print(f"DEBUG: Valores finales en BD - subtotal: {factura.subtotal}, impuesto: {factura.impuesto}, total: {factura.total}")
        except Exception as save_error:
            print(f"ERROR al guardar factura: {save_error}")
            print(f"ERROR - Valores problemáticos - subtotal: {factura.subtotal}, impuesto: {factura.impuesto}, total: {factura.total}")
            return JsonResponse({
                'success': False,
                'error': f'Error al guardar factura: {str(save_error)}'
            })
        
        return JsonResponse({
            'success': True,
            'factura_id': factura.folio,
            'serie_folio': f"{factura.serie}-{factura.folio:06d}",
            'message': 'Factura guardada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def timbrar_factura_ajax(request, folio):
    """Vista AJAX para timbrar una factura"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from .services.facturacion_service import FacturacionService
        
        # Obtener la factura por folio
        factura = get_object_or_404(Factura, folio=folio)
        
        # Intentar timbrar la factura
        resultado = FacturacionService.timbrar_factura(factura)
        
        if resultado['exito']:
            return JsonResponse({
                'success': True,
                'message': 'Factura timbrada exitosamente',
                'serie_folio': f"A-{folio:06d}",
                'uuid': resultado.get('uuid', ''),
                'fecha_timbrado': resultado.get('fecha_timbrado', ''),
                'estado': 'TIMBRADO'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': resultado.get('error', 'Error desconocido al timbrar'),
                'codigo_error': resultado.get('codigo_error', 'UNKNOWN_ERROR'),
                'detalles': resultado.get('detalles', [])
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

@login_required
def probar_conexion_pac_ajax(request, emisor_id):
    """Vista AJAX para probar la conexión con el PAC"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from .services.facturacion_service import FacturacionService
        
        # Probar conexión con el PAC
        resultado = FacturacionService.probar_conexion_pac(emisor_id)
        
        if resultado['exito']:
            return JsonResponse({
                'success': True,
                'message': resultado.get('mensaje', 'Conexión exitosa'),
                'tiempo_respuesta': resultado.get('tiempo_respuesta', 0)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': resultado.get('error', 'Error desconocido'),
                'codigo_error': resultado.get('codigo_error', 'UNKNOWN_ERROR')
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
