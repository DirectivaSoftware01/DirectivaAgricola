"""
Vistas para facturación electrónica CFDI 4.0
"""

import json
from datetime import datetime
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone
from .models import Emisor, Cliente, ProductoServicio, Factura, FacturaDetalle
from .services.pdf_service import PDFService


# Vistas principales de facturación

class FacturacionView(LoginRequiredMixin, TemplateView):
    """Vista principal para crear facturas"""
    template_name = 'core/facturacion.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Facturación CFDI 4.0'
        
        # Obtener emisores activos
        context['emisores'] = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        # Obtener clientes activos
        context['clientes'] = Cliente.objects.filter(activo=True).order_by('razon_social')
        
        # Obtener productos/servicios activos
        context['productos'] = ProductoServicio.objects.filter(activo=True).order_by('descripcion')
        
        return context


class ListadoFacturasView(LoginRequiredMixin, ListView):
    """Vista para listar facturas agrupadas por Emisor y Receptor"""
    model = Factura
    template_name = 'core/listado_facturas.html'
    context_object_name = 'facturas'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Factura.objects.select_related('emisor', 'receptor').order_by('-fecha_emision', 'serie', 'folio')
        
        # Filtros de búsqueda
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(serie__icontains=search) |
                Q(folio__icontains=search) |
                Q(emisor__razon_social__icontains=search) |
                Q(receptor__razon_social__icontains=search) |
                Q(uuid__icontains=search)
            )
        
        # Filtro por estado de timbrado
        estado = self.request.GET.get('estado', '')
        if estado:
            queryset = queryset.filter(estado_timbrado=estado)
        
        # Filtro por emisor
        emisor_id = self.request.GET.get('emisor_id', '')
        if emisor_id:
            queryset = queryset.filter(emisor__codigo=emisor_id)
        
        # Filtro por receptor
        receptor_id = self.request.GET.get('receptor_id', '')
        if receptor_id:
            queryset = queryset.filter(receptor__codigo=receptor_id)
        
        # Filtro por fecha desde
        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde:
            queryset = queryset.filter(fecha_emision__date__gte=fecha_desde)
        
        # Filtro por fecha hasta
        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta:
            queryset = queryset.filter(fecha_emision__date__lte=fecha_hasta)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Facturas'
        context['emisores'] = Emisor.objects.filter(activo=True).order_by('razon_social')
        context['receptores'] = Cliente.objects.filter(activo=True).order_by('razon_social')
        context['estados_timbrado'] = Factura.ESTADO_TIMBRADO_CHOICES
        
        # Agregar filtros para el template
        context['filtros'] = {
            'emisor_id': self.request.GET.get('emisor_id', ''),
            'receptor_id': self.request.GET.get('receptor_id', ''),
            'fecha_desde': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
        }
        
        return context


class FacturaDetailView(LoginRequiredMixin, DetailView):
    """Vista para mostrar detalles de una factura"""
    model = Factura
    template_name = 'core/factura_detail.html'
    context_object_name = 'factura'
    pk_url_kwarg = 'folio'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Factura: {self.object.serie} - {self.object.folio:06d}'
        context['detalles'] = self.object.detalles.all()
        return context


# Vistas para PDF

@login_required
def generar_pdf_factura(request, folio):
    """Vista para generar PDF de una factura"""
    if not request.user.is_staff:
        return HttpResponse('No tienes permisos para acceder a esta sección', status=403)
    
    try:
        factura = get_object_or_404(Factura, folio=folio)
        return PDFService.generar_pdf_factura(factura)
    except Exception as e:
        return HttpResponse(f'Error generando PDF: {str(e)}', status=500)


@login_required
def vista_previa_pdf_factura(request, folio):
    """Vista para mostrar vista previa del PDF de una factura"""
    if not request.user.is_staff:
        return HttpResponse('No tienes permisos para acceder a esta sección', status=403)
    
    try:
        factura = get_object_or_404(Factura, folio=folio)
        html_content = PDFService.generar_vista_previa_pdf(factura)
        return HttpResponse(html_content, content_type='text/html; charset=utf-8')
    except Exception as e:
        return HttpResponse(f'Error generando vista previa: {str(e)}', status=500)


@login_required
def descargar_xml_factura(request, folio):
    """Vista para descargar XML timbrado de una factura"""
    if not request.user.is_staff:
        return HttpResponse('No tienes permisos para acceder a esta sección', status=403)
    
    try:
        factura = get_object_or_404(Factura, folio=folio)
        
        # Verificar que la factura esté timbrada
        if not factura.xml_timbrado:
            return HttpResponse('Esta factura no tiene XML timbrado', status=404)
        
        # Crear respuesta con el XML
        response = HttpResponse(
            factura.xml_timbrado,
            content_type='application/xml; charset=utf-8'
        )
        
        # Configurar headers para descarga
        filename = f"CFDI_{factura.serie}_{factura.folio:06d}_{factura.uuid}.xml"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(factura.xml_timbrado.encode('utf-8'))
        
        return response
        
    except Exception as e:
        return HttpResponse(f'Error descargando XML: {str(e)}', status=500)


# Vistas AJAX existentes


@login_required
def validar_emisor_ajax(request, codigo):
    """Vista AJAX para validar configuración de emisor"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from .services.configuracion_entorno import ConfiguracionEntornoService
        from .services.certificado_service import CertificadoService
        
        # Obtener el emisor
        emisor = get_object_or_404(Emisor, codigo=codigo)
        
        # Validar configuración
        config_validacion = ConfiguracionEntornoService.validar_configuracion_emisor(emisor)
        
        # Si la configuración es válida, validar certificado
        if config_validacion['valido']:
            cert_validacion = CertificadoService.validar_certificado_completo(emisor)
            if not cert_validacion['valido']:
                config_validacion['errores'].extend(cert_validacion['errores'])
                config_validacion['valido'] = False
            if cert_validacion.get('advertencias'):
                config_validacion['advertencias'].extend(cert_validacion['advertencias'])
        
        return JsonResponse(config_validacion)
        
    except Exception as e:
        return JsonResponse({
            'valido': False,
            'errores': [f'Error interno del servidor: {str(e)}'],
            'advertencias': []
        }, status=500)


@login_required
def validar_cfdi_ajax(request):
    """Vista AJAX para validar CFDI"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from .validators.cfdi_validator import CFDIValidator
        
        # Obtener datos del request
        data = json.loads(request.body)
        
        # Crear objetos temporales para validación
        emisor = get_object_or_404(Emisor, codigo=data['emisor_id'])
        receptor = get_object_or_404(Cliente, id=data['receptor_id'])
        
        # Crear factura temporal
        factura = Factura(
            serie=data['serie'],
            folio=1,  # Temporal
            fecha_emision=timezone.now(),  # Fecha actual con zona horaria de México
            emisor=emisor,
            lugar_expedicion=data['lugar_expedicion'],
            receptor=receptor,
            uso_cfdi=data['uso_cfdi'],
            exportacion=data['exportacion'],
            metodo_pago=data['metodo_pago'],
            moneda=data['moneda'],
            forma_pago=data['forma_pago'],
            tipo_cambio=float(data['tipo_cambio']),
            subtotal=0,  # Se calculará
            impuesto=0,  # Se calculará
            total=0  # Se calculará
        )
        
        # Crear detalles temporales
        detalles = []
        subtotal = 0
        impuesto = 0
        
        for detalle_data in data['detalles']:
            producto = get_object_or_404(ProductoServicio, id=detalle_data['producto_id'])
            
            detalle = FacturaDetalle(
                factura=factura,
                producto_servicio=producto,
                no_identificacion=detalle_data['no_identificacion'],
                concepto=detalle_data['concepto'],
                cantidad=float(detalle_data['cantidad']),
                precio=float(detalle_data['precio']),
                clave_prod_serv=detalle_data['clave_prod_serv'],
                unidad=detalle_data['unidad'],
                objeto_impuesto=detalle_data['objeto_impuesto']
            )
            
            # Calcular importe e impuesto
            detalle.importe = detalle.cantidad * detalle.precio
            from core.utils.tax_utils import calcular_impuesto_concepto
            detalle.impuesto_concepto = calcular_impuesto_concepto(
                detalle.importe, 
                producto.impuesto, 
                detalle.objeto_impuesto
            )
            
            subtotal += detalle.importe
            impuesto += detalle.impuesto_concepto
            detalles.append(detalle)
        
        # Actualizar totales
        factura.subtotal = subtotal
        factura.impuesto = impuesto
        factura.total = subtotal + impuesto
        
        # Validar CFDI
        validacion = CFDIValidator.validar_factura_completa(factura, detalles)
        
        return JsonResponse(validacion)
        
    except Exception as e:
        return JsonResponse({
            'valido': False,
            'errores': [f'Error interno del servidor: {str(e)}'],
            'advertencias': []
        }, status=500)


@login_required
def timbrar_factura_ajax(request, factura_id):
    """Vista AJAX para timbrar factura"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from .services.facturacion_service import FacturacionService
        
        # Timbrar la factura
        resultado = FacturacionService.timbrar_factura(factura_id)
        
        return JsonResponse(resultado)
        
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'error': f'Error interno del servidor: {str(e)}',
            'codigo_error': 'INTERNAL_ERROR'
        }, status=500)


@login_required
def cancelar_factura_ajax(request, factura_id):
    """Vista AJAX para cancelar factura"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from .services.facturacion_service import FacturacionService
        
        # Obtener datos del request
        data = json.loads(request.body)
        motivo = data.get('motivo', '')
        folio_sustitucion = data.get('folio_sustitucion', None)
        
        # Cancelar la factura
        resultado = FacturacionService.cancelar_factura(factura_id, motivo, folio_sustitucion)
        
        return JsonResponse(resultado)
        
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'error': f'Error interno del servidor: {str(e)}',
            'codigo_error': 'INTERNAL_ERROR'
        }, status=500)


@login_required
def consultar_estatus_factura_ajax(request, factura_id):
    """Vista AJAX para consultar estatus de factura"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from .services.facturacion_service import FacturacionService
        
        # Consultar estatus
        resultado = FacturacionService.consultar_estatus_factura(factura_id)
        
        return JsonResponse(resultado)
        
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'error': f'Error interno del servidor: {str(e)}',
            'codigo_error': 'INTERNAL_ERROR'
        }, status=500)


@login_required
def probar_conexion_pac_ajax(request, emisor_id):
    """Vista AJAX para probar conexión con PAC"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección'}, status=403)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from .services.facturacion_service import FacturacionService
        
        # Probar conexión
        resultado = FacturacionService.probar_conexion_pac(emisor_id)
        
        return JsonResponse(resultado)
        
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'error': f'Error interno del servidor: {str(e)}',
            'codigo_error': 'INTERNAL_ERROR'
        }, status=500)