from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q, F
from django.views.generic import ListView, TemplateView
from django.utils import timezone
from decimal import Decimal
import json

from .models import Factura, Cliente, PagoFactura
from .pago_forms import PagoFacturaForm, FiltroEstadoCuentaForm


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
            
            # Validar que no exceda el saldo pendiente
            saldo_pendiente = factura.obtener_saldo_pendiente()
            if monto_pago > saldo_pendiente:
                return JsonResponse({
                    'success': False,
                    'error': f'El monto del pago (${monto_pago}) no puede exceder el saldo pendiente (${saldo_pendiente})'
                })
            
            # Determinar tipo de pago
            if monto_pago >= saldo_pendiente:
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
    
    pagos = factura.pagos.all().order_by('-fecha_pago')
    
    pagos_data = []
    for pago in pagos:
        pagos_data.append({
            'id': pago.id,
            'fecha_pago': pago.fecha_pago.strftime('%d/%m/%Y %H:%M'),
            'monto': float(pago.monto_pago),
            'tipo': pago.get_tipo_pago_display(),
            'referencia': pago.referencia_pago or '',
            'observaciones': pago.observaciones or '',
            'usuario': pago.usuario_registro.nombre,
            'saldo_anterior': float(pago.saldo_anterior),
            'saldo_despues': float(pago.saldo_despues),
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
