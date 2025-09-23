from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Q, F
from django.views.generic import ListView, TemplateView
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from datetime import datetime
import json
import logging
import os

logger = logging.getLogger(__name__)

from .models import Factura, Cliente, PagoFactura
from .pago_forms import PagoFacturaForm, FiltroEstadoCuentaForm
from .services.complemento_pago_xml_builder import ComplementoPagoXMLBuilder
from .services.timbrado_service import TimbradoService
from .services.configuracion_entorno import ConfiguracionEntornoService
from .services.certificado_service import CertificadoService


class EstadoCuentaView(ListView):
    """Vista para mostrar el estado de cuenta de un cliente"""
    template_name = 'core/estado_cuenta_standalone.html'
    context_object_name = 'facturas'
    paginate_by = 20
    
    def get_queryset(self):
        """Obtiene las facturas PPD del cliente"""
        cliente_id = self.kwargs.get('cliente_id')
        cliente = get_object_or_404(Cliente, codigo=cliente_id)
        
        # Obtener facturas PPD del cliente
        facturas = Factura.objects.filter(
            receptor=cliente,
            metodo_pago='PPD'
        ).order_by('-fecha_emision')
        
        return facturas
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente_id = self.kwargs.get('cliente_id')
        cliente = get_object_or_404(Cliente, codigo=cliente_id)
        
        # Calcular totales
        facturas = self.get_queryset()
        total_facturado = facturas.aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')
        
        total_pagado = PagoFactura.objects.filter(
            factura__receptor=cliente,
            factura__metodo_pago='PPD'
        ).aggregate(
            total=Sum('monto_pago')
        )['total'] or Decimal('0.00')
        
        saldo_pendiente = total_facturado - total_pagado
        
        context.update({
            'cliente': cliente,
            'total_facturado': total_facturado,
            'total_pagado': total_pagado,
            'saldo_pendiente': saldo_pendiente,
            'fecha_actual': timezone.now().strftime('%d/%m/%Y %H:%M'),
        })
        
        return context


@login_required
def registrar_pago(request, factura_id):
    """Vista para registrar un pago de factura"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para realizar esta acción'}, status=403)
    
    factura = get_object_or_404(Factura, folio=factura_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validar que la factura sea PPD
            if factura.metodo_pago != 'PPD':
                return JsonResponse({
                    'success': False,
                    'error': 'Solo se pueden registrar pagos para facturas con método PPD (crédito)'
                })
            
            # Validar monto
            monto_pago = Decimal(str(data.get('monto_pago', 0)))
            if monto_pago <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'El monto del pago debe ser mayor a cero'
                })
            
            # Validar que no exceda el saldo anterior real (antes de aplicar este pago)
            # Usar únicamente saldo del servidor (solo pagos timbrados), ignorando valores calculados en la UI
            saldo_servidor = factura.obtener_saldo_pendiente()
            logger.info(f"Validación CP: factura={factura.folio}, total={factura.total}, saldo_servidor={saldo_servidor}, monto_solicitado={monto_pago}")
            if monto_pago > saldo_servidor:
                return JsonResponse({
                    'success': False,
                    'error': f'El monto del pago (${monto_pago}) no puede exceder el saldo pendiente (${saldo_servidor})'
                })
            
            # Determinar tipo de pago
            if monto_pago >= saldo_servidor:
                tipo_pago = 'COMPLETO'
            else:
                tipo_pago = 'PARCIAL'
            
            # Crear el pago
            pago = PagoFactura.objects.create(
                factura=factura,
                monto_pago=monto_pago,
                tipo_pago=tipo_pago,
                referencia_pago=data.get('referencia_pago', ''),
                observaciones=data.get('observaciones', ''),
                num_parcialidad=int(data.get('num_parcialidad', 1)),
                forma_pago=data.get('forma_pago', '03'),
                fecha_pago=data.get('fecha_pago'),
                usuario_registro=request.user
            )
            
            # Actualizar estado de la factura si está completamente pagada
            if factura.esta_pagada():
                factura.estado = 'PAGADA'
                factura.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Pago registrado correctamente',
                'pago': {
                    'id': pago.id,
                    'monto': float(pago.monto_pago),
                    'tipo': pago.get_tipo_pago_display(),
                    'fecha': pago.fecha_pago.strftime('%d/%m/%Y %H:%M'),
                    'referencia': pago.referencia_pago or '',
                    'saldo_anterior': float(pago.saldo_anterior),
                    'saldo_despues': float(pago.saldo_despues),
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Error al procesar los datos del pago'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al registrar el pago: {str(e)}'
            })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def obtener_historial_pagos(request, factura_id):
    """Vista para obtener el historial de pagos de una factura"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para realizar esta acción'}, status=403)
    
    factura = get_object_or_404(Factura, folio=factura_id)
    
    pagos = factura.pagos.all().order_by('-fecha_creacion')
    
    pagos_data = []
    for pago in pagos:
        pagos_data.append({
            'id': pago.id,
            'fecha_documento': pago.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'fecha_pago': pago.fecha_pago.strftime('%d/%m/%Y %H:%M'),
            'monto': float(pago.monto_pago),
            'tipo': pago.get_tipo_pago_display(),
            'referencia': pago.referencia_pago or '',
            'observaciones': pago.observaciones or '',
            'usuario': pago.usuario_registro.nombre,
            'saldo_anterior': float(pago.saldo_anterior),
            'saldo_despues': float(pago.saldo_despues),
            'uuid': pago.uuid or '',
            'timbrado': bool(pago.xml_timbrado),
            'num_parcialidad': pago.num_parcialidad,
        })
    
    return JsonResponse({
        'success': True,
        'factura': {
            'serie': factura.serie,
            'folio': factura.folio,
            'total': float(factura.total),
            'total_pagado': float(factura.obtener_total_pagado()),
            'saldo_pendiente': float(factura.obtener_saldo_pendiente()),
            'estado_pago': factura.obtener_estado_pago(),
        },
        'pagos': pagos_data
    })


@login_required
def listado_estados_cuenta(request):
    """Vista para mostrar el listado de estados de cuenta por cliente"""
    if not request.user.is_staff:
        return render(request, 'core/error.html', {
            'error': 'No tienes permisos para acceder a esta sección'
        })
    
    # Obtener clientes con facturas PPD
    clientes_con_facturas = Cliente.objects.filter(
        facturas__metodo_pago='PPD'
    ).distinct().order_by('razon_social')
    
    # Calcular totales por cliente
    clientes_data = []
    for cliente in clientes_con_facturas:
        facturas = Factura.objects.filter(
            receptor=cliente,
            metodo_pago='PPD'
        )
        
        total_facturado = facturas.aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')
        
        total_pagado = PagoFactura.objects.filter(
            factura__receptor=cliente,
            factura__metodo_pago='PPD'
        ).aggregate(
            total=Sum('monto_pago')
        )['total'] or Decimal('0.00')
        
        saldo_pendiente = total_facturado - total_pagado
        
        # Contar facturas por estado
        facturas_pendientes = facturas.filter(
            pagos__isnull=True
        ).count()
        
        facturas_parciales = facturas.filter(
            pagos__isnull=False
        ).exclude(
            pagos__monto_pago__gte=models.F('total')
        ).distinct().count()
        
        facturas_pagadas = facturas.filter(
            pagos__monto_pago__gte=models.F('total')
        ).distinct().count()
        
        clientes_data.append({
            'cliente': cliente,
            'total_facturado': total_facturado,
            'total_pagado': total_pagado,
            'saldo_pendiente': saldo_pendiente,
            'facturas_pendientes': facturas_pendientes,
            'facturas_parciales': facturas_parciales,
            'facturas_pagadas': facturas_pagadas,
            'total_facturas': facturas.count(),
        })
    
    context = {
        'clientes_data': clientes_data,
        'fecha_actual': timezone.now().strftime('%d/%m/%Y %H:%M'),
    }
    
    return render(request, 'core/listado_estados_cuenta.html', context)


class ComplementoPagoView(TemplateView):
    """Vista principal para el complemento de pago"""
    template_name = 'core/complemento_pago.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener facturas PPD pendientes de pago
        facturas_ppd = Factura.objects.filter(
            metodo_pago='PPD'
        ).select_related('receptor', 'emisor').order_by('-fecha_emision')
        
        # Agrupar por cliente
        clientes_con_facturas = {}
        for factura in facturas_ppd:
            cliente = factura.receptor
            if cliente.codigo not in clientes_con_facturas:
                clientes_con_facturas[cliente.codigo] = {
                    'cliente': cliente,
                    'facturas': [],
                    'total_facturado': Decimal('0.00'),
                    'total_pagado': Decimal('0.00'),
                    'saldo_pendiente': Decimal('0.00'),
                }
            
            total_pagado = factura.obtener_total_pagado()
            saldo_pendiente = factura.obtener_saldo_pendiente()
            
            clientes_con_facturas[cliente.codigo]['facturas'].append({
                'factura': factura,
                'total_pagado': total_pagado,
                'saldo_pendiente': saldo_pendiente,
                'estado_pago': factura.obtener_estado_pago(),
            })
            
            clientes_con_facturas[cliente.codigo]['total_facturado'] += factura.total
            clientes_con_facturas[cliente.codigo]['total_pagado'] += total_pagado
            clientes_con_facturas[cliente.codigo]['saldo_pendiente'] += saldo_pendiente
        
        # Calcular porcentaje de pago para cada cliente
        for cliente_data in clientes_con_facturas.values():
            if cliente_data['total_facturado'] > 0:
                porcentaje = (cliente_data['total_pagado'] / cliente_data['total_facturado']) * 100
                cliente_data['porcentaje_pagado'] = porcentaje
            else:
                cliente_data['porcentaje_pagado'] = 0
        
        context.update({
            'clientes_data': list(clientes_con_facturas.values()),
            'fecha_actual': timezone.now().strftime('%d/%m/%Y %H:%M'),
        })
        
        return context


@login_required
def obtener_info_factura_ajax(request, factura_id):
    """Vista AJAX para obtener información de una factura"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para realizar esta acción'}, status=403)
    
    factura = get_object_or_404(Factura, folio=factura_id)
    
    return JsonResponse({
        'success': True,
        'factura': {
            'serie': factura.serie,
            'folio': factura.folio,
            'total': float(factura.total),
            'total_pagado': float(factura.obtener_total_pagado()),
            'saldo_pendiente': float(factura.obtener_saldo_pendiente()),
            'estado_pago': factura.obtener_estado_pago(),
        }
    })


@login_required
def guardar_complemento_pago_ajax(request, factura_id):
    """Vista AJAX para guardar complemento de pago"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para realizar esta acción'}, status=403)
    
    factura = get_object_or_404(Factura, folio=factura_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validar que la factura sea PPD
            if factura.metodo_pago != 'PPD':
                return JsonResponse({
                    'success': False,
                    'error': 'Solo se pueden registrar complementos de pago para facturas con método PPD (crédito)'
                })
            
            # Validar datos requeridos
            monto_pago = Decimal(str(data.get('monto', 0)))
            if monto_pago <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'El monto del pago debe ser mayor a cero'
                })
            
            # Validar que no exceda el saldo anterior real (antes de aplicar este pago)
            pagos_anteriores = factura.pagos.aggregate(total=Sum('monto_pago'))['total'] or Decimal('0.00')
            saldo_anterior = factura.total - pagos_anteriores
            if monto_pago > saldo_anterior:
                return JsonResponse({
                    'success': False,
                    'error': f'El monto del pago (${monto_pago}) no puede exceder el saldo pendiente (${saldo_anterior})'
                })
            
            # Determinar tipo de pago
            if monto_pago >= saldo_anterior:
                tipo_pago = 'COMPLETO'
            else:
                tipo_pago = 'PARCIAL'
            
            # Generar y timbrar XML del complemento de pago PRIMERO
            try:
                # Obtener configuración del PAC
                config_service = ConfiguracionEntornoService()
                configuracion = config_service.obtener_configuracion_pac(factura.emisor)
                
                # Debug: verificar tipo de configuración
                if not isinstance(configuracion, dict):
                    return JsonResponse({
                        'success': False,
                        'error': f'Error en configuración PAC: se esperaba diccionario, se recibió {type(configuracion)}'
                    })
                
                # Verificar que la configuración tenga los campos necesarios
                if 'url' not in configuracion or 'credenciales' not in configuracion:
                    return JsonResponse({
                        'success': False,
                        'error': f'Configuración PAC incompleta: {configuracion}'
                    })
                
                # Obtener certificado del emisor
                certificado_data = CertificadoService.extraer_datos_certificado(factura.emisor)
                
                # Debug: verificar certificado data
                logger.info(f"Certificado data obtenido: {certificado_data}")
                
                if not certificado_data or not certificado_data.get('valido'):
                    return JsonResponse({
                        'success': False,
                        'error': f'No se pudo obtener el certificado del emisor: {certificado_data.get("error", "Error desconocido")}'
                    })
                
                # Verificar que el certificado no esté vacío
                if not certificado_data.get('certificado_base64'):
                    return JsonResponse({
                        'success': False,
                        'error': 'El certificado del emisor está vacío'
                    })
                
                # Cargar llave privada
                llave_privada = CertificadoService.cargar_llave_privada(factura.emisor)
                if not llave_privada:
                    return JsonResponse({
                        'success': False,
                        'error': 'No se pudo cargar la llave privada del emisor'
                    })
                
                # Recalcular saldo del servidor por seguridad
                saldo_servidor = factura.obtener_saldo_pendiente()
                
                # Forzar saldos coherentes desde servidor para el XML (ignorar lo que venga de la UI)
                saldo_anterior_num = Decimal(saldo_servidor)
                saldo_insoluto_num = max(saldo_anterior_num - monto_pago, Decimal('0.00'))
                data['imp_saldo_ant'] = f"{saldo_anterior_num:.2f}"
                data['imp_pagado'] = f"{monto_pago:.2f}"
                data['imp_saldo_insoluto'] = f"{saldo_insoluto_num:.2f}"
                
                # Debug: Log de los datos que se van a usar para generar el XML
                logger.info(f"Datos del pago para XML (normalizados): {data}")
                logger.info(f"Certificado data: {certificado_data}")
                
                # Generar cadena original primero (como en facturación)
                cadena_original = ComplementoPagoXMLBuilder.generar_cadena_original_desde_modelos(factura, data)
                logger.info(f"Cadena original generada: {cadena_original[:200]}...")
                
                # Generar sello digital
                sello = CertificadoService.generar_sello_digital(cadena_original, llave_privada)
                
                if not sello:
                    return JsonResponse({
                        'success': False,
                        'error': 'No se pudo generar el sello digital'
                    })
                
                logger.info(f"Sello digital generado: {sello[:50]}...")
                
                # Generar XML del complemento de pago CON sello (como en facturación)
                xml_complemento = ComplementoPagoXMLBuilder.construir_xml_complemento_pago(
                    factura, data, certificado_data, sello
                )
                
                logger.info(f"XML final con sello generado: {xml_complemento[:500]}...")
                
                # Guardar XML para debugging
                debug_dir = os.path.join(settings.MEDIA_ROOT, 'debug_xml')
                os.makedirs(debug_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Guardar XML enviado
                debug_file_sent = os.path.join(debug_dir, f'complemento_pago_enviado_{factura.folio}_{timestamp}.xml')
                with open(debug_file_sent, 'w', encoding='utf-8') as f:
                    f.write(xml_complemento)
                logger.info(f"XML enviado guardado para debugging en: {debug_file_sent}")
                
                # Timbrar con PAC
                timbrado_service = TimbradoService(configuracion, factura.emisor)
                resultado_timbrado = timbrado_service.timbrar_cfdi(xml_complemento)
                
                # Guardar respuesta del PAC
                debug_file_response = os.path.join(debug_dir, f'complemento_pago_respuesta_{factura.folio}_{timestamp}.txt')
                with open(debug_file_response, 'w', encoding='utf-8') as f:
                    f.write(f"Resultado del timbrado: {resultado_timbrado}\n\n")
                    f.write(f"XML enviado:\n{xml_complemento}\n\n")
                    f.write(f"Respuesta completa del PAC:\n{resultado_timbrado.get('xml_respuesta', 'No disponible')}")
                logger.info(f"Respuesta del PAC guardada para debugging en: {debug_file_response}")
                
                # Debug: Log del resultado del timbrado
                logger.info(f"Resultado del timbrado: {resultado_timbrado}")
                logger.info(f"timbradoOk: {resultado_timbrado.get('timbradoOk')}")
                logger.info(f"exito: {resultado_timbrado.get('exito')}")
                
                if resultado_timbrado.get('timbradoOk') or resultado_timbrado.get('exito'):
                    # SOLO SI EL TIMBRADO ES EXITOSO, crear el pago
                    pago = PagoFactura.objects.create(
                        factura=factura,
                        monto_pago=monto_pago,
                        tipo_pago=tipo_pago,
                        referencia_pago=data.get('referencia_pago', ''),
                        observaciones=data.get('observaciones', ''),
                        num_parcialidad=int(data.get('num_parcialidad', 1)),
                        forma_pago=data.get('forma_pago', '03'),
                        fecha_pago=data.get('fecha_pago'),
                        usuario_registro=request.user
                    )
                    
                    # Los saldos se calculan automáticamente mediante propiedades del modelo
                    
                    # Debug: verificar campos del resultado (aceptar snake_case y camelCase)
                    xml_base64 = resultado_timbrado.get('xmlBase64') or resultado_timbrado.get('xml_base64', '')
                    uuid = resultado_timbrado.get('uuid', '')
                    logger.info(f"Debug timbrado exitoso - xmlBase64: {bool(xml_base64)}, uuid: {uuid}")
                    
                    # Guardar datos del timbrado
                    pago.xml_timbrado = xml_base64
                    pago.uuid = uuid
                    pago.sello = resultado_timbrado.get('selloCFD') or resultado_timbrado.get('sello_cfd', '')
                    pago.sello_sat = resultado_timbrado.get('selloSAT') or resultado_timbrado.get('sello_sat', '')
                    pago.no_certificado_sat = resultado_timbrado.get('noCertificadoSAT') or resultado_timbrado.get('no_certificado_sat', '')
                    pago.fecha_timbrado = resultado_timbrado.get('FechaTimbrado') or resultado_timbrado.get('fecha_timbrado', '')
                    
                    # Guardar código QR y cadena original del PAC
                    pago.codigo_qr = resultado_timbrado.get('qr_base64', '')
                    pago.cadena_original_sat = resultado_timbrado.get('cadena_original_sat', '')
                    
                    pago.save()
                    
                    # Actualizar estado de la factura si está completamente pagada
                    if factura.esta_pagada():
                        factura.estado = 'PAGADA'
                        factura.save()
                    
                    mensaje = f'Complemento de pago registrado y timbrado exitosamente. UUID: {pago.uuid}'
                    
                    return JsonResponse({
                        'success': True,
                        'message': mensaje,
                        'pago': {
                            'id': pago.id,
                            'monto': float(pago.monto_pago),
                            'tipo': pago.get_tipo_pago_display(),
                            'fecha': pago.fecha_pago.strftime('%d/%m/%Y %H:%M'),
                            'referencia': pago.referencia_pago or '',
                            'saldo_anterior': float(pago.saldo_anterior),
                            'saldo_despues': float(pago.saldo_despues),
                            'uuid': pago.uuid or '',
                            'timbrado': bool(pago.xml_timbrado)
                        }
                    })
                else:
                    # Si el timbrado falla, NO crear ni persistir pago
                    error_msg = resultado_timbrado.get('mensaje', resultado_timbrado.get('error', 'Error desconocido'))
                    codigo_error = resultado_timbrado.get('codigo_error', 'UNKNOWN')
                    logger.error(f"Timbrado falló - Error: {error_msg}, Código: {codigo_error}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Error en timbrado: {error_msg} (Código: {codigo_error})'
                    })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error en el proceso de timbrado: {str(e)}'
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Error al procesar los datos del complemento de pago'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al registrar el complemento de pago: {str(e)}'
            })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def imprimir_estado_cuenta(request, cliente_id):
    """Vista para imprimir el estado de cuenta de un cliente"""
    if not request.user.is_staff:
        return render(request, 'core/error.html', {
            'error': 'No tienes permisos para acceder a esta sección'
        })
    
    cliente = get_object_or_404(Cliente, codigo=cliente_id)
    
    # Obtener facturas PPD del cliente
    facturas = Factura.objects.filter(
        receptor=cliente,
        metodo_pago='PPD'
    ).order_by('-fecha_emision')
    
    # Calcular totales
    total_facturado = facturas.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')
    
    total_pagado = PagoFactura.objects.filter(
        factura__receptor=cliente,
        factura__metodo_pago='PPD'
    ).aggregate(
        total=Sum('monto_pago')
    )['total'] or Decimal('0.00')
    
    saldo_pendiente = total_facturado - total_pagado
    
    context = {
        'cliente': cliente,
        'facturas': facturas,
        'total_facturado': total_facturado,
        'total_pagado': total_pagado,
        'saldo_pendiente': saldo_pendiente,
        'fecha_actual': timezone.now().strftime('%d/%m/%Y %H:%M'),
        'title': f'Estado de Cuenta - {cliente.razon_social}'
    }
    
    return render(request, 'core/estado_cuenta_imprimir.html', context)


@login_required
def descargar_debug_xml(request, tipo, factura_folio, timestamp):
    """
    Descarga archivos de debugging del complemento de pago
    
    Args:
        tipo: 'enviado' o 'respuesta'
        factura_folio: Folio de la factura
        timestamp: Timestamp del archivo
    """
    try:
        debug_dir = os.path.join(settings.MEDIA_ROOT, 'debug_xml')
        
        if tipo == 'enviado':
            filename = f'complemento_pago_enviado_{factura_folio}_{timestamp}.xml'
            content_type = 'application/xml'
        elif tipo == 'respuesta':
            filename = f'complemento_pago_respuesta_{factura_folio}_{timestamp}.txt'
            content_type = 'text/plain'
        else:
            return HttpResponse('Tipo de archivo no válido', status=400)
        
        file_path = os.path.join(debug_dir, filename)
        
        if not os.path.exists(file_path):
            return HttpResponse('Archivo no encontrado', status=404)
        
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
    except Exception as e:
        logger.error(f"Error descargando archivo de debugging: {e}")
        return HttpResponse('Error al descargar el archivo', status=500)


@login_required
def vista_previa_complemento_pago(request, pago_id):
    """
    Vista para mostrar vista previa del PDF del complemento de pago
    """
    try:
        pago = get_object_or_404(PagoFactura, id=pago_id)
        
        # Debug: verificar estado del pago
        logger.info(f"Debug vista previa pago {pago_id}: uuid={pago.uuid}, xml_timbrado={bool(pago.xml_timbrado)}")
        
        # Verificar que el pago esté timbrado
        if not pago.uuid or not pago.xml_timbrado:
            logger.warning(f"Pago {pago_id} no está timbrado: uuid={pago.uuid}, xml_timbrado={bool(pago.xml_timbrado)}")
            return HttpResponse('El complemento de pago no está timbrado', status=400)
        
        # Generar vista previa usando PDFService
        from .services.pdf_service import PDFService
        html_content = PDFService.generar_vista_previa_complemento_pago(pago)
        return HttpResponse(html_content, content_type='text/html; charset=utf-8')
        
    except Exception as e:
        logger.error(f"Error generando vista previa de complemento de pago: {e}")
        return HttpResponse(f'Error generando vista previa: {str(e)}', status=500)


@login_required
def imprimir_complemento_pago(request, pago_id):
    """
    Vista para imprimir PDF del complemento de pago
    """
    try:
        pago = get_object_or_404(PagoFactura, id=pago_id)
        factura = pago.factura
        
        # Verificar que el pago esté timbrado
        if not pago.uuid or not pago.xml_timbrado:
            messages.error(request, 'El complemento de pago no está timbrado')
            return redirect('core:listado_facturas')
        
        # Decodificar el XML timbrado
        import base64
        xml_timbrado = base64.b64decode(pago.xml_timbrado).decode('utf-8')
        
        context = {
            'pago': pago,
            'factura': factura,
            'xml_timbrado': xml_timbrado,
        }
        
        return render(request, 'core/complemento_pago_pdf.html', context)
        
    except Exception as e:
        logger.error(f"Error imprimiendo complemento de pago: {e}")
        messages.error(request, 'Error al generar el PDF del complemento de pago')
        return redirect('core:listado_facturas')


@login_required
def descargar_xml_complemento_pago(request, pago_id):
    """
    Vista para descargar XML del complemento de pago
    """
    try:
        pago = get_object_or_404(PagoFactura, id=pago_id)
        
        # Verificar que el pago esté timbrado
        if not pago.uuid or not pago.xml_timbrado:
            messages.error(request, 'El complemento de pago no está timbrado')
            return redirect('core:listado_facturas')
        
        # Decodificar el XML timbrado
        import base64
        xml_timbrado = base64.b64decode(pago.xml_timbrado).decode('utf-8')
        
        # Crear respuesta HTTP con el XML
        response = HttpResponse(xml_timbrado, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="complemento_pago_{pago.uuid}.xml"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error descargando XML del complemento de pago: {e}")
        messages.error(request, 'Error al descargar el XML del complemento de pago')
        return redirect('core:listado_facturas')
