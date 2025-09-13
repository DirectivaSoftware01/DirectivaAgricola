from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
from datetime import datetime
from decimal import Decimal
from .models import Emisor, Cliente, ProductoServicio, Factura, FacturaDetalle
from django.core.paginator import Paginator


class FacturacionView(LoginRequiredMixin, TemplateView):
    """Vista para crear facturas"""
    template_name = 'core/facturacion.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Facturación'
        
        # Obtener emisores activos
        context['emisores'] = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        # Obtener clientes activos
        context['clientes'] = Cliente.objects.filter(activo=True).order_by('razon_social')
        
        # Obtener productos/servicios activos
        context['productos'] = ProductoServicio.objects.filter(activo=True).order_by('descripcion')
        
        return context


@login_required
def obtener_emisor_ajax(request, codigo):
    """Vista AJAX para obtener datos del emisor"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        emisor = get_object_or_404(Emisor, codigo=codigo, activo=True)
        
        data = {
            'success': True,
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
            }
        }
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def obtener_cliente_ajax(request, codigo):
    """Vista AJAX para obtener datos del cliente"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        cliente = get_object_or_404(Cliente, codigo=codigo, activo=True)
        
        data = {
            'success': True,
            'cliente': {
                'codigo': cliente.codigo,
                'razon_social': cliente.razon_social,
                'rfc': cliente.rfc,
                'codigo_postal': cliente.codigo_postal,
                'regimen_fiscal': cliente.regimen_fiscal.regimen if cliente.regimen_fiscal else '',
                'regimen_fiscal_display': cliente.regimen_fiscal.descripcion if cliente.regimen_fiscal else '',
            }
        }
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def obtener_producto_ajax(request, codigo):
    """Vista AJAX para obtener datos del producto"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        producto = get_object_or_404(ProductoServicio, codigo=codigo, activo=True)
        
        # Calcular tasa de impuesto según el tipo
        tasa_impuesto = 0.0
        if producto.impuesto == 'IVA_16':
            tasa_impuesto = 0.16
        elif producto.impuesto in ['IVA_0', 'IVA_EXENTO']:
            tasa_impuesto = 0.0
        
        data = {
            'success': True,
            'producto': {
                'codigo': producto.codigo,
                'descripcion': producto.descripcion,
                'clave_prod_serv': producto.clave_sat,  # Clave SAT
                'unidad_medida': producto.unidad_medida,
                'impuesto': producto.impuesto,  # Tipo de impuesto (IVA_16, IVA_0, etc.)
                'tasa_impuesto': tasa_impuesto,  # Tasa calculada (0.16, 0.0)
            }
        }
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def guardar_factura_ajax(request):
    """Vista AJAX para guardar factura"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener datos del formulario
        serie = request.POST.get('serie', '').strip()
        fecha_emision = request.POST.get('fecha_emision', '').strip()
        emisor_id = request.POST.get('emisor_id', '').strip()
        lugar_expedicion = request.POST.get('lugar_expedicion', '').strip()
        receptor_id = request.POST.get('receptor_id', '').strip()
        uso_cfdi = request.POST.get('uso_cfdi', '').strip()
        exportacion = request.POST.get('exportacion', '01').strip()
        metodo_pago = request.POST.get('metodo_pago', 'PUE').strip()
        moneda = request.POST.get('moneda', 'MXN').strip()
        forma_pago = request.POST.get('forma_pago', '99').strip()
        tipo_cambio = request.POST.get('tipo_cambio', '1.0000').strip()
        
        # Validar campos requeridos
        if not serie or not fecha_emision or not emisor_id or not receptor_id:
            return JsonResponse({'error': 'Faltan campos requeridos'}, status=400)
        
        # Obtener emisor y receptor
        emisor = get_object_or_404(Emisor, codigo=emisor_id, activo=True)
        receptor = get_object_or_404(Cliente, codigo=receptor_id, activo=True)
        
        # Crear factura
        factura = Factura.objects.create(
            serie=serie,
            fecha_emision=datetime.strptime(fecha_emision, '%Y-%m-%dT%H:%M'),
            emisor=emisor,
            lugar_expedicion=lugar_expedicion,
            receptor=receptor,
            uso_cfdi=uso_cfdi,
            exportacion=exportacion,
            metodo_pago=metodo_pago,
            moneda=moneda,
            forma_pago=forma_pago,
            tipo_cambio=Decimal(str(tipo_cambio)),
            usuario_creacion=request.user
        )
        
        # Obtener detalles de la factura
        detalles_data = json.loads(request.POST.get('detalles', '[]'))
        subtotal = Decimal('0')
        impuesto_total = Decimal('0')
        
        for detalle_data in detalles_data:
            producto = get_object_or_404(ProductoServicio, codigo=detalle_data['producto_id'])
            
            cantidad = Decimal(str(detalle_data['cantidad']))
            precio = Decimal(str(detalle_data['precio']))
            importe = cantidad * precio
            
            # Calcular impuesto según la tasa del producto
            impuesto_concepto = Decimal('0')
            if detalle_data.get('objeto_impuesto') == '02':
                # Obtener la tasa de impuesto del producto
                if producto.impuesto == 'IVA_16':
                    impuesto_concepto = importe * Decimal('0.16')
                elif producto.impuesto in ['IVA_0', 'IVA_EXENTO']:
                    impuesto_concepto = Decimal('0')
            
            # Crear detalle
            FacturaDetalle.objects.create(
                factura=factura,
                producto_servicio=producto,
                no_identificacion=detalle_data['no_identificacion'],
                concepto=detalle_data['concepto'],
                cantidad=cantidad,
                precio=precio,
                clave_prod_serv=detalle_data['clave_prod_serv'],
                unidad=detalle_data['unidad'],
                objeto_impuesto=detalle_data.get('objeto_impuesto', '02'),
                importe=importe,
                impuesto_concepto=impuesto_concepto
            )
            
            subtotal += importe
            impuesto_total += impuesto_concepto
        
        # Actualizar totales
        factura.subtotal = subtotal
        factura.impuesto = impuesto_total
        factura.total = subtotal + impuesto_total
        factura.save()
        
        data = {
            'success': True,
            'factura_id': factura.folio,
            'serie_folio': str(factura),
            'total': float(factura.total)
        }
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ListadoFacturasView(LoginRequiredMixin, TemplateView):
    """Vista para listar facturas emitidas"""
    template_name = 'core/listado_facturas.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros de filtrado
        fecha_desde = self.request.GET.get('fecha_desde', '')
        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        emisor_id = self.request.GET.get('emisor_id', '')
        receptor_id = self.request.GET.get('receptor_id', '')
        
        # Construir consulta
        facturas = Factura.objects.select_related('emisor', 'receptor').order_by('-fecha_creacion')
        
        # Aplicar filtros
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                facturas = facturas.filter(fecha_emision__date__gte=fecha_desde_obj)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                facturas = facturas.filter(fecha_emision__date__lte=fecha_hasta_obj)
            except ValueError:
                pass
        
        if emisor_id:
            facturas = facturas.filter(emisor__codigo=emisor_id)
        
        if receptor_id:
            facturas = facturas.filter(receptor__codigo=receptor_id)
        
        # Paginación
        paginator = Paginator(facturas, 20)  # 20 facturas por página
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Obtener emisores y receptores para los filtros
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        receptores = Cliente.objects.filter(activo=True).order_by('razon_social')
        
        # Calcular totales
        total_subtotal = sum(factura.subtotal for factura in page_obj)
        total_impuesto = sum(factura.impuesto for factura in page_obj)
        total_general = total_subtotal + total_impuesto
        
        context.update({
            'page_obj': page_obj,
            'facturas': page_obj,
            'emisores': emisores,
            'receptores': receptores,
            'total_subtotal': total_subtotal,
            'total_impuesto': total_impuesto,
            'total_general': total_general,
            'filtros': {
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'emisor_id': emisor_id,
                'receptor_id': receptor_id,
            }
        })
        
        return context


@login_required
def cancelar_factura_ajax(request, folio):
    """Vista AJAX para cancelar una factura"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener la factura
        factura = get_object_or_404(Factura, folio=folio)
        
        # Verificar que no esté ya cancelada
        if factura.cancelada:
            return JsonResponse({'error': 'La factura ya está cancelada'}, status=400)
        
        # Obtener datos del formulario
        motivo_cancelacion = request.POST.get('motivo_cancelacion', '').strip()
        uuid = request.POST.get('uuid', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()
        
        # Validar campos requeridos
        if not motivo_cancelacion:
            return JsonResponse({'error': 'El motivo de cancelación es requerido'}, status=400)
        
        if not uuid:
            return JsonResponse({'error': 'El UUID es requerido'}, status=400)
        
        # Actualizar la factura
        factura.cancelada = True
        factura.usuario_modificacion = request.user
        factura.save()
        
        # Aquí podrías guardar los datos de cancelación en un modelo separado si lo necesitas
        # Por ahora solo actualizamos el estado de cancelada
        
        return JsonResponse({
            'success': True,
            'message': f'Factura {factura.serie}-{factura.folio:04d} cancelada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class FacturaDetailView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar los detalles de una factura"""
    template_name = 'core/factura_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener la factura por folio
        folio = self.kwargs.get('folio')
        factura = get_object_or_404(Factura, folio=folio)
        
        # Obtener los detalles de la factura
        detalles = factura.detalles.all().order_by('id')
        
        # Calcular totales
        total_subtotal = sum(detalle.importe for detalle in detalles)
        total_impuesto = sum(detalle.impuesto_concepto for detalle in detalles)
        total_general = total_subtotal + total_impuesto
        
        context.update({
            'factura': factura,
            'detalles': detalles,
            'total_subtotal': total_subtotal,
            'total_impuesto': total_impuesto,
            'total_general': total_general,
        })
        
        return context
