"""
Servicio para generación de PDFs de facturas
"""

import os
import logging
import qrcode
import base64
from io import BytesIO
from datetime import datetime

logger = logging.getLogger(__name__)
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    HTML = None
    CSS = None
    FontConfiguration = None

logger = logging.getLogger(__name__)


class PDFService:
    """Servicio para generar PDFs de facturas"""
    
    @classmethod
    def generar_pdf_factura(cls, factura) -> HttpResponse:
        """
        Genera el PDF de una factura
        
        Args:
            factura: Instancia del modelo Factura
            
        Returns:
            HttpResponse: PDF generado
        """
        try:
            # Obtener detalles de la factura
            detalles = factura.detalles.all()
            
            # Obtener configuración del sistema
            from ..models import ConfiguracionSistema
            configuracion = ConfiguracionSistema.objects.first()
            
            # Preparar contexto para el template
            context = {
                'factura': factura,
                'detalles': detalles,
                'fecha_actual': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'logo_empresa': cls._obtener_logo_empresa(),
                'configuracion': configuracion,
                'codigo_qr': cls._generar_codigo_qr(factura),
            }
            
            # Renderizar template HTML
            html_string = render_to_string('core/factura_pdf.html', context)
            
            # Generar PDF
            if not WEASYPRINT_AVAILABLE:
                logger.warning("WeasyPrint no está disponible, generando respuesta temporal")
                return HttpResponse("PDF generation requires WeasyPrint to be installed", status=500)
            
            # Configurar WeasyPrint
            font_config = FontConfiguration()
            
            # Crear documento HTML con configuración mejorada
            html_doc = HTML(
                string=html_string,
                base_url=settings.BASE_DIR,
                encoding='utf-8'
            )
            
            # Generar PDF con configuración optimizada
            pdf_file = html_doc.write_pdf(
                font_config=font_config,
                optimize_images=True,
                jpeg_quality=95
            )
            
            # Verificar que el PDF se generó correctamente
            if not pdf_file or len(pdf_file) < 1000:  # PDF mínimo de 1KB
                logger.error(f"PDF generado es muy pequeño o vacío para factura {factura.folio}")
                return HttpResponse("Error: PDF generado está vacío o dañado", status=500)
            
            # Crear respuesta HTTP
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="factura_{factura.serie}_{factura.folio:06d}.pdf"'
            response['Content-Length'] = len(pdf_file)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generando PDF de factura {factura.folio}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return HttpResponse(f"Error generando PDF: {str(e)}", status=500)
    
    @classmethod
    def _obtener_logo_empresa(cls) -> str:
        """Obtiene la ruta absoluta del logo de la empresa para WeasyPrint"""
        try:
            # Buscar logo en la configuración del sistema
            from ..models import ConfiguracionSistema
            config = ConfiguracionSistema.objects.first()
            
            if config and config.logo_empresa:
                # Convertir URL relativa a ruta absoluta
                logo_path = os.path.join(settings.MEDIA_ROOT, config.logo_empresa.name)
                if os.path.exists(logo_path):
                    return f"file://{logo_path}"
                else:
                    # Si no existe en MEDIA_ROOT, usar la URL
                    return config.logo_empresa.url
            else:
                # Logo por defecto - buscar en STATIC_ROOT
                logo_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'images', 'logoAgroDam.png')
                if os.path.exists(logo_path):
                    return f"file://{logo_path}"
                else:
                    # Fallback a la URL estática
                    return '/static/images/logoAgroDam.png'
                
        except Exception as e:
            logger.warning(f"Error obteniendo logo de empresa: {e}")
            return '/static/images/logoAgroDam.png'
    
    @classmethod
    def _obtener_logo_empresa_vista_previa(cls) -> str:
        """Obtiene la URL del logo de la empresa para vista previa (navegador)"""
        try:
            # Buscar logo en la configuración del sistema
            from ..models import ConfiguracionSistema
            config = ConfiguracionSistema.objects.first()
            
            if config and config.logo_empresa:
                # Usar URL relativa para el navegador
                return config.logo_empresa.url
            else:
                # Logo por defecto
                return '/static/images/logoAgroDam.png'
                
        except Exception as e:
            logger.warning(f"Error obteniendo logo de empresa para vista previa: {e}")
            return '/static/images/logoAgroDam.png'
    
    @classmethod
    def _generar_codigo_qr(cls, factura) -> str:
        """
        Genera el código QR para la factura CFDI 4.0
        
        Primero intenta usar el código QR proporcionado por el PAC,
        si no está disponible, genera uno manualmente.
        """
        try:
            # Si el PAC proporcionó un código QR, usarlo directamente
            if factura.codigo_qr:
                logger.info(f"Usando código QR del PAC para factura {factura.folio}")
                return f"data:image/png;base64,{factura.codigo_qr}"
            
            # Si no hay código QR del PAC, generar uno manualmente
            if not factura.uuid or not factura.sello:
                logger.warning(f"Factura {factura.folio} no tiene UUID o sello para generar QR")
                return None
            
            logger.info(f"Generando código QR manualmente para factura {factura.folio}")
            
            # Construir la URL del QR
            uuid = factura.uuid
            rfc_emisor = factura.emisor.rfc
            rfc_receptor = factura.receptor.rfc
            total = str(int(factura.total))  # Total sin decimales
            siglas_sello = factura.sello[-8:]  # Últimos 8 caracteres del sello
            
            url_qr = f"https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id={uuid}&re={rfc_emisor}&rr={rfc_receptor}&tt={total}&fe={siglas_sello}"
            
            # Generar el código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=3,
                border=2,
            )
            qr.add_data(url_qr)
            qr.make(fit=True)
            
            # Crear la imagen
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64 para incluir en el HTML
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error generando código QR para factura {factura.folio}: {e}")
            return None
    
    @classmethod
    def _obtener_css_factura(cls) -> str:
        """Obtiene el CSS para el PDF de la factura"""
        return """
        @page {
            size: A4;
            margin: 1cm;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            font-size: 10px;
            line-height: 1.2;
            color: #333;
            margin-top: 10px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
            padding-top: 5px;
            padding-bottom: 6px;
            border-bottom: 2px solid #2c5aa0;
        }
        
        .company-info {
            flex: 1;
        }
        
        .company-logo-section {
            display: flex;
            align-items: flex-start;
            margin-bottom: 8px;
        }
        
        .company-logo-img {
            height: 60px;
            width: auto;
            margin-right: 15px;
        }
        
        .company-text {
            flex: 1;
        }
        
        .company-logo {
            font-size: 24px;
            font-weight: bold;
            color: #2c5aa0;
            margin-bottom: 4px;
        }
        
        .company-slogan {
            font-size: 12px;
            color: #666;
            font-style: italic;
        }
        
        .company-details {
            font-size: 9px;
            line-height: 1.1;
        }
        
        .document-info {
            text-align: right;
            flex: 0 0 240px;
            background-color: #f8f9fa;
            padding: 8px;
            border: 1px solid #dee2e6;
            border-radius: 3px;
        }
        
        .document-title {
            font-size: 20px;
            font-weight: bold;
            color: #2c5aa0;
            margin-bottom: 10px;
        }
        
        .document-number {
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .document-date {
            font-size: 14px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .document-uuid {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
            word-break: break-all;
        }
        
        .document-cert {
            font-size: 10px;
            color: #666;
        }
        
        .page-info {
            text-align: right;
            font-size: 9px;
            color: #666;
            margin-top: 5px;
        }
        
        .disclaimer {
            font-size: 8px;
            color: #666;
            margin-top: 5px;
            text-align: center;
        }
        
        .sections-container {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .section {
            flex: 1;
            border: 1px solid #dee2e6;
            border-radius: 3px;
            padding: 6px;
            background-color: #f8f9fa;
        }
        
        .section-title {
            font-size: 10px;
            font-weight: bold;
            color: #2c5aa0;
            margin-bottom: 6px;
            padding-bottom: 2px;
            border-bottom: 1px solid #dee2e6;
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 3px;
            font-size: 9px;
        }
        
        .info-label {
            font-weight: bold;
            color: #555;
        }
        
        .info-value {
            color: #333;
        }
        
        .cfdi-section {
            flex: 0 0 200px;
        }
        
        .details-table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            font-size: 9px;
        }
        
        .details-table th {
            background-color: #e9ecef;
            border: 1px solid #dee2e6;
            padding: 3px;
            text-align: center;
            font-weight: bold;
            font-size: 8px;
        }
        
        .details-table td {
            border: 1px solid #dee2e6;
            padding: 3px;
            text-align: center;
        }
        
        .details-table .text-left {
            text-align: left;
        }
        
        .details-table .text-right {
            text-align: right;
        }
        
        .totals-section {
            margin-top: 10px;
            text-align: right;
        }
        
        .totals-container {
            display: inline-block;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 3px;
            padding: 8px;
            min-width: 200px;
        }
        
        .total-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 10px;
        }
        
        .total-label {
            font-weight: bold;
        }
        
        .total-value {
            font-weight: bold;
        }
        
        .total-final {
            font-size: 12px;
            border-top: 2px solid #333;
            padding-top: 5px;
            margin-top: 5px;
        }
        
        .payment-info {
            margin-top: 10px;
            display: flex;
            justify-content: space-between;
            font-size: 9px;
        }
        
        .payment-left {
            flex: 1;
        }
        
        .payment-right {
            flex: 1;
            text-align: right;
        }
        
        .amount-in-words {
            margin-top: 10px;
            font-size: 9px;
            font-style: italic;
            color: #666;
        }
        
        .digital-seals {
            margin-top: 15px;
            font-size: 8px;
            color: #666;
        }
        
        .seal-row {
            margin-bottom: 5px;
            word-break: break-all;
        }
        
        .seal-label {
            font-weight: bold;
            margin-bottom: 2px;
        }
        
        .seal-value {
            font-family: monospace;
            font-size: 7px;
        }
        
        .qr-section {
            text-align: center;
            margin-top: 15px;
        }
        
        .qr-code {
            width: 120px;
            height: 120px;
            border: 1px solid #ccc;
            display: inline-block;
            background-color: #f8f9fa;
        }
        
        .footer {
            margin-top: 15px;
            text-align: center;
            font-size: 8px;
            color: #666;
            border-top: 1px solid #ccc;
            padding-top: 8px;
        }
        """
    
    @classmethod
    def generar_vista_previa_pdf(cls, factura) -> str:
        """
        Genera una vista previa HTML del PDF
        
        Args:
            factura: Instancia del modelo Factura
            
        Returns:
            str: HTML de la vista previa
        """
        try:
            # Obtener detalles de la factura
            detalles = factura.detalles.all()
            
            # Obtener configuración del sistema
            from ..models import ConfiguracionSistema
            configuracion = ConfiguracionSistema.objects.first()
            
            # Preparar contexto para el template
            context = {
                'factura': factura,
                'detalles': detalles,
                'fecha_actual': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'logo_empresa': cls._obtener_logo_empresa_vista_previa(),
                'configuracion': configuracion,
                'codigo_qr': cls._generar_codigo_qr(factura),
                'es_vista_previa': True,
            }
            
            # Renderizar template HTML
            html_string = render_to_string('core/factura_pdf.html', context)
            
            return html_string
            
        except Exception as e:
            logger.error(f"Error generando vista previa de factura {factura.folio}: {e}")
            return f"<p>Error generando vista previa: {str(e)}</p>"
    
    @classmethod
    def generar_vista_previa_complemento_pago(cls, pago) -> str:
        """
        Genera una vista previa HTML del PDF del complemento de pago
        
        Args:
            pago: Instancia del modelo PagoFactura
            
        Returns:
            str: HTML de la vista previa
        """
        try:
            # Debug: verificar estado del pago
            logger.info(f"Debug complemento pago {pago.id}: uuid={pago.uuid}, xml_timbrado={bool(pago.xml_timbrado)}")
            
            # Verificar que el pago esté timbrado
            if not pago.uuid or not pago.xml_timbrado:
                logger.warning(f"Complemento de pago {pago.id} no está timbrado: uuid={pago.uuid}, xml_timbrado={bool(pago.xml_timbrado)}")
                return f"<p>El complemento de pago no está timbrado (UUID: {pago.uuid}, XML: {bool(pago.xml_timbrado)})</p>"
            
            # Decodificar el XML timbrado
            import base64
            xml_timbrado = base64.b64decode(pago.xml_timbrado).decode('utf-8')
            
            # Preparar contexto para el template
            context = {
                'pago': pago,
                'factura': pago.factura,
                'xml_timbrado': xml_timbrado,
                'fecha_actual': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'es_vista_previa': True,
            }
            
            # Renderizar template HTML
            html_string = render_to_string('core/complemento_pago_pdf.html', context)
            
            return html_string
            
        except Exception as e:
            logger.error(f"Error generando vista previa de complemento de pago {pago.id}: {e}")
            return f"<p>Error generando vista previa: {str(e)}</p>"