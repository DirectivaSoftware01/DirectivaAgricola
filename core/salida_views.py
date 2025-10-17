from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
import json
from decimal import Decimal

from .models import (
    SalidaInventario, SalidaInventarioDetalle, TipoSalida, 
    ProductoServicio, Almacen, CentroCosto, AutorizoGasto,
    ConfiguracionSistema, Kardex
)
from .salida_forms import SalidaInventarioForm, SalidaInventarioDetalleForm, TipoSalidaForm


@login_required
def salida_inventario_list(request):
    """Lista de salidas de inventario"""
    salidas = SalidaInventario.objects.filter(activo=True).order_by('-fecha', '-folio')
    
    context = {
        'title': 'Salidas de Inventario',
        'salidas': salidas,
    }
    return render(request, 'core/salida_inventario_list.html', context)


@login_required
def salida_inventario_create(request):
    """Crear nueva salida de inventario"""
    if request.method == 'POST':
        form = SalidaInventarioForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Validar existencias antes de crear la salida
                    detalles_data = request.POST.get('detalles_data')
                    if detalles_data:
                        detalles = json.loads(detalles_data)
                        errores_existencia = []
                        
                        for detalle_data in detalles:
                            producto_id = detalle_data['producto']
                            almacen_id = detalle_data['almacen']
                            cantidad_solicitada = Decimal(detalle_data['cantidad'])
                            
                            # Obtener la existencia actual del producto en el almacén
                            ultimo_movimiento = Kardex.objects.filter(
                                producto_id=producto_id,
                                almacen_id=almacen_id
                            ).order_by('-fecha', '-id').first()
                            
                            existencia_disponible = ultimo_movimiento.existencia_actual if ultimo_movimiento else 0
                            
                            if cantidad_solicitada > existencia_disponible:
                                producto = ProductoServicio.objects.get(codigo=producto_id)
                                almacen = Almacen.objects.get(codigo=almacen_id)
                                errores_existencia.append(
                                    f'{producto.descripcion} en {almacen.descripcion}: '
                                    f'solicitado {cantidad_solicitada}, disponible {existencia_disponible}'
                                )
                        
                        if errores_existencia:
                            messages.error(request, 'No se puede crear la salida debido a existencias insuficientes:')
                            for error in errores_existencia:
                                messages.error(request, f'• {error}')
                            return render(request, 'core/salida_inventario_form.html', {
                                'title': 'Nueva Salida de Inventario',
                                'form': form,
                                'productos': ProductoServicio.objects.filter(activo=True).order_by('descripcion'),
                                'almacenes': Almacen.objects.filter(activo=True).order_by('descripcion'),
                                'centros_costo': CentroCosto.objects.filter(activo=True).order_by('descripcion'),
                            })
                    
                    # Crear la salida
                    salida = form.save(commit=False)
                    salida.usuario_creacion = request.user
                    salida.save()
                    
                    # Procesar detalles si existen
                    if detalles_data:
                        detalles = json.loads(detalles_data)
                        for detalle_data in detalles:
                            SalidaInventarioDetalle.objects.create(
                                salida=salida,
                                producto_id=detalle_data['producto'],
                                almacen_id=detalle_data['almacen'],
                                cantidad=Decimal(detalle_data['cantidad']),
                                centro_costo_id=detalle_data['centro_costo']
                            )
                    
                    messages.success(request, f'Salida de inventario {salida.folio} creada exitosamente.')
                    return redirect('core:salida_inventario_detail', pk=salida.pk)
            except Exception as e:
                messages.error(request, f'Error al crear la salida: {str(e)}')
    else:
        form = SalidaInventarioForm()
    
    # Obtener datos para el formulario
    productos = ProductoServicio.objects.filter(activo=True).order_by('descripcion')
    almacenes = Almacen.objects.filter(activo=True).order_by('descripcion')
    centros_costo = CentroCosto.objects.filter(activo=True).order_by('descripcion')
    
    context = {
        'title': 'Nueva Salida de Inventario',
        'form': form,
        'productos': productos,
        'almacenes': almacenes,
        'centros_costo': centros_costo,
    }
    return render(request, 'core/salida_inventario_form.html', context)


@login_required
def salida_inventario_detail(request, pk):
    """Detalle de salida de inventario"""
    salida = get_object_or_404(SalidaInventario, pk=pk)
    detalles = salida.detalles.all()
    
    context = {
        'title': f'Salida de Inventario {salida.folio}',
        'salida': salida,
        'detalles': detalles,
    }
    return render(request, 'core/salida_inventario_detail.html', context)


@login_required
def salida_inventario_update(request, pk):
    """Editar salida de inventario"""
    salida = get_object_or_404(SalidaInventario, pk=pk)
    
    if request.method == 'POST':
        form = SalidaInventarioForm(request.POST, instance=salida)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Actualizar la salida
                    salida = form.save(commit=False)
                    salida.usuario_modificacion = request.user
                    salida.save()
                    
                    messages.success(request, f'Salida de inventario {salida.folio} actualizada exitosamente.')
                    return redirect('core:salida_inventario_detail', pk=salida.pk)
            except Exception as e:
                messages.error(request, f'Error al actualizar la salida: {str(e)}')
    else:
        form = SalidaInventarioForm(instance=salida)
    
    context = {
        'title': f'Editar Salida de Inventario {salida.folio}',
        'form': form,
        'salida': salida,
    }
    return render(request, 'core/salida_inventario_form.html', context)


@login_required
def salida_inventario_delete(request, pk):
    """Eliminar salida de inventario"""
    salida = get_object_or_404(SalidaInventario, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Eliminar detalles (esto también eliminará los movimientos de Kardex)
                salida.detalles.all().delete()
                
                # Marcar como inactiva
                salida.activo = False
                salida.save()
                
                messages.success(request, f'Salida de inventario {salida.folio} eliminada exitosamente.')
                return redirect('core:salida_inventario_list')
        except Exception as e:
            messages.error(request, f'Error al eliminar la salida: {str(e)}')
    
    context = {
        'title': f'Eliminar Salida de Inventario {salida.folio}',
        'salida': salida,
    }
    return render(request, 'core/salida_inventario_confirm_delete.html', context)


@login_required
@csrf_exempt
def crear_tipo_salida(request):
    """Crear nuevo tipo de salida via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            descripcion = data.get('descripcion', '').strip()
            
            if not descripcion:
                return JsonResponse({'success': False, 'error': 'La descripción es requerida'})
            
            # Verificar si ya existe
            if TipoSalida.objects.filter(descripcion__iexact=descripcion).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe un tipo de salida con esa descripción'})
            
            # Crear el tipo de salida
            tipo_salida = TipoSalida.objects.create(descripcion=descripcion)
            
            return JsonResponse({
                'success': True,
                'tipo_salida': {
                    'codigo': tipo_salida.codigo,
                    'descripcion': tipo_salida.descripcion
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def obtener_existencia_producto(request):
    """Obtener existencia de un producto en un almacén específico"""
    if request.method == 'GET':
        producto_id = request.GET.get('producto_id')
        almacen_id = request.GET.get('almacen_id')
        
        if not producto_id or not almacen_id:
            return JsonResponse({'success': False, 'error': 'Parámetros requeridos'})
        
        try:
            from .models import Kardex
            
            # Obtener el último movimiento del producto en el almacén
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
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def salida_inventario_imprimir(request, pk):
    """Imprimir salida de inventario"""
    salida = get_object_or_404(SalidaInventario, pk=pk)
    
    # Obtener detalles de la salida
    detalles = salida.detalles.all()
    
    # Obtener configuración de la empresa
    try:
        from .models import ConfiguracionSistema
        configuracion = ConfiguracionSistema.objects.first()
    except:
        configuracion = None
    
    context = {
        'salida': salida,
        'detalles': detalles,
        'configuracion': configuracion,
    }
    
    return render(request, 'core/salida_inventario_imprimir.html', context)
