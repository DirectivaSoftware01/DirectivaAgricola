from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, get_object_or_404
import json
from django.db.models import Sum, Count
from django.db import models
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from ..models import Usuario, Cliente, RegimenFiscal, Proveedor, Transportista, LoteOrigen, ClasificacionGasto, CentroCosto, ProductoServicio, ConfiguracionSistema, Cultivo, Remision, RemisionDetalle, CuentaBancaria, PagoRemision, PresupuestoGasto, Presupuesto, PresupuestoDetalle, Gasto, GastoDetalle, Emisor, Factura, FacturaDetalle, AutorizoGasto, Almacen, Compra, CompraDetalle, Kardex, PagoCompra
from ..forms import LoginForm, UsuarioForm, ClienteForm, ClienteSearchForm, RegimenFiscalForm, ProveedorForm, ProveedorSearchForm, TransportistaForm, TransportistaSearchForm, LoteOrigenForm, LoteOrigenSearchForm, ClasificacionGastoForm, ClasificacionGastoSearchForm, CentroCostoForm, CentroCostoSearchForm, ProductoServicioForm, ProductoServicioSearchForm, ConfiguracionSistemaForm, CultivoForm, CultivoSearchForm, RemisionForm, RemisionDetalleForm, RemisionSearchForm, RemisionLiquidacionForm, RemisionCancelacionForm, CobranzaSearchForm, PresupuestoGastoForm, PresupuestoGastoSearchForm, PresupuestoForm, PresupuestoDetalleForm, PresupuestoSearchForm, GastoForm, GastoDetalleForm, AlmacenForm, AlmacenSearchForm, CompraForm, CompraDetalleForm, CompraSearchForm, KardexSearchForm

# Create your views here.

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Directiva Agrícola - Dashboard'
        
        # Obtener estadísticas del dashboard
        context['clientes_activos'] = Cliente.objects.filter(activo=True).count()
        context['total_clientes'] = Cliente.objects.count()
        context['usuarios_activos'] = Usuario.objects.filter(is_active=True).count()
        
        # Obtener lista de clientes para el filtro del primer gráfico
        clientes = Cliente.objects.filter(activo=True).order_by('razon_social')
        print(f"DEBUG: Clientes encontrados: {clientes.count()}")
        for cliente in clientes:
            print(f"DEBUG: Cliente Código: {cliente.codigo}, Razón Social: {cliente.razon_social}")
        context['clientes'] = clientes
        
        # Obtener lista de lotes de origen para el filtro del primer gráfico
        lotes_origen = LoteOrigen.objects.filter(activo=True).order_by('nombre')
        print(f"DEBUG: Lotes de origen encontrados: {lotes_origen.count()}")
        for lote in lotes_origen:
            print(f"DEBUG: Lote Código: {lote.codigo}, Nombre: {lote.nombre}")
        context['lotes_origen'] = lotes_origen
        
        # Estadísticas de remisiones del ciclo actual
        # Obtener el ciclo actual de la configuración
        try:
            config = ConfiguracionSistema.objects.first()
            ciclo_actual = config.ciclo_actual if config else ''
        except:
            ciclo_actual = ''
        
        # Filtrar solo remisiones del ciclo actual (igual que en RemisionListView)
        if ciclo_actual:
            remisiones_qs = Remision.objects.filter(ciclo=ciclo_actual)
        else:
            remisiones_qs = Remision.objects.all()
        
        # Contar pendientes y preliquidadas del ciclo actual
        pendientes = 0
        preliquidadas = 0
        diagnostico_pendientes = []
        
        for remision in remisiones_qs:
            if remision.esta_liquidada():
                preliquidadas += 1
            else:
                pendientes += 1
                # Diagnóstico de por qué no está preliquidada
                detalles = remision.detalles.all()
                if not detalles.exists():
                    razon = 'Sin detalles'
                else:
                    tiene_valores = False
                    tiene_auditoria = False
                    for d in detalles:
                        if (getattr(d, 'kgs_liquidados', 0) > 0 or
                            getattr(d, 'kgs_merma', 0) > 0 or
                            getattr(d, 'precio', 0) > 0 or
                            getattr(d, 'importe_liquidado', 0) > 0):
                            tiene_valores = True
                        if getattr(d, 'usuario_liquidacion', None) is not None and getattr(d, 'fecha_liquidacion', None) is not None:
                            tiene_auditoria = True
                    if not tiene_valores:
                        razon = 'Sin valores de liquidación en detalles'
                    elif not tiene_auditoria:
                        razon = 'Falta auditoría (usuario/fecha) en detalles'
                    else:
                        razon = 'Condiciones de liquidación no cumplidas'
                diagnostico_pendientes.append({
                    'id': remision.pk,
                    'ciclo': remision.ciclo,
                    'folio': remision.folio,
                    'cliente': getattr(remision.cliente, 'razon_social', ''),
                    'razon': razon,
                })
        
        context['remisiones_pendientes'] = pendientes
        context['remisiones_preliquidadas'] = preliquidadas
        context['diagnostico_remisiones_pendientes'] = diagnostico_pendientes
        context['ciclo_actual'] = ciclo_actual
        
        # Estadísticas de presupuestos del ciclo actual
        if ciclo_actual:
            presupuestos_qs = Presupuesto.objects.filter(activo=True, ciclo=ciclo_actual)
        else:
            presupuestos_qs = Presupuesto.objects.filter(activo=True)
        
        # Calcular totales de presupuestos
        total_presupuestado = 0
        total_gastos = 0
        presupuestos_info = []
        
        for presupuesto in presupuestos_qs:
            # Obtener todos los gastos del presupuesto
            gastos = Gasto.objects.filter(presupuesto=presupuesto, activo=True)
            presupuesto_gastos = 0
            
            for gasto in gastos:
                # Sumar todos los detalles de gasto activos
                from django.db.models import Sum
                total_detalle = gasto.detalles.filter(activo=True).aggregate(
                    total=Sum('importe')
                )['total'] or 0
                presupuesto_gastos += float(total_detalle)
            
            total_presupuestado += float(presupuesto.total_presupuestado)
            total_gastos += presupuesto_gastos
            
            presupuestos_info.append({
                'centro_costo': presupuesto.centro_costo.descripcion,
                'presupuestado': float(presupuesto.total_presupuestado),
                'gastos': presupuesto_gastos
            })
        
        context['presupuestos_info'] = presupuestos_info
        context['total_presupuestado'] = total_presupuestado
        context['total_gastos'] = total_gastos
        
        # Calcular saldo pendiente general de remisiones preliquidadas
        saldo_pendiente_general = 0
        if ciclo_actual:
            remisiones_preliquidadas_qs = Remision.objects.filter(ciclo=ciclo_actual)
        else:
            remisiones_preliquidadas_qs = Remision.objects.all()
        
        for remision in remisiones_preliquidadas_qs:
            if remision.esta_liquidada():
                # Calcular el saldo pendiente de esta remisión
                saldo_remision = remision.saldo_pendiente
                saldo_pendiente_general += float(saldo_remision)
        
        context['saldo_pendiente_general'] = saldo_pendiente_general
        
        # Calcular saldo pendiente en facturas
        from core.factura_models import Factura
        saldo_facturas = 0
        facturas_activas = Factura.objects.filter(cancelada=False)
        
        for factura in facturas_activas:
            saldo_factura = factura.obtener_saldo_pendiente()
            saldo_facturas += float(saldo_factura)
        
        context['saldo_facturas'] = saldo_facturas
        
        # Datos para gráfica de calidad de productos (remisiones no canceladas del ciclo actual)
        from django.db.models import Sum
        from collections import defaultdict
        
        # Filtrar solo las remisiones no canceladas del ciclo actual (incluye preliquidadas y no preliquidadas)
        remisiones_no_canceladas = [r for r in remisiones_qs if not r.cancelada]
        remisiones_no_canceladas_ids = [r.pk for r in remisiones_no_canceladas]
        
        # Obtener detalles de remisiones no canceladas del ciclo actual
        detalles_qs = RemisionDetalle.objects.filter(remision__in=remisiones_no_canceladas_ids)
        
        # Agrupar por calidad y calcular totales
        calidad_data = defaultdict(lambda: {'kgs_netos_enviados': 0, 'kgs_liquidados': 0})
        
        for detalle in detalles_qs:
            calidad = detalle.calidad
            calidad_data[calidad]['kgs_netos_enviados'] += float(detalle.kgs_neto_envio or 0)
            calidad_data[calidad]['kgs_liquidados'] += float(detalle.kgs_liquidados or 0)
        
        # Convertir a lista para el template
        grafica_calidad_data = []
        for calidad, datos in calidad_data.items():
            diferencia = round(datos['kgs_netos_enviados'] - datos['kgs_liquidados'], 2)
            grafica_calidad_data.append({
                'calidad': calidad,
                'kgs_netos_enviados': round(datos['kgs_netos_enviados'], 2),
                'kgs_liquidados': round(datos['kgs_liquidados'], 2),
                'diferencia': diferencia
            })
        
        # Ordenar por calidad
        grafica_calidad_data.sort(key=lambda x: x['calidad'])
        
        context['grafica_calidad_data'] = grafica_calidad_data
        
        # Datos para gráfica de kgs enviados vs liquidados (remisiones no canceladas del ciclo actual)
        # Usar los mismos detalles_qs ya filtrados
        kgs_enviados_data = defaultdict(lambda: {'kgs_enviados': 0, 'kgs_liquidados': 0})
        
        for detalle in detalles_qs:
            calidad = detalle.calidad
            kgs_enviados_data[calidad]['kgs_enviados'] += float(detalle.kgs_enviados or 0)
            kgs_enviados_data[calidad]['kgs_liquidados'] += float(detalle.kgs_liquidados or 0)
        
        # Convertir a lista para el template
        grafica_kgs_enviados_data = []
        for calidad, datos in kgs_enviados_data.items():
            diferencia = round(datos['kgs_enviados'] - datos['kgs_liquidados'], 2)
            grafica_kgs_enviados_data.append({
                'calidad': calidad,
                'kgs_enviados': round(datos['kgs_enviados'], 2),
                'kgs_liquidados': round(datos['kgs_liquidados'], 2),
                'diferencia': diferencia
            })
        
        # Ordenar por calidad
        grafica_kgs_enviados_data.sort(key=lambda x: x['calidad'])
        
        context['grafica_kgs_enviados_data'] = grafica_kgs_enviados_data
        
        # Datos para gráfica de merma (remisiones no canceladas del ciclo actual)
        merma_data = defaultdict(lambda: {
            'kgs_merma_enviada': 0, 
            'kgs_merma_liquidada': 0,
            'total_no_arps': 0,
            'total_no_arps_liquidados': 0,
            'sum_merma_arps': 0,
            'count_detalles': 0
        })
        
        for detalle in detalles_qs:
            calidad = detalle.calidad
            merma_data[calidad]['kgs_merma_enviada'] += float(detalle.kgs_merma or 0)
            merma_data[calidad]['kgs_merma_liquidada'] += float(detalle.kgs_merma_liquidados or 0)
            merma_data[calidad]['total_no_arps'] += float(detalle.no_arps or 0)
            merma_data[calidad]['total_no_arps_liquidados'] += float(detalle.no_arps_liquidados or 0)
            merma_data[calidad]['sum_merma_arps'] += float(detalle.merma_arps or 0)
            merma_data[calidad]['count_detalles'] += 1
        
        # Convertir a lista para el template
        grafica_merma_data = []
        for calidad, datos in merma_data.items():
            diferencia_merma = round(datos['kgs_merma_enviada'] - datos['kgs_merma_liquidada'], 2)
            # Calcular promedio de merma por arp enviado
            promedio_merma_arp_enviado = round(datos['sum_merma_arps'] / datos['count_detalles'], 2) if datos['count_detalles'] > 0 else 0
            # Calcular promedio de merma por arp liquidado
            promedio_merma_arp_liquidado = round(datos['kgs_merma_liquidada'] / datos['total_no_arps_liquidados'], 2) if datos['total_no_arps_liquidados'] > 0 else 0
            
            grafica_merma_data.append({
                'calidad': calidad,
                'kgs_merma_enviada': round(datos['kgs_merma_enviada'], 2),
                'kgs_merma_liquidada': round(datos['kgs_merma_liquidada'], 2),
                'diferencia_merma': diferencia_merma,
                'promedio_merma_arp_enviado': promedio_merma_arp_enviado,
                'promedio_merma_arp_liquidado': promedio_merma_arp_liquidado
            })
        
        # Ordenar por calidad
        grafica_merma_data.sort(key=lambda x: x['calidad'])
        
        context['grafica_merma_data'] = grafica_merma_data
        
        # Datos para gráfica de importes neto enviado vs preliquidado (remisiones no canceladas del ciclo actual)
        importes_data = defaultdict(lambda: {'importe_neto_enviado': 0, 'importe_preliquidado': 0})
        
        for detalle in detalles_qs:
            calidad = detalle.calidad
            importes_data[calidad]['importe_neto_enviado'] += float(detalle.importe_envio or 0)
            importes_data[calidad]['importe_preliquidado'] += float(detalle.importe_liquidado or 0)
        
        # Convertir a lista para el template
        grafica_importes_data = []
        for calidad, datos in importes_data.items():
            diferencia_importes = round(datos['importe_neto_enviado'] - datos['importe_preliquidado'], 2)
            grafica_importes_data.append({
                'calidad': calidad,
                'importe_neto_enviado': round(datos['importe_neto_enviado'], 2),
                'importe_preliquidado': round(datos['importe_preliquidado'], 2),
                'diferencia_importes': diferencia_importes
            })
        
        # Ordenar por calidad con "Mixtas" al final
        def sort_key(item):
            calidad = item['calidad']
            if calidad == 'Mixtas':
                return (1, calidad)  # 1 para que vaya al final
            else:
                return (0, calidad)  # 0 para que vaya al principio
        
        grafica_importes_data.sort(key=sort_key)
        
        context['grafica_importes_data'] = grafica_importes_data
        
        # Datos para ranking de clientes (solo remisiones preliquidadas del ciclo actual)
        from django.db.models import Sum, Count
        
        # Agrupar remisiones preliquidadas por cliente y calcular totales
        clientes_data = defaultdict(lambda: {'importe_preliquidado': 0, 'importe_liquidado': 0, 'total_pagos': 0, 'total_remisiones': 0})
        
        for remision in remisiones_qs:
            if remision.esta_liquidada():  # Solo remisiones preliquidadas
                cliente_nombre = remision.cliente.razon_social
                # Sumar importes preliquidados y liquidados de todos los detalles de la remisión
                importe_preliquidado_remision = sum(float(detalle.importe_envio or 0) for detalle in remision.detalles.all())
                importe_liquidado_remision = sum(float(detalle.importe_liquidado or 0) for detalle in remision.detalles.all())
                # Sumar pagos realizados de la remisión
                total_pagos_remision = sum(float(pago.monto or 0) for pago in remision.pagos.filter(activo=True))
                
                clientes_data[cliente_nombre]['importe_preliquidado'] += importe_preliquidado_remision
                clientes_data[cliente_nombre]['importe_liquidado'] += importe_liquidado_remision
                clientes_data[cliente_nombre]['total_pagos'] += total_pagos_remision
                clientes_data[cliente_nombre]['total_remisiones'] += 1
        
        # Convertir a lista y ordenar por importe liquidado (descendente)
        ranking_clientes_data = []
        for cliente_nombre, datos in clientes_data.items():
            # Saldo pendiente = Importe liquidado - Pagos realizados
            saldo_pendiente = datos['importe_liquidado'] - datos['total_pagos']
            ranking_clientes_data.append({
                'cliente_nombre': cliente_nombre,
                'importe_preliquidado': round(datos['importe_preliquidado'], 2),
                'importe_liquidado': round(datos['importe_liquidado'], 2),
                'total_pagos': round(datos['total_pagos'], 2),
                'saldo_pendiente': round(saldo_pendiente, 2),
                'total_remisiones': datos['total_remisiones']
            })
        
        # Ordenar por importe liquidado descendente (ranking)
        ranking_clientes_data.sort(key=lambda x: x['importe_liquidado'], reverse=True)
        
        # Limitar a top 10 clientes
        ranking_clientes_data = ranking_clientes_data[:10]
        
        context['ranking_clientes_data'] = ranking_clientes_data
        
        # Datos para gráfica de gastos autorizados (Compras de productos del inventario)
        from core.models import Compra, AutorizoGasto
        
        # Obtener todas las compras activas
        compras_qs = Compra.objects.filter(estado='activa').select_related('autorizo')
        
        # Agrupar por autorizo y calcular totales
        gastos_data = defaultdict(lambda: {'total': 0, 'cantidad': 0})
        
        for compra in compras_qs:
            if compra.autorizo:
                autorizo_nombre = compra.autorizo.nombre
                gastos_data[autorizo_nombre]['total'] += float(compra.total or 0)
                gastos_data[autorizo_nombre]['cantidad'] += 1
        
        # Convertir a lista y ordenar por total (descendente)
        grafica_gastos_data = []
        for autorizo_nombre, datos in gastos_data.items():
            grafica_gastos_data.append({
                'autorizo_nombre': autorizo_nombre,
                'total': round(datos['total'], 2),
                'cantidad': datos['cantidad']
            })
        
        # Ordenar por total descendente
        grafica_gastos_data.sort(key=lambda x: x['total'], reverse=True)
        
        context['grafica_gastos_data'] = grafica_gastos_data
        
        # Obtener lista de autorizos para el filtro del gráfico de gastos
        autorizos = AutorizoGasto.objects.filter(activo=True).order_by('nombre')
        context['autorizos'] = autorizos
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('core:dashboard')
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    """Vista de logout"""
    logout(request)
    return redirect('core:login')

class ConfiguracionView(LoginRequiredMixin, ListView):
    """Vista para listar usuarios en configuración"""
    model = Usuario
    template_name = 'core/configuracion.html'
    context_object_name = 'usuarios'
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Usuario.objects.all().order_by('nombre')

class UsuarioCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear usuarios"""
    model = Usuario
    form_class = UsuarioForm
    template_name = 'core/usuario_form.html'
    success_url = reverse_lazy('core:configuracion')
    
    def form_valid(self, form):
        try:
            # Validar que el usuario actual tenga permisos de administrador
            if not self.request.user.is_admin and not self.request.user.is_superuser:
                messages.error(self.request, 'No tiene permisos para crear usuarios.')
                return redirect('core:configuracion')
            
            response = super().form_valid(form)
            messages.success(self.request, f'Usuario "{form.instance.username}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear usuario: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)

class UsuarioUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar usuarios"""
    model = Usuario
    form_class = UsuarioForm
    template_name = 'core/usuario_form.html'
    success_url = reverse_lazy('core:configuracion')
    
    def form_valid(self, form):
        try:
            # Validar que el usuario actual tenga permisos de administrador
            if not self.request.user.is_admin and not self.request.user.is_superuser:
                messages.error(self.request, 'No tiene permisos para editar usuarios.')
                return redirect('core:configuracion')
            
            # Prevenir que un usuario se edite a sí mismo para quitarse los permisos de admin
            if (self.object == self.request.user and 
                not form.cleaned_data.get('is_admin') and 
                self.request.user.is_admin):
                messages.error(self.request, 'No puede quitarse sus propios permisos de administrador.')
                return self.form_invalid(form)
            
            response = super().form_valid(form)
            messages.success(self.request, f'Usuario "{form.instance.username}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar usuario: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)

class UsuarioDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar usuarios"""
    model = Usuario
    template_name = 'core/usuario_confirm_delete.html'
    success_url = reverse_lazy('core:configuracion')
    
    def delete(self, request, *args, **kwargs):
        try:
            # Validar que el usuario actual tenga permisos de administrador
            if not self.request.user.is_admin and not self.request.user.is_superuser:
                messages.error(self.request, 'No tiene permisos para eliminar usuarios.')
                return redirect('core:configuracion')
            
            # Prevenir que un usuario se elimine a sí mismo
            if self.object == self.request.user:
                messages.error(self.request, 'No puede eliminarse a sí mismo.')
                return redirect('core:configuracion')
            
            # Prevenir eliminar el último administrador
            if self.object.is_admin:
                admin_count = Usuario.objects.filter(is_admin=True).count()
                if admin_count <= 1:
                    messages.error(self.request, 'No se puede eliminar el último administrador del sistema.')
                    return redirect('core:configuracion')
            
            username = self.object.username
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Usuario "{username}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar usuario: {str(e)}')
            return redirect('core:configuracion')


# ===========================
# VISTAS PARA CRUD DE CLIENTES
# ===========================

class ClienteListView(LoginRequiredMixin, ListView):
    """Vista para listar clientes con búsqueda y filtros"""
    model = Cliente
    template_name = 'core/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Cliente.objects.select_related('regimen_fiscal', 'usuario_creacion').all()
        
        # Obtener parámetros de búsqueda
        form = ClienteSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            regimen_fiscal = form.cleaned_data.get('regimen_fiscal')
            activo = form.cleaned_data.get('activo')
            
            # Filtrar por búsqueda
            if busqueda:
                queryset = queryset.filter(
                    Q(razon_social__icontains=busqueda) |
                    Q(rfc__icontains=busqueda) |
                    Q(codigo__icontains=busqueda)
                )
            
            # Filtrar por régimen fiscal
            if regimen_fiscal:
                queryset = queryset.filter(regimen_fiscal=regimen_fiscal)
            
            # Filtrar por estado activo
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ClienteSearchForm(self.request.GET)
        context['title'] = 'Gestión de Clientes'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ClienteCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear clientes"""
    model = Cliente
    form_class = ClienteForm
    template_name = 'core/cliente_form.html'
    success_url = reverse_lazy('core:cliente_list')
    
    def form_valid(self, form):
        try:
            # Asignar el usuario que crea el registro
            form.instance.usuario_creacion = self.request.user
            
            response = super().form_valid(form)
            messages.success(self.request, f'Cliente "{form.instance.razon_social}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear cliente: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Cliente'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar clientes"""
    model = Cliente
    form_class = ClienteForm
    template_name = 'core/cliente_form.html'
    success_url = reverse_lazy('core:cliente_list')
    
    def form_valid(self, form):
        try:
            # Asignar el usuario que modifica el registro
            form.instance.usuario_modificacion = self.request.user
            
            response = super().form_valid(form)
            messages.success(self.request, f'Cliente "{form.instance.razon_social}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar cliente: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Cliente: {self.object.razon_social}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ClienteDetailView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar detalles de un cliente"""
    template_name = 'core/cliente_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = get_object_or_404(Cliente, pk=kwargs['pk'])
        context['cliente'] = cliente
        context['title'] = f'Cliente: {cliente.razon_social}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar clientes"""
    model = Cliente
    template_name = 'core/cliente_confirm_delete.html'
    success_url = reverse_lazy('core:cliente_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            cliente = self.get_object()
            razon_social = cliente.razon_social
            
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Cliente "{razon_social}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar cliente: {str(e)}')
            return redirect('core:cliente_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Cliente: {self.object.razon_social}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# ====================================
# VISTAS PARA CRUD DE RÉGIMEN FISCAL
# ====================================

class RegimenFiscalListView(LoginRequiredMixin, ListView):
    """Vista para listar regímenes fiscales"""
    model = RegimenFiscal
    template_name = 'core/regimen_fiscal_list.html'
    context_object_name = 'regimenes'
    paginate_by = 20
    
    def get_queryset(self):
        return RegimenFiscal.objects.all().order_by('codigo')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Regímenes Fiscales'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class RegimenFiscalCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear regímenes fiscales"""
    model = RegimenFiscal
    form_class = RegimenFiscalForm
    template_name = 'core/regimen_fiscal_form.html'
    success_url = reverse_lazy('core:regimen_fiscal_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Solo administradores pueden gestionar regímenes fiscales
        if not getattr(request.user, 'is_admin', False) and not request.user.is_superuser:
            messages.error(request, 'No tiene permisos para gestionar regímenes fiscales.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'Régimen fiscal "{form.instance.codigo}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear régimen fiscal: {str(e)}')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Régimen Fiscal'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class RegimenFiscalUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar regímenes fiscales"""
    model = RegimenFiscal
    form_class = RegimenFiscalForm
    template_name = 'core/regimen_fiscal_form.html'
    success_url = reverse_lazy('core:regimen_fiscal_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Solo administradores pueden gestionar regímenes fiscales
        if not getattr(request.user, 'is_admin', False) and not request.user.is_superuser:
            messages.error(request, 'No tiene permisos para gestionar regímenes fiscales.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'Régimen fiscal "{form.instance.codigo}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar régimen fiscal: {str(e)}')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Régimen Fiscal: {self.object.codigo}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class RegimenFiscalDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar regímenes fiscales"""
    model = RegimenFiscal
    template_name = 'core/regimen_fiscal_confirm_delete.html'
    success_url = reverse_lazy('core:regimen_fiscal_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Solo administradores pueden gestionar regímenes fiscales
        if not getattr(request.user, 'is_admin', False) and not request.user.is_superuser:
            messages.error(request, 'No tiene permisos para gestionar regímenes fiscales.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        try:
            regimen = self.get_object()
            
            # Verificar si hay clientes usando este régimen fiscal
            clientes_count = Cliente.objects.filter(regimen_fiscal=regimen).count()
            if clientes_count > 0:
                messages.error(
                    self.request, 
                    f'No se puede eliminar el régimen fiscal "{regimen.codigo}" porque está siendo usado por {clientes_count} cliente(s).'
                )
                return redirect('core:regimen_fiscal_list')
            
            codigo = regimen.codigo
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Régimen fiscal "{codigo}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar régimen fiscal: {str(e)}')
            return redirect('core:regimen_fiscal_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Régimen Fiscal: {self.object.codigo}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# ===========================
# VISTAS PARA CRUD DE PROVEEDORES
# ===========================

class ProveedorListView(LoginRequiredMixin, ListView):
    model = Proveedor
    template_name = 'core/proveedor_list.html'
    context_object_name = 'proveedores'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Proveedor.objects.select_related('usuario_creacion').all()
        form = ProveedorSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(nombre__icontains=busqueda) | 
                    Q(rfc__icontains=busqueda) | 
                    Q(codigo__icontains=busqueda)
                )
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProveedorSearchForm(self.request.GET)
        context['title'] = 'Gestión de Proveedores'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ProveedorCreateView(LoginRequiredMixin, CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'core/proveedor_form.html'
    success_url = reverse_lazy('core:proveedor_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Proveedor "{form.instance.nombre}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear proveedor: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Proveedor'
        context['is_edit'] = False
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'core/proveedor_form.html'
    success_url = reverse_lazy('core:proveedor_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Proveedor "{form.instance.nombre}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar proveedor: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Proveedor: {self.object.nombre}'
        context['is_edit'] = True
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ProveedorDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/proveedor_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proveedor = get_object_or_404(Proveedor, pk=kwargs['pk'])
        context['proveedor'] = proveedor
        context['title'] = f'Proveedor: {proveedor.nombre}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ProveedorDeleteView(LoginRequiredMixin, DeleteView):
    model = Proveedor
    template_name = 'core/proveedor_confirm_delete.html'
    success_url = reverse_lazy('core:proveedor_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            proveedor = self.get_object()
            nombre = proveedor.nombre
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Proveedor "{nombre}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar proveedor: {str(e)}')
            return redirect('core:proveedor_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Proveedor: {self.object.nombre}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# ===========================
# VISTAS PARA CRUD DE TRANSPORTISTAS
# ===========================

class TransportistaListView(LoginRequiredMixin, ListView):
    model = Transportista
    template_name = 'core/transportista_list.html'
    context_object_name = 'transportistas'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Transportista.objects.select_related('usuario_creacion').all()
        form = TransportistaSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(nombre_completo__icontains=busqueda) | 
                    Q(licencia__icontains=busqueda) | 
                    Q(placas_unidad__icontains=busqueda) |
                    Q(placas_remolque__icontains=busqueda) |
                    Q(codigo__icontains=busqueda)
                )
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TransportistaSearchForm(self.request.GET)
        context['title'] = 'Gestión de Transportistas'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class TransportistaCreateView(LoginRequiredMixin, CreateView):
    model = Transportista
    form_class = TransportistaForm
    template_name = 'core/transportista_form.html'
    success_url = reverse_lazy('core:transportista_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Transportista "{form.instance.nombre_completo}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear transportista: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Transportista'
        context['is_edit'] = False
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class TransportistaUpdateView(LoginRequiredMixin, UpdateView):
    model = Transportista
    form_class = TransportistaForm
    template_name = 'core/transportista_form.html'
    success_url = reverse_lazy('core:transportista_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Transportista "{form.instance.nombre_completo}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar transportista: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Transportista: {self.object.nombre_completo}'
        context['is_edit'] = True
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class TransportistaDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/transportista_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transportista = get_object_or_404(Transportista, pk=kwargs['pk'])
        context['transportista'] = transportista
        context['title'] = f'Transportista: {transportista.nombre_completo}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class TransportistaDeleteView(LoginRequiredMixin, DeleteView):
    model = Transportista
    template_name = 'core/transportista_confirm_delete.html'
    success_url = reverse_lazy('core:transportista_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            transportista = self.get_object()
            nombre = transportista.nombre_completo
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Transportista "{nombre}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar transportista: {str(e)}')
            return redirect('core:transportista_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Transportista: {self.object.nombre_completo}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# ===========================
# VISTAS PARA CRUD DE LOTES - ORIGEN
# ===========================

class LoteOrigenListView(LoginRequiredMixin, ListView):
    model = LoteOrigen
    template_name = 'core/lote_origen_list.html'
    context_object_name = 'lotes_origen'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = LoteOrigen.objects.select_related('usuario_creacion').all()
        form = LoteOrigenSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(nombre__icontains=busqueda) | 
                    Q(observaciones__icontains=busqueda) | 
                    Q(codigo__icontains=busqueda)
                )
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = LoteOrigenSearchForm(self.request.GET)
        context['title'] = 'Gestión de Lotes - Origen'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class LoteOrigenCreateView(LoginRequiredMixin, CreateView):
    model = LoteOrigen
    form_class = LoteOrigenForm
    template_name = 'core/lote_origen_form.html'
    success_url = reverse_lazy('core:lote_origen_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Lote de origen "{form.instance.nombre}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear lote de origen: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Lote de Origen'
        context['is_edit'] = False
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class LoteOrigenUpdateView(LoginRequiredMixin, UpdateView):
    model = LoteOrigen
    form_class = LoteOrigenForm
    template_name = 'core/lote_origen_form.html'
    success_url = reverse_lazy('core:lote_origen_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Lote de origen "{form.instance.nombre}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar lote de origen: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Lote de Origen: {self.object.nombre}'
        context['is_edit'] = True
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class LoteOrigenDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/lote_origen_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lote_origen = get_object_or_404(LoteOrigen, pk=kwargs['pk'])
        context['lote_origen'] = lote_origen
        context['title'] = f'Lote de Origen: {lote_origen.nombre}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class LoteOrigenDeleteView(LoginRequiredMixin, DeleteView):
    model = LoteOrigen
    template_name = 'core/lote_origen_confirm_delete.html'
    success_url = reverse_lazy('core:lote_origen_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            lote_origen = self.get_object()
            nombre = lote_origen.nombre
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Lote de origen "{nombre}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar lote de origen: {str(e)}')
            return redirect('core:lote_origen_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Lote de Origen: {self.object.nombre}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# ===========================
# VISTAS PARA CRUD DE CLASIFICACIÓN DE GASTOS
# ===========================

class ClasificacionGastoListView(LoginRequiredMixin, ListView):
    model = ClasificacionGasto
    template_name = 'core/clasificacion_gasto_list.html'
    context_object_name = 'clasificaciones_gasto'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = ClasificacionGasto.objects.select_related('usuario_creacion').all()
        form = ClasificacionGastoSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(descripcion__icontains=busqueda) | 
                    Q(observaciones__icontains=busqueda) | 
                    Q(codigo__icontains=busqueda)
                )
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ClasificacionGastoSearchForm(self.request.GET)
        context['title'] = 'Gestión de Clasificación de Gastos'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ClasificacionGastoCreateView(LoginRequiredMixin, CreateView):
    model = ClasificacionGasto
    form_class = ClasificacionGastoForm
    template_name = 'core/clasificacion_gasto_form.html'
    success_url = reverse_lazy('core:clasificacion_gasto_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Clasificación de gasto "{form.instance.descripcion}" creada exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear clasificación de gasto: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nueva Clasificación de Gasto'
        context['is_edit'] = False
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ClasificacionGastoUpdateView(LoginRequiredMixin, UpdateView):
    model = ClasificacionGasto
    form_class = ClasificacionGastoForm
    template_name = 'core/clasificacion_gasto_form.html'
    success_url = reverse_lazy('core:clasificacion_gasto_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Clasificación de gasto "{form.instance.descripcion}" actualizada exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar clasificación de gasto: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Clasificación de Gasto: {self.object.descripcion}'
        context['is_edit'] = True
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ClasificacionGastoDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/clasificacion_gasto_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clasificacion_gasto = get_object_or_404(ClasificacionGasto, pk=kwargs['pk'])
        context['clasificacion_gasto'] = clasificacion_gasto
        context['title'] = f'Clasificación de Gasto: {clasificacion_gasto.descripcion}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ClasificacionGastoDeleteView(LoginRequiredMixin, DeleteView):
    model = ClasificacionGasto
    template_name = 'core/clasificacion_gasto_confirm_delete.html'
    success_url = reverse_lazy('core:clasificacion_gasto_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        try:
            clasificacion_gasto = self.get_object()
            descripcion = clasificacion_gasto.descripcion
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Clasificación de gasto "{descripcion}" eliminada exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar clasificación de gasto: {str(e)}')
            return redirect('core:clasificacion_gasto_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Clasificación de Gasto: {self.object.descripcion}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# ===========================
# VISTAS PARA CRUD DE CENTRO DE COSTOS
# ===========================

class CentroCostoListView(LoginRequiredMixin, ListView):
    model = CentroCosto
    template_name = 'core/centro_costo_list.html'
    context_object_name = 'centros_costo'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = CentroCosto.objects.select_related('usuario_creacion').all()
        form = CentroCostoSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(descripcion__icontains=busqueda) | 
                    Q(observaciones__icontains=busqueda) | 
                    Q(codigo__icontains=busqueda)
                )
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = CentroCostoSearchForm(self.request.GET)
        context['title'] = 'Gestión de Centros de Costos'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CentroCostoCreateView(LoginRequiredMixin, CreateView):
    model = CentroCosto
    form_class = CentroCostoForm
    template_name = 'core/centro_costo_form.html'
    success_url = reverse_lazy('core:centro_costo_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Centro de costo "{form.instance.descripcion}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear centro de costo: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Centro de Costo'
        context['is_edit'] = False
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CentroCostoUpdateView(LoginRequiredMixin, UpdateView):
    model = CentroCosto
    form_class = CentroCostoForm
    template_name = 'core/centro_costo_form.html'
    success_url = reverse_lazy('core:centro_costo_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Centro de costo "{form.instance.descripcion}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar centro de costo: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Centro de Costo: {self.object.descripcion}'
        context['is_edit'] = True
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CentroCostoDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/centro_costo_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro_costo = get_object_or_404(CentroCosto, pk=kwargs['pk'])
        context['centro_costo'] = centro_costo
        context['title'] = f'Centro de Costo: {centro_costo.descripcion}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CentroCostoDeleteView(LoginRequiredMixin, DeleteView):
    model = CentroCosto
    template_name = 'core/centro_costo_confirm_delete.html'
    success_url = reverse_lazy('core:centro_costo_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        try:
            centro_costo = self.get_object()
            descripcion = centro_costo.descripcion
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Centro de costo "{descripcion}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar centro de costo: {str(e)}')
            return redirect('core:centro_costo_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Centro de Costo: {self.object.descripcion}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# ===========================
# VISTAS PARA CRUD DE PRODUCTOS Y SERVICIOS
# ===========================

class ProductoServicioListView(LoginRequiredMixin, ListView):
    model = ProductoServicio
    template_name = 'core/producto_servicio_list.html'
    context_object_name = 'productos_servicios'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ProductoServicio.objects.select_related('usuario_creacion').all()
        form = ProductoServicioSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            tipo = form.cleaned_data.get('tipo')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(sku__icontains=busqueda) | 
                    Q(descripcion__icontains=busqueda) | 
                    Q(clave_sat__icontains=busqueda) |
                    Q(codigo__icontains=busqueda)
                )
            
            if tipo != '':
                queryset = queryset.filter(producto_servicio=tipo == '1')
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductoServicioSearchForm(self.request.GET)
        context['title'] = 'Gestión de Productos y Servicios'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ProductoServicioCreateView(LoginRequiredMixin, CreateView):
    model = ProductoServicio
    form_class = ProductoServicioForm
    template_name = 'core/producto_servicio_form.html'
    success_url = reverse_lazy('core:producto_servicio_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            tipo = "Producto" if form.instance.producto_servicio else "Servicio"
            messages.success(self.request, f'{tipo} "{form.instance.descripcion}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear producto o servicio: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Producto o Servicio'
        context['is_edit'] = False
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ProductoServicioUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductoServicio
    form_class = ProductoServicioForm
    template_name = 'core/producto_servicio_form.html'
    success_url = reverse_lazy('core:producto_servicio_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            tipo = "Producto" if form.instance.producto_servicio else "Servicio"
            messages.success(self.request, f'{tipo} "{form.instance.descripcion}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar producto o servicio: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = "Producto" if self.object.producto_servicio else "Servicio"
        context['title'] = f'Editar {tipo}: {self.object.descripcion}'
        context['is_edit'] = True
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ProductoServicioDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/producto_servicio_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producto_servicio = get_object_or_404(ProductoServicio, pk=kwargs['pk'])
        context['producto_servicio'] = producto_servicio
        tipo = "Producto" if producto_servicio.producto_servicio else "Servicio"
        context['title'] = f'{tipo}: {producto_servicio.descripcion}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class ProductoServicioDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductoServicio
    template_name = 'core/producto_servicio_confirm_delete.html'
    success_url = reverse_lazy('core:producto_servicio_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            producto_servicio = self.get_object()
            descripcion = producto_servicio.descripcion
            tipo = "Producto" if producto_servicio.producto_servicio else "Servicio"
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'{tipo} "{descripcion}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar producto o servicio: {str(e)}')
            return redirect('core:producto_servicio_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = "Producto" if self.object.producto_servicio else "Servicio"
        context['title'] = f'Eliminar {tipo}: {self.object.descripcion}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
# Vistas para Configuración del Sistema

class ConfiguracionSistemaView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar y editar la configuración del sistema"""
    template_name = 'core/configuracion_sistema.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Configuración del Sistema'
        
        # Obtener la configuración del sistema
        configuracion = ConfiguracionSistema.objects.first()
        
        # Si no existe configuración, crear una instancia vacía para el formulario
        if not configuracion:
            configuracion = ConfiguracionSistema()
        
        # Crear el formulario con la configuración existente
        form = ConfiguracionSistemaForm(instance=configuracion)
        
        context['configuracion'] = configuracion
        context['form'] = form
        
        # Agregar información sobre certificados existentes
        context['tiene_certificado'] = bool(configuracion and configuracion.certificado)
        context['tiene_llave'] = bool(configuracion and configuracion.llave)
        context['tiene_password'] = bool(configuracion and configuracion.password_llave)
        context['certificado_nombre'] = configuracion.certificado_nombre if configuracion else ''
        context['llave_nombre'] = configuracion.llave_nombre if configuracion else ''
        
        return context

    def post(self, request, *args, **kwargs):
        """Manejar el envío del formulario"""
        try:
            configuracion = ConfiguracionSistema.objects.first()
            
            # Verificar si es un guardado parcial por sección
            seccion = request.POST.get('seccion')
            
            if seccion:
                # Guardado parcial por sección
                if seccion == 'ciclo':
                    if 'ciclo_actual' in request.POST:
                        if not configuracion:
                            configuracion = ConfiguracionSistema()
                        configuracion.ciclo_actual = request.POST.get('ciclo_actual')
                        if not configuracion.pk:
                            configuracion.usuario_creacion = request.user
                        else:
                            configuracion.usuario_modificacion = request.user
                        configuracion.save()
                        messages.success(request, 'Ciclo de producción guardado correctamente.')
                        
                        # Si es una petición AJAX, devolver JSON
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': True, 'message': 'Ciclo de producción guardado correctamente'})
                
                elif seccion == 'empresa':
                    # Validar permisos de administrador
                    if not request.user.is_admin:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'error': 'No tienes permisos para modificar esta sección.'}, status=403)
                        messages.error(request, 'No tienes permisos para modificar esta sección.')
                        return redirect('core:configuracion_sistema')
                    
                    if not configuracion:
                        configuracion = ConfiguracionSistema()
                    
                    if 'razon_social' in request.POST:
                        configuracion.razon_social = request.POST.get('razon_social')
                    if 'rfc' in request.POST:
                        configuracion.rfc = request.POST.get('rfc')
                    if 'direccion' in request.POST:
                        configuracion.direccion = request.POST.get('direccion')
                    if 'telefono' in request.POST:
                        configuracion.telefono = request.POST.get('telefono')
                    if 'logo_empresa' in request.FILES:
                        print(f"DEBUG: Archivo logo_empresa encontrado: {request.FILES.get('logo_empresa').name}")
                        configuracion.logo_empresa = request.FILES.get('logo_empresa')
                    else:
                        print("DEBUG: No se encontró logo_empresa en request.FILES")
                        print(f"DEBUG: Archivos disponibles: {list(request.FILES.keys())}")
                    
                    if not configuracion.pk:
                        configuracion.usuario_creacion = request.user
                    else:
                        configuracion.usuario_modificacion = request.user
                    configuracion.save()
                    messages.success(request, 'Datos de la empresa guardados correctamente.')
                    
                    # Si es una petición AJAX, devolver JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Datos de la empresa guardados correctamente'})
                
                elif seccion == 'timbrado':
                    if not configuracion:
                        configuracion = ConfiguracionSistema()
                    
                    if 'nombre_pac' in request.POST:
                        configuracion.nombre_pac = request.POST.get('nombre_pac')
                    if 'contrato' in request.POST:
                        configuracion.contrato = request.POST.get('contrato')
                    if 'usuario_pac' in request.POST:
                        configuracion.usuario_pac = request.POST.get('usuario_pac')
                    if 'password_pac' in request.POST:
                        configuracion.password_pac = request.POST.get('password_pac')
                    
                    if not configuracion.pk:
                        configuracion.usuario_creacion = request.user
                    else:
                        configuracion.usuario_modificacion = request.user
                    configuracion.save()
                    messages.success(request, 'Configuración de timbrado guardada correctamente.')
                    
                    # Si es una petición AJAX, devolver JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Configuración de timbrado guardada correctamente'})
                
                elif seccion == 'certificados':
                    if not configuracion:
                        configuracion = ConfiguracionSistema()
                    
                    # Procesar archivos de certificado y llave
                    if 'certificado_file' in request.FILES:
                        certificado_file = request.FILES.get('certificado_file')
                        # Convertir archivo a base64
                        import base64
                        configuracion.certificado = base64.b64encode(certificado_file.read()).decode('utf-8')
                        # Guardar nombre del archivo original
                        configuracion.certificado_nombre = certificado_file.name
                    
                    if 'llave_file' in request.FILES:
                        llave_file = request.FILES.get('llave_file')
                        # Convertir archivo a base64
                        import base64
                        configuracion.llave = base64.b64encode(llave_file.read()).decode('utf-8')
                        # Guardar nombre del archivo original
                        configuracion.llave_nombre = llave_file.name
                    
                    if 'password_llave' in request.POST:
                        configuracion.password_llave = request.POST.get('password_llave')
                    
                    if not configuracion.pk:
                        configuracion.usuario_creacion = request.user
                    else:
                        configuracion.usuario_modificacion = request.user
                    configuracion.save()
                    messages.success(request, 'Certificados guardados correctamente.')
                    
                    # Si es una petición AJAX, devolver JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Sección guardada correctamente'})
                    
                    return redirect('core:configuracion_sistema')
                
            else:
                # Guardado completo del formulario
                form = ConfiguracionSistemaForm(request.POST, request.FILES, instance=configuracion)
                
                if form.is_valid():
                    configuracion = form.save(commit=False)
                    
                    # Si es una nueva configuración, asignar usuario de creación
                    if not configuracion.pk:
                        configuracion.usuario_creacion = request.user
                    else:
                        configuracion.usuario_modificacion = request.user
                    
                    configuracion.save()
                    
                    messages.success(request, 'Configuración guardada correctamente.')
                    return redirect('core:configuracion_sistema')
                else:
                    # Mostrar errores específicos del formulario
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            error_messages.append(f"{form.fields[field].label}: {error}")
                    
                    if error_messages:
                        messages.error(request, f'Errores en el formulario: {"; ".join(error_messages)}')
                    else:
                        messages.error(request, 'Por favor, corrija los errores en el formulario.')
            
        except Exception as e:
            messages.error(request, f'Error al guardar la configuración: {str(e)}')
        
        context = self.get_context_data()
        # Crear el formulario con la configuración existente
        configuracion = ConfiguracionSistema.objects.first()
        if not configuracion:
            configuracion = ConfiguracionSistema()
        form = ConfiguracionSistemaForm(instance=configuracion)
        context['form'] = form
        context['configuracion'] = configuracion
        
        return render(request, self.template_name, context)


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

# Vistas para Cultivos

class CultivoListView(LoginRequiredMixin, ListView):
    """Vista para listar cultivos"""
    model = Cultivo
    template_name = 'core/cultivo_list.html'
    context_object_name = 'cultivos'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filtrar cultivos según los parámetros de búsqueda"""
        queryset = Cultivo.objects.all()
        search = self.request.GET.get('search')
        activo = self.request.GET.get('activo')
        
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) | 
                Q(variedad__icontains=search)
            )
        
        if activo:
            queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('nombre', 'variedad')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cultivos'
        context['search_form'] = CultivoSearchForm(self.request.GET)
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CultivoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear cultivos"""
    model = Cultivo
    form_class = CultivoForm
    template_name = 'core/cultivo_form.html'
    success_url = reverse_lazy('core:cultivo_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Asignar usuario de creación"""
        form.instance.usuario_creacion = self.request.user
        messages.success(self.request, 'Cultivo creado correctamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Cultivo'
        context['is_edit'] = False
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CultivoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar cultivos"""
    model = Cultivo
    form_class = CultivoForm
    template_name = 'core/cultivo_form.html'
    success_url = reverse_lazy('core:cultivo_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Asignar usuario de modificación"""
        form.instance.usuario_modificacion = self.request.user
        messages.success(self.request, 'Cultivo actualizado correctamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Cultivo: {self.object.nombre} - {self.object.variedad}'
        context['is_edit'] = True
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CultivoDetailView(LoginRequiredMixin, TemplateView):
    """Vista para ver detalles de un cultivo"""
    template_name = 'core/cultivo_detail.html'
    
    def get_object(self):
        return get_object_or_404(Cultivo, pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cultivo = self.get_object()
        context['cultivo'] = cultivo
        context['title'] = f'Cultivo: {cultivo.nombre} - {cultivo.variedad}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CultivoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar cultivos"""
    model = Cultivo
    template_name = 'core/cultivo_confirm_delete.html'
    success_url = reverse_lazy('core:cultivo_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea administrador"""
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Eliminar con mensaje de confirmación"""
        try:
            self.object = self.get_object()
            nombre = f"{self.object.nombre} - {self.object.variedad}"
            self.object.delete()
            messages.success(request, f'Cultivo "{nombre}" eliminado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar cultivo: {str(e)}')
        return redirect('core:cultivo_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Cultivo: {self.object.nombre} - {self.object.variedad}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# ===========================
# VISTAS PARA CRUD DE REMISIONES
# ===========================

class RemisionListView(LoginRequiredMixin, ListView):
    """Vista para listar remisiones con búsqueda y filtros"""
    model = Remision
    template_name = 'core/remision_list.html'
    context_object_name = 'remisiones'
    paginate_by = 20
    
    def get_queryset(self):
        # Obtener el ciclo actual de la configuración
        try:
            config = ConfiguracionSistema.objects.first()
            ciclo_actual = config.ciclo_actual if config else ''
        except:
            ciclo_actual = ''
        
        # Filtrar por ciclo actual si está configurado
        if ciclo_actual:
            queryset = Remision.objects.select_related(
                'cliente', 'lote_origen', 'transportista', 'usuario_creacion'
            ).filter(ciclo=ciclo_actual)
        else:
            queryset = Remision.objects.select_related(
                'cliente', 'lote_origen', 'transportista', 'usuario_creacion'
            ).all()
        
        # Obtener parámetros de búsqueda
        form = RemisionSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            cliente = form.cleaned_data.get('cliente')
            lote_origen = form.cleaned_data.get('lote_origen')
            transportista = form.cleaned_data.get('transportista')
            fecha_desde = form.cleaned_data.get('fecha_desde')
            fecha_hasta = form.cleaned_data.get('fecha_hasta')
            
            # Filtrar por búsqueda
            if busqueda:
                queryset = queryset.filter(
                    Q(ciclo__icontains=busqueda) |
                    Q(folio__icontains=busqueda) |
                    Q(cliente__razon_social__icontains=busqueda) |
                    Q(observaciones__icontains=busqueda)
                )
            
            # Filtrar por cliente
            if cliente:
                queryset = queryset.filter(cliente=cliente)
            
            # Filtrar por lote origen (múltiple)
            if lote_origen:
                queryset = queryset.filter(lote_origen__in=lote_origen)
            
            # Filtrar por transportista
            if transportista:
                queryset = queryset.filter(transportista=transportista)
            
            # Filtrar por rango de fechas
            if fecha_desde:
                queryset = queryset.filter(fecha__gte=fecha_desde)
            
            if fecha_hasta:
                queryset = queryset.filter(fecha__lte=fecha_hasta)
            
            # Filtrar por estado (usar agregados para evitar duplicados por joins)
            estado = form.cleaned_data.get('estado')
            if estado:
                from django.db.models import Sum
                queryset = queryset.annotate(
                    total_kgs_liq=Sum('detalles__kgs_liquidados'),
                    total_imp_liq=Sum('detalles__importe_liquidado'),
                )
                if estado == 'pendiente':
                    queryset = queryset.filter(
                        (Q(total_kgs_liq__isnull=True) | Q(total_kgs_liq=0)) &
                        (Q(total_imp_liq__isnull=True) | Q(total_imp_liq=0))
                    )
                elif estado == 'preliquidada':
                    queryset = queryset.filter(
                        Q(total_kgs_liq__gt=0) | Q(total_imp_liq__gt=0)
                    )
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = RemisionSearchForm(self.request.GET)
        context['title'] = 'Gestión de Remisiones'
        
        # Agregar lotes activos al contexto para el dropdown personalizado
        context['lotes_disponibles'] = LoteOrigen.objects.filter(activo=True).order_by('nombre')
        
        # Agregar ciclo actual al contexto
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class RemisionCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear remisiones"""
    model = Remision
    form_class = RemisionForm
    template_name = 'core/remision_form.html'
    success_url = reverse_lazy('core:remision_list')
    
    def form_valid(self, form):
        try:
            # Verificar que se hayan agregado detalles antes de crear la remisión
            detalles_count = self.request.POST.get('detalles_count', 0)
            try:
                detalles_count = int(detalles_count)
            except (ValueError, TypeError):
                detalles_count = 0
            
            if detalles_count == 0:
                messages.error(self.request, 'No se puede crear una remisión sin detalles. Por favor, agregue al menos un detalle en la pestaña "Detalles de la Remisión".')
                return self.form_invalid(form)
            
            # Asignar el usuario que crea el registro
            form.instance.usuario_creacion = self.request.user
            
            # Inicializar campos de preliquidación con valores por defecto
            from decimal import Decimal
            form.instance.importe_cliente = Decimal('0.00')
            form.instance.diferencia_importe = Decimal('0.00')
            
            # Obtener el ciclo actual de la configuración
            from ..models import ConfiguracionSistema
            configuracion = ConfiguracionSistema.objects.first()
            if configuracion and configuracion.ciclo_actual:
                form.instance.ciclo = configuracion.ciclo_actual
            
            # Guardar la remisión primero
            response = super().form_valid(form)
            
            # Ahora crear los detalles temporales
            self.crear_detalles_temporales(form.instance)
            
            messages.success(self.request, f'Remisión "{form.instance.ciclo} - {form.instance.folio:06d}" creada exitosamente con {detalles_count} detalle(s).')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear remisión: {str(e)}')
            return self.form_invalid(form)
    
    def crear_detalles_temporales(self, remision):
        """Crear los detalles temporales que se enviaron desde el frontend"""
        import json
        
        # Obtener los detalles temporales del POST (enviados como JSON)
        detalles_json = self.request.POST.get('detalles_temporales', '[]')
        try:
            detalles_data = json.loads(detalles_json)
        except (json.JSONDecodeError, TypeError):
            detalles_data = []
        
        # Crear cada detalle
        for detalle_data in detalles_data:
            try:
                from ..models import RemisionDetalle, Cultivo
                
                # Obtener el cultivo
                cultivo = Cultivo.objects.get(pk=detalle_data['cultivo']['id'])
                
                # Crear el detalle (el peso_promedio se calcula automáticamente en el método save)
                detalle = RemisionDetalle.objects.create(
                    remision=remision,
                    cultivo=cultivo,
                    calidad=detalle_data['calidad'],
                    no_arps=detalle_data['no_arps'],
                    kgs_enviados=round(detalle_data['kgs_enviados'], 2),
                    merma_arps=round(detalle_data['merma_arps'], 2),  # Convertir a Decimal con 2 decimales
                    kgs_liquidados=round(detalle_data['kgs_liquidados'], 2),
                    kgs_merma=round(detalle_data['kgs_merma'], 2),
                    precio=round(detalle_data['precio'], 2),
                    importe_liquidado=round(detalle_data['importe_liquidado'], 2),
                    # Campos de envío
                    precio_envio=round(detalle_data.get('precio_envio', 0), 2),
                    importe_envio=round(detalle_data.get('importe_envio', 0), 2),
                    kgs_neto_envio=round(detalle_data.get('kgs_neto_envio', 0), 2),
                    importe_neto_envio=round(detalle_data.get('importe_neto_envio', 0), 2),
                    usuario_creacion=self.request.user
                )
            except Exception as e:
                # Si hay error creando un detalle, continuar con los demás
                print(f"Error creando detalle: {e}")
                continue


def get_cultivos_ajax(request):
    """Vista AJAX para obtener cultivos activos"""
    if request.method == 'GET':
        cultivos = Cultivo.objects.filter(activo=True).values('codigo', 'nombre', 'variedad')
        # Renombrar 'codigo' a 'id' para el frontend
        cultivos_data = []
        for cultivo in cultivos:
            cultivos_data.append({
                'id': cultivo['codigo'],
                'nombre': cultivo['nombre'],
                'variedad': cultivo['variedad']
            })
        return JsonResponse(cultivos_data, safe=False)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

class RemisionLiquidacionView(LoginRequiredMixin, TemplateView):
    """Vista para preliquidar una remisión"""
    template_name = 'core/remision_liquidacion.html'

    def get_object(self):
        return get_object_or_404(Remision, pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        print(f"[DEBUG GET] GET recibido - Remisión ID: {kwargs.get('pk')}", flush=True)
        self.object = self.get_object()
        if self.object.cancelada:
            messages.error(request, 'No se puede preliquidar una remisión cancelada.')
            return redirect('core:remision_list')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object = self.get_object()
        context['title'] = f'Liquidar Remisión {self.object.ciclo} - {self.object.folio:06d}'
        context['remision'] = self.object
        context['detalles'] = self.object.detalles.all()
        # Catálogo de cultivos activos para permitir agregar nuevos renglones
        from core.models import Cultivo
        context['cultivos'] = Cultivo.objects.filter(activo=True).order_by('nombre', 'variedad')
        return context

    def post(self, request, *args, **kwargs):
        print(f"[DEBUG POST] POST recibido - Remisión ID: {kwargs.get('pk')}", flush=True)
        print(f"[DEBUG POST] POST data keys: {list(request.POST.keys())}", flush=True)
        self.object = self.get_object()
        if self.esta_liquidada(self.object):
            print("[DEBUG POST] Remisión ya está preliquidada", flush=True)
            messages.error(request, 'Esta remisión ya ha sido preliquidada.')
            return redirect('core:remision_list')
        if self.object.cancelada:
            messages.error(request, 'No se puede preliquidar una remisión cancelada.')
            return redirect('core:remision_list')
        
        # Procesar los datos de la remisión
        peso_bruto_liquidado = request.POST.get('peso_bruto_liquidado', 0)
        merma_arps_liquidados = request.POST.get('merma_arps_liquidados', 0)
        importe_cliente = request.POST.get('importe_cliente', 0)
        
        print(f"[DEBUG] merma_arps_liquidados recibido: '{merma_arps_liquidados}' (tipo: {type(merma_arps_liquidados)})", flush=True)
        
        try:
            from decimal import Decimal
            peso_value = Decimal(str(round(float(peso_bruto_liquidado or 0), 2)))
            merma_value = Decimal(str(round(float(merma_arps_liquidados or 0), 2)))
            importe_cliente_value = Decimal(str(round(float(importe_cliente or 0), 2)))
            print(f"[DEBUG] Valores Decimal creados - peso: {peso_value}, merma: {merma_value}, importe_cliente: {importe_cliente_value}", flush=True)
            
            self.object.peso_bruto_liquidado = peso_value
            self.object.merma_arps_liquidados = merma_value
            self.object.importe_cliente = importe_cliente_value
            
            # Calcular diferencia_importe después de procesar todos los detalles
            # (se calculará más adelante cuando tengamos el total_importe_liquidado)
            
            print(f"[DEBUG] Remisión guardada - ID: {self.object.pk}, merma_arps_liquidados: {self.object.merma_arps_liquidados}", flush=True)
            
        except (ValueError, TypeError) as e:
            print(f"[ERROR] Error al guardar liquidación: {e}", flush=True)
            import traceback
            traceback.print_exc()
            messages.error(request, 'Error en los datos de liquidación de la remisión.')
            return self.form_invalid(None)
        
        detalles = self.object.detalles.all()
        from django.utils import timezone
        from core.models import Cultivo, RemisionDetalle
        total_importe_liquidado = Decimal('0.00')
        for detalle in detalles:
            # Obtener todos los campos de liquidación
            no_arps_liquidados = request.POST.get(f'no_arps_liquidados_{detalle.pk}', 0)
            kgs_liquidados = request.POST.get(f'kgs_liquidados_{detalle.pk}', 0)
            kgs_merma_liquidados = request.POST.get(f'kgs_merma_liquidados_{detalle.pk}', 0)
            peso_promedio_liquidado = request.POST.get(f'peso_promedio_liquidado_{detalle.pk}', 0)
            kgs_merma = request.POST.get(f'kgs_merma_{detalle.pk}', 0)
            precio = request.POST.get(f'precio_{detalle.pk}', 0)
            importe_liquidado = request.POST.get(f'importe_liquidado_{detalle.pk}', 0)
            
            try:
                from decimal import Decimal
                # Guardar todos los campos de liquidación
                detalle.no_arps_liquidados = int(no_arps_liquidados or 0)
                detalle.kgs_liquidados = Decimal(str(round(float(kgs_liquidados or 0), 2)))
                detalle.kgs_merma_liquidados = Decimal(str(round(float(kgs_merma_liquidados or 0), 2)))
                detalle.peso_promedio_liquidado = Decimal(str(round(float(peso_promedio_liquidado or 0), 2)))
                detalle.kgs_merma = Decimal(str(round(float(kgs_merma or 0), 2)))
                detalle.precio = Decimal(str(round(float(precio or 0), 4)))
                detalle.importe_liquidado = Decimal(str(round(float(importe_liquidado or 0), 2)))
                
                # Calcular diferencias automáticamente
                detalle.dif_peso_promedio = Decimal(str(round(float(detalle.peso_promedio - detalle.peso_promedio_liquidado), 2)))
                detalle.dif_no_arps = detalle.no_arps - detalle.no_arps_liquidados
                detalle.dif_kgs_merma = Decimal(str(round(float(detalle.kgs_merma - detalle.kgs_merma_liquidados), 2)))
                detalle.dif_kgs_liquidados = Decimal(str(round(float(detalle.kgs_neto_envio - detalle.kgs_liquidados), 2)))
                detalle.dif_precio = Decimal(str(round(float(detalle.precio_envio - detalle.precio), 4)))
                detalle.dif_importes = Decimal(str(round(float(detalle.importe_neto_envio - detalle.importe_liquidado), 2)))
                
                # Guardar información de auditoría de liquidación
                detalle.usuario_liquidacion = request.user
                detalle.fecha_liquidacion = timezone.now()
                detalle.save()
                
                # Acumular importe liquidado para calcular diferencia
                total_importe_liquidado += detalle.importe_liquidado
                
            except (ValueError, TypeError):
                messages.error(request, f'Error en los datos del detalle {detalle.cultivo.nombre}.')
                return self.form_invalid(None)
        
        # Procesar nuevos detalles adicionales agregados durante la preliquidación
        nuevos_detalles_ids = {
            key.replace('es_nuevo_', '')
            for key in request.POST.keys()
            if key.startswith('es_nuevo_')
        }
        
        for nuevo_id in nuevos_detalles_ids:
            cultivo_id = request.POST.get(f'cultivo_id_{nuevo_id}')
            calidad = request.POST.get(f'calidad_{nuevo_id}')
            no_arps_liquidados = request.POST.get(f'no_arps_liquidados_{nuevo_id}', 0)
            kgs_liquidados = request.POST.get(f'kgs_liquidados_{nuevo_id}', 0)
            kgs_merma_liquidados = request.POST.get(f'kgs_merma_liquidados_{nuevo_id}', 0)
            peso_promedio_liquidado = request.POST.get(f'peso_promedio_liquidado_{nuevo_id}', 0)
            precio = request.POST.get(f'precio_{nuevo_id}', 0)
            importe_liquidado = request.POST.get(f'importe_liquidado_{nuevo_id}', 0)
            
            if not cultivo_id or not calidad:
                continue
            
            try:
                cultivo = Cultivo.objects.get(pk=cultivo_id)
                
                no_arps_liq_value = Decimal(str(round(float(no_arps_liquidados or 0), 2)))
                kgs_liq_value = Decimal(str(round(float(kgs_liquidados or 0), 2)))
                kgs_merma_liq_value = Decimal(str(round(float(kgs_merma_liquidados or 0), 2)))
                peso_prom_liq_value = Decimal(str(round(float(peso_promedio_liquidado or 0), 2)))
                precio_value = Decimal(str(round(float(precio or 0), 4)))
                importe_liq_value = Decimal(str(round(float(importe_liquidado or 0), 2)))
                
                nuevo_detalle = RemisionDetalle(
                    remision=self.object,
                    cultivo=cultivo,
                    calidad=calidad,
                    # Campos de envío: todos en cero porque este cultivo no estaba en el envío original
                    no_arps=0,
                    kgs_enviados=Decimal('0.00'),
                    merma_arps=Decimal('0.00'),
                    peso_promedio=Decimal('0.00'),
                    # Campos de liquidación: valores ingresados durante la preliquidación
                    no_arps_liquidados=no_arps_liq_value,
                    kgs_liquidados=kgs_liq_value,
                    kgs_merma_liquidados=kgs_merma_liq_value,
                    peso_promedio_liquidado=peso_prom_liq_value,
                    kgs_merma=Decimal('0.00'),  # Kgs merma de envío (no hay envío, es 0)
                    precio=precio_value,
                    importe_liquidado=importe_liq_value,
                    # Campos de envío (precio, importe, etc.): todos en cero
                    precio_envio=Decimal('0.00'),
                    importe_envio=Decimal('0.00'),
                    kgs_neto_envio=Decimal('0.00'),
                    importe_neto_envio=Decimal('0.00'),
                    # Diferencias: todas en cero porque no hay valores de envío original
                    dif_peso_promedio=Decimal('0.00'),
                    dif_no_arps=0,
                    dif_kgs_merma=Decimal('0.00'),
                    dif_kgs_liquidados=Decimal('0.00'),
                    dif_precio=Decimal('0.00'),
                    dif_importes=Decimal('0.00'),
                    # Auditoría
                    usuario_creacion=request.user,
                    usuario_liquidacion=request.user,
                    fecha_liquidacion=timezone.now()
                )
                nuevo_detalle.save()
                total_importe_liquidado += nuevo_detalle.importe_liquidado
            except Cultivo.DoesNotExist:
                messages.error(request, 'El cultivo seleccionado ya no está disponible.')
                continue
            except (ValueError, TypeError):
                messages.error(request, 'Error en los datos del cultivo adicional.')
                continue
        
        # Calcular diferencia_importe = Total Importe Liquidado - Importe Cliente
        diferencia_importe = total_importe_liquidado - self.object.importe_cliente
        self.object.diferencia_importe = diferencia_importe
        self.object.save()
        
        print(f"[DEBUG] Total Importe Liquidado: {total_importe_liquidado}, Importe Cliente: {self.object.importe_cliente}, Diferencia: {diferencia_importe}", flush=True)
        
        messages.success(request, f'Remisión "{self.object.ciclo} - {self.object.folio:06d}" preliquidada exitosamente.')
        return redirect('core:remision_list')

    def esta_liquidada(self, remision):
        """Determinar si una remisión está preliquidada basándose en los campos de liquidación
        Y si tiene información de auditoría (usuario_liquidacion y fecha_liquidacion)
        """
        detalles = remision.detalles.all()
        if not detalles.exists():
            return False
        
        # Una remisión está preliquidada si al menos un detalle tiene valores de liquidación
        # Y tiene información de auditoría (usuario_liquidacion y fecha_liquidacion)
        for detalle in detalles:
            if ((detalle.kgs_liquidados > 0 or 
                 detalle.kgs_merma > 0 or 
                 detalle.precio > 0 or 
                 detalle.importe_liquidado > 0) and
                detalle.usuario_liquidacion is not None and
                detalle.fecha_liquidacion is not None):
                return True
        return False
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error en el formulario de liquidación.')
        return super().form_invalid(form)


class RemisionUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar remisiones"""
    model = Remision
    form_class = RemisionForm
    template_name = 'core/remision_form.html'
    success_url = reverse_lazy('core:remision_list')
    
    def get(self, request, *args, **kwargs):
        """Verificar que la remisión no esté cancelada antes de permitir la edición"""
        self.object = self.get_object()
        
        if self.object.cancelada:
            messages.error(request, 'No se puede editar una remisión cancelada.')
            return redirect('core:remision_list')
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Verificar que la remisión no esté cancelada antes de procesar la actualización"""
        self.object = self.get_object()
        
        if self.object.cancelada:
            messages.error(request, 'No se puede editar una remisión cancelada.')
            return redirect('core:remision_list')
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            # Asignar el usuario que modifica el registro
            form.instance.usuario_modificacion = self.request.user
            
            response = super().form_valid(form)
            messages.success(self.request, f'Remisión "{form.instance.ciclo} - {form.instance.folio:06d}" actualizada exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar remisión: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Remisión: {self.object.ciclo} - {self.object.folio:06d}'
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Forzar iniciales desde la instancia para evitar que se muestren vacíos
        if self.object:
            try:
                form.fields['peso_bruto_embarque'].initial = self.object.peso_bruto_embarque
            except Exception:
                pass
            try:
                form.fields['merma_arps_global'].initial = self.object.merma_arps_global
            except Exception:
                pass
        return form


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class RemisionDetailView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar detalles de una remisión"""
    template_name = 'core/remision_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        remision = get_object_or_404(Remision, pk=kwargs['pk'])
        detalles = remision.detalles.all()
        
        print(f"[DEBUG DETAIL VIEW] Remisión {remision.codigo} - merma_arps_liquidados: {remision.merma_arps_liquidados}", flush=True)
        
        # Calcular totales enviados
        total_arps = sum(detalle.no_arps for detalle in detalles)
        total_kgs_enviados = sum(detalle.kgs_enviados for detalle in detalles)
        total_kgs_merma = sum(detalle.kgs_merma for detalle in detalles)
        total_kgs_netos = sum(detalle.kgs_neto_envio for detalle in detalles)
        total_importe_neto_envio = sum(detalle.importe_neto_envio for detalle in detalles)
        
        # Calcular totales preliquidados
        total_arps_liquidados = sum(detalle.no_arps_liquidados for detalle in detalles)
        total_kgs_liquidados = sum(detalle.kgs_liquidados for detalle in detalles)
        total_kgs_merma_liquidados = sum(detalle.kgs_merma_liquidados for detalle in detalles)
        total_importe_liquidado = sum(detalle.importe_liquidado for detalle in detalles)
        
        context['remision'] = remision
        context['detalles'] = detalles
        context['title'] = f'Remisión: {remision.ciclo} - {remision.folio:06d}'
        
        # Totales enviados
        context['total_arps'] = total_arps
        context['total_kgs_enviados'] = total_kgs_enviados
        context['total_kgs_merma'] = total_kgs_merma
        context['total_kgs_netos'] = total_kgs_netos
        context['total_importe_neto_envio'] = total_importe_neto_envio
        
        # Totales preliquidados
        context['total_arps_liquidados'] = total_arps_liquidados
        context['total_kgs_liquidados'] = total_kgs_liquidados
        context['total_kgs_merma_liquidados'] = total_kgs_merma_liquidados
        context['total_importe_liquidado'] = total_importe_liquidado
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class RemisionImprimirView(LoginRequiredMixin, TemplateView):
    """Vista para imprimir formato de remisión"""
    template_name = 'core/remision_imprimir.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        remision = get_object_or_404(Remision, pk=kwargs['pk'])
        detalles = remision.detalles.all()
        
        # Agregar campo calculado kg_merma_total a cada detalle
        detalles_procesados = []
        for detalle in detalles:
            # Agregar atributo calculado para merma enviados
            detalle.kg_merma_total = float(detalle.no_arps or 0) * float(detalle.merma_arps or 0)
            # Agregar atributo calculado para merma recibido por arp
            if detalle.no_arps_liquidados and detalle.no_arps_liquidados > 0:
                detalle.merma_por_arp_recibido = float(detalle.kgs_merma or 0) / float(detalle.no_arps_liquidados)
            else:
                detalle.merma_por_arp_recibido = 0
            detalles_procesados.append(detalle)
        
        # Calcular totales enviados
        total_arps = sum(detalle.no_arps for detalle in detalles_procesados)
        total_kgs_enviados = sum(detalle.kgs_enviados for detalle in detalles_procesados)
        total_kgs_merma = sum(detalle.kgs_merma for detalle in detalles_procesados)
        total_importe_neto_envio = sum(detalle.importe_neto_envio for detalle in detalles_procesados)
        total_kgs_netos = total_kgs_enviados - total_kgs_merma
        
        # Calcular totales preliquidados
        total_arps_liquidados = sum(detalle.no_arps_liquidados for detalle in detalles_procesados)
        total_kgs_liquidados = sum(detalle.kgs_liquidados for detalle in detalles_procesados)
        total_kgs_merma_liquidados = sum(detalle.kgs_merma_liquidados for detalle in detalles_procesados)
        total_importe_liquidado = sum(detalle.importe_liquidado for detalle in detalles_procesados)
        
        # Obtener el primer cultivo de los detalles (para mostrar en la información del producto)
        primer_cultivo = None
        for detalle in detalles_procesados:
            if detalle.cultivo:
                primer_cultivo = detalle.cultivo
                break
        
        context['remision'] = remision
        context['detalles'] = detalles_procesados
        context['primer_cultivo'] = primer_cultivo
        
        # Totales enviados
        context['total_arps'] = total_arps
        context['total_kgs_enviados'] = total_kgs_enviados
        context['total_kgs_merma'] = total_kgs_merma
        context['total_importe_neto_envio'] = total_importe_neto_envio
        context['total_kgs_netos'] = total_kgs_netos
        
        # Totales preliquidados
        context['total_arps_liquidados'] = total_arps_liquidados
        context['total_kgs_liquidados'] = total_kgs_liquidados
        context['total_kgs_merma_liquidados'] = total_kgs_merma_liquidados
        context['total_importe_liquidado'] = total_importe_liquidado
        
        # Obtener datos de configuración de la empresa
        configuracion = ConfiguracionSistema.objects.first()
        context['configuracion'] = configuracion
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class RemisionDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar remisiones"""
    model = Remision
    template_name = 'core/remision_confirm_delete.html'
    success_url = reverse_lazy('core:remision_list')
    
    def get(self, request, *args, **kwargs):
        """Verificar que la remisión no esté cancelada antes de permitir la eliminación"""
        self.object = self.get_object()
        
        if self.object.cancelada:
            messages.error(request, 'No se puede eliminar una remisión cancelada.')
            return redirect('core:remision_list')
        
        return super().get(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        try:
            remision = self.get_object()
            
            # Verificar que la remisión no esté cancelada
            if remision.cancelada:
                messages.error(request, 'No se puede eliminar una remisión cancelada.')
                return redirect('core:remision_list')
            
            remision_str = f"{remision.ciclo} - {remision.folio:06d}"
            
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Remisión "{remision_str}" eliminada exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar remisión: {str(e)}')
            return redirect('core:remision_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Remisión: {self.object.ciclo} - {self.object.folio:06d}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# ===========================
# VISTAS PARA CRUD DE DETALLES DE REMISIONES
# ===========================

class RemisionDetalleCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear detalles de remisiones"""
    model = RemisionDetalle
    form_class = RemisionDetalleForm
    template_name = 'core/remision_detalle_form.html'
    
    def get_success_url(self):
        return reverse_lazy('core:remision_detail', kwargs={'pk': self.kwargs['remision_id']})
    
    def form_valid(self, form):
        try:
            # Asignar la remisión y el usuario que crea el registro
            remision = get_object_or_404(Remision, pk=self.kwargs['remision_id'])
            form.instance.remision = remision
            form.instance.usuario_creacion = self.request.user
            
            response = super().form_valid(form)
            messages.success(self.request, f'Detalle de remisión creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear detalle de remisión: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        remision = get_object_or_404(Remision, pk=self.kwargs['remision_id'])
        context['remision'] = remision
        context['title'] = f'Nuevo Detalle - Remisión: {remision.ciclo} - {remision.folio:06d}'
        return context


@login_required
def remision_detalle_create_ajax(request, remision_id):
    """Crear detalle de remisión vía AJAX desde el modal en edición."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        remision = get_object_or_404(Remision, pk=remision_id)

        cultivo_id = request.POST.get('cultivo_id')
        calidad = request.POST.get('calidad')
        no_arps = request.POST.get('no_arps')
        precio_envio = request.POST.get('precio_envio', '0')
        kgs_enviados = request.POST.get('kgs_enviados', '0')
        kgs_merma = request.POST.get('kgs_merma', '0')
        kgs_neto_envio = request.POST.get('kgs_neto_envio', '0')
        importe_envio = request.POST.get('importe_envio', '0')
        importe_neto_envio = request.POST.get('importe_neto_envio', '0')
        peso_promedio = request.POST.get('peso_promedio', '0')

        if not cultivo_id or not calidad or not no_arps:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)

        cultivo = get_object_or_404(Cultivo, pk=int(cultivo_id))

        detalle = RemisionDetalle.objects.create(
            remision=remision,
            cultivo=cultivo,
            calidad=calidad,
            no_arps=int(no_arps),
            kgs_enviados=Decimal(str(kgs_enviados or 0)),
            merma_arps=Decimal(str(remision.merma_arps_global or 0)),
            kgs_merma=Decimal(str(kgs_merma or 0)),
            kgs_neto_envio=Decimal(str(kgs_neto_envio or 0)),
            precio_envio=Decimal(str(precio_envio or 0)),
            importe_envio=Decimal(str(importe_envio or 0)),
            importe_neto_envio=Decimal(str(importe_neto_envio or 0)),
            peso_promedio=Decimal(str(peso_promedio or 0)),
            kgs_liquidados=Decimal('0'),
            precio=Decimal('0'),
            importe_liquidado=Decimal('0'),
            usuario_creacion=request.user
        )

        # Recalcular TODOS los detalles con el nuevo peso promedio global
        try:
            total_arps = remision.detalles.aggregate(total=models.Sum('no_arps'))['total'] or 0
            peso_bruto = remision.peso_bruto_embarque or Decimal('0')
            merma_arps_global = remision.merma_arps_global or Decimal('0')

            if total_arps and peso_bruto and total_arps > 0 and peso_bruto > 0:
                peso_promedio_global = Decimal(peso_bruto) / Decimal(total_arps)
                for det in remision.detalles.all():
                    det.peso_promedio = peso_promedio_global
                    det.kgs_enviados = (peso_promedio_global * Decimal(det.no_arps)).quantize(Decimal('0.01'))
                    det.merma_arps = merma_arps_global
                    det.kgs_merma = (merma_arps_global * Decimal(det.no_arps)).quantize(Decimal('0.01'))
                    det.kgs_neto_envio = (det.kgs_enviados - det.kgs_merma).quantize(Decimal('0.01'))
                    det.importe_envio = (Decimal(det.precio_envio or 0) * det.kgs_enviados).quantize(Decimal('0.01'))
                    det.importe_neto_envio = (Decimal(det.precio_envio or 0) * det.kgs_neto_envio).quantize(Decimal('0.01'))
                    det.save(update_fields=['peso_promedio','kgs_enviados','merma_arps','kgs_merma','kgs_neto_envio','importe_envio','importe_neto_envio'])
        except Exception as _:
            # No interrumpir la creación si el recálculo falla; el front recargará de todas formas
            pass

        return JsonResponse({
            'success': True,
            'detalle': {
                'id': detalle.pk,
                'cultivo': f"{detalle.cultivo.nombre} - {detalle.cultivo.variedad}",
                'calidad': detalle.calidad,
                'no_arps': detalle.no_arps,
                'kgs_enviados': float(detalle.kgs_enviados),
                'kgs_merma': float(detalle.kgs_merma),
                'kgs_neto_envio': float(detalle.kgs_neto_envio),
                'precio_envio': float(detalle.precio_envio),
                'importe_envio': float(detalle.importe_envio),
                'importe_neto_envio': float(detalle.importe_neto_envio),
                'peso_promedio': float(detalle.peso_promedio),
            }
        })
    except Exception as e:
        return JsonResponse({'error': f'Error interno del servidor: {str(e)}'}, status=500)


@login_required
def remision_recalcular_detalles_ajax(request, remision_id):
    """Recalcula todos los detalles de una remisión usando el peso bruto y merma/arps actuales."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        remision = get_object_or_404(Remision, pk=remision_id)

        # Permitir opcionalmente recibir nuevos valores desde el front
        peso_bruto_str = request.POST.get('peso_bruto_embarque')
        merma_arps_str = request.POST.get('merma_arps_global')

        if peso_bruto_str is not None:
            try:
                remision.peso_bruto_embarque = Decimal(peso_bruto_str)
            except Exception:
                pass
        if merma_arps_str is not None:
            try:
                remision.merma_arps_global = Decimal(merma_arps_str)
            except Exception:
                pass

        remision.save(update_fields=['peso_bruto_embarque', 'merma_arps_global'])

        total_arps = remision.detalles.aggregate(total=models.Sum('no_arps'))['total'] or 0
        peso_bruto = remision.peso_bruto_embarque or Decimal('0')
        merma_arps_global = remision.merma_arps_global or Decimal('0')

        detalles_response = []
        if total_arps and peso_bruto and total_arps > 0 and peso_bruto > 0:
            peso_promedio_global = Decimal(peso_bruto) / Decimal(total_arps)
            for det in remision.detalles.all():
                det.peso_promedio = peso_promedio_global
                det.kgs_enviados = (peso_promedio_global * Decimal(det.no_arps)).quantize(Decimal('0.01'))
                det.merma_arps = merma_arps_global
                det.kgs_merma = (merma_arps_global * Decimal(det.no_arps)).quantize(Decimal('0.01'))
                det.kgs_neto_envio = (det.kgs_enviados - det.kgs_merma).quantize(Decimal('0.01'))
                det.importe_envio = (Decimal(det.precio_envio or 0) * det.kgs_enviados).quantize(Decimal('0.01'))
                det.importe_neto_envio = (Decimal(det.precio_envio or 0) * det.kgs_neto_envio).quantize(Decimal('0.01'))
                det.save(update_fields=['peso_promedio','kgs_enviados','merma_arps','kgs_merma','kgs_neto_envio','importe_envio','importe_neto_envio'])

                detalles_response.append({
                    'id': det.pk,
                    'no_arps': det.no_arps,
                    'kgs_enviados': float(det.kgs_enviados),
                    'kgs_merma': float(det.kgs_merma),
                    'kgs_neto_envio': float(det.kgs_neto_envio),
                    'precio_envio': float(det.precio_envio or 0),
                    'importe_envio': float(det.importe_envio),
                    'importe_neto_envio': float(det.importe_neto_envio),
                    'peso_promedio': float(det.peso_promedio),
                })

        return JsonResponse({'success': True, 'detalles': detalles_response})
    except Exception as e:
        return JsonResponse({'error': f'Error interno del servidor: {str(e)}'}, status=500)

# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class RemisionDetalleUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar detalles de remisiones"""
    model = RemisionDetalle
    form_class = RemisionDetalleForm
    template_name = 'core/remision_detalle_form.html'
    
    def get_success_url(self):
        return reverse_lazy('core:remision_detail', kwargs={'pk': self.object.remision.pk})
    
    def form_valid(self, form):
        try:
            # Asignar el usuario que modifica el registro
            form.instance.usuario_modificacion = self.request.user
            
            response = super().form_valid(form)
            messages.success(self.request, f'Detalle de remisión actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar detalle de remisión: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['remision'] = self.object.remision
        context['title'] = f'Editar Detalle - Remisión: {self.object.remision.ciclo} - {self.object.remision.folio:06d}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class RemisionDetalleDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar detalles de remisiones"""
    model = RemisionDetalle
    template_name = 'core/remision_detalle_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('core:remision_detail', kwargs={'pk': self.object.remision.pk})
    
    def delete(self, request, *args, **kwargs):
        try:
            detalle = self.get_object()
            remision_str = f"{detalle.remision.ciclo} - {detalle.remision.folio:06d}"
            
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Detalle de remisión eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar detalle de remisión: {str(e)}')
            return redirect('core:remision_detail', pk=self.object.remision.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['remision'] = self.object.remision
        context['title'] = f'Eliminar Detalle - Remisión: {self.object.remision.ciclo} - {self.object.remision.folio:06d}'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def cancelar_remision_ajax(request, pk):
    """Vista AJAX para cancelar una remisión"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Verificar que el usuario sea administrador
    try:
        remision = get_object_or_404(Remision, pk=pk)
        
        # Verificar que la remisión no esté ya cancelada
        if remision.cancelada:
            return JsonResponse({'error': 'Esta remisión ya está cancelada'}, status=400)
        
        # Procesar el formulario
        form = RemisionCancelacionForm(request.POST)
        
        if form.is_valid():
            # Actualizar la remisión con los datos de cancelación
            from django.utils import timezone
            
            remision.cancelada = True
            remision.motivo_cancelacion = form.cleaned_data['motivo_cancelacion']
            remision.folio_sustituto = form.cleaned_data['folio_sustituto'] or None
            remision.usuario_cancelacion = request.user
            remision.fecha_cancelacion = timezone.now()
            remision.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Remisión "{remision.ciclo} - {remision.folio:06d}" cancelada exitosamente.',
                'remision_id': remision.pk,
                'estado': 'Cancelada'
            })
        else:
            # Devolver errores del formulario
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0] if error_list else ''
            
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CobranzaListView(LoginRequiredMixin, ListView):
    """Vista para listar remisiones preliquidadas agrupadas por cliente para cobranza"""
    model = Remision
    template_name = 'core/cobranza_list.html'
    context_object_name = 'remisiones_agrupadas'
    paginate_by = 20
    
    def get_queryset(self):
        """Obtener remisiones preliquidadas agrupadas por cliente con filtros"""
        # Obtener parámetros de búsqueda
        busqueda = self.request.GET.get('busqueda', '')
        cliente_id = self.request.GET.get('cliente', '')
        estado_facturacion = self.request.GET.get('estado_facturacion', '')
        estado_pago = self.request.GET.get('estado_pago', '')
        fecha_desde = self.request.GET.get('fecha_desde', '')
        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        
        # Filtrar solo remisiones preliquidadas y no canceladas
        remisiones = Remision.objects.filter(
            cancelada=False
        ).select_related('cliente').prefetch_related('detalles')
        
        # Aplicar filtros
        if busqueda:
            remisiones = remisiones.filter(
                Q(ciclo__icontains=busqueda) |
                Q(folio__icontains=busqueda) |
                Q(cliente__razon_social__icontains=busqueda)
            )
        
        if cliente_id:
            remisiones = remisiones.filter(cliente_id=cliente_id)
        
        if estado_facturacion == 'pendiente':
            remisiones = remisiones.filter(facturado=False)
        elif estado_facturacion == 'facturado':
            remisiones = remisiones.filter(facturado=True)
        
        
        if fecha_desde:
            remisiones = remisiones.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            remisiones = remisiones.filter(fecha__lte=fecha_hasta)
        
        # Filtrar solo las que están preliquidadas
        remisiones_preliquidadas = []
        for remision in remisiones:
            if remision.esta_liquidada():
                # Aplicar filtro de estado de pago basado en saldo pendiente
                saldo_pendiente = remision.saldo_pendiente
                
                if estado_pago == 'pendiente':
                    # Mostrar solo remisiones con saldo pendiente (no pagadas completamente)
                    if saldo_pendiente > 0:
                        remisiones_preliquidadas.append(remision)
                elif estado_pago == 'pagado':
                    # Mostrar solo remisiones con saldo cero (completamente pagadas)
                    if saldo_pendiente == 0:
                        remisiones_preliquidadas.append(remision)
                else:
                    # Sin filtro de estado de pago, mostrar solo las no pagadas (comportamiento por defecto)
                    if saldo_pendiente > 0:
                        remisiones_preliquidadas.append(remision)
        
        # Agrupar por cliente
        clientes_dict = {}
        for remision in remisiones_preliquidadas:
            cliente = remision.cliente
            if cliente not in clientes_dict:
                clientes_dict[cliente] = []
            clientes_dict[cliente].append(remision)
        
        # Convertir a lista de tuplas (cliente, lista_remisiones)
        clientes_agrupados = []
        for cliente, remisiones_cliente in clientes_dict.items():
            # Ordenar remisiones por fecha descendente
            remisiones_cliente.sort(key=lambda x: x.fecha, reverse=True)
            clientes_agrupados.append((cliente, remisiones_cliente))
        
        # Ordenar por razón social del cliente
        clientes_agrupados.sort(key=lambda x: x[0].razon_social)
        
        return clientes_agrupados
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cobranza - Remisiones Preliquidadas'
        
        # Agregar formulario de búsqueda
        context['search_form'] = CobranzaSearchForm(self.request.GET)
        
        # Calcular totales por cliente y agregar a cada tupla
        remisiones_agrupadas_con_totales = []
        total_general = 0
        saldo_general = 0
        
        for cliente, remisiones in context['remisiones_agrupadas']:
            total_importe = 0
            saldo_cliente = 0
            remisiones_con_importe = []
            
            for remision in remisiones:
                # Calcular el importe total de esta remisión
                importe_remision = 0
                for detalle in remision.detalles.all():
                    importe_remision += detalle.importe_liquidado
                
                # Calcular el saldo pendiente de la remisión
                saldo_remision = remision.saldo_pendiente
                
                # Agregar el importe de la remisión al total del cliente
                total_importe += importe_remision
                saldo_cliente += saldo_remision
                
                # Crear una tupla con la remisión y su importe
                remisiones_con_importe.append((remision, importe_remision))
            
            # Agregar el total y saldo a la tupla
            remisiones_agrupadas_con_totales.append((cliente, remisiones_con_importe, total_importe, saldo_cliente))
            total_general += total_importe
            saldo_general += saldo_cliente
        
        context['remisiones_agrupadas'] = remisiones_agrupadas_con_totales
        context['total_general'] = total_general
        context['saldo_general'] = saldo_general
        # Datos para modal de filtros de Reporte de Pagos
        context['clientes'] = Cliente.objects.all().order_by('razon_social')
        context['cuentas_bancarias'] = CuentaBancaria.objects.filter(activo=True).order_by('nombre_corto')
        # Ciclo actual desde configuración (para prefijar en el modal)
        try:
            configuracion = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = configuracion.ciclo_actual if configuracion else ''
        except Exception:
            context['ciclo_actual'] = ''
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def actualizar_estado_cobranza_ajax(request, pk):
    """Vista AJAX para actualizar el estado de facturado o pagado de una remisión"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        remision = get_object_or_404(Remision, pk=pk)
        
        # Verificar que la remisión esté preliquidada
        if not remision.esta_liquidada():
            return JsonResponse({
                'error': 'Solo se pueden actualizar remisiones preliquidadas'
            }, status=400)
        
        # Verificar que la remisión no esté cancelada
        if remision.cancelada:
            return JsonResponse({
                'error': 'No se puede actualizar una remisión cancelada'
            }, status=400)
        
        # Obtener la acción a realizar
        accion = request.POST.get('accion')
        
        if accion == 'facturado':
            # Marcar como facturado
            remision.facturado = True
            remision.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Remisión "{remision.ciclo} - {remision.folio:06d}" marcada como facturada.',
                'remision_id': remision.pk,
                'estado': 'Facturado'
            })
            
        elif accion == 'pagado':
            # Verificar que esté facturado antes de marcar como pagado
            if not remision.facturado:
                return JsonResponse({
                    'error': 'La remisión debe estar facturada antes de marcarla como pagada'
                }, status=400)
            
            # Calcular el total de la remisión
            total_remision = remision.detalles.aggregate(
                total=models.Sum('importe_liquidado')
            )['total'] or 0
            
            # Verificar si ya existe un pago registrado
            pago_existente = PagoRemision.objects.filter(remision=remision, activo=True).first()
            
            if not pago_existente and total_remision > 0:
                # Crear un registro de pago automáticamente
                PagoRemision.objects.create(
                    remision=remision,
                    cuenta_bancaria=None,  # Sin cuenta bancaria específica
                    metodo_pago='efectivo',  # Método por defecto
                    monto=total_remision,
                    fecha_pago=timezone.now().date(),
                    referencia='Marcado como pagado en cobranza',
                    observaciones='Pago registrado automáticamente al marcar la remisión como pagada',
                    activo=True,
                    usuario_creacion=request.user
                )
            
            # Marcar como pagado
            remision.pagado = True
            remision.fecha_pago = timezone.now().date()
            remision.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Remisión "{remision.ciclo} - {remision.folio:06d}" marcada como pagada.',
                'remision_id': remision.pk,
                'estado': 'Pagado'
            })
            
        else:
            return JsonResponse({
                'error': 'Acción no válida. Use "facturado" o "pagado"'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CobranzaImprimirView(LoginRequiredMixin, TemplateView):
    """Vista para imprimir el estado de cuenta de cobranza"""
    template_name = 'core/cobranza_imprimir.html'
    
    def get_queryset(self):
        """Obtener remisiones preliquidadas con los mismos filtros que la vista principal"""
        # Obtener parámetros de búsqueda (mismo código que CobranzaListView)
        busqueda = self.request.GET.get('busqueda', '')
        cliente_id = self.request.GET.get('cliente', '')
        estado_facturacion = self.request.GET.get('estado_facturacion', '')
        estado_pago = self.request.GET.get('estado_pago', '')
        fecha_desde = self.request.GET.get('fecha_desde', '')
        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        
        # Filtrar solo remisiones preliquidadas y no canceladas
        remisiones = Remision.objects.filter(
            cancelada=False
        ).select_related('cliente').prefetch_related('detalles')
        
        # Aplicar filtros (mismo código que CobranzaListView)
        if busqueda:
            remisiones = remisiones.filter(
                Q(ciclo__icontains=busqueda) |
                Q(folio__icontains=busqueda) |
                Q(cliente__razon_social__icontains=busqueda)
            )
        
        if cliente_id:
            remisiones = remisiones.filter(cliente_id=cliente_id)
        
        if estado_facturacion == 'pendiente':
            remisiones = remisiones.filter(facturado=False)
        elif estado_facturacion == 'facturado':
            remisiones = remisiones.filter(facturado=True)
        
        
        if fecha_desde:
            remisiones = remisiones.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            remisiones = remisiones.filter(fecha__lte=fecha_hasta)
        
        # Filtrar solo las que están preliquidadas
        remisiones_preliquidadas = []
        for remision in remisiones:
            if remision.esta_liquidada():
                # Aplicar filtro de estado de pago basado en saldo pendiente
                saldo_pendiente = remision.saldo_pendiente
                
                if estado_pago == 'pendiente':
                    # Mostrar solo remisiones con saldo pendiente (no pagadas completamente)
                    if saldo_pendiente > 0:
                        remisiones_preliquidadas.append(remision)
                elif estado_pago == 'pagado':
                    # Mostrar solo remisiones con saldo cero (completamente pagadas)
                    if saldo_pendiente == 0:
                        remisiones_preliquidadas.append(remision)
                else:
                    # Sin filtro de estado de pago, mostrar solo las no pagadas (comportamiento por defecto)
                    if saldo_pendiente > 0:
                        remisiones_preliquidadas.append(remision)
        
        # Agrupar por cliente
        clientes_dict = {}
        for remision in remisiones_preliquidadas:
            cliente = remision.cliente
            if cliente not in clientes_dict:
                clientes_dict[cliente] = []
            clientes_dict[cliente].append(remision)
        
        # Convertir a lista de tuplas (cliente, lista_remisiones)
        clientes_agrupados = []
        for cliente, remisiones_cliente in clientes_dict.items():
            # Ordenar remisiones por fecha descendente
            remisiones_cliente.sort(key=lambda x: x.fecha, reverse=True)
            clientes_agrupados.append((cliente, remisiones_cliente))
        
        # Ordenar por razón social del cliente
        clientes_agrupados.sort(key=lambda x: x[0].razon_social)
        
        return clientes_agrupados
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Estado de Cuenta - Cobranza'
        
        # Obtener datos de configuración de la empresa
        configuracion = ConfiguracionSistema.objects.first()
        context['configuracion'] = configuracion
        
        # Obtener datos con filtros aplicados
        remisiones_agrupadas = self.get_queryset()
        
        # Calcular totales por cliente y agregar a cada tupla
        remisiones_agrupadas_con_totales = []
        total_general = 0
        saldo_general = 0
        total_remisiones = 0
        
        for cliente, remisiones in remisiones_agrupadas:
            # Contar las remisiones de este cliente
            total_remisiones += len(remisiones)
            total_importe = 0
            saldo_cliente = 0
            remisiones_con_importe = []
            
            for remision in remisiones:
                # Calcular el importe total de esta remisión
                importe_remision = 0
                for detalle in remision.detalles.all():
                    importe_remision += detalle.importe_liquidado
                
                # Calcular el saldo pendiente de la remisión
                saldo_remision = remision.saldo_pendiente
                
                # Agregar el importe de la remisión al total del cliente
                total_importe += importe_remision
                saldo_cliente += saldo_remision
                
                # Crear una tupla con la remisión y su importe
                remisiones_con_importe.append((remision, importe_remision))
            
            # Agregar el total y saldo a la tupla
            remisiones_agrupadas_con_totales.append((cliente, remisiones_con_importe, total_importe, saldo_cliente))
            total_general += total_importe
            saldo_general += saldo_cliente
        
        context['remisiones_agrupadas'] = remisiones_agrupadas_con_totales
        context['total_general'] = total_general
        context['saldo_general'] = saldo_general
        context['total_remisiones'] = total_remisiones
        
        # Información de filtros aplicados
        context['filtros_aplicados'] = {
            'busqueda': self.request.GET.get('busqueda', ''),
            'cliente_id': self.request.GET.get('cliente', ''),
            'estado_facturacion': self.request.GET.get('estado_facturacion', ''),
            'estado_pago': self.request.GET.get('estado_pago', ''),
            'fecha_desde': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
        }
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# ===========================
# VISTAS AJAX PARA CUENTAS BANCARIAS
# ===========================

@login_required
def agregar_cuenta_bancaria_ajax(request):
    """Vista AJAX para agregar una cuenta bancaria"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
    try:
        from ..models import CuentaBancaria
        
        # Obtener datos del formulario
        nombre_banco = request.POST.get('nombre_banco', '').strip()
        numero_cuenta = request.POST.get('numero_cuenta', '').strip()
        nombre_corto = request.POST.get('nombre_corto', '').strip()
        
        # Validar campos requeridos
        if not nombre_banco:
            return JsonResponse({'error': 'El nombre del banco es requerido'}, status=400)
        
        if not numero_cuenta:
            return JsonResponse({'error': 'El número de cuenta es requerido'}, status=400)
        
        if not nombre_corto:
            return JsonResponse({'error': 'El nombre corto es requerido'}, status=400)
        
        # Crear la cuenta bancaria
        cuenta = CuentaBancaria.objects.create(
            nombre_banco=nombre_banco,
            numero_cuenta=numero_cuenta,
            nombre_corto=nombre_corto,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Cuenta bancaria agregada exitosamente',
            'cuenta': {
                'codigo': cuenta.codigo,
                'nombre_banco': cuenta.nombre_banco,
                'numero_cuenta': cuenta.numero_cuenta,
                'nombre_corto': cuenta.nombre_corto,
                'activo': cuenta.activo
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def listar_cuentas_bancarias_ajax(request):
    """Vista AJAX para listar cuentas bancarias"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from ..models import CuentaBancaria
        
        # Obtener todas las cuentas bancarias activas
        cuentas = CuentaBancaria.objects.filter(activo=True).order_by('nombre_corto')
        
        cuentas_data = []
        for cuenta in cuentas:
            cuentas_data.append({
                'codigo': cuenta.codigo,
                'nombre_banco': cuenta.nombre_banco,
                'numero_cuenta': cuenta.numero_cuenta,
                'nombre_corto': cuenta.nombre_corto,
                'activo': cuenta.activo
            })
        
        return JsonResponse({
            'success': True,
            'cuentas': cuentas_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_cuenta_bancaria_ajax(request, codigo):
    """Vista AJAX para eliminar una cuenta bancaria"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
    try:
        from ..models import CuentaBancaria
        
        # Obtener la cuenta bancaria
        cuenta = get_object_or_404(CuentaBancaria, codigo=codigo)
        
        # Marcar como inactiva en lugar de eliminar
        cuenta.activo = False
        cuenta.usuario_modificacion = request.user
        cuenta.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cuenta bancaria eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
@login_required
def capturar_pago_ajax(request, remision_id):
    """Vista AJAX para capturar pagos de remisiones"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        remision = Remision.objects.get(pk=remision_id)
        
        # Obtener datos del formulario
        monto = float(request.POST.get('monto', 0))
        metodo_pago = request.POST.get('metodo_pago')
        cuenta_bancaria_id = request.POST.get('cuenta_bancaria')
        fecha_pago = request.POST.get('fecha_pago')
        referencia = request.POST.get('referencia', '')
        observaciones = request.POST.get('observaciones', '')
        facturar_pago = request.POST.get('facturar_pago', 'false') == 'true'
        
        # Validaciones
        if monto <= 0:
            return JsonResponse({'error': 'El monto debe ser mayor a 0'}, status=400)
        
        if not metodo_pago:
            return JsonResponse({'error': 'Debe seleccionar un método de pago'}, status=400)
        
        if metodo_pago in ['transferencia', 'cheque'] and not cuenta_bancaria_id:
            return JsonResponse({'error': 'Debe seleccionar una cuenta bancaria para transferencias y cheques'}, status=400)
        
        if not fecha_pago:
            return JsonResponse({'error': 'Debe seleccionar una fecha de pago'}, status=400)
        
        # Obtener cuenta bancaria si es necesaria
        cuenta_bancaria = None
        if cuenta_bancaria_id:
            try:
                cuenta_bancaria = CuentaBancaria.objects.get(pk=cuenta_bancaria_id, activo=True)
            except CuentaBancaria.DoesNotExist:
                return JsonResponse({'error': 'Cuenta bancaria no encontrada'}, status=400)
        
        # Crear el pago
        from datetime import datetime
        fecha_pago_obj = datetime.strptime(fecha_pago, '%Y-%m-%d').date()
        
        pago = PagoRemision.objects.create(
            remision=remision,
            cuenta_bancaria=cuenta_bancaria,
            metodo_pago=metodo_pago,
            monto=monto,
            fecha_pago=fecha_pago_obj,
            referencia=referencia,
            observaciones=observaciones,
            usuario_creacion=request.user
        )
        
        # Calcular el total pagado de la remisión
        total_pagado = PagoRemision.objects.filter(remision=remision, activo=True).aggregate(
            total=models.Sum('monto')
        )['total'] or 0
        
        # Calcular el total de la remisión (suma de detalles)
        total_remision = remision.detalles.aggregate(
            total=models.Sum('importe_liquidado')
        )['total'] or 0
        
        # Marcar como pagada solo si el total pagado es mayor o igual al total de la remisión
        if total_pagado >= total_remision:
            remision.pagado = True
            remision.fecha_pago = fecha_pago_obj
            remision.save()
        
        response_data = {
            'success': True,
            'message': f'Pago de ${monto:,.2f} capturado correctamente',
            'pago_id': pago.codigo
        }
        
        # Si se debe facturar, agregar información para redirigir
        if facturar_pago:
            response_data['facturar'] = True
            response_data['pago_id'] = pago.codigo
        
        return JsonResponse(response_data)
        
    except Remision.DoesNotExist:
        return JsonResponse({'error': 'Remisión no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Error al capturar el pago: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def reporte_pagos_view(request):
    """Vista para mostrar reporte de pagos agrupados por cuenta bancaria"""
    # Obtener parámetros de filtro
    cliente_id = request.GET.get('cliente_id') or request.GET.get('cliente')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    remision = request.GET.get('remision')
    cuenta_bancaria_id = request.GET.get('cuenta_bancaria')
    metodo_pago = request.GET.get('metodo_pago')
    
    # Filtro de Ciclo (por defecto ciclo actual)
    ciclo_param = request.GET.get('ciclo', '').strip()
    try:
        ciclo_actual = (ConfiguracionSistema.objects.last().ciclo_actual or '').strip()
    except Exception:
        ciclo_actual = ''
    ciclo = ciclo_param or ciclo_actual

    # Obtener pagos
    pagos_query = PagoRemision.objects.filter(activo=True).select_related(
        'remision', 'cuenta_bancaria', 'remision__cliente'
    )
    
    # Aplicar filtros
    if cliente_id:
        pagos_query = pagos_query.filter(remision__cliente_id=cliente_id)
        cliente = Cliente.objects.get(pk=cliente_id)
        titulo = f"Reporte de Pagos - {cliente.razon_social}"
    else:
        cliente = None
        titulo = "Reporte General de Pagos"
    
    if fecha_desde:
        pagos_query = pagos_query.filter(fecha_pago__gte=fecha_desde)
    
    if fecha_hasta:
        pagos_query = pagos_query.filter(fecha_pago__lte=fecha_hasta)
    
    if remision:
        # Buscar por ciclo-folio
        if '-' in remision:
            try:
                ciclo, folio = remision.split('-', 1)
                pagos_query = pagos_query.filter(
                    remision__ciclo=ciclo,
                    remision__folio=int(folio)
                )
            except (ValueError, IndexError):
                pass  # Si no se puede parsear, no filtrar
    
    if cuenta_bancaria_id:
        if cuenta_bancaria_id == 'efectivo':
            pagos_query = pagos_query.filter(cuenta_bancaria__isnull=True)
        else:
            pagos_query = pagos_query.filter(cuenta_bancaria_id=cuenta_bancaria_id)
    
    if metodo_pago:
        pagos_query = pagos_query.filter(metodo_pago=metodo_pago)
    
    # Filtrar por ciclo si hay valor
    if ciclo:
        pagos_query = pagos_query.filter(remision__ciclo=ciclo)

    # Agrupar por cuenta bancaria
    pagos_por_cuenta = {}
    total_general = 0
    
    for pago in pagos_query:
        if pago.cuenta_bancaria:
            cuenta_key = pago.cuenta_bancaria.codigo
            cuenta_nombre = pago.cuenta_bancaria.nombre_corto
        else:
            cuenta_key = f'efectivo_{pago.metodo_pago}'
            cuenta_nombre = f'Efectivo ({pago.get_metodo_pago_display()})'
        
        if cuenta_key not in pagos_por_cuenta:
            pagos_por_cuenta[cuenta_key] = {
                'cuenta_nombre': cuenta_nombre,
                'pagos': [],
                'total': 0,
                'cantidad': 0
            }
        
        pagos_por_cuenta[cuenta_key]['pagos'].append(pago)
        pagos_por_cuenta[cuenta_key]['total'] += pago.monto
        pagos_por_cuenta[cuenta_key]['cantidad'] += 1
        total_general += pago.monto
    
    # Obtener datos para el modal de filtros
    clientes = Cliente.objects.all().order_by('razon_social')
    cuentas_bancarias = CuentaBancaria.objects.filter(activo=True).order_by('nombre_corto')
    
    # Obtener datos de configuración de la empresa
    configuracion = ConfiguracionSistema.objects.first()
    
    context = {
        'titulo': titulo,
        'cliente': cliente,
        'pagos_por_cuenta': pagos_por_cuenta,
        'total_general': total_general,
        'fecha_reporte': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'clientes': clientes,
        'cuentas_bancarias': cuentas_bancarias,
        'ciclo': ciclo,
        'ciclo_actual': ciclo_actual,
        'configuracion': configuracion,
    }
    
    return render(request, 'core/reporte_pagos.html', context)


# ==================== VISTAS DE PRESUPUESTOS ====================

class PresupuestoGastoListView(LoginRequiredMixin, ListView):
    """Vista para listar presupuestos de gastos"""
    model = PresupuestoGasto
    template_name = 'core/presupuesto_gasto_list.html'
    context_object_name = 'presupuestos'
    paginate_by = 20
    
    def get_queryset(self):
        """Obtener presupuestos con filtros"""
        # Obtener parámetros de búsqueda
        busqueda = self.request.GET.get('busqueda', '')
        centro_costo_id = self.request.GET.get('centro_costo', '')
        clasificacion_gasto_id = self.request.GET.get('clasificacion_gasto', '')
        ciclo = self.request.GET.get('ciclo', '')
        
        # Filtrar solo presupuestos activos
        presupuestos = PresupuestoGasto.objects.filter(
            activo=True
        ).select_related('centro_costo', 'clasificacion_gasto', 'usuario_creacion')
        
        # Aplicar filtros
        if busqueda:
            presupuestos = presupuestos.filter(
                Q(centro_costo__descripcion__icontains=busqueda) |
                Q(clasificacion_gasto__descripcion__icontains=busqueda) |
                Q(ciclo__icontains=busqueda)
            )
        
        if centro_costo_id:
            presupuestos = presupuestos.filter(centro_costo_id=centro_costo_id)
        
        if clasificacion_gasto_id:
            presupuestos = presupuestos.filter(clasificacion_gasto_id=clasificacion_gasto_id)
        
        if ciclo:
            presupuestos = presupuestos.filter(ciclo__icontains=ciclo)
        
        return presupuestos.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Presupuestos de Gastos'
        
        # Agregar formulario de búsqueda
        context['search_form'] = PresupuestoGastoSearchForm(self.request.GET)
        
        # Obtener ciclo actual de la configuración
        try:
            configuracion = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = configuracion.ciclo_actual if configuracion else ''
        except:
            context['ciclo_actual'] = ''
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class PresupuestoGastoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear presupuestos de gastos"""
    model = PresupuestoGasto
    form_class = PresupuestoGastoForm
    template_name = 'core/presupuesto_gasto_form.html'
    success_url = reverse_lazy('core:presupuesto_gasto_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Presupuesto de Gasto'
        
        # Obtener ciclo actual de la configuración
        try:
            configuracion = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = configuracion.ciclo_actual if configuracion else ''
        except:
            context['ciclo_actual'] = ''
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
    
    def form_valid(self, form):
        # Asignar el usuario actual y el ciclo actual
        form.instance.usuario_creacion = self.request.user
        
        # Obtener ciclo actual de la configuración
        try:
            configuracion = ConfiguracionSistema.objects.first()
            if configuracion and configuracion.ciclo_actual:
                form.instance.ciclo = configuracion.ciclo_actual
        except:
            pass
        
        return super().form_valid(form)


class PresupuestoGastoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar presupuestos de gastos"""
    model = PresupuestoGasto
    form_class = PresupuestoGastoForm
    template_name = 'core/presupuesto_gasto_form.html'
    success_url = reverse_lazy('core:presupuesto_gasto_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Presupuesto de Gasto'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
    
    def form_valid(self, form):
        # Asignar el usuario de modificación
        form.instance.usuario_modificacion = self.request.user
        return super().form_valid(form)


class PresupuestoGastoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar presupuestos de gastos"""
    model = PresupuestoGasto
    template_name = 'core/presupuesto_gasto_confirm_delete.html'
    success_url = reverse_lazy('core:presupuesto_gasto_list')
    
    def delete(self, request, *args, **kwargs):
        # En lugar de eliminar, marcar como inactivo
        self.object = self.get_object()
        self.object.activo = False
        self.object.usuario_modificacion = request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


@login_required
def presupuesto_gasto_ajax(request, pk):
    """Vista AJAX para obtener datos de un presupuesto específico"""
    try:
        presupuesto = PresupuestoGasto.objects.get(pk=pk, activo=True)
        data = {
            'codigo': presupuesto.codigo,
            'centro_costo': presupuesto.centro_costo.descripcion,
            'clasificacion_gasto': presupuesto.clasificacion_gasto.descripcion,
            'ciclo': presupuesto.ciclo,
            'importe': float(presupuesto.importe),
            'observaciones': presupuesto.observaciones or '',
            'fecha_creacion': presupuesto.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'usuario_creacion': presupuesto.usuario_creacion.get_full_name() or presupuesto.usuario_creacion.username
        }
        return JsonResponse(data)
    except PresupuestoGasto.DoesNotExist:
        return JsonResponse({'error': 'Presupuesto no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===========================
# VISTAS PARA PRESUPUESTOS (NUEVA ESTRUCTURA)
# ===========================

class PresupuestoListView(LoginRequiredMixin, ListView):
    """Vista para listar presupuestos"""
    model = Presupuesto
    template_name = 'core/presupuesto_list.html'
    context_object_name = 'presupuestos'
    paginate_by = 20
    
    def get_queryset(self):
        # Obtener el ciclo actual de la configuración
        try:
            config = ConfiguracionSistema.objects.first()
            ciclo_actual = config.ciclo_actual if config else ''
        except:
            ciclo_actual = ''
        
        # Filtrar por ciclo actual si está configurado (mostrar todos, activos e inactivos)
        if ciclo_actual:
            queryset = Presupuesto.objects.filter(ciclo=ciclo_actual).select_related('centro_costo', 'usuario_creacion')
        else:
            queryset = Presupuesto.objects.all().select_related('centro_costo', 'usuario_creacion')
        
        # Aplicar filtros de búsqueda
        busqueda = self.request.GET.get('busqueda', '')
        centro_costo_id = self.request.GET.get('centro_costo', '')
        ciclo = self.request.GET.get('ciclo', '')
        
        if busqueda:
            queryset = queryset.filter(
                Q(centro_costo__descripcion__icontains=busqueda) |
                Q(ciclo__icontains=busqueda) |
                Q(observaciones__icontains=busqueda)
            )
        
        if centro_costo_id:
            queryset = queryset.filter(centro_costo_id=centro_costo_id)
        
        if ciclo:
            queryset = queryset.filter(ciclo__icontains=ciclo)
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PresupuestoSearchForm(self.request.GET)
        context['centros_costo'] = CentroCosto.objects.filter(activo=True)
        
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        
        # Calcular total de gastos para cada presupuesto
        presupuestos_con_gastos = []
        for presupuesto in context['presupuestos']:
            # Obtener todos los gastos del presupuesto
            gastos = Gasto.objects.filter(presupuesto=presupuesto, activo=True)
            total_gastos = 0
            
            for gasto in gastos:
                # Sumar todos los detalles de gasto activos
                from django.db.models import Sum
                total_detalle = gasto.detalles.filter(activo=True).aggregate(
                    total=Sum('importe')
                )['total'] or 0
                total_gastos += float(total_detalle)
            
            presupuestos_con_gastos.append({
                'presupuesto': presupuesto,
                'total_gastos': total_gastos
            })
        
        context['presupuestos_con_gastos'] = presupuestos_con_gastos
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class PresupuestoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear presupuestos"""
    model = Presupuesto
    form_class = PresupuestoForm
    template_name = 'core/presupuesto_form.html'
    success_url = reverse_lazy('core:presupuesto_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el usuario sea administrador
        if not (request.user.is_admin or request.user.is_superuser):
            messages.error(request, 'No tienes permisos para crear presupuestos.')
            return HttpResponseRedirect(reverse_lazy('core:presupuesto_list'))
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        """Inicializar el formulario con el ciclo actual"""
        initial = super().get_initial()
        try:
            config = ConfiguracionSistema.objects.first()
            initial['ciclo'] = config.ciclo_actual if config else '2025-2026'
        except:
            initial['ciclo'] = '2025-2026'
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else 'No definido'
        except:
            context['ciclo_actual'] = 'No definido'
        
        # Obtener clasificaciones de gastos para el modal
        context['clasificaciones_gastos'] = ClasificacionGasto.objects.filter(activo=True)
        
        return context

    def form_valid(self, form):
        # Asignar usuario de creación para evitar ValidationError
        form.instance.usuario_creacion = self.request.user
        
        # Guardar el presupuesto primero
        response = super().form_valid(form)
        
        # Crear los detalles temporales si existen
        detalles_temporales = self.request.POST.get('detalles_temporales')
        
        # Debug: verificar que el campo llegó
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'Detalles temporales recibidos: {detalles_temporales}')
        
        if detalles_temporales:
            try:
                import json
                detalles_data = json.loads(detalles_temporales)
                logger.info(f'Detalles parseados: {detalles_data}')
                
                detalles_creados = 0
                for detalle_data in detalles_data:
                    try:
                        clasificacion_gasto = ClasificacionGasto.objects.get(
                            codigo=detalle_data['clasificacion_gasto']['codigo']
                        )
                        
                        PresupuestoDetalle.objects.create(
                            presupuesto=form.instance,
                            clasificacion_gasto=clasificacion_gasto,
                            importe=detalle_data['importe'],
                            usuario_creacion=self.request.user
                        )
                        detalles_creados += 1
                    except ClasificacionGasto.DoesNotExist:
                        logger.error(f'Clasificación de gasto no encontrada: {detalle_data.get("clasificacion_gasto", {}).get("codigo")}')
                        messages.error(self.request, f'Clasificación de gasto no encontrada: {detalle_data.get("clasificacion_gasto", {}).get("descripcion", "Desconocida")}')
                    except Exception as e:
                        logger.error(f'Error al crear detalle: {str(e)}')
                        messages.error(self.request, f'Error al crear detalle: {str(e)}')
                
                if detalles_creados > 0:
                    messages.success(self.request, f'Presupuesto creado con {detalles_creados} clasificación(es) de gasto.')
            except json.JSONDecodeError as e:
                logger.error(f'Error al parsear JSON de detalles: {str(e)}')
                messages.error(self.request, f'Error al procesar los detalles: Formato JSON inválido')
            except Exception as e:
                # Si hay error al crear detalles, agregar mensaje de error
                logger.error(f'Error general al crear detalles: {str(e)}')
                messages.error(self.request, f'Error al crear algunos detalles: {str(e)}')
        else:
            logger.info('No se recibieron detalles temporales')
        
        return response


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)




class PresupuestoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar presupuestos"""
    model = Presupuesto
    form_class = PresupuestoForm
    template_name = 'core/presupuesto_form.html'
    success_url = reverse_lazy('core:presupuesto_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el usuario sea administrador
        if not (request.user.is_admin or request.user.is_superuser):
            messages.error(request, 'No tienes permisos para editar presupuestos.')
            return HttpResponseRedirect(reverse_lazy('core:presupuesto_list'))
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        """Inicializar el formulario con el ciclo actual"""
        initial = super().get_initial()
        try:
            config = ConfiguracionSistema.objects.first()
            initial['ciclo'] = config.ciclo_actual if config else '2025-2026'
        except:
            initial['ciclo'] = '2025-2026'
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else 'No definido'
        except:
            context['ciclo_actual'] = 'No definido'
        
        # Obtener clasificaciones de gastos para el modal
        context['clasificaciones_gastos'] = ClasificacionGasto.objects.filter(activo=True)
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
    
    def form_valid(self, form):
        # Establecer el usuario de modificación
        form.instance.usuario_modificacion = self.request.user
        
        return super().form_valid(form)
    
    def post(self, request, *args, **kwargs):
        # Manejar AJAX para agregar/eliminar detalles
        if request.headers.get('Content-Type') == 'application/json' or 'action' in request.POST:
            action = request.POST.get('action')
            
            if action == 'add_detalle':
                return self.add_detalle(request)
            elif action == 'delete_detalle':
                return self.delete_detalle(request)
        
        return super().post(request, *args, **kwargs)
    
    def add_detalle(self, request):
        """Agregar un detalle al presupuesto"""
        try:
            presupuesto_id = self.get_object().codigo
            clasificacion_gasto_id = request.POST.get('clasificacion_gasto')
            importe = request.POST.get('importe')
            
            if not all([presupuesto_id, clasificacion_gasto_id, importe]):
                return JsonResponse({'success': False, 'message': 'Faltan datos requeridos'})
            
            presupuesto = Presupuesto.objects.get(pk=presupuesto_id)
            clasificacion_gasto = ClasificacionGasto.objects.get(pk=clasificacion_gasto_id)
            
            detalle = PresupuestoDetalle.objects.create(
                presupuesto=presupuesto,
                clasificacion_gasto=clasificacion_gasto,
                importe=importe,
                usuario_creacion=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Detalle agregado correctamente',
                'detalle': {
                    'id': detalle.codigo,
                    'clasificacion': detalle.clasificacion_gasto.descripcion,
                    'importe': float(detalle.importe)
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    def delete_detalle(self, request):
        """Eliminar un detalle del presupuesto"""
        try:
            detalle_id = request.POST.get('detalle_id')
            detalle = PresupuestoDetalle.objects.get(pk=detalle_id)
            detalle.delete()
            
            return JsonResponse({'success': True, 'message': 'Detalle eliminado correctamente'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


class PresupuestoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar presupuestos"""
    model = Presupuesto
    template_name = 'core/presupuesto_confirm_delete.html'
    success_url = reverse_lazy('core:presupuesto_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el usuario sea administrador
        if not (request.user.is_admin or request.user.is_superuser):
            messages.error(request, 'No tienes permisos para eliminar presupuestos.')
            return HttpResponseRedirect(reverse_lazy('core:presupuesto_list'))
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Eliminar lógicamente el presupuesto"""
        self.object = self.get_object()
        self.object.activo = False
        self.object.usuario_modificacion = request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


def clasificaciones_gastos_ajax(request):
    """Vista AJAX para obtener clasificaciones de gastos activas"""
    try:
        clasificaciones = ClasificacionGasto.objects.filter(activo=True).values('codigo', 'descripcion')
        data = {
            'success': True,
            'clasificaciones': list(clasificaciones)
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def presupuesto_detalle_ajax(request, pk):
    """Vista AJAX para agregar un detalle a un presupuesto existente"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            # Obtener el presupuesto
            presupuesto = get_object_or_404(Presupuesto, codigo=pk, activo=True)
            
            # Obtener la clasificación de gasto
            clasificacion_gasto = get_object_or_404(ClasificacionGasto, codigo=data['clasificacion_gasto']['codigo'], activo=True)
            
            # Crear el detalle
            detalle = PresupuestoDetalle.objects.create(
                presupuesto=presupuesto,
                clasificacion_gasto=clasificacion_gasto,
                importe=data['importe'],
                usuario_creacion=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Detalle agregado correctamente',
                'detalle_codigo': detalle.codigo
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


class PresupuestoDetailView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar los detalles de un presupuesto"""
    template_name = 'core/presupuesto_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        presupuesto = get_object_or_404(Presupuesto, codigo=kwargs['pk'], activo=True)
        context['presupuesto'] = presupuesto
        
        # Calcular gastos por clasificación primero (necesario para calcular gastos/hectárea)
        gastos_por_clasificacion = {}
        total_gastado = 0
        
        # Obtener todos los gastos del presupuesto
        gastos = Gasto.objects.filter(presupuesto=presupuesto, activo=True)
        
        for gasto in gastos:
            for detalle_gasto in gasto.detalles.filter(activo=True):
                clasificacion_id = detalle_gasto.clasificacion_gasto.codigo
                if clasificacion_id not in gastos_por_clasificacion:
                    gastos_por_clasificacion[clasificacion_id] = 0
                gastos_por_clasificacion[clasificacion_id] += float(detalle_gasto.importe)
                total_gastado += float(detalle_gasto.importe)
        
        context['gastos_por_clasificacion'] = gastos_por_clasificacion
        context['total_gastado'] = total_gastado
        
        # Obtener detalles y calcular costo por hectárea y gastos por hectárea para cada uno
        detalles_queryset = presupuesto.detalles.filter(activo=True).order_by('clasificacion_gasto__descripcion')
        detalles_con_costo_hect = []
        from decimal import Decimal
        
        for detalle in detalles_queryset:
            detalle_dict = {
                'detalle': detalle,
                'costo_hectarea': None,
                'gastos_hectarea': None
            }
            if presupuesto.centro_costo.hectareas and presupuesto.centro_costo.hectareas > 0:
                # Calcular costo por hectárea
                costo_hect = detalle.importe / presupuesto.centro_costo.hectareas
                detalle_dict['costo_hectarea'] = costo_hect
                
                # Calcular gastos por hectárea
                gastos_clasificacion = gastos_por_clasificacion.get(detalle.clasificacion_gasto.codigo, 0)
                gastos_hect = Decimal(str(gastos_clasificacion)) / presupuesto.centro_costo.hectareas
                detalle_dict['gastos_hectarea'] = gastos_hect
            detalles_con_costo_hect.append(detalle_dict)
        
        context['detalles'] = detalles_con_costo_hect
        
        # Calcular costo por hectárea total
        if presupuesto.centro_costo.hectareas and presupuesto.centro_costo.hectareas > 0:
            costo_hectarea = presupuesto.total_presupuestado / presupuesto.centro_costo.hectareas
            context['costo_hectarea'] = costo_hectarea
            
            # Calcular gastos por hectárea
            gastos_hectarea = Decimal(str(total_gastado)) / presupuesto.centro_costo.hectareas
            context['gastos_hectarea'] = gastos_hectarea
        else:
            context['costo_hectarea'] = None
            context['gastos_hectarea'] = None
        
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# Vistas para Gastos
class GastoListView(LoginRequiredMixin, ListView):
    """Vista para listar gastos"""
    model = Gasto
    template_name = 'core/gasto_list.html'
    context_object_name = 'gastos'
    paginate_by = 20

    def get_queryset(self):
        queryset = Gasto.objects.filter(activo=True).select_related(
            'presupuesto', 'presupuesto__centro_costo', 'usuario_creacion'
        ).order_by('-fecha_creacion')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Gastos'
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class GastoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear gastos con modal master-detail"""
    model = Gasto
    form_class = GastoForm
    template_name = 'core/gasto_form.html'
    success_url = reverse_lazy('core:gasto_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        return context

    def post(self, request, *args, **kwargs):
        # Si es una petición AJAX desde el modal
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'detalles_temporales' in request.POST:
            return self.handle_ajax_request(request)
        return super().post(request, *args, **kwargs)

    def handle_ajax_request(self, request):
        """Manejar petición AJAX para crear gasto desde modal"""
        try:
            # Escribir datos recibidos a archivo para debugging
            with open('/tmp/gasto_debug.log', 'a') as f:
                from datetime import datetime
                f.write(f"\n=== DEBUG GASTO {datetime.now()} ===\n")
                f.write(f"POST data: {dict(request.POST)}\n")
                f.write("=" * 50 + "\n")
            
            # Obtener datos del formulario
            presupuesto_codigo = request.POST.get('presupuesto')
            ciclo = request.POST.get('ciclo')
            fecha_gasto = request.POST.get('fecha_gasto')
            observaciones = request.POST.get('observaciones', '')
            
            # Validar que el presupuesto existe y está activo
            presupuesto = Presupuesto.objects.get(codigo=presupuesto_codigo)
            
            # Validar que el presupuesto esté activo
            if not presupuesto.activo:
                return JsonResponse({
                    'error': 'No se puede crear un gasto para un presupuesto inactivo'
                }, status=400)
            
            # Crear el gasto principal
            gasto = Gasto.objects.create(
                presupuesto=presupuesto,
                ciclo=ciclo,
                fecha_gasto=fecha_gasto,
                observaciones=observaciones,
                activo=True,
                usuario_creacion=request.user
            )
            
            # Procesar detalles temporales
            detalles_temporales = request.POST.get('detalles_temporales')
            if detalles_temporales:
                import json
                detalles_data = json.loads(detalles_temporales)
                
                for detalle_data in detalles_data:
                    proveedor = Proveedor.objects.get(codigo=detalle_data['proveedor']['codigo'])
                    clasificacion_gasto = ClasificacionGasto.objects.get(
                        codigo=detalle_data['clasificacion_gasto']['codigo']
                    )
                    
                    # Convertir importe a Decimal
                    from decimal import Decimal
                    importe_decimal = Decimal(str(detalle_data['importe']))
                    
                    # Obtener autorizó si está presente
                    autorizo = None
                    if 'autorizo' in detalle_data and detalle_data['autorizo'] and 'id' in detalle_data['autorizo']:
                        try:
                            autorizo = AutorizoGasto.objects.get(id=detalle_data['autorizo']['id'])
                        except AutorizoGasto.DoesNotExist:
                            pass
                    
                    # Extraer el código de forma de pago si viene como objeto
                    forma_pago_codigo = detalle_data.get('forma_pago')
                    if isinstance(forma_pago_codigo, dict):
                        forma_pago_codigo = forma_pago_codigo.get('codigo')
                    
                    GastoDetalle.objects.create(
                        gasto=gasto,
                        proveedor=proveedor,
                        factura=detalle_data['factura'],
                        clasificacion_gasto=clasificacion_gasto,
                        concepto=detalle_data['concepto'],
                        forma_pago=forma_pago_codigo,
                        autorizo=autorizo,
                        importe=importe_decimal,
                        usuario_creacion=request.user
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'Gasto creado correctamente',
                'gasto_id': gasto.codigo
            })
            
        except Exception as e:
            import traceback
            from datetime import datetime
            error_trace = traceback.format_exc()
            
            # Escribir error a archivo para debugging
            with open('/tmp/gasto_error.log', 'a') as f:
                f.write(f"\n=== ERROR GASTO {datetime.now()} ===\n")
                f.write(f"POST data: {dict(request.POST)}\n")
                f.write(f"Error: {str(e)}\n")
                f.write(f"Traceback: {error_trace}\n")
                f.write("=" * 50 + "\n")
            
            return JsonResponse({
                'success': False,
                'error': f"{e.__class__.__name__}: {str(e)}"
            }, status=500)


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        form.instance.ciclo = form.cleaned_data['ciclo']
        response = super().form_valid(form)
        
        # Procesar detalles temporales si existen
        detalles_temporales = self.request.POST.get('detalles_temporales')
        if detalles_temporales:
            try:
                import json
                detalles_data = json.loads(detalles_temporales)
                for detalle_data in detalles_data:
                    proveedor = Proveedor.objects.get(codigo=detalle_data['proveedor']['codigo'])
                    clasificacion_gasto = ClasificacionGasto.objects.get(
                        codigo=detalle_data['clasificacion_gasto']['codigo']
                    )
                    # Obtener autorizó si está presente
                    autorizo = None
                    if 'autorizo' in detalle_data and detalle_data['autorizo'] and 'id' in detalle_data['autorizo']:
                        try:
                            autorizo = AutorizoGasto.objects.get(id=detalle_data['autorizo']['id'])
                        except AutorizoGasto.DoesNotExist:
                            pass
                    
                    # Extraer el código de forma de pago si viene como objeto
                    forma_pago_codigo = detalle_data.get('forma_pago')
                    if isinstance(forma_pago_codigo, dict):
                        forma_pago_codigo = forma_pago_codigo.get('codigo')
                    
                    GastoDetalle.objects.create(
                        gasto=form.instance,
                        proveedor=proveedor,
                        factura=detalle_data['factura'],
                        clasificacion_gasto=clasificacion_gasto,
                        concepto=detalle_data['concepto'],
                        forma_pago=forma_pago_codigo,
                        autorizo=autorizo,
                        importe=detalle_data['importe'],
                        usuario_creacion=self.request.user
                    )
            except Exception as e:
                messages.error(self.request, f'Error al crear algunos detalles: {str(e)}')
        
        return response


class GastoDetailView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar los detalles de un gasto"""
    template_name = 'core/gasto_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gasto = get_object_or_404(Gasto, codigo=kwargs['pk'], activo=True)
        context['gasto'] = gasto
        context['detalles'] = gasto.detalles.filter(activo=True).order_by('proveedor__razon_social')
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class GastoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar gastos"""
    model = Gasto
    form_class = GastoForm
    template_name = 'core/gasto_form.html'
    success_url = reverse_lazy('core:gasto_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

    def form_valid(self, form):
        form.instance.usuario_modificacion = self.request.user
        return super().form_valid(form)


class GastoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar gastos (inactivar)"""
    model = Gasto
    template_name = 'core/gasto_confirm_delete.html'
    success_url = reverse_lazy('core:gasto_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.activo = False
        self.object.usuario_modificacion = request.user
        self.object.save()
        messages.success(request, 'Gasto eliminado correctamente.')
        return HttpResponseRedirect(self.get_success_url())


# Vistas AJAX para gastos
def proveedores_ajax(request):
    """Vista AJAX para obtener proveedores activos"""
    try:
        proveedores = Proveedor.objects.filter(activo=True).values('codigo', 'nombre')
        data = {
            'success': True,
            'proveedores': list(proveedores)
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def clasificaciones_gastos_presupuesto_ajax(request, presupuesto_id):
    """Vista AJAX para obtener clasificaciones de gastos de un presupuesto específico"""
    try:
        presupuesto = get_object_or_404(Presupuesto, codigo=presupuesto_id, activo=True)
        
        # Obtener las clasificaciones de gastos configuradas en el presupuesto
        clasificaciones_ids = presupuesto.detalles.filter(activo=True).values_list('clasificacion_gasto_id', flat=True)
        
        if clasificaciones_ids:
            # Si hay clasificaciones configuradas en el presupuesto, mostrarlas
            clasificaciones = ClasificacionGasto.objects.filter(
                codigo__in=clasificaciones_ids,
                activo=True
            ).values('codigo', 'descripcion').order_by('descripcion')
        else:
            # Si no hay clasificaciones configuradas, mostrar todas las disponibles
            clasificaciones = ClasificacionGasto.objects.filter(activo=True).values('codigo', 'descripcion').order_by('descripcion')
        
        data = {
            'success': True,
            'clasificaciones': list(clasificaciones)
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


class PresupuestoGastoFormView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar el formulario de captura de gastos para un presupuesto específico"""
    template_name = 'core/presupuesto_gasto_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        presupuesto = get_object_or_404(Presupuesto, codigo=kwargs['pk'], activo=True)
        context['presupuesto'] = presupuesto
        
        # Calcular gastos por clasificación
        gastos_por_clasificacion = {}
        total_gastado = 0
        
        # Obtener todos los gastos del presupuesto
        gastos = Gasto.objects.filter(presupuesto=presupuesto, activo=True)
        
        for gasto in gastos:
            for detalle_gasto in gasto.detalles.filter(activo=True):
                clasificacion_id = detalle_gasto.clasificacion_gasto.codigo
                if clasificacion_id not in gastos_por_clasificacion:
                    gastos_por_clasificacion[clasificacion_id] = 0
                gastos_por_clasificacion[clasificacion_id] += float(detalle_gasto.importe)
                total_gastado += float(detalle_gasto.importe)
        
        context['gastos_por_clasificacion'] = gastos_por_clasificacion
        context['total_gastado'] = total_gastado
        
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
class PresupuestoGastosReporteView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar el reporte de gastos de un presupuesto específico"""
    template_name = 'core/presupuesto_gastos_reporte.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros de filtro
        ciclo = self.request.GET.get('ciclo')
        centro_costo_id = self.request.GET.get('centro_costo')
        forma_pago = self.request.GET.get('forma_pago')
        autorizo_id = self.request.GET.get('autorizo')
        
        # Obtener el ciclo actual como default
        try:
            config = ConfiguracionSistema.objects.first()
            ciclo_actual = config.ciclo_actual if config else ''
        except:
            ciclo_actual = ''
        
        # Si no se especifica ciclo, usar el actual
        if not ciclo:
            ciclo = ciclo_actual
        
        # Construir query base
        gastos_query = Gasto.objects.filter(activo=True).prefetch_related('detalles__proveedor', 'detalles__clasificacion_gasto', 'presupuesto__centro_costo')
        
        # Aplicar filtros
        if ciclo:
            gastos_query = gastos_query.filter(ciclo=ciclo)
        
        if centro_costo_id:
            gastos_query = gastos_query.filter(presupuesto__centro_costo_id=centro_costo_id)
        
        # Si se especifica un presupuesto específico, filtrar por él
        if 'pk' in kwargs:
            presupuesto = get_object_or_404(Presupuesto, codigo=kwargs['pk'], activo=True)
            context['presupuesto'] = presupuesto
            gastos_query = gastos_query.filter(presupuesto=presupuesto)
        else:
            context['presupuesto'] = None
        
        # Agrupar gastos por clasificación
        gastos_por_clasificacion = {}
        total_gastado = 0
        
        for gasto in gastos_query:
            detalles_query = gasto.detalles.filter(activo=True)
            
            # Aplicar filtros de forma de pago y autorizó
            if forma_pago:
                detalles_query = detalles_query.filter(forma_pago=forma_pago)
            
            if autorizo_id:
                try:
                    autorizo_id_int = int(autorizo_id)
                    detalles_query = detalles_query.filter(autorizo_id=autorizo_id_int)
                except (ValueError, TypeError):
                    pass  # Ignorar si el ID no es válido
            
            for detalle in detalles_query:
                clasificacion = detalle.clasificacion_gasto
                if clasificacion.codigo not in gastos_por_clasificacion:
                    gastos_por_clasificacion[clasificacion.codigo] = {
                        'clasificacion': clasificacion,
                        'detalles': [],
                        'subtotal': 0
                    }
                
                detalle_info = {
                    'gasto': gasto,
                    'proveedor': detalle.proveedor,
                    'factura': detalle.factura,
                    'concepto': detalle.concepto,
                    'forma_pago': detalle.forma_pago,
                    'autorizo': detalle.autorizo,
                    'importe': detalle.importe,
                    'fecha_gasto': gasto.fecha_gasto,
                    'presupuesto': gasto.presupuesto,
                    'centro_costo': gasto.presupuesto.centro_costo
                }
                
                gastos_por_clasificacion[clasificacion.codigo]['detalles'].append(detalle_info)
                gastos_por_clasificacion[clasificacion.codigo]['subtotal'] += float(detalle.importe)
                total_gastado += float(detalle.importe)
        
        # Ordenar por descripción de clasificación
        gastos_ordenados = sorted(gastos_por_clasificacion.values(), key=lambda x: x['clasificacion'].descripcion)
        
        # Obtener datos para los filtros
        ciclos_disponibles = Gasto.objects.filter(activo=True).values_list('ciclo', flat=True).distinct().order_by('-ciclo')
        centros_costo = CentroCosto.objects.filter(activo=True).order_by('descripcion')
        personas_autorizan = AutorizoGasto.objects.filter(activo=True).order_by('nombre')
        
        context['gastos_por_clasificacion'] = gastos_ordenados
        context['total_gastado'] = total_gastado
        context['ciclo_actual'] = ciclo_actual
        context['ciclo'] = ciclo
        context['centro_costo_id'] = centro_costo_id
        context['forma_pago'] = forma_pago
        context['autorizo_id'] = autorizo_id
        context['ciclos_disponibles'] = ciclos_disponibles
        context['centros_costo'] = centros_costo
        context['personas_autorizan'] = personas_autorizan
        
        return context


# Vistas AJAX para Emisores

@login_required
def listar_emisores_ajax(request):
    """Vista AJAX para listar emisores"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todos los emisores activos
        emisores = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        emisores_data = []
        for emisor in emisores:
            emisores_data.append({
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'serie': emisor.serie,
                'archivo_certificado': emisor.archivo_certificado.name if emisor.archivo_certificado else None,
                'archivo_llave': emisor.archivo_llave.name if emisor.archivo_llave else None,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'emisores': emisores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def agregar_emisor_ajax(request):
    """Vista AJAX para agregar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Validar permisos de administrador
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
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
        
        # Validar campos requeridos
        if not razon_social:
            return JsonResponse({'error': 'La razón social es requerida'}, status=400)
        
        if not rfc:
            return JsonResponse({'error': 'El RFC es requerido'}, status=400)
        
        if not codigo_postal:
            return JsonResponse({'error': 'El código postal es requerido'}, status=400)
        
        if not password_llave:
            return JsonResponse({'error': 'La contraseña de la llave es requerida'}, status=400)
        
        # Validar archivos
        if 'archivo_certificado' not in request.FILES:
            return JsonResponse({'error': 'El archivo de certificado es requerido'}, status=400)
        
        if 'archivo_llave' not in request.FILES:
            return JsonResponse({'error': 'El archivo de llave es requerido'}, status=400)
        
        certificado_file = request.FILES.get('archivo_certificado')
        llave_file = request.FILES.get('archivo_llave')
        
        # Validar extensiones
        if not certificado_file.name.endswith('.cer'):
            return JsonResponse({'error': 'El archivo de certificado debe tener extensión .cer'}, status=400)
        
        if not llave_file.name.endswith('.key'):
            return JsonResponse({'error': 'El archivo de llave debe tener extensión .key'}, status=400)
        
        # Crear el emisor
        emisor = Emisor.objects.create(
            razon_social=razon_social,
            rfc=rfc,
            codigo_postal=codigo_postal,
            serie=serie,
            archivo_certificado=certificado_file,
            archivo_llave=llave_file,
            password_llave=password_llave,
            nombre_pac=nombre_pac,
            contrato=contrato,
            usuario_pac=usuario_pac,
            password_pac=password_pac,
            timbrado_prueba=timbrado_prueba,
            regimen_fiscal=regimen_fiscal,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor agregado exitosamente',
            'emisor': {
                'codigo': emisor.codigo,
                'razon_social': emisor.razon_social,
                'rfc': emisor.rfc,
                'codigo_postal': emisor.codigo_postal,
                'archivo_certificado': emisor.archivo_certificado.name,
                'archivo_llave': emisor.archivo_llave.name,
                'tiene_password': bool(emisor.password_llave),
                'nombre_pac': emisor.nombre_pac,
                'contrato': emisor.contrato,
                'usuario_pac': emisor.usuario_pac,
                'tiene_password_pac': bool(emisor.password_pac),
                'timbrado_prueba': emisor.timbrado_prueba,
                'regimen_fiscal': emisor.regimen_fiscal,
                'regimen_fiscal_display': emisor.get_regimen_fiscal_display(),
                'activo': emisor.activo,
                'fecha_creacion': emisor.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_emisor_ajax(request, codigo):
    """Vista AJAX para eliminar un emisor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Marcar como inactivo en lugar de eliminar
        emisor.activo = False
        emisor.usuario_modificacion = request.user
        emisor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Emisor eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def cancelar_gasto_ajax(request, gasto_id):
    """Vista AJAX para cancelar un gasto"""
    try:
        # Obtener el gasto
        gasto = get_object_or_404(Gasto, codigo=gasto_id, activo=True)
        
        # Marcar como inactivo
        gasto.activo = False
        gasto.usuario_modificacion = request.user
        gasto.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Gasto cancelado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# ===========================
# VISTAS PARA ALMACENES
# ===========================

@login_required
def almacenes_list(request):
    """Vista para listar almacenes"""
    
    # Validar permisos de administrador
    if not request.user.is_admin:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
    
    # Formulario de búsqueda
    search_form = AlmacenSearchForm(request.GET)
    
    # Query base
    almacenes = Almacen.objects.all()
    
    # Aplicar filtros
    if search_form.is_valid():
        busqueda = search_form.cleaned_data.get('busqueda')
        activo = search_form.cleaned_data.get('activo')
        
        if busqueda:
            almacenes = almacenes.filter(
                Q(descripcion__icontains=busqueda) |
                Q(codigo__icontains=busqueda)
            )
        
        if activo == '1':
            almacenes = almacenes.filter(activo=True)
        elif activo == '0':
            almacenes = almacenes.filter(activo=False)
    
    # Ordenar por descripción
    almacenes = almacenes.order_by('descripcion')
    
    # Paginación
    paginator = Paginator(almacenes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'title': 'Almacenes'
    }
    
    return render(request, 'core/almacen_list.html', context)


@login_required
def almacen_create(request):
    """Vista para crear almacén"""
    
    # Validar permisos de administrador
    if not request.user.is_admin:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
    
    if request.method == 'POST':
        form = AlmacenForm(request.POST)
        if form.is_valid():
            almacen = form.save()
            messages.success(request, f'Almacén "{almacen.descripcion}" creado correctamente.')
            return redirect('core:almacenes_list')
    else:
        form = AlmacenForm()
    
    context = {
        'form': form,
        'title': 'Crear Almacén',
        'action': 'Crear'
    }
    
    return render(request, 'core/almacen_form.html', context)


@login_required
def almacen_edit(request, codigo):
    """Vista para editar almacén"""
    
    # Validar permisos de administrador
    if not request.user.is_admin:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
    
    try:
        almacen = Almacen.objects.get(codigo=codigo)
    except Almacen.DoesNotExist:
        messages.error(request, 'El almacén no existe.')
        return redirect('almacenes_list')
    
    if request.method == 'POST':
        form = AlmacenForm(request.POST, instance=almacen)
        if form.is_valid():
            almacen = form.save()
            messages.success(request, f'Almacén "{almacen.descripcion}" actualizado correctamente.')
            return redirect('core:almacenes_list')
    else:
        form = AlmacenForm(instance=almacen)
    
    context = {
        'form': form,
        'almacen': almacen,
        'title': 'Editar Almacén',
        'action': 'Actualizar'
    }
    
    return render(request, 'core/almacen_form.html', context)


@login_required
def almacen_delete(request, codigo):
    """Vista para eliminar almacén"""
    
    # Validar permisos de administrador
    if not request.user.is_admin:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
    
    try:
        almacen = Almacen.objects.get(codigo=codigo)
    except Almacen.DoesNotExist:
        messages.error(request, 'El almacén no existe.')
        return redirect('almacenes_list')
    
    if request.method == 'POST':
        descripcion = almacen.descripcion
        almacen.delete()
        messages.success(request, f'Almacén "{descripcion}" eliminado correctamente.')
        return redirect('almacenes_list')
    
    context = {
        'almacen': almacen,
        'title': 'Eliminar Almacén'
    }
    
    return render(request, 'core/almacen_confirm_delete.html', context)


# ===========================
# VISTAS PARA COMPRAS
# ===========================

@login_required
def compras_list(request):
    """Vista para listar compras"""

    # Formulario de búsqueda
    search_form = CompraSearchForm(request.GET)

    # Query base
    compras = Compra.objects.select_related('proveedor').prefetch_related('pagos')

    # Aplicar filtros
    if search_form.is_valid():
        busqueda = search_form.cleaned_data.get('busqueda')
        proveedor = search_form.cleaned_data.get('proveedor')
        tipo = search_form.cleaned_data.get('tipo')
        estado = search_form.cleaned_data.get('estado')
        fecha_desde = search_form.cleaned_data.get('fecha_desde')
        fecha_hasta = search_form.cleaned_data.get('fecha_hasta')
        autorizo = search_form.cleaned_data.get('autorizo')

        if busqueda:
            compras = compras.filter(
                Q(folio__icontains=busqueda) |
                Q(proveedor__nombre__icontains=busqueda) |
                Q(factura__icontains=busqueda) |
                Q(serie__icontains=busqueda)
            )

        if proveedor:
            compras = compras.filter(proveedor=proveedor)

        if tipo:
            compras = compras.filter(tipo=tipo)

        if estado:
            compras = compras.filter(estado=estado)

        if fecha_desde:
            compras = compras.filter(fecha__gte=fecha_desde)

        if fecha_hasta:
            compras = compras.filter(fecha__lte=fecha_hasta)
        
        if autorizo:
            compras = compras.filter(autorizo=autorizo)

    # Ordenar por fecha y folio
    compras = compras.order_by('-fecha', '-folio')

    # Paginación
    paginator = Paginator(compras, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Obtener opciones para el modal de pago
    from core.models import AutorizoGasto
    autorizos_options = AutorizoGasto.objects.filter(activo=True).order_by('nombre')
    
    # Obtener proveedores únicos para el modal de imprimir pagos
    proveedores_unicos = Proveedor.objects.filter(
        activo=True,
        compra__isnull=False
    ).distinct().order_by('nombre')
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'autorizos_options': autorizos_options,
        'proveedores_unicos': proveedores_unicos,
        'title': 'Compras de Productos'
    }

    return render(request, 'core/compra_list.html', context)


@login_required
def compra_create(request):
    """Vista para crear compra"""

    if request.method == 'POST':
        print(f"=== REQUEST POST RECIBIDO ===")
        print(f"POST data recibido: {request.POST}")
        print(f"detalles_data: {request.POST.get('detalles_data', 'NO ENCONTRADO')}")
        print(f"CSRF token: {request.POST.get('csrfmiddlewaretoken', 'NO ENCONTRADO')}")
        
        form = CompraForm(request.POST)
        print(f"Formulario válido: {form.is_valid()}")
        if not form.is_valid():
            print(f"Errores del formulario: {form.errors}")
        
        if form.is_valid():
            try:
                compra = form.save()
                print(f"Compra creada con folio: {compra.folio}")
                
                # Procesar detalles si se enviaron
                if 'detalles_data' in request.POST:
                    print("Procesando detalles...")
                    procesar_detalles_compra(request, compra)
                    print("Detalles procesados")
                
                messages.success(request, f'Compra {compra.folio:06d} creada correctamente.')
                print(f"Redirigiendo a: /compras/")
                return redirect('core:compras_list')
                
            except Exception as e:
                print(f"Error al procesar la compra: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error al crear la compra: {str(e)}')
        else:
            print(f"Errores del formulario: {form.errors}")
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = CompraForm()

    # Obtener productos y almacenes para el template
    productos = ProductoServicio.objects.filter(activo=True).order_by('descripcion')
    almacenes = Almacen.objects.filter(activo=True).order_by('descripcion')

    context = {
        'form': form,
        'productos': productos,
        'almacenes': almacenes,
        'title': 'Crear Compra',
        'action': 'Crear'
    }

    return render(request, 'core/compra_form.html', context)


@login_required
def compra_edit(request, folio):
    """Vista para editar compra"""
    
    # Validar permisos de administrador
    if not request.user.is_admin:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permisos para realizar esta acción.")

    try:
        compra = Compra.objects.get(folio=folio)
    except Compra.DoesNotExist:
        messages.error(request, 'La compra no existe.')
        return redirect('core:compras_list')

    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        if form.is_valid():
            compra = form.save()
            
            # Procesar detalles si se enviaron
            if 'detalles' in request.POST:
                procesar_detalles_compra(request, compra)
            
            messages.success(request, f'Compra {compra.folio:06d} actualizada correctamente.')
            return redirect('core:compras_list')
    else:
        form = CompraForm(instance=compra)

    # Obtener detalles de la compra
    detalles = CompraDetalle.objects.filter(compra=compra).select_related('producto', 'almacen')
    
    # Obtener productos y almacenes para el template
    productos = ProductoServicio.objects.filter(activo=True).order_by('descripcion')
    almacenes = Almacen.objects.filter(activo=True).order_by('descripcion')

    context = {
        'form': form,
        'compra': compra,
        'detalles': detalles,
        'productos': productos,
        'almacenes': almacenes,
        'title': 'Editar Compra',
        'action': 'Actualizar'
    }

    return render(request, 'core/compra_form.html', context)


def procesar_detalles_compra(request, compra):
    """Procesar los detalles de la compra"""
    import json
    from decimal import Decimal
    
    try:
        detalles_json = request.POST.get('detalles_data', '[]')
        print(f"Detalles JSON recibido: {detalles_json}")
        
        detalles_data = json.loads(detalles_json)
        print(f"Detalles parseados: {detalles_data}")
        
        # Eliminar detalles existentes
        CompraDetalle.objects.filter(compra=compra).delete()
        
        # Crear nuevos detalles
        for detalle_data in detalles_data:
            if not detalle_data:
                continue
                
            # El JavaScript envía los datos con la estructura: {producto: {codigo: ...}, almacen: {codigo: ...}, ...}
            producto_obj = detalle_data.get('producto', {})
            almacen_obj = detalle_data.get('almacen', {})
            
            producto_codigo = producto_obj.get('codigo') if isinstance(producto_obj, dict) else producto_obj
            almacen_codigo = almacen_obj.get('codigo') if isinstance(almacen_obj, dict) else almacen_obj
            cantidad = detalle_data.get('cantidad')
            precio = detalle_data.get('precio')
            
            print(f"Procesando detalle: producto_codigo={producto_codigo}, almacen_codigo={almacen_codigo}, cantidad={cantidad}, precio={precio}")
            
            if producto_codigo and almacen_codigo and cantidad and precio:
                try:
                    producto = ProductoServicio.objects.get(codigo=producto_codigo)
                    almacen = Almacen.objects.get(codigo=almacen_codigo)
                    
                    detalle = CompraDetalle.objects.create(
                        compra=compra,
                        producto=producto,
                        almacen=almacen,
                        cantidad=Decimal(str(cantidad)),
                        precio=Decimal(str(precio))
                    )
                    
                    print(f"Detalle creado exitosamente: {detalle}")
                    
                    # El movimiento de kardex se crea automáticamente en el método save() del modelo CompraDetalle
                    
                except (ProductoServicio.DoesNotExist, Almacen.DoesNotExist, ValueError, TypeError) as e:
                    print(f"Error procesando detalle: {e}")
                    print(f"Datos del detalle: {detalle_data}")
                    continue
            else:
                print(f"Datos incompletos en detalle: {detalle_data}")
                
    except json.JSONDecodeError as e:
        print(f"Error decodificando JSON: {e}")
        print(f"JSON recibido: {detalles_json}")
    except Exception as e:
        print(f"Error general procesando detalles: {e}")
        import traceback
        traceback.print_exc()


def crear_movimiento_kardex(compra, detalle):
    """Crear movimiento en kardex para el detalle de compra"""
    from django.utils import timezone
    from decimal import Decimal
    
    try:
        # Obtener la existencia anterior
        ultimo_movimiento = Kardex.objects.filter(
            producto=detalle.producto,
            almacen=detalle.almacen
        ).order_by('-fecha', '-id').first()
        
        existencia_anterior = ultimo_movimiento.existencia_actual if ultimo_movimiento else Decimal('0')
        existencia_actual = existencia_anterior + detalle.cantidad
        
        # Calcular costo promedio anterior
        costo_promedio_anterior = ultimo_movimiento.costo_promedio_actual if ultimo_movimiento else Decimal('0')
        
        # Calcular costo total
        costo_total = detalle.cantidad * detalle.precio
        
        # Calcular costo promedio actual (método de costo promedio)
        if existencia_anterior > 0:
            costo_total_anterior = existencia_anterior * costo_promedio_anterior
            costo_total_actual = costo_total_anterior + costo_total
            costo_promedio_actual = costo_total_actual / existencia_actual
        else:
            costo_promedio_actual = detalle.precio
        
        # Crear el movimiento con todos los campos calculados manualmente
        kardex = Kardex.objects.create(
            producto=detalle.producto,
            almacen=detalle.almacen,
            fecha=timezone.now(),
            tipo_movimiento='entrada',
            cantidad=detalle.cantidad,
            precio_unitario=detalle.precio,
            costo_total=costo_total,
            existencia_anterior=existencia_anterior,
            existencia_actual=existencia_actual,
            costo_promedio_anterior=costo_promedio_anterior,
            costo_promedio_actual=costo_promedio_actual,
            referencia=f"Compra {compra.folio:06d}"
        )
        
        print(f"Movimiento kardex creado exitosamente: {kardex}")
        
    except Exception as e:
        print(f"Error al crear movimiento kardex: {e}")
        import traceback
        traceback.print_exc()
        # No re-lanzar la excepción para que no interrumpa el proceso de compra
        # El movimiento de kardex es importante pero no crítico para la compra


@login_required
def compra_delete(request, folio):
    """Vista para eliminar compra"""
    
    # Validar permisos de administrador
    if not request.user.is_admin:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permisos para realizar esta acción.")

    try:
        compra = Compra.objects.get(folio=folio)
    except Compra.DoesNotExist:
        messages.error(request, 'La compra no existe.')
        return redirect('core:compras_list')

    if request.method == 'POST':
        folio_num = compra.folio
        compra.delete()
        messages.success(request, f'Compra {folio_num:06d} eliminada correctamente.')
        return redirect('core:compras_list')

    context = {
        'compra': compra,
        'title': 'Eliminar Compra'
    }

    return render(request, 'core/compra_confirm_delete.html', context)


@login_required
def compra_detail(request, folio):
    """Vista para ver detalle de compra"""

    try:
        compra = Compra.objects.get(folio=folio)
    except Compra.DoesNotExist:
        messages.error(request, 'La compra no existe.')
        return redirect('core:compras_list')

    # Obtener detalles de la compra
    detalles = CompraDetalle.objects.filter(compra=compra).select_related('producto', 'almacen')

    context = {
        'compra': compra,
        'detalles': detalles,
        'title': f'Detalle de Compra {compra.folio:06d}'
    }

    return render(request, 'core/compra_detail.html', context)


# ===========================
# VISTAS PARA KARDEX
# ===========================

@login_required
def kardex_list(request):
    """Vista para listar kardex"""

    # Formulario de búsqueda
    search_form = KardexSearchForm(request.GET)

    # Query base
    kardex = Kardex.objects.select_related('producto', 'almacen').all()

    # Aplicar filtros
    if search_form.is_valid():
        producto = search_form.cleaned_data.get('producto')
        almacen = search_form.cleaned_data.get('almacen')
        tipo_movimiento = search_form.cleaned_data.get('tipo_movimiento')
        fecha_desde = search_form.cleaned_data.get('fecha_desde')
        fecha_hasta = search_form.cleaned_data.get('fecha_hasta')

        if producto:
            kardex = kardex.filter(producto=producto)

        if almacen:
            kardex = kardex.filter(almacen=almacen)

        if tipo_movimiento:
            kardex = kardex.filter(tipo_movimiento=tipo_movimiento)

        if fecha_desde:
            kardex = kardex.filter(fecha__date__gte=fecha_desde)

        if fecha_hasta:
            kardex = kardex.filter(fecha__date__lte=fecha_hasta)

    # Ordenar por fecha y producto
    kardex = kardex.order_by('-fecha', 'producto__descripcion')

    # Paginación
    paginator = Paginator(kardex, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'title': 'Control de Existencias y Costos (Kardex)'
    }

    return render(request, 'core/kardex_list.html', context)


@login_required
def existencias_list(request):
    """Vista para mostrar existencias actuales agrupadas por almacén con botón de Kardex"""

    # Obtener parámetros de filtro
    producto_filtro = request.GET.get('producto', '')
    almacen_filtro = request.GET.get('almacen', '')
    mostrar_vacios = request.GET.get('mostrar_vacios', False)
    
    
    # Obtener las existencias actuales agrupadas por almacén
    existencias_por_almacen = {}
    
    # Obtener todos los almacenes activos
    almacenes = Almacen.objects.filter(activo=True).order_by('descripcion')
    
    # Aplicar filtro de almacén si se especifica
    if almacen_filtro:
        almacenes = almacenes.filter(codigo=almacen_filtro)
    
    for almacen in almacenes:
        # Si hay filtro de producto, buscar en todos los productos, sino solo en los que tienen movimientos
        if producto_filtro:
            # Buscar productos que coincidan con el filtro
            productos_filtrados = ProductoServicio.objects.filter(
                activo=True
            ).filter(
                Q(descripcion__icontains=producto_filtro) | Q(sku__icontains=producto_filtro)
            )
            productos_con_movimientos = productos_filtrados.values_list('codigo', flat=True)
        else:
            # Obtener todos los productos únicos que tienen movimientos en este almacén
            productos_con_movimientos = Kardex.objects.filter(
                almacen=almacen
            ).values_list('producto', flat=True).distinct()
        
        # Obtener información de existencias para cada producto en este almacén
        productos_existencias = []
        
        for producto_id in productos_con_movimientos:
            try:
                producto = ProductoServicio.objects.get(codigo=producto_id)
                
                # El filtro de producto ya se aplicó a nivel de base de datos
                
                # Obtener el último movimiento para este producto/almacén
                ultimo_movimiento = Kardex.objects.filter(
                    producto=producto,
                    almacen=almacen
                ).order_by('-fecha', '-id').first()
                
                # Mostrar productos según el filtro de mostrar_vacios
                if mostrar_vacios or (ultimo_movimiento and ultimo_movimiento.existencia_actual > 0):
                    # Verificar si el producto ya está en la lista
                    producto_ya_existe = any(
                        p['producto'].codigo == producto.codigo 
                        for p in productos_existencias
                    )
                    
                    if not producto_ya_existe:
                        # Manejar productos sin movimientos o con existencia 0
                        if ultimo_movimiento:
                            existencia_actual = ultimo_movimiento.existencia_actual
                            costo_promedio = ultimo_movimiento.costo_promedio_actual
                            valor_inventario = existencia_actual * costo_promedio
                            ultimo_movimiento_fecha = ultimo_movimiento.fecha
                        else:
                            existencia_actual = 0
                            costo_promedio = 0
                            valor_inventario = 0
                            ultimo_movimiento_fecha = None
                        
                        productos_existencias.append({
                            'producto': producto,
                            'existencia_actual': existencia_actual,
                            'costo_promedio': costo_promedio,
                            'valor_inventario': valor_inventario,
                            'ultimo_movimiento': ultimo_movimiento_fecha
                        })
            except ProductoServicio.DoesNotExist:
                continue
        
        # Ordenar productos por descripción
        productos_existencias.sort(key=lambda x: x['producto'].descripcion)
        
        # Agregar almacenes según el filtro de mostrar_vacios
        if productos_existencias or mostrar_vacios:
            # Calcular valor total del almacén
            valor_total_almacen = sum(p['valor_inventario'] for p in productos_existencias)
            existencias_por_almacen[almacen] = {
                'productos': productos_existencias,
                'valor_total': valor_total_almacen
            }

    # Calcular estadísticas generales
    # Contar productos únicos (no duplicados entre almacenes)
    productos_unicos = set()
    for almacen_data in existencias_por_almacen.values():
        for producto_info in almacen_data['productos']:
            productos_unicos.add(producto_info['producto'].codigo)
    
    total_productos = len(productos_unicos)
    total_almacenes = len(existencias_por_almacen)
    valor_total_inventario = sum(almacen_data['valor_total'] for almacen_data in existencias_por_almacen.values())
    
    # Obtener opciones para los filtros
    productos_options = ProductoServicio.objects.filter(activo=True).order_by('descripcion')
    almacenes_options = Almacen.objects.filter(activo=True).order_by('descripcion')
    
    context = {
        'existencias_por_almacen': existencias_por_almacen,
        'total_productos': total_productos,
        'total_almacenes': total_almacenes,
        'valor_total_inventario': valor_total_inventario,
        'productos_options': productos_options,
        'almacenes_options': almacenes_options,
        'producto_filtro': producto_filtro,
        'almacen_filtro': almacen_filtro,
        'mostrar_vacios': mostrar_vacios,
        'title': 'Control de Existencias y Costos'
    }

    return render(request, 'core/existencias_list.html', context)


@login_required
def existencias_imprimir(request):
    """Vista para imprimir reporte de existencias con formato profesional"""
    
    # Obtener parámetros de filtro
    producto_filtro = request.GET.get('producto', '')
    almacen_filtro = request.GET.get('almacen', '')
    mostrar_vacios = request.GET.get('mostrar_vacios', False)
    
    # Obtener las existencias actuales agrupadas por almacén
    existencias_por_almacen = {}
    
    # Obtener todos los almacenes activos
    almacenes = Almacen.objects.filter(activo=True).order_by('descripcion')
    
    # Aplicar filtro de almacén si se especifica
    if almacen_filtro:
        almacenes = almacenes.filter(codigo=almacen_filtro)
    
    for almacen in almacenes:
        # Si hay filtro de producto, buscar en todos los productos, sino solo en los que tienen movimientos
        if producto_filtro:
            # Buscar productos que coincidan con el filtro
            productos_filtrados = ProductoServicio.objects.filter(
                activo=True
            ).filter(
                Q(descripcion__icontains=producto_filtro) | Q(sku__icontains=producto_filtro)
            )
            productos_con_movimientos = productos_filtrados.values_list('codigo', flat=True)
        else:
            # Obtener todos los productos únicos que tienen movimientos en este almacén
            productos_con_movimientos = Kardex.objects.filter(
                almacen=almacen
            ).values_list('producto', flat=True).distinct()
        
        # Obtener información de existencias para cada producto en este almacén
        productos_existencias = []
        
        for producto_id in productos_con_movimientos:
            try:
                producto = ProductoServicio.objects.get(codigo=producto_id)
                
                # El filtro de producto ya se aplicó a nivel de base de datos
                
                # Obtener el último movimiento para este producto/almacén
                ultimo_movimiento = Kardex.objects.filter(
                    producto=producto,
                    almacen=almacen
                ).order_by('-fecha', '-id').first()
                
                # Mostrar productos según el filtro de mostrar_vacios
                if mostrar_vacios or (ultimo_movimiento and ultimo_movimiento.existencia_actual > 0):
                    # Verificar si el producto ya está en la lista
                    producto_ya_existe = any(
                        p['producto'].codigo == producto.codigo 
                        for p in productos_existencias
                    )
                    
                    if not producto_ya_existe:
                        # Manejar productos sin movimientos o con existencia 0
                        if ultimo_movimiento:
                            existencia_actual = ultimo_movimiento.existencia_actual
                            costo_promedio = ultimo_movimiento.costo_promedio_actual
                            valor_inventario = existencia_actual * costo_promedio
                            ultimo_movimiento_fecha = ultimo_movimiento.fecha
                        else:
                            existencia_actual = 0
                            costo_promedio = 0
                            valor_inventario = 0
                            ultimo_movimiento_fecha = None
                        
                        productos_existencias.append({
                            'producto': producto,
                            'existencia_actual': existencia_actual,
                            'costo_promedio': costo_promedio,
                            'valor_inventario': valor_inventario,
                            'ultimo_movimiento': ultimo_movimiento_fecha
                        })
            except ProductoServicio.DoesNotExist:
                continue
        
        # Ordenar productos por descripción
        productos_existencias.sort(key=lambda x: x['producto'].descripcion)
        
        # Agregar almacenes según el filtro de mostrar_vacios
        if productos_existencias or mostrar_vacios:
            # Calcular valor total del almacén
            valor_total_almacen = sum(p['valor_inventario'] for p in productos_existencias)
            existencias_por_almacen[almacen] = {
                'productos': productos_existencias,
                'valor_total': valor_total_almacen
            }

    # Calcular estadísticas generales
    # Contar productos únicos (no duplicados entre almacenes)
    productos_unicos = set()
    for almacen_data in existencias_por_almacen.values():
        for producto_info in almacen_data['productos']:
            productos_unicos.add(producto_info['producto'].codigo)
    
    total_productos = len(productos_unicos)
    total_almacenes = len(existencias_por_almacen)
    valor_total_inventario = sum(almacen_data['valor_total'] for almacen_data in existencias_por_almacen.values())
    
    # Obtener datos de configuración de la empresa
    configuracion = ConfiguracionSistema.objects.first()
    
    context = {
        'existencias_por_almacen': existencias_por_almacen,
        'total_productos': total_productos,
        'total_almacenes': total_almacenes,
        'valor_total_inventario': valor_total_inventario,
        'producto_filtro': producto_filtro,
        'almacen_filtro': almacen_filtro,
        'mostrar_vacios': mostrar_vacios,
        'configuracion': configuracion,
        'title': 'Reporte de Existencias y Costos'
    }

    return render(request, 'core/existencias_imprimir.html', context)


@login_required
def cuentas_por_pagar_list(request):
    """Vista para listar compras a crédito pendientes de pago"""
    from django.db.models import Sum, Q
    
    # Obtener compras a crédito con saldo pendiente
    compras_credito = Compra.objects.filter(
        tipo='credito',
        estado='activa'
    ).select_related('proveedor').prefetch_related('pagos')
    
    # Filtrar por proveedor si se especifica
    proveedor_filtro = request.GET.get('proveedor', '')
    if proveedor_filtro:
        compras_credito = compras_credito.filter(
            Q(proveedor__nombre__icontains=proveedor_filtro) |
            Q(proveedor__rfc__icontains=proveedor_filtro)
        )
    
    # Filtrar por estado de pago
    estado_pago = request.GET.get('estado_pago', '')
    if estado_pago == 'pendientes':
        compras_credito = compras_credito.filter(
            ~Q(pagos__isnull=False) | Q(pagos__monto__lt=models.F('total'))
        )
    elif estado_pago == 'parciales':
        compras_credito = compras_credito.annotate(
            total_pagado=Sum('pagos__monto')
        ).filter(
            total_pagado__gt=0,
            total_pagado__lt=models.F('total')
        )
    elif estado_pago == 'pagadas':
        compras_credito = compras_credito.annotate(
            total_pagado=Sum('pagos__monto')
        ).filter(total_pagado__gte=models.F('total'))
    
    # Ordenar por fecha de compra
    compras_credito = compras_credito.order_by('fecha', 'folio')
    
    # Calcular estadísticas
    total_compras = compras_credito.count()
    total_deuda = sum(compra.saldo_pendiente for compra in compras_credito)
    
    # Obtener proveedores para el filtro
    proveedores_options = Proveedor.objects.filter(activo=True).order_by('nombre')
    
    # Obtener opciones para el modal de pago
    from core.models import AutorizoGasto
    autorizos_options = AutorizoGasto.objects.filter(activo=True).order_by('nombre')
    
    # Formas de pago del SAT
    formas_pago = [
        ('01', 'Efectivo'),
        ('02', 'Cheque nominativo'),
        ('03', 'Transferencia electrónica de fondos'),
        ('04', 'Tarjeta de crédito'),
        ('05', 'Monedero electrónico'),
        ('06', 'Dinero electrónico'),
        ('08', 'Vales de despensa'),
        ('12', 'Dación en pago'),
        ('13', 'Pago por subrogación'),
        ('14', 'Pago por consignación'),
        ('15', 'Condonación'),
        ('17', 'Compensación'),
        ('23', 'Novación'),
        ('24', 'Confusión'),
        ('25', 'Remisión de deuda'),
        ('26', 'Prescripción o caducidad'),
        ('27', 'A satisfacción del acreedor'),
        ('28', 'Tarjeta de débito'),
        ('29', 'Tarjeta de servicios'),
        ('30', 'Aplicación de anticipos'),
        ('31', 'Intermediario pagos'),
        ('99', 'Por definir'),
    ]
    
    context = {
        'compras_credito': compras_credito,
        'total_compras': total_compras,
        'total_deuda': total_deuda,
        'proveedores_options': proveedores_options,
        'autorizos_options': autorizos_options,
        'formas_pago': formas_pago,
        'proveedor_filtro': proveedor_filtro,
        'estado_pago': estado_pago,
        'title': 'Cuentas por Pagar'
    }
    
    return render(request, 'core/cuentas_por_pagar_list.html', context)


@login_required
def pagos_imprimir(request):
    """Vista para imprimir reporte de pagos realizados por factura"""
    from django.db.models import Sum
    
    # Obtener parámetros de filtro
    compra_id = request.GET.get('compra_id', '')
    proveedor_filtro = request.GET.get('proveedor', '')
    autorizo_filtro = request.GET.get('autorizo', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    # Query base - obtener todos los pagos
    pagos = PagoCompra.objects.select_related('compra', 'compra__proveedor', 'autorizo').order_by('-fecha_pago')
    
    # Aplicar filtros
    if compra_id:
        pagos = pagos.filter(compra__folio=compra_id)
    
    if proveedor_filtro:
        pagos = pagos.filter(compra__proveedor__nombre__icontains=proveedor_filtro)
    
    if autorizo_filtro:
        pagos = pagos.filter(autorizo__nombre__icontains=autorizo_filtro)
    
    if fecha_desde:
        pagos = pagos.filter(fecha_pago__gte=fecha_desde)
    
    if fecha_hasta:
        pagos = pagos.filter(fecha_pago__lte=fecha_hasta)
    
    # Agrupar pagos por compra
    compras_con_pagos = {}
    for pago in pagos:
        compra = pago.compra
        if compra.folio not in compras_con_pagos:
            compras_con_pagos[compra.folio] = {
                'compra': compra,
                'pagos': [],
                'total_pagado': 0
            }
        compras_con_pagos[compra.folio]['pagos'].append(pago)
        compras_con_pagos[compra.folio]['total_pagado'] += pago.monto
    
    # Calcular totales generales
    total_pagos = sum(pago.monto for pago in pagos)
    total_compras = len(compras_con_pagos)
    
    # Obtener configuración del sistema
    try:
        configuracion = ConfiguracionSistema.objects.first()
    except:
        configuracion = None
    
    # Obtener proveedores para filtros
    proveedores_options = Proveedor.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'compras_con_pagos': compras_con_pagos,
        'total_pagos': total_pagos,
        'total_compras': total_compras,
        'configuracion': configuracion,
        'proveedores_options': proveedores_options,
        'filtros_aplicados': {
            'compra_id': compra_id,
            'proveedor': proveedor_filtro,
            'autorizo': autorizo_filtro,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
    }
    
    return render(request, 'core/pagos_imprimir.html', context)


@login_required
def registrar_pago_ajax(request):
    """Vista AJAX para registrar pagos de compras a crédito"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        compra_id = request.POST.get('compra_id')
        fecha_pago = request.POST.get('fecha_pago')
        monto = request.POST.get('monto')
        forma_pago = request.POST.get('forma_pago', '01')
        autorizo_id = request.POST.get('autorizo')
        observaciones = request.POST.get('observaciones', '')
        
        # Validar datos requeridos
        if not all([compra_id, fecha_pago, monto]):
            return JsonResponse({
                'success': False,
                'error': 'Faltan datos requeridos'
            })
        
        # Obtener la compra
        compra = Compra.objects.get(pk=compra_id)
        
        # Validar que sea compra a crédito
        if compra.tipo != 'credito':
            return JsonResponse({
                'success': False,
                'error': 'Solo se pueden registrar pagos para compras a crédito'
            })
        
        # Validar monto
        monto_decimal = Decimal(monto)
        if monto_decimal <= 0:
            return JsonResponse({
                'success': False,
                'error': 'El monto debe ser mayor a 0'
            })
        
        if monto_decimal > compra.saldo_pendiente:
            return JsonResponse({
                'success': False,
                'error': f'El monto no puede ser mayor al saldo pendiente (${compra.saldo_pendiente})'
            })
        
        # Obtener el autorizó si se proporcionó
        autorizo = None
        if autorizo_id:
            try:
                from core.models import AutorizoGasto
                autorizo = AutorizoGasto.objects.get(pk=autorizo_id)
            except AutorizoGasto.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Autorizó no encontrado'
                })
        
        # Crear el pago
        pago = PagoCompra.objects.create(
            compra=compra,
            fecha_pago=fecha_pago,
            monto=monto_decimal,
            forma_pago=forma_pago,
            autorizo=autorizo,
            observaciones=observaciones
        )
        
        # Calcular nuevo saldo
        nuevo_saldo = compra.saldo_pendiente
        
        return JsonResponse({
            'success': True,
            'message': 'Pago registrado exitosamente',
            'pago_id': pago.id,
            'nuevo_saldo': float(nuevo_saldo),
            'esta_pagada': compra.esta_pagada
        })
        
    except Compra.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Compra no encontrada'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al registrar pago: {str(e)}'
        })


@login_required
def kardex_producto(request, producto_codigo, almacen_codigo):
    """Vista para mostrar el kardex de un producto específico en un almacén"""

    try:
        producto = ProductoServicio.objects.get(codigo=producto_codigo)
        almacen = Almacen.objects.get(codigo=almacen_codigo)
    except (ProductoServicio.DoesNotExist, Almacen.DoesNotExist):
        messages.error(request, 'Producto o almacén no encontrado.')
        return redirect('core:existencias_list')

    # Obtener todos los movimientos del producto en el almacén
    movimientos = Kardex.objects.filter(
        producto=producto,
        almacen=almacen
    ).order_by('-fecha', '-id')

    # Calcular estadísticas
    total_entradas = movimientos.filter(tipo_movimiento='entrada').aggregate(
        total=models.Sum('cantidad')
    )['total'] or 0
    
    total_salidas = movimientos.filter(tipo_movimiento='salida').aggregate(
        total=models.Sum('cantidad')
    )['total'] or 0
    
    # Obtener existencia actual (último movimiento)
    ultimo_movimiento = movimientos.first()
    existencia_actual = ultimo_movimiento.existencia_actual if ultimo_movimiento else 0
    costo_promedio_actual = ultimo_movimiento.costo_promedio_actual if ultimo_movimiento else 0

    # Paginación
    paginator = Paginator(movimientos, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'producto': producto,
        'almacen': almacen,
        'page_obj': page_obj,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
        'existencia_actual': existencia_actual,
        'costo_promedio_actual': costo_promedio_actual,
        'title': f'Kardex - {producto.descripcion} - {almacen.descripcion}'
    }

    return render(request, 'core/kardex_producto.html', context)


class EstadisticasPreliquidacionView(LoginRequiredMixin, ListView):
    """Vista para mostrar estadísticas de preliquidación"""
    model = Remision
    template_name = 'core/estadisticas_preliquidacion.html'
    context_object_name = 'remisiones'
    paginate_by = 20
    
    def get_queryset(self):
        # Obtener el ciclo actual de la configuración
        try:
            config = ConfiguracionSistema.objects.first()
            ciclo_actual = config.ciclo_actual if config else ''
        except:
            ciclo_actual = ''
        
        # Filtrar por ciclo actual si está configurado
        if ciclo_actual:
            queryset = Remision.objects.select_related(
                'cliente', 'lote_origen', 'transportista', 'usuario_creacion'
            ).filter(ciclo=ciclo_actual)
        else:
            queryset = Remision.objects.select_related(
                'cliente', 'lote_origen', 'transportista', 'usuario_creacion'
            ).all()
        
        # Obtener parámetros de búsqueda
        form = RemisionSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            cliente = form.cleaned_data.get('cliente')
            lote_origen = form.cleaned_data.get('lote_origen')
            transportista = form.cleaned_data.get('transportista')
            fecha_desde = form.cleaned_data.get('fecha_desde')
            fecha_hasta = form.cleaned_data.get('fecha_hasta')
            
            # Filtrar por búsqueda
            if busqueda:
                queryset = queryset.filter(
                    Q(ciclo__icontains=busqueda) |
                    Q(folio__icontains=busqueda) |
                    Q(cliente__razon_social__icontains=busqueda) |
                    Q(observaciones__icontains=busqueda)
                )
            
            # Filtrar por cliente
            if cliente:
                queryset = queryset.filter(cliente=cliente)
            
            # Filtrar por lote origen
            if lote_origen:
                queryset = queryset.filter(lote_origen=lote_origen)
            
            # Filtrar por transportista
            if transportista:
                queryset = queryset.filter(transportista=transportista)
            
            # Filtrar por rango de fechas
            if fecha_desde:
                queryset = queryset.filter(fecha__gte=fecha_desde)
            
            if fecha_hasta:
                queryset = queryset.filter(fecha__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = RemisionSearchForm(self.request.GET)
        context['title'] = 'Estadísticas de Preliquidación'
        
        # Agregar ciclo actual al contexto
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        
        return context


class AnalisisKgsImprimirView(LoginRequiredMixin, TemplateView):
    """Vista para imprimir reporte de análisis de kgs enviados vs liquidados"""
    template_name = 'core/analisis_kgs_imprimir.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener datos de configuración de la empresa
        configuracion = ConfiguracionSistema.objects.first()
        context['configuracion'] = configuracion
        
        # Obtener ciclo actual
        ciclo_actual = configuracion.ciclo_actual if configuracion else ''
        context['ciclo_actual'] = ciclo_actual
        
        # Obtener parámetros de filtro si existen
        cliente_codigo = self.request.GET.get('cliente_codigo')
        lote_origen_codigo = self.request.GET.get('lote_origen_codigo')
        calidad = self.request.GET.get('calidad')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        cliente_filtrado = None
        lote_origen_filtrado = None
        
        if cliente_codigo:
            try:
                cliente_filtrado = Cliente.objects.get(codigo=cliente_codigo)
                context['cliente_filtrado'] = cliente_filtrado
            except Cliente.DoesNotExist:
                pass
        
        if lote_origen_codigo:
            try:
                lote_origen_filtrado = LoteOrigen.objects.get(codigo=lote_origen_codigo)
                context['lote_origen_filtrado'] = lote_origen_filtrado
            except LoteOrigen.DoesNotExist:
                pass
        
        if calidad:
            context['calidad_filtrada'] = calidad
        
        if fecha_desde:
            context['fecha_desde'] = fecha_desde
        
        if fecha_hasta:
            context['fecha_hasta'] = fecha_hasta
        
        # Obtener datos del mismo modo que en el dashboard
        from collections import defaultdict
        
        # Filtrar detalles de remisiones no canceladas del ciclo actual
        # Primero obtener las remisiones del ciclo actual que no estén canceladas
        remisiones_qs = Remision.objects.filter(
            cancelada=False,
            ciclo=ciclo_actual
        ).select_related('cliente').prefetch_related('detalles')
        
        # Aplicar filtro de fechas si se proporcionan
        if fecha_desde:
            remisiones_qs = remisiones_qs.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            remisiones_qs = remisiones_qs.filter(fecha__lte=fecha_hasta)
        
        # Si se especifica un cliente, filtrar por ese cliente
        if cliente_filtrado:
            remisiones_qs = remisiones_qs.filter(cliente=cliente_filtrado)
        
        # Si se especifica un lote-origen, filtrar por ese lote-origen
        if lote_origen_filtrado:
            remisiones_qs = remisiones_qs.filter(lote_origen=lote_origen_filtrado)
        
        # Datos para análisis de kgs enviados vs liquidados
        kgs_enviados_data = defaultdict(lambda: {
            'kgs_enviados': 0, 
            'kgs_liquidados': 0,
            'total_remisiones': 0,
            'remisiones': []
        })
        
        # Incluir todas las remisiones no canceladas (tanto preliquidadas como no preliquidadas)
        remisiones_no_canceladas = list(remisiones_qs)
        remision_ids = [r.pk for r in remisiones_no_canceladas]
        detalles_qs = RemisionDetalle.objects.filter(
            remision_id__in=remision_ids
        ).select_related('remision', 'cultivo')
        
        # Si se especifica una calidad, filtrar por esa calidad
        if calidad:
            detalles_qs = detalles_qs.filter(calidad=calidad)
        
        for detalle in detalles_qs:
            calidad = detalle.calidad
            kgs_enviados_data[calidad]['kgs_enviados'] += float(detalle.kgs_enviados or 0)
            kgs_enviados_data[calidad]['kgs_liquidados'] += float(detalle.kgs_liquidados or 0)
            kgs_enviados_data[calidad]['total_remisiones'] += 1
            
            # Agregar información de la remisión para el detalle
            kgs_enviados_data[calidad]['remisiones'].append({
                'remision': detalle.remision,
                'cliente': detalle.remision.cliente.razon_social,
                'fecha': detalle.remision.fecha,
                'kgs_enviados': float(detalle.kgs_enviados or 0),
                'kgs_liquidados': float(detalle.kgs_liquidados or 0),
                'diferencia': float(detalle.kgs_enviados or 0) - float(detalle.kgs_liquidados or 0)
            })
        
        # Convertir a lista para el template
        grafica_kgs_enviados_data = []
        for calidad, datos in kgs_enviados_data.items():
            diferencia = round(datos['kgs_enviados'] - datos['kgs_liquidados'], 2)
            grafica_kgs_enviados_data.append({
                'calidad': calidad,
                'kgs_enviados': round(datos['kgs_enviados'], 2),
                'kgs_liquidados': round(datos['kgs_liquidados'], 2),
                'diferencia': diferencia,
                'total_remisiones': datos['total_remisiones'],
                'remisiones': datos['remisiones']
            })
        
        # Ordenar por calidad
        grafica_kgs_enviados_data.sort(key=lambda x: x['calidad'])
        
        # Calcular totales generales
        total_kgs_enviados = sum(item['kgs_enviados'] for item in grafica_kgs_enviados_data)
        total_kgs_liquidados = sum(item['kgs_liquidados'] for item in grafica_kgs_enviados_data)
        total_diferencia = total_kgs_enviados - total_kgs_liquidados
        total_remisiones = sum(item['total_remisiones'] for item in grafica_kgs_enviados_data)
        
        context['grafica_kgs_enviados_data'] = grafica_kgs_enviados_data
        context['total_kgs_enviados'] = round(total_kgs_enviados, 2)
        context['total_kgs_liquidados'] = round(total_kgs_liquidados, 2)
        context['total_diferencia'] = round(total_diferencia, 2)
        context['total_remisiones'] = total_remisiones
        
        return context


class AnalisisCalidadImprimirView(LoginRequiredMixin, TemplateView):
    """Vista para imprimir reporte de análisis por calidad de producto"""
    template_name = 'core/analisis_calidad_imprimir.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener datos de configuración de la empresa
        configuracion = ConfiguracionSistema.objects.first()
        context['configuracion'] = configuracion
        
        # Obtener ciclo actual
        ciclo_actual = configuracion.ciclo_actual if configuracion else ''
        context['ciclo_actual'] = ciclo_actual
        
        # Obtener parámetros de filtro si existen
        cliente_codigo = self.request.GET.get('cliente_codigo')
        lote_origen_codigo = self.request.GET.get('lote_origen_codigo')
        calidad = self.request.GET.get('calidad')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        cliente_filtrado = None
        lote_origen_filtrado = None
        
        if cliente_codigo:
            try:
                cliente_filtrado = Cliente.objects.get(codigo=cliente_codigo)
                context['cliente_filtrado'] = cliente_filtrado
            except Cliente.DoesNotExist:
                pass
        
        if lote_origen_codigo:
            try:
                lote_origen_filtrado = LoteOrigen.objects.get(codigo=lote_origen_codigo)
                context['lote_origen_filtrado'] = lote_origen_filtrado
            except LoteOrigen.DoesNotExist:
                pass
        
        if calidad:
            context['calidad_filtrada'] = calidad
        
        if fecha_desde:
            context['fecha_desde'] = fecha_desde
        
        if fecha_hasta:
            context['fecha_hasta'] = fecha_hasta
        
        # Obtener datos del mismo modo que en el dashboard
        from collections import defaultdict
        
        # Filtrar detalles de remisiones no canceladas del ciclo actual
        # Primero obtener las remisiones del ciclo actual que no estén canceladas
        remisiones_qs = Remision.objects.filter(
            cancelada=False,
            ciclo=ciclo_actual
        ).select_related('cliente').prefetch_related('detalles')
        
        # Aplicar filtro de fechas si se proporcionan
        if fecha_desde:
            remisiones_qs = remisiones_qs.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            remisiones_qs = remisiones_qs.filter(fecha__lte=fecha_hasta)
        
        # Si se especifica un cliente, filtrar por ese cliente
        if cliente_filtrado:
            remisiones_qs = remisiones_qs.filter(cliente=cliente_filtrado)
        
        # Si se especifica un lote-origen, filtrar por ese lote-origen
        if lote_origen_filtrado:
            remisiones_qs = remisiones_qs.filter(lote_origen=lote_origen_filtrado)
        
        # Incluir todas las remisiones no canceladas (tanto preliquidadas como no preliquidadas)
        remisiones_no_canceladas = list(remisiones_qs)
        
        # Obtener los detalles de las remisiones no canceladas
        remision_ids = [r.pk for r in remisiones_no_canceladas]
        detalles_qs = RemisionDetalle.objects.filter(
            remision_id__in=remision_ids
        ).select_related('remision', 'cultivo')
        
        # Si se especifica una calidad, filtrar por esa calidad
        if calidad:
            detalles_qs = detalles_qs.filter(calidad=calidad)
        
        # Datos para análisis por calidad de producto
        calidad_data = defaultdict(lambda: {
            'kgs_netos_enviados': 0, 
            'kgs_liquidados': 0,
            'total_remisiones': 0,
            'remisiones': []
        })
        
        for detalle in detalles_qs:
            calidad = detalle.calidad
            calidad_data[calidad]['kgs_netos_enviados'] += float(detalle.kgs_neto_envio or 0)
            calidad_data[calidad]['kgs_liquidados'] += float(detalle.kgs_liquidados or 0)
            calidad_data[calidad]['total_remisiones'] += 1
            
            # Agregar información de la remisión para el detalle
            calidad_data[calidad]['remisiones'].append({
                'remision': detalle.remision,
                'cliente': detalle.remision.cliente.razon_social,
                'fecha': detalle.remision.fecha,
                'cultivo': detalle.cultivo.nombre,
                'kgs_netos_enviados': float(detalle.kgs_neto_envio or 0),
                'kgs_liquidados': float(detalle.kgs_liquidados or 0),
                'diferencia': float(detalle.kgs_neto_envio or 0) - float(detalle.kgs_liquidados or 0)
            })
        
        # Convertir a lista para el template
        grafica_calidad_data = []
        for calidad, datos in calidad_data.items():
            diferencia = round(datos['kgs_netos_enviados'] - datos['kgs_liquidados'], 2)
            grafica_calidad_data.append({
                'calidad': calidad,
                'kgs_netos_enviados': round(datos['kgs_netos_enviados'], 2),
                'kgs_liquidados': round(datos['kgs_liquidados'], 2),
                'diferencia': diferencia,
                'total_remisiones': datos['total_remisiones'],
                'remisiones': datos['remisiones']
            })
        
        # Ordenar por calidad
        grafica_calidad_data.sort(key=lambda x: x['calidad'])
        
        # Calcular totales generales
        total_kgs_netos_enviados = sum(item['kgs_netos_enviados'] for item in grafica_calidad_data)
        total_kgs_liquidados = sum(item['kgs_liquidados'] for item in grafica_calidad_data)
        total_diferencia = total_kgs_netos_enviados - total_kgs_liquidados
        total_remisiones = sum(item['total_remisiones'] for item in grafica_calidad_data)
        
        context['grafica_calidad_data'] = grafica_calidad_data
        context['total_kgs_netos_enviados'] = round(total_kgs_netos_enviados, 2)
        context['total_kgs_liquidados'] = round(total_kgs_liquidados, 2)
        context['total_diferencia'] = round(total_diferencia, 2)
        context['total_remisiones'] = total_remisiones
        
        return context


class AnalisisMermaImprimirView(LoginRequiredMixin, TemplateView):
    """Vista para imprimir reporte de análisis de merma por calidad de producto"""
    template_name = 'core/analisis_merma_imprimir.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        configuracion = ConfiguracionSistema.objects.first()
        context['configuracion'] = configuracion
        ciclo_actual = configuracion.ciclo_actual if configuracion else ''
        context['ciclo_actual'] = ciclo_actual
        
        # Obtener parámetros de filtro si existen
        cliente_codigo = self.request.GET.get('cliente_codigo')
        lote_origen_codigo = self.request.GET.get('lote_origen_codigo')
        calidad = self.request.GET.get('calidad')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        cliente_filtrado = None
        lote_origen_filtrado = None
        
        if cliente_codigo:
            try:
                cliente_filtrado = Cliente.objects.get(codigo=cliente_codigo)
                context['cliente_filtrado'] = cliente_filtrado
            except Cliente.DoesNotExist:
                pass
        
        if lote_origen_codigo:
            try:
                lote_origen_filtrado = LoteOrigen.objects.get(codigo=lote_origen_codigo)
                context['lote_origen_filtrado'] = lote_origen_filtrado
            except LoteOrigen.DoesNotExist:
                pass
        
        if calidad:
            context['calidad_filtrada'] = calidad
        
        if fecha_desde:
            context['fecha_desde'] = fecha_desde
        
        if fecha_hasta:
            context['fecha_hasta'] = fecha_hasta
        
        from collections import defaultdict
        
        # Obtener remisiones del ciclo actual
        remisiones_qs = Remision.objects.filter(
            cancelada=False,
            ciclo=ciclo_actual
        ).select_related('cliente').prefetch_related('detalles')
        
        # Aplicar filtro de fechas si se proporcionan
        if fecha_desde:
            remisiones_qs = remisiones_qs.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            remisiones_qs = remisiones_qs.filter(fecha__lte=fecha_hasta)
        
        # Si se especifica un cliente, filtrar por ese cliente
        if cliente_filtrado:
            remisiones_qs = remisiones_qs.filter(cliente=cliente_filtrado)
        
        # Si se especifica un lote-origen, filtrar por ese lote-origen
        if lote_origen_filtrado:
            remisiones_qs = remisiones_qs.filter(lote_origen=lote_origen_filtrado)
        
        # Incluir todas las remisiones no canceladas (tanto preliquidadas como no preliquidadas)
        remisiones_no_canceladas = list(remisiones_qs)
        
        # Obtener IDs de remisiones no canceladas
        remision_ids = [r.pk for r in remisiones_no_canceladas]
        
        # Obtener detalles de remisiones no canceladas
        detalles_qs = RemisionDetalle.objects.filter(
            remision_id__in=remision_ids
        ).select_related('remision', 'cultivo')
        
        # Si se especifica una calidad, filtrar por esa calidad
        if calidad:
            detalles_qs = detalles_qs.filter(calidad=calidad)
        
        # Agrupar datos por calidad
        merma_data = defaultdict(lambda: {
            'kgs_merma_enviada': 0, 
            'kgs_merma_liquidada': 0,
            'total_remisiones': 0,
            'total_no_arps': 0,
            'total_no_arps_liquidados': 0,
            'sum_merma_arps': 0,
            'count_detalles': 0,
            'remisiones': []
        })
        
        for detalle in detalles_qs:
            calidad = detalle.calidad
            merma_data[calidad]['kgs_merma_enviada'] += float(detalle.kgs_merma or 0)
            merma_data[calidad]['kgs_merma_liquidada'] += float(detalle.kgs_merma_liquidados or 0)
            merma_data[calidad]['total_remisiones'] += 1
            merma_data[calidad]['total_no_arps'] += float(detalle.no_arps or 0)
            merma_data[calidad]['total_no_arps_liquidados'] += float(detalle.no_arps_liquidados or 0)
            merma_data[calidad]['sum_merma_arps'] += float(detalle.merma_arps or 0)
            merma_data[calidad]['count_detalles'] += 1
            
            # Agregar información de la remisión para el detalle
            merma_data[calidad]['remisiones'].append({
                'remision': detalle.remision,
                'cliente': detalle.remision.cliente.razon_social,
                'fecha': detalle.remision.fecha,
                'cultivo': detalle.cultivo.nombre,
                'kgs_merma_enviada': float(detalle.kgs_merma or 0),
                'kgs_merma_liquidada': float(detalle.kgs_merma_liquidados or 0),
                'diferencia_merma': float(detalle.kgs_merma or 0) - float(detalle.kgs_merma_liquidados or 0)
            })
        
        # Convertir a lista para el template
        grafica_merma_data = []
        for calidad, datos in merma_data.items():
            diferencia_merma = round(datos['kgs_merma_enviada'] - datos['kgs_merma_liquidada'], 2)
            # Calcular promedio de merma por arp enviado
            promedio_merma_arp_enviado = round(datos['sum_merma_arps'] / datos['count_detalles'], 2) if datos['count_detalles'] > 0 else 0
            # Calcular promedio de merma por arp liquidado
            promedio_merma_arp_liquidado = round(datos['kgs_merma_liquidada'] / datos['total_no_arps_liquidados'], 2) if datos['total_no_arps_liquidados'] > 0 else 0
            
            grafica_merma_data.append({
                'calidad': calidad,
                'kgs_merma_enviada': round(datos['kgs_merma_enviada'], 2),
                'kgs_merma_liquidada': round(datos['kgs_merma_liquidada'], 2),
                'diferencia_merma': diferencia_merma,
                'total_remisiones': datos['total_remisiones'],
                'promedio_merma_arp_enviado': promedio_merma_arp_enviado,
                'promedio_merma_arp_liquidado': promedio_merma_arp_liquidado,
                'remisiones': datos['remisiones']
            })
        
        # Ordenar por calidad
        grafica_merma_data.sort(key=lambda x: x['calidad'])
        
        # Calcular totales generales
        total_kgs_merma_enviada = sum(item['kgs_merma_enviada'] for item in grafica_merma_data)
        total_kgs_merma_liquidada = sum(item['kgs_merma_liquidada'] for item in grafica_merma_data)
        total_diferencia_merma = total_kgs_merma_enviada - total_kgs_merma_liquidada
        total_remisiones = sum(item['total_remisiones'] for item in grafica_merma_data)
        
        # Calcular promedios totales
        total_sum_merma_arps = sum(datos['sum_merma_arps'] for datos in merma_data.values())
        total_count_detalles = sum(datos['count_detalles'] for datos in merma_data.values())
        total_no_arps_liquidados = sum(datos['total_no_arps_liquidados'] for datos in merma_data.values())
        
        promedio_total_merma_arp_enviado = round(total_sum_merma_arps / total_count_detalles, 2) if total_count_detalles > 0 else 0
        promedio_total_merma_arp_liquidado = round(total_kgs_merma_liquidada / total_no_arps_liquidados, 2) if total_no_arps_liquidados > 0 else 0
        
        context['grafica_merma_data'] = grafica_merma_data
        context['total_kgs_merma_enviada'] = round(total_kgs_merma_enviada, 2)
        context['total_kgs_merma_liquidada'] = round(total_kgs_merma_liquidada, 2)
        context['total_diferencia_merma'] = round(total_diferencia_merma, 2)
        context['total_remisiones'] = total_remisiones
        context['promedio_total_merma_arp_enviado'] = promedio_total_merma_arp_enviado
        context['promedio_total_merma_arp_liquidado'] = promedio_total_merma_arp_liquidado
        
        return context


class RankingClientesImprimirView(LoginRequiredMixin, TemplateView):
    """Vista para imprimir reporte de ranking de clientes por importe liquidado"""
    template_name = 'core/ranking_clientes_imprimir.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        configuracion = ConfiguracionSistema.objects.first()
        context['configuracion'] = configuracion
        ciclo_actual = configuracion.ciclo_actual if configuracion else ''
        context['ciclo_actual'] = ciclo_actual
        
        from collections import defaultdict
        
        # Obtener parámetros de filtro
        cliente_codigo = self.request.GET.get('cliente_codigo', '').strip()
        lote_origen_codigo = self.request.GET.get('lote_origen_codigo', '').strip()
        calidad = self.request.GET.get('calidad', '').strip()
        fecha_desde = self.request.GET.get('fecha_desde', '').strip()
        fecha_hasta = self.request.GET.get('fecha_hasta', '').strip()
        
        # Obtener objetos de filtro si se proporcionan
        cliente_filtrado = None
        lote_origen_filtrado = None
        
        if cliente_codigo:
            try:
                cliente_filtrado = Cliente.objects.get(codigo=cliente_codigo)
                context['cliente_filtrado'] = cliente_filtrado
            except Cliente.DoesNotExist:
                pass
        
        if lote_origen_codigo:
            try:
                lote_origen_filtrado = LoteOrigen.objects.get(codigo=lote_origen_codigo)
                context['lote_origen_filtrado'] = lote_origen_filtrado
            except LoteOrigen.DoesNotExist:
                pass
        
        if calidad:
            context['calidad_filtrada'] = calidad
        
        if fecha_desde:
            context['fecha_desde'] = fecha_desde
        
        if fecha_hasta:
            context['fecha_hasta'] = fecha_hasta
        
        # Obtener remisiones del ciclo actual
        remisiones_qs = Remision.objects.filter(
            cancelada=False,
            ciclo=ciclo_actual
        ).select_related('cliente', 'lote_origen').prefetch_related('detalles')
        
        # Aplicar filtros de fecha si se proporcionan
        if fecha_desde:
            remisiones_qs = remisiones_qs.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            remisiones_qs = remisiones_qs.filter(fecha__lte=fecha_hasta)
        
        # Filtrar solo remisiones preliquidadas
        remisiones_preliquidadas = []
        for remision in remisiones_qs:
            if remision.esta_liquidada():
                # Aplicar filtros de cliente y lote-origen
                if cliente_filtrado and remision.cliente != cliente_filtrado:
                    continue
                if lote_origen_filtrado and remision.lote_origen != lote_origen_filtrado:
                    continue
                
                remisiones_preliquidadas.append(remision)
        
        # Agrupar remisiones preliquidadas por cliente y calcular totales
        clientes_data = defaultdict(lambda: {
            'importe_preliquidado': 0,
            'importe_liquidado': 0, 
            'total_pagos': 0,
            'total_remisiones': 0,
            'remisiones': []
        })
        
        # Obtener detalles filtrados por calidad si se especifica
        detalles_filtrados = {}
        if calidad:
            detalles_qs = RemisionDetalle.objects.filter(remision__in=[r.pk for r in remisiones_preliquidadas])
            detalles_qs = detalles_qs.filter(calidad=calidad)
            detalles_filtrados = {detalle.remision_id: detalle for detalle in detalles_qs}
        
        for remision in remisiones_preliquidadas:
            cliente_nombre = remision.cliente.razon_social
            
            # Si hay filtro de calidad, usar solo los detalles filtrados
            if calidad:
                if remision.pk in detalles_filtrados:
                    detalle = detalles_filtrados[remision.pk]
                    importe_preliquidado_remision = float(detalle.importe_envio or 0)
                    importe_liquidado_remision = float(detalle.importe_liquidado or 0)
                else:
                    # Si la remisión no tiene detalles con la calidad seleccionada, saltarla
                    continue
            else:
                # Sin filtro de calidad, usar todos los detalles de la remisión
                importe_preliquidado_remision = sum(float(detalle.importe_envio or 0) for detalle in remision.detalles.all())
                importe_liquidado_remision = sum(float(detalle.importe_liquidado or 0) for detalle in remision.detalles.all())
            
            # Sumar pagos realizados de la remisión
            total_pagos_remision = sum(float(pago.monto or 0) for pago in remision.pagos.filter(activo=True))
            
            clientes_data[cliente_nombre]['importe_preliquidado'] += importe_preliquidado_remision
            clientes_data[cliente_nombre]['importe_liquidado'] += importe_liquidado_remision
            clientes_data[cliente_nombre]['total_pagos'] += total_pagos_remision
            clientes_data[cliente_nombre]['total_remisiones'] += 1
            
            # Agregar información de la remisión para el detalle
            clientes_data[cliente_nombre]['remisiones'].append({
                'remision': remision,
                'fecha': remision.fecha,
                'importe_preliquidado': importe_preliquidado_remision,
                'importe_liquidado': importe_liquidado_remision,
                'total_pagos': total_pagos_remision,
                'total_detalles': remision.detalles.count()
            })
        
        # Convertir a lista y ordenar por importe liquidado (descendente)
        ranking_clientes_data = []
        for cliente_nombre, datos in clientes_data.items():
            # Saldo pendiente = Importe liquidado - Pagos realizados
            saldo_pendiente = datos['importe_liquidado'] - datos['total_pagos']
            ranking_clientes_data.append({
                'cliente_nombre': cliente_nombre,
                'importe_preliquidado': round(datos['importe_preliquidado'], 2),
                'importe_liquidado': round(datos['importe_liquidado'], 2),
                'total_pagos': round(datos['total_pagos'], 2),
                'saldo_pendiente': round(saldo_pendiente, 2),
                'total_remisiones': datos['total_remisiones'],
                'promedio_por_remision': round(datos['importe_liquidado'] / datos['total_remisiones'], 2) if datos['total_remisiones'] > 0 else 0,
                'remisiones': datos['remisiones']
            })
        
        # Ordenar por importe liquidado descendente (ranking)
        ranking_clientes_data.sort(key=lambda x: x['importe_liquidado'], reverse=True)
        
        # Calcular totales generales
        total_importe_preliquidado = sum(item['importe_preliquidado'] for item in ranking_clientes_data)
        total_importe_liquidado = sum(item['importe_liquidado'] for item in ranking_clientes_data)
        total_pagos = sum(item['total_pagos'] for item in ranking_clientes_data)
        total_saldo_pendiente = sum(item['saldo_pendiente'] for item in ranking_clientes_data)
        total_remisiones = sum(item['total_remisiones'] for item in ranking_clientes_data)
        total_clientes = len(ranking_clientes_data)
        promedio_por_cliente = round(total_importe_liquidado / total_clientes, 2) if total_clientes > 0 else 0
        
        context['ranking_clientes_data'] = ranking_clientes_data
        context['total_importe_preliquidado'] = round(total_importe_preliquidado, 2)
        context['total_importe_liquidado'] = round(total_importe_liquidado, 2)
        context['total_pagos'] = round(total_pagos, 2)
        context['total_saldo_pendiente'] = round(total_saldo_pendiente, 2)
        context['total_remisiones'] = total_remisiones
        context['total_clientes'] = total_clientes
        context['promedio_por_cliente'] = promedio_por_cliente
        
        return context


def actualizar_grafico_kgs_ajax(request):
    """Vista AJAX para actualizar el gráfico de kgs enviados vs liquidados con filtro de cliente"""
    from django.http import JsonResponse
    from collections import defaultdict
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Vista AJAX llamada con método: {request.method}")
    
    cliente_id = request.GET.get('cliente_id')
    lote_origen_id = request.GET.get('lote_origen_id')
    calidad = request.GET.get('calidad')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    logger.info(f"Cliente ID recibido: {cliente_id}")
    logger.info(f"Lote-Origen ID recibido: {lote_origen_id}")
    logger.info(f"Calidad recibida: {calidad}")
    logger.info(f"Fecha desde: {fecha_desde}")
    logger.info(f"Fecha hasta: {fecha_hasta}")
    
    # Obtener el ciclo actual
    try:
        config = ConfiguracionSistema.objects.first()
        ciclo_actual = config.ciclo_actual if config else ''
        logger.info(f"Ciclo actual: {ciclo_actual}")
    except Exception as e:
        logger.error(f"Error obteniendo configuración: {e}")
        ciclo_actual = ''
    
    # Filtrar remisiones del ciclo actual
    if ciclo_actual:
        remisiones_qs = Remision.objects.filter(ciclo=ciclo_actual)
    else:
        remisiones_qs = Remision.objects.all()
    
    # Aplicar filtro de fechas si se proporcionan
    if fecha_desde:
        remisiones_qs = remisiones_qs.filter(fecha__gte=fecha_desde)
        logger.info(f"Filtro fecha desde aplicado: {fecha_desde}")
    
    if fecha_hasta:
        remisiones_qs = remisiones_qs.filter(fecha__lte=fecha_hasta)
        logger.info(f"Filtro fecha hasta aplicado: {fecha_hasta}")
    
    logger.info(f"Total remisiones encontradas: {remisiones_qs.count()}")
    
    # Filtrar solo las remisiones no canceladas
    remisiones_no_canceladas = [r for r in remisiones_qs if not r.cancelada]
    logger.info(f"Remisiones no canceladas: {len(remisiones_no_canceladas)}")
    
    # Si se especifica un cliente, filtrar por ese cliente
    if cliente_id:
        remisiones_no_canceladas = [r for r in remisiones_no_canceladas if r.cliente.codigo == int(cliente_id)]
        logger.info(f"Remisiones filtradas por cliente {cliente_id}: {len(remisiones_no_canceladas)}")
    
    # Si se especifica un lote-origen, filtrar por ese lote-origen
    if lote_origen_id:
        remisiones_no_canceladas = [r for r in remisiones_no_canceladas if r.lote_origen.codigo == int(lote_origen_id)]
        logger.info(f"Remisiones filtradas por lote-origen {lote_origen_id}: {len(remisiones_no_canceladas)}")
    
    remisiones_no_canceladas_ids = [r.pk for r in remisiones_no_canceladas]
    
    # Obtener detalles de remisiones filtradas
    detalles_qs = RemisionDetalle.objects.filter(remision__in=remisiones_no_canceladas_ids)
    
    # Si se especifica una calidad, filtrar por esa calidad
    if calidad:
        detalles_qs = detalles_qs.filter(calidad=calidad)
        logger.info(f"Detalles filtrados por calidad {calidad}: {detalles_qs.count()}")
    
    logger.info(f"Detalles encontrados: {detalles_qs.count()}")
    
    # Agrupar por calidad y calcular totales
    kgs_enviados_data = defaultdict(lambda: {'kgs_enviados': 0, 'kgs_liquidados': 0})
    
    for detalle in detalles_qs:
        calidad = detalle.calidad
        kgs_enviados_data[calidad]['kgs_enviados'] += float(detalle.kgs_enviados or 0)
        kgs_enviados_data[calidad]['kgs_liquidados'] += float(detalle.kgs_liquidados or 0)
    
    # Convertir a lista para el template
    grafica_kgs_enviados_data = []
    for calidad, datos in kgs_enviados_data.items():
        diferencia = round(datos['kgs_enviados'] - datos['kgs_liquidados'], 2)
        grafica_kgs_enviados_data.append({
            'calidad': calidad,
            'kgs_enviados': round(datos['kgs_enviados'], 2),
            'kgs_liquidados': round(datos['kgs_liquidados'], 2),
            'diferencia': diferencia
        })
    
    # Ordenar por calidad
    grafica_kgs_enviados_data.sort(key=lambda x: x['calidad'])
    
    logger.info(f"Datos finales: {grafica_kgs_enviados_data}")
    
    return JsonResponse({
        'success': True,
        'data': grafica_kgs_enviados_data
    })

# @login_required # Temporarily removed for debugging
def actualizar_grafico_calidad_ajax(request):
    """Vista AJAX para actualizar el gráfico de calidad de producto con filtros"""
    from django.http import JsonResponse
    from collections import defaultdict
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Vista AJAX calidad llamada con método: {request.method}")
    
    cliente_id = request.GET.get('cliente_id')
    lote_origen_id = request.GET.get('lote_origen_id')
    calidad = request.GET.get('calidad')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    logger.info(f"Cliente ID recibido: {cliente_id}")
    logger.info(f"Lote-Origen ID recibido: {lote_origen_id}")
    logger.info(f"Calidad recibida: {calidad}")
    logger.info(f"Fecha desde: {fecha_desde}")
    logger.info(f"Fecha hasta: {fecha_hasta}")
    
    # Obtener el ciclo actual
    try:
        config = ConfiguracionSistema.objects.first()
        ciclo_actual = config.ciclo_actual if config else ''
        logger.info(f"Ciclo actual: {ciclo_actual}")
    except Exception as e:
        logger.error(f"Error obteniendo configuración: {e}")
        ciclo_actual = ''
    
    # Filtrar remisiones del ciclo actual
    if ciclo_actual:
        remisiones_qs = Remision.objects.filter(ciclo=ciclo_actual)
    else:
        remisiones_qs = Remision.objects.all()
    
    # Aplicar filtro de fechas si se proporcionan
    if fecha_desde:
        remisiones_qs = remisiones_qs.filter(fecha__gte=fecha_desde)
        logger.info(f"Filtro fecha desde aplicado: {fecha_desde}")
    
    if fecha_hasta:
        remisiones_qs = remisiones_qs.filter(fecha__lte=fecha_hasta)
        logger.info(f"Filtro fecha hasta aplicado: {fecha_hasta}")
    
    logger.info(f"Total remisiones encontradas: {remisiones_qs.count()}")
    
    # Filtrar solo las remisiones no canceladas
    remisiones_no_canceladas = [r for r in remisiones_qs if not r.cancelada]
    logger.info(f"Remisiones no canceladas: {len(remisiones_no_canceladas)}")
    
    # Si se especifica un cliente, filtrar por ese cliente
    if cliente_id:
        remisiones_no_canceladas = [r for r in remisiones_no_canceladas if r.cliente.codigo == int(cliente_id)]
        logger.info(f"Remisiones filtradas por cliente {cliente_id}: {len(remisiones_no_canceladas)}")
    
    # Si se especifica un lote-origen, filtrar por ese lote-origen
    if lote_origen_id:
        remisiones_no_canceladas = [r for r in remisiones_no_canceladas if r.lote_origen.codigo == int(lote_origen_id)]
        logger.info(f"Remisiones filtradas por lote-origen {lote_origen_id}: {len(remisiones_no_canceladas)}")
    
    remisiones_no_canceladas_ids = [r.pk for r in remisiones_no_canceladas]
    
    # Obtener detalles de remisiones filtradas
    detalles_qs = RemisionDetalle.objects.filter(remision__in=remisiones_no_canceladas_ids)
    
    # Si se especifica una calidad, filtrar por esa calidad
    if calidad:
        detalles_qs = detalles_qs.filter(calidad=calidad)
        logger.info(f"Detalles filtrados por calidad {calidad}: {detalles_qs.count()}")
    
    logger.info(f"Detalles encontrados: {detalles_qs.count()}")
    
    # Agrupar por calidad y calcular totales
    calidad_data = defaultdict(lambda: {'kgs_netos_enviados': 0, 'kgs_liquidados': 0})
    
    for detalle in detalles_qs:
        calidad_nombre = detalle.calidad
        calidad_data[calidad_nombre]['kgs_netos_enviados'] += float(detalle.kgs_neto_envio or 0)
        calidad_data[calidad_nombre]['kgs_liquidados'] += float(detalle.kgs_liquidados or 0)
    
    # Convertir a lista para el template
    grafica_calidad_data = []
    for calidad_nombre, datos in calidad_data.items():
        diferencia = round(datos['kgs_netos_enviados'] - datos['kgs_liquidados'], 2)
        grafica_calidad_data.append({
            'calidad': calidad_nombre,
            'kgs_netos_enviados': round(datos['kgs_netos_enviados'], 2),
            'kgs_liquidados': round(datos['kgs_liquidados'], 2),
            'diferencia': diferencia
        })
    
    # Ordenar por calidad
    grafica_calidad_data.sort(key=lambda x: x['calidad'])
    
    logger.info(f"Datos finales calidad: {grafica_calidad_data}")
    
    return JsonResponse({
        'success': True,
        'data': grafica_calidad_data
    })

# @login_required # Temporarily removed for debugging
def actualizar_grafico_merma_ajax(request):
    """Vista AJAX para actualizar el gráfico de merma por calidad con filtros"""
    from django.http import JsonResponse
    from collections import defaultdict
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Vista AJAX merma llamada con método: {request.method}")
    
    cliente_id = request.GET.get('cliente_id')
    lote_origen_id = request.GET.get('lote_origen_id')
    calidad = request.GET.get('calidad')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    logger.info(f"Cliente ID recibido: {cliente_id}")
    logger.info(f"Lote-Origen ID recibido: {lote_origen_id}")
    logger.info(f"Calidad recibida: {calidad}")
    logger.info(f"Fecha desde: {fecha_desde}")
    logger.info(f"Fecha hasta: {fecha_hasta}")
    
    # Obtener el ciclo actual
    try:
        config = ConfiguracionSistema.objects.first()
        ciclo_actual = config.ciclo_actual if config else ''
        logger.info(f"Ciclo actual: {ciclo_actual}")
    except Exception as e:
        logger.error(f"Error obteniendo configuración: {e}")
        ciclo_actual = ''
    
    # Filtrar remisiones del ciclo actual
    if ciclo_actual:
        remisiones_qs = Remision.objects.filter(ciclo=ciclo_actual)
    else:
        remisiones_qs = Remision.objects.all()
    
    # Aplicar filtro de fechas si se proporcionan
    if fecha_desde:
        remisiones_qs = remisiones_qs.filter(fecha__gte=fecha_desde)
        logger.info(f"Filtro fecha desde aplicado: {fecha_desde}")
    
    if fecha_hasta:
        remisiones_qs = remisiones_qs.filter(fecha__lte=fecha_hasta)
        logger.info(f"Filtro fecha hasta aplicado: {fecha_hasta}")
    
    logger.info(f"Total remisiones encontradas: {remisiones_qs.count()}")
    
    # Filtrar solo las remisiones no canceladas
    remisiones_no_canceladas = [r for r in remisiones_qs if not r.cancelada]
    logger.info(f"Remisiones no canceladas: {len(remisiones_no_canceladas)}")
    
    # Si se especifica un cliente, filtrar por ese cliente
    if cliente_id:
        remisiones_no_canceladas = [r for r in remisiones_no_canceladas if r.cliente.codigo == int(cliente_id)]
        logger.info(f"Remisiones filtradas por cliente {cliente_id}: {len(remisiones_no_canceladas)}")
    
    # Si se especifica un lote-origen, filtrar por ese lote-origen
    if lote_origen_id:
        remisiones_no_canceladas = [r for r in remisiones_no_canceladas if r.lote_origen.codigo == int(lote_origen_id)]
        logger.info(f"Remisiones filtradas por lote-origen {lote_origen_id}: {len(remisiones_no_canceladas)}")
    
    remisiones_no_canceladas_ids = [r.pk for r in remisiones_no_canceladas]
    
    # Obtener detalles de remisiones filtradas
    detalles_qs = RemisionDetalle.objects.filter(remision__in=remisiones_no_canceladas_ids)
    
    # Si se especifica una calidad, filtrar por esa calidad
    if calidad:
        detalles_qs = detalles_qs.filter(calidad=calidad)
        logger.info(f"Detalles filtrados por calidad {calidad}: {detalles_qs.count()}")
    
    logger.info(f"Detalles encontrados: {detalles_qs.count()}")
    
    # Agrupar por calidad y calcular totales de merma
    merma_data = defaultdict(lambda: {
        'kgs_merma_enviada': 0, 
        'kgs_merma_liquidada': 0,
        'total_no_arps': 0,
        'total_no_arps_liquidados': 0,
        'sum_merma_arps': 0,
        'count_detalles': 0
    })
    
    for detalle in detalles_qs:
        calidad_nombre = detalle.calidad
        merma_data[calidad_nombre]['kgs_merma_enviada'] += float(detalle.kgs_merma or 0)
        merma_data[calidad_nombre]['kgs_merma_liquidada'] += float(detalle.kgs_merma_liquidados or 0)
        merma_data[calidad_nombre]['total_no_arps'] += float(detalle.no_arps or 0)
        merma_data[calidad_nombre]['total_no_arps_liquidados'] += float(detalle.no_arps_liquidados or 0)
        merma_data[calidad_nombre]['sum_merma_arps'] += float(detalle.merma_arps or 0)
        merma_data[calidad_nombre]['count_detalles'] += 1
    
    # Convertir a lista para el template
    grafica_merma_data = []
    for calidad_nombre, datos in merma_data.items():
        diferencia_merma = round(datos['kgs_merma_enviada'] - datos['kgs_merma_liquidada'], 2)
        # Calcular promedio de merma por arp enviado
        promedio_merma_arp_enviado = round(datos['sum_merma_arps'] / datos['count_detalles'], 2) if datos['count_detalles'] > 0 else 0
        # Calcular promedio de merma por arp liquidado
        promedio_merma_arp_liquidado = round(datos['kgs_merma_liquidada'] / datos['total_no_arps_liquidados'], 2) if datos['total_no_arps_liquidados'] > 0 else 0
        
        grafica_merma_data.append({
            'calidad': calidad_nombre,
            'kgs_merma_enviada': round(datos['kgs_merma_enviada'], 2),
            'kgs_merma_liquidada': round(datos['kgs_merma_liquidada'], 2),
            'diferencia_merma': diferencia_merma,
            'promedio_merma_arp_enviado': promedio_merma_arp_enviado,
            'promedio_merma_arp_liquidado': promedio_merma_arp_liquidado
        })
    
    # Ordenar por calidad
    grafica_merma_data.sort(key=lambda x: x['calidad'])
    
    logger.info(f"Datos finales merma: {grafica_merma_data}")
    
    return JsonResponse({
        'success': True,
        'data': grafica_merma_data
    })


def actualizar_grafico_ranking_ajax(request):
    """Vista AJAX para actualizar el gráfico de ranking de clientes con filtros"""
    from django.http import JsonResponse
    from collections import defaultdict
    import logging
    
    logger = logging.getLogger(__name__)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener parámetros de filtro
        cliente_id = request.GET.get('cliente_id', '').strip()
        lote_origen_id = request.GET.get('lote_origen_id', '').strip()
        calidad = request.GET.get('calidad', '').strip()
        fecha_desde = request.GET.get('fecha_desde', '').strip()
        fecha_hasta = request.GET.get('fecha_hasta', '').strip()
        
        logger.info(f"Filtros ranking - Cliente: {cliente_id}, Lote-Origen: {lote_origen_id}, Calidad: {calidad}, Fecha desde: {fecha_desde}, Fecha hasta: {fecha_hasta}")
        
        # Obtener el ciclo actual
        try:
            configuracion = Configuracion.objects.first()
            ciclo_actual = configuracion.ciclo_actual if configuracion else ''
        except Exception as e:
            logger.error(f"Error obteniendo configuración: {e}")
            ciclo_actual = ''
        
        # Filtrar remisiones del ciclo actual
        if ciclo_actual:
            remisiones_qs = Remision.objects.filter(ciclo=ciclo_actual)
        else:
            remisiones_qs = Remision.objects.all()
        
        # Aplicar filtro de fechas si se proporcionan
        if fecha_desde:
            remisiones_qs = remisiones_qs.filter(fecha__gte=fecha_desde)
            logger.info(f"Filtro fecha desde aplicado: {fecha_desde}")
        
        if fecha_hasta:
            remisiones_qs = remisiones_qs.filter(fecha__lte=fecha_hasta)
            logger.info(f"Filtro fecha hasta aplicado: {fecha_hasta}")
        
        logger.info(f"Total remisiones encontradas: {remisiones_qs.count()}")
        
        # Filtrar solo las remisiones no canceladas
        remisiones_no_canceladas = [r for r in remisiones_qs if not r.cancelada]
        logger.info(f"Remisiones no canceladas: {len(remisiones_no_canceladas)}")
        
        # Si se especifica un cliente, filtrar por ese cliente
        if cliente_id:
            remisiones_no_canceladas = [r for r in remisiones_no_canceladas if r.cliente.codigo == int(cliente_id)]
            logger.info(f"Remisiones filtradas por cliente {cliente_id}: {len(remisiones_no_canceladas)}")
        
        # Si se especifica un lote-origen, filtrar por ese lote-origen
        if lote_origen_id:
            remisiones_no_canceladas = [r for r in remisiones_no_canceladas if r.lote_origen.codigo == int(lote_origen_id)]
            logger.info(f"Remisiones filtradas por lote-origen {lote_origen_id}: {len(remisiones_no_canceladas)}")
        
        remisiones_no_canceladas_ids = [r.pk for r in remisiones_no_canceladas]
        
        # Obtener detalles de remisiones filtradas
        detalles_qs = RemisionDetalle.objects.filter(remision__in=remisiones_no_canceladas_ids)
        
        # Si se especifica una calidad, filtrar por esa calidad
        if calidad:
            detalles_qs = detalles_qs.filter(calidad=calidad)
            logger.info(f"Detalles filtrados por calidad {calidad}: {detalles_qs.count()}")
        
        logger.info(f"Detalles encontrados: {detalles_qs.count()}")
        
        # Agrupar remisiones preliquidadas por cliente y calcular totales
        clientes_data = defaultdict(lambda: {'importe_preliquidado': 0, 'importe_liquidado': 0, 'total_pagos': 0, 'total_remisiones': 0})
        
        # Obtener detalles filtrados por calidad si se especifica
        detalles_filtrados = {}
        if calidad:
            detalles_filtrados = {detalle.remision_id: detalle for detalle in detalles_qs}
            logger.info(f"Detalles filtrados por calidad: {len(detalles_filtrados)}")
        
        for remision in remisiones_no_canceladas:
            if remision.esta_liquidada():  # Solo remisiones preliquidadas
                cliente_nombre = remision.cliente.razon_social
                
                # Si hay filtro de calidad, usar solo los detalles filtrados
                if calidad:
                    if remision.pk in detalles_filtrados:
                        detalle = detalles_filtrados[remision.pk]
                        importe_preliquidado_remision = float(detalle.importe_envio or 0)
                        importe_liquidado_remision = float(detalle.importe_liquidado or 0)
                    else:
                        # Si la remisión no tiene detalles con la calidad seleccionada, saltarla
                        continue
                else:
                    # Sin filtro de calidad, usar todos los detalles de la remisión
                    importe_preliquidado_remision = sum(float(detalle.importe_envio or 0) for detalle in remision.detalles.all())
                    importe_liquidado_remision = sum(float(detalle.importe_liquidado or 0) for detalle in remision.detalles.all())
                
                # Sumar pagos realizados de la remisión
                total_pagos_remision = sum(float(pago.monto or 0) for pago in remision.pagos.filter(activo=True))
                
                clientes_data[cliente_nombre]['importe_preliquidado'] += importe_preliquidado_remision
                clientes_data[cliente_nombre]['importe_liquidado'] += importe_liquidado_remision
                clientes_data[cliente_nombre]['total_pagos'] += total_pagos_remision
                clientes_data[cliente_nombre]['total_remisiones'] += 1
        
        # Convertir a lista y ordenar por importe liquidado (descendente)
        ranking_clientes_data = []
        for cliente_nombre, datos in clientes_data.items():
            # Saldo pendiente = Importe liquidado - Pagos realizados
            saldo_pendiente = datos['importe_liquidado'] - datos['total_pagos']
            ranking_clientes_data.append({
                'cliente_nombre': cliente_nombre,
                'importe_preliquidado': round(datos['importe_preliquidado'], 2),
                'importe_liquidado': round(datos['importe_liquidado'], 2),
                'total_pagos': round(datos['total_pagos'], 2),
                'saldo_pendiente': round(saldo_pendiente, 2),
                'total_remisiones': datos['total_remisiones']
            })
        
        # Ordenar por importe liquidado descendente
        ranking_clientes_data.sort(key=lambda x: x['importe_liquidado'], reverse=True)
        
        logger.info(f"Datos finales ranking: {len(ranking_clientes_data)} clientes")
        
        return JsonResponse({
            'success': True,
            'data': ranking_clientes_data
        })
        
    except Exception as e:
        logger.error(f"Error en actualizar_grafico_ranking_ajax: {e}")
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


def actualizar_grafico_importes_ajax(request):
    """Vista AJAX para actualizar el gráfico de análisis por importe neto enviado vs preliquidado"""
    from django.http import JsonResponse
    from collections import defaultdict
    import logging
    
    logger = logging.getLogger(__name__)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener parámetros de filtro
        cliente_id = request.GET.get('cliente_id', '').strip()
        lote_origen_id = request.GET.get('lote_origen_id', '').strip()
        calidad = request.GET.get('calidad', '').strip()
        fecha_desde = request.GET.get('fecha_desde', '').strip()
        fecha_hasta = request.GET.get('fecha_hasta', '').strip()
        
        logger.info(f"Filtros importes - Cliente: {cliente_id}, Lote-Origen: {lote_origen_id}, Calidad: {calidad}, Fecha desde: {fecha_desde}, Fecha hasta: {fecha_hasta}")
        
        # Obtener el ciclo actual
        try:
            configuracion = Configuracion.objects.first()
            ciclo_actual = configuracion.ciclo_actual if configuracion else ''
        except Exception as e:
            logger.error(f"Error obteniendo configuración: {e}")
            ciclo_actual = ''
        
        # Filtrar remisiones del ciclo actual
        if ciclo_actual:
            remisiones_qs = Remision.objects.filter(ciclo=ciclo_actual)
        else:
            remisiones_qs = Remision.objects.all()
        
        # Aplicar filtro de fechas si se proporcionan
        if fecha_desde:
            remisiones_qs = remisiones_qs.filter(fecha__gte=fecha_desde)
            logger.info(f"Filtro fecha desde aplicado: {fecha_desde}")
        
        if fecha_hasta:
            remisiones_qs = remisiones_qs.filter(fecha__lte=fecha_hasta)
            logger.info(f"Filtro fecha hasta aplicado: {fecha_hasta}")
        
        logger.info(f"Total remisiones encontradas: {remisiones_qs.count()}")
        
        # Filtrar solo las remisiones no canceladas
        remisiones_no_canceladas = [r for r in remisiones_qs if not r.cancelada]
        logger.info(f"Remisiones no canceladas: {len(remisiones_no_canceladas)}")
        
        # Si se especifica un cliente, filtrar por ese cliente
        if cliente_id:
            remisiones_no_canceladas = [r for r in remisiones_no_canceladas if r.cliente.codigo == int(cliente_id)]
            logger.info(f"Remisiones filtradas por cliente {cliente_id}: {len(remisiones_no_canceladas)}")
        
        # Si se especifica un lote-origen, filtrar por ese lote-origen
        if lote_origen_id:
            remisiones_no_canceladas = [r for r in remisiones_no_canceladas if r.lote_origen.codigo == int(lote_origen_id)]
            logger.info(f"Remisiones filtradas por lote-origen {lote_origen_id}: {len(remisiones_no_canceladas)}")
        
        remisiones_no_canceladas_ids = [r.pk for r in remisiones_no_canceladas]
        
        # Obtener detalles de remisiones filtradas
        detalles_qs = RemisionDetalle.objects.filter(remision__in=remisiones_no_canceladas_ids)
        
        # Si se especifica una calidad, filtrar por esa calidad
        if calidad:
            detalles_qs = detalles_qs.filter(calidad=calidad)
            logger.info(f"Detalles filtrados por calidad {calidad}: {detalles_qs.count()}")
        
        logger.info(f"Detalles encontrados: {detalles_qs.count()}")
        
        # Agrupar por calidad y calcular totales
        calidad_data = defaultdict(lambda: {'importe_neto_enviado': 0, 'importe_preliquidado': 0})
        
        for detalle in detalles_qs:
            calidad_nombre = detalle.calidad
            importe_neto_enviado = float(detalle.importe_envio or 0)
            importe_preliquidado = float(detalle.importe_liquidado or 0)
            
            calidad_data[calidad_nombre]['importe_neto_enviado'] += importe_neto_enviado
            calidad_data[calidad_nombre]['importe_preliquidado'] += importe_preliquidado
        
        # Convertir a lista y ordenar por importe neto enviado (descendente)
        grafica_importes_data = []
        for calidad_nombre, datos in calidad_data.items():
            grafica_importes_data.append({
                'calidad': calidad_nombre,
                'importe_neto_enviado': round(datos['importe_neto_enviado'], 2),
                'importe_preliquidado': round(datos['importe_preliquidado'], 2)
            })
        
        # Ordenar por calidad con "Mixtas" al final
        def sort_key(item):
            calidad = item['calidad']
            if calidad == 'Mixtas':
                return (1, calidad)  # 1 para que vaya al final
            else:
                return (0, calidad)  # 0 para que vaya al principio
        
        grafica_importes_data.sort(key=sort_key)
        
        logger.info(f"Datos finales importes: {len(grafica_importes_data)} calidades")
        
        return JsonResponse({
            'success': True,
            'data': grafica_importes_data
        })
        
    except Exception as e:
        logger.error(f"Error en actualizar_grafico_importes_ajax: {e}")
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


def actualizar_grafico_gastos_ajax(request):
    """Vista AJAX para actualizar el gráfico de gastos autorizados (compras de productos del inventario)"""
    from django.http import JsonResponse
    from collections import defaultdict
    import logging
    
    logger = logging.getLogger(__name__)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener parámetros de filtro
        autorizo_id = request.GET.get('autorizo_id', '').strip()
        fecha_desde = request.GET.get('fecha_desde', '').strip()
        fecha_hasta = request.GET.get('fecha_hasta', '').strip()
        
        logger.info(f"Filtros gastos - Autorizó: {autorizo_id}, Fecha desde: {fecha_desde}, Fecha hasta: {fecha_hasta}")
        
        # Obtener todas las compras activas
        compras_qs = Compra.objects.filter(estado='activa').select_related('autorizo')
        
        # Aplicar filtro de autorizador si se proporciona
        if autorizo_id:
            compras_qs = compras_qs.filter(autorizo__codigo=autorizo_id)
            logger.info(f"Filtro autorizo aplicado: {autorizo_id}")
        
        # Aplicar filtro de fechas si se proporcionan
        if fecha_desde:
            compras_qs = compras_qs.filter(fecha__gte=fecha_desde)
            logger.info(f"Filtro fecha desde aplicado: {fecha_desde}")
        
        if fecha_hasta:
            compras_qs = compras_qs.filter(fecha__lte=fecha_hasta)
            logger.info(f"Filtro fecha hasta aplicado: {fecha_hasta}")
        
        logger.info(f"Total compras encontradas: {compras_qs.count()}")
        
        # Agrupar por autorizo y calcular totales
        gastos_data = defaultdict(lambda: {'total': 0, 'cantidad': 0})
        
        for compra in compras_qs:
            if compra.autorizo:
                autorizo_nombre = compra.autorizo.nombre
                gastos_data[autorizo_nombre]['total'] += float(compra.total or 0)
                gastos_data[autorizo_nombre]['cantidad'] += 1
        
        # Convertir a lista y ordenar por total (descendente)
        grafica_gastos_data = []
        for autorizo_nombre, datos in gastos_data.items():
            grafica_gastos_data.append({
                'autorizo_nombre': autorizo_nombre,
                'total': round(datos['total'], 2),
                'cantidad': datos['cantidad']
            })
        
        # Ordenar por total descendente
        grafica_gastos_data.sort(key=lambda x: x['total'], reverse=True)
        
        logger.info(f"Datos finales gastos: {len(grafica_gastos_data)} autorizadores")
        
        return JsonResponse({
            'success': True,
            'data': grafica_gastos_data
        })
        
    except Exception as e:
        logger.error(f"Error en actualizar_grafico_gastos_ajax: {e}")
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class AnalisisImportesImprimirView(LoginRequiredMixin, TemplateView):
    """Vista para imprimir reporte de análisis por importe neto enviado vs preliquidado"""
    template_name = 'core/analisis_importes_imprimir.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        configuracion = ConfiguracionSistema.objects.first()
        context['configuracion'] = configuracion
        ciclo_actual = configuracion.ciclo_actual if configuracion else ''
        context['ciclo_actual'] = ciclo_actual
        
        from collections import defaultdict
        
        # Obtener parámetros de filtro
        cliente_codigo = self.request.GET.get('cliente_codigo', '').strip()
        lote_origen_codigo = self.request.GET.get('lote_origen_codigo', '').strip()
        calidad = self.request.GET.get('calidad', '').strip()
        fecha_desde = self.request.GET.get('fecha_desde', '').strip()
        fecha_hasta = self.request.GET.get('fecha_hasta', '').strip()
        
        # Obtener objetos de filtro si se proporcionan
        cliente_filtrado = None
        lote_origen_filtrado = None
        
        if cliente_codigo:
            try:
                cliente_filtrado = Cliente.objects.get(codigo=cliente_codigo)
                context['cliente_filtrado'] = cliente_filtrado
            except Cliente.DoesNotExist:
                pass
        
        if lote_origen_codigo:
            try:
                lote_origen_filtrado = LoteOrigen.objects.get(codigo=lote_origen_codigo)
                context['lote_origen_filtrado'] = lote_origen_filtrado
            except LoteOrigen.DoesNotExist:
                pass
        
        if calidad:
            context['calidad_filtrada'] = calidad
        
        if fecha_desde:
            context['fecha_desde'] = fecha_desde
        
        if fecha_hasta:
            context['fecha_hasta'] = fecha_hasta
        
        # Obtener remisiones del ciclo actual
        remisiones_qs = Remision.objects.filter(
            cancelada=False,
            ciclo=ciclo_actual
        ).select_related('cliente', 'lote_origen').prefetch_related('detalles')
        
        # Aplicar filtros de fecha si se proporcionan
        if fecha_desde:
            remisiones_qs = remisiones_qs.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            remisiones_qs = remisiones_qs.filter(fecha__lte=fecha_hasta)
        
        # Filtrar por cliente y lote-origen si se proporcionan
        if cliente_filtrado:
            remisiones_qs = remisiones_qs.filter(cliente=cliente_filtrado)
        
        if lote_origen_filtrado:
            remisiones_qs = remisiones_qs.filter(lote_origen=lote_origen_filtrado)
        
        # Obtener detalles de remisiones filtradas
        detalles_qs = RemisionDetalle.objects.filter(remision__in=remisiones_qs)
        
        # Si se especifica una calidad, filtrar por esa calidad
        if calidad:
            detalles_qs = detalles_qs.filter(calidad=calidad)
        
        # Agrupar por calidad y calcular totales
        calidad_data = defaultdict(lambda: {'importe_neto_enviado': 0, 'importe_preliquidado': 0})
        
        for detalle in detalles_qs:
            calidad_nombre = detalle.calidad
            importe_neto_enviado = float(detalle.importe_envio or 0)
            importe_preliquidado = float(detalle.importe_liquidado or 0)
            
            calidad_data[calidad_nombre]['importe_neto_enviado'] += importe_neto_enviado
            calidad_data[calidad_nombre]['importe_preliquidado'] += importe_preliquidado
        
        # Convertir a lista y ordenar por importe neto enviado (descendente)
        grafica_importes_data = []
        for calidad_nombre, datos in calidad_data.items():
            grafica_importes_data.append({
                'calidad': calidad_nombre,
                'importe_neto_enviado': round(datos['importe_neto_enviado'], 2),
                'importe_preliquidado': round(datos['importe_preliquidado'], 2)
            })
        
        # Ordenar por calidad con "Mixtas" al final
        def sort_key(item):
            calidad = item['calidad']
            if calidad == 'Mixtas':
                return (1, calidad)  # 1 para que vaya al final
            else:
                return (0, calidad)  # 0 para que vaya al principio
        
        grafica_importes_data.sort(key=sort_key)
        
        # Calcular totales generales
        total_importe_neto_enviado = sum(item['importe_neto_enviado'] for item in grafica_importes_data)
        total_importe_preliquidado = sum(item['importe_preliquidado'] for item in grafica_importes_data)
        total_calidades = len(grafica_importes_data)
        
        context['grafica_importes_data'] = grafica_importes_data
        context['total_importe_neto_enviado'] = round(total_importe_neto_enviado, 2)
        context['total_importe_preliquidado'] = round(total_importe_preliquidado, 2)
        context['total_calidades'] = total_calidades
        
        return context
