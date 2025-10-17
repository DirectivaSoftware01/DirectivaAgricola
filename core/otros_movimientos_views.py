from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
import json

from .models import OtroMovimiento, OtroMovimientoDetalle, ProductoServicio, Almacen, Kardex
from .otros_movimientos_forms import OtroMovimientoForm, OtroMovimientoDetalleForm, OtroMovimientoSearchForm


@login_required
def otros_movimientos_list(request):
    """Vista para listar otros movimientos"""
    
    # Formulario de búsqueda
    search_form = OtroMovimientoSearchForm(request.GET)
    
    # Query base
    movimientos = OtroMovimiento.objects.all()
    
    # Aplicar filtros
    if search_form.is_valid():
        folio = search_form.cleaned_data.get('folio')
        tipo_movimiento = search_form.cleaned_data.get('tipo_movimiento')
        fecha_desde = search_form.cleaned_data.get('fecha_desde')
        fecha_hasta = search_form.cleaned_data.get('fecha_hasta')
        
        if folio:
            movimientos = movimientos.filter(folio=folio)
        
        if tipo_movimiento:
            movimientos = movimientos.filter(tipo_movimiento=tipo_movimiento)
        
        if fecha_desde:
            movimientos = movimientos.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            movimientos = movimientos.filter(fecha__lte=fecha_hasta)
    
    # Ordenar por fecha y folio
    movimientos = movimientos.order_by('-fecha', '-folio')
    
    # Paginación
    paginator = Paginator(movimientos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'title': 'Otros Movimientos'
    }
    
    return render(request, 'core/otros_movimientos_list.html', context)


@login_required
def otro_movimiento_create(request):
    """Vista para crear otro movimiento"""
    
    if request.method == 'POST':
        form = OtroMovimientoForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.usuario_creacion = request.user
            movimiento.save()
            
            # Procesar detalles si existen
            detalles_data = request.POST.get('detalles_data')
            if detalles_data:
                try:
                    detalles = json.loads(detalles_data)
                    for detalle_data in detalles:
                        producto = ProductoServicio.objects.get(codigo=detalle_data['producto'])
                        almacen_origen = Almacen.objects.get(codigo=detalle_data['almacen_origen']) if detalle_data.get('almacen_origen') else None
                        almacen_destino = Almacen.objects.get(codigo=detalle_data['almacen_destino']) if detalle_data.get('almacen_destino') else None
                        
                        OtroMovimientoDetalle.objects.create(
                            movimiento=movimiento,
                            producto=producto,
                            almacen_origen=almacen_origen,
                            almacen_destino=almacen_destino,
                            cantidad=Decimal(str(detalle_data['cantidad'])),
                            precio_unitario=Decimal(str(detalle_data['precio_unitario'])),
                            observaciones=detalle_data.get('observaciones', '')
                        )
                except Exception as e:
                    messages.error(request, f'Error al procesar detalles: {str(e)}')
                    return render(request, 'core/otros_movimientos_form.html', {'form': form, 'title': 'Crear Otro Movimiento'})
            
            messages.success(request, f'Movimiento {movimiento.folio} creado correctamente.')
            return redirect('core:otros_movimientos_list')
    else:
        form = OtroMovimientoForm()
    
    # Obtener datos para el template
    productos = ProductoServicio.objects.filter(activo=True).order_by('descripcion')
    almacenes = Almacen.objects.filter(activo=True).order_by('descripcion')
    
    context = {
        'form': form,
        'productos': productos,
        'almacenes': almacenes,
        'title': 'Crear Otro Movimiento',
        'action': 'Crear'
    }
    
    return render(request, 'core/otros_movimientos_form.html', context)


@login_required
def otro_movimiento_detail(request, folio):
    """Vista para ver detalles de otro movimiento"""
    
    movimiento = get_object_or_404(OtroMovimiento, folio=folio)
    detalles = OtroMovimientoDetalle.objects.filter(movimiento=movimiento)
    
    context = {
        'movimiento': movimiento,
        'detalles': detalles,
        'title': f'Detalle del Movimiento {movimiento.folio}'
    }
    
    return render(request, 'core/otros_movimientos_detail.html', context)


@login_required
def otro_movimiento_update(request, folio):
    """Vista para editar otro movimiento"""
    
    movimiento = get_object_or_404(OtroMovimiento, folio=folio)
    
    if request.method == 'POST':
        form = OtroMovimientoForm(request.POST, instance=movimiento)
        if form.is_valid():
            form.save()
            messages.success(request, f'Movimiento {movimiento.folio} actualizado correctamente.')
            return redirect('core:otros_movimientos_list')
    else:
        form = OtroMovimientoForm(instance=movimiento)
    
    context = {
        'form': form,
        'movimiento': movimiento,
        'title': 'Editar Otro Movimiento',
        'action': 'Actualizar'
    }
    
    return render(request, 'core/otros_movimientos_form.html', context)


@login_required
def otro_movimiento_delete(request, folio):
    """Vista para eliminar otro movimiento"""
    
    movimiento = get_object_or_404(OtroMovimiento, folio=folio)
    
    if request.method == 'POST':
        folio_num = movimiento.folio
        movimiento.delete()
        messages.success(request, f'Movimiento {folio_num} eliminado correctamente.')
        return redirect('core:otros_movimientos_list')
    
    context = {
        'movimiento': movimiento,
        'title': 'Eliminar Otro Movimiento'
    }
    
    return render(request, 'core/otros_movimientos_confirm_delete.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def obtener_existencia_producto_otro_movimiento(request):
    """AJAX para obtener existencia de producto en almacén"""
    
    try:
        producto_id = request.POST.get('producto_id')
        almacen_id = request.POST.get('almacen_id')
        
        if not producto_id or not almacen_id:
            return JsonResponse({'success': False, 'error': 'Faltan parámetros'})
        
        # Obtener último movimiento en Kardex
        ultimo_movimiento = Kardex.objects.filter(
            producto_id=producto_id,
            almacen_id=almacen_id
        ).order_by('-fecha', '-id').first()
        
        existencia = ultimo_movimiento.existencia_actual if ultimo_movimiento else 0
        
        return JsonResponse({
            'success': True,
            'existencia': float(existencia)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
