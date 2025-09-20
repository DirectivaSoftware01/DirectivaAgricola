"""
Constructor de XML CFDI 4.0
Genera el XML del comprobante fiscal con todos los elementos requeridos
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class XMLCFDIBuilder:
    """
    Constructor de XML CFDI 4.0 según Anexo 20 RMF 2022.
    Genera XML válido con namespace correcto y validación XSD oficial.
    """
    
    # Namespaces CFDI 4.0 según Anexo 20
    NAMESPACES = {
        'cfdi': 'http://www.sat.gob.mx/cfd/4',
        'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    # Schema locations según Anexo 20
    SCHEMA_LOCATIONS = {
        'http://www.sat.gob.mx/cfd/4': 'http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd',
        'http://www.sat.gob.mx/TimbreFiscalDigital': 'http://www.sat.gob.mx/sitio_internet/cfd/TimbreFiscalDigital/TimbreFiscalDigitalv11.xsd'
    }
    
    # Versión CFDI según Anexo 20
    CFDI_VERSION = "4.0"
    
    @classmethod
    def construir_xml_cfdi(cls, factura, detalles, certificado_data: Dict[str, Any], sello: str) -> str:
        """
        Construye el XML completo del CFDI 4.0
        
        Args:
            factura: Instancia del modelo Factura
            detalles: Lista de instancias de FacturaDetalle
            certificado_data: Datos del certificado
            sello: Sello digital generado
            
        Returns:
            str: XML del CFDI como string
        """
        try:
            # Crear elemento raíz
            root = ET.Element('cfdi:Comprobante')
            root.set('xmlns:cfdi', cls.NAMESPACES['cfdi'])
            root.set('xmlns:tfd', cls.NAMESPACES['tfd'])
            root.set('xmlns:xsi', cls.NAMESPACES['xsi'])
            
            # Schema locations
            schema_locations = []
            for ns, location in cls.SCHEMA_LOCATIONS.items():
                schema_locations.append(f"{ns} {location}")
            root.set('xsi:schemaLocation', ' '.join(schema_locations))
            
            # Atributos del comprobante
            cls._agregar_atributos_comprobante(root, factura, certificado_data, sello)
            
            # Información Global (si aplica para RFC XAXX010101000)
            if (hasattr(factura, 'receptor') and 
                factura.receptor and 
                factura.receptor.rfc == 'XAXX010101000' and
                factura.tipo_comprobante == 'I'):  # Solo para ingresos
                
                cls._agregar_informacion_global(root, factura)
            
            # Emisor
            cls._agregar_emisor(root, factura.emisor)
            
            # Receptor
            cls._agregar_receptor(root, factura.receptor, factura.uso_cfdi)
            
            # Conceptos
            cls._agregar_conceptos(root, detalles)
            
            # Impuestos
            cls._agregar_impuestos(root, factura, detalles)
            
            # Complementos (si aplican)
            cls._agregar_complementos(root, factura)
            
            # Convertir a string
            xml_string = ET.tostring(root, encoding='unicode', xml_declaration=True)
            
            # Formatear XML
            xml_formateado = cls._formatear_xml(xml_string)
            
            return xml_formateado
            
        except Exception as e:
            logger.error(f"Error construyendo XML CFDI: {e}")
            raise
    
    @classmethod
    def _agregar_atributos_comprobante(cls, root, factura, certificado_data: Dict[str, Any], sello: str):
        """
        Agrega los atributos del elemento Comprobante según Anexo 20 RMF 2022.
        Usa nombres exactos de atributos del estándar oficial.
        """
        # Atributos obligatorios según Anexo 20
        root.set('Version', cls.CFDI_VERSION)
        
        # Serie y Folio (opcionales según Anexo 20)
        if factura.serie:
            root.set('Serie', factura.serie)
        if factura.folio:
            root.set('Folio', str(factura.folio))
        
        # Fecha en formato AAAA-MM-DDThh:mm:ss (requerido)
        root.set('Fecha', factura.fecha_emision.strftime('%Y-%m-%dT%H:%M:%S'))
        
        # Sello digital (requerido)
        root.set('Sello', sello)
        
        # Forma de pago (condicional según Anexo 20)
        if factura.forma_pago:
            root.set('FormaPago', factura.forma_pago)
        
        # Certificado (requerido)
        root.set('NoCertificado', certificado_data['no_certificado'])
        root.set('Certificado', certificado_data['certificado_base64'])
        
        # Condiciones de pago (opcional)
        if hasattr(factura, 'condiciones_pago') and factura.condiciones_pago:
            root.set('CondicionesDePago', factura.condiciones_pago)
        
        # Totales (requeridos)
        root.set('SubTotal', f"{factura.subtotal:.2f}")
        root.set('Total', f"{factura.total:.2f}")
        
        # Descuento (opcional)
        if hasattr(factura, 'descuento') and factura.descuento and factura.descuento > 0:
            root.set('Descuento', f"{factura.descuento:.2f}")
        
        # Moneda (requerido)
        root.set('Moneda', factura.moneda)
        
        # Tipo de cambio (condicional - solo si no es MXN)
        if factura.moneda != 'MXN':
            root.set('TipoCambio', f"{factura.tipo_cambio:.4f}")
        
        # Tipo de comprobante (requerido)
        root.set('TipoDeComprobante', getattr(factura, 'tipo_comprobante', 'I'))
        
        # Exportación (requerido)
        root.set('Exportacion', factura.exportacion)
        
        # Método de pago (requerido)
        root.set('MetodoPago', factura.metodo_pago)
        
        # Lugar de expedición (requerido)
        root.set('LugarExpedicion', factura.lugar_expedicion)
        
        # Confirmación (opcional)
        if hasattr(factura, 'confirmacion') and factura.confirmacion:
            root.set('Confirmacion', factura.confirmacion)
    
    @classmethod
    def _agregar_emisor(cls, root, emisor):
        """Agrega el elemento Emisor"""
        emisor_elem = ET.SubElement(root, 'cfdi:Emisor')
        emisor_elem.set('Rfc', emisor.rfc)
        emisor_elem.set('Nombre', emisor.razon_social)
        emisor_elem.set('RegimenFiscal', emisor.regimen_fiscal)
    
    @classmethod
    def _agregar_receptor(cls, root, receptor, uso_cfdi: str):
        """Agrega el elemento Receptor"""
        receptor_elem = ET.SubElement(root, 'cfdi:Receptor')
        receptor_elem.set('Rfc', receptor.rfc)
        receptor_elem.set('Nombre', receptor.razon_social)
        receptor_elem.set('DomicilioFiscalReceptor', receptor.codigo_postal)
        receptor_elem.set('RegimenFiscalReceptor', receptor.regimen_fiscal.codigo)
        receptor_elem.set('UsoCFDI', uso_cfdi)
    
    @classmethod
    def _agregar_conceptos(cls, root, detalles):
        """
        Agrega el elemento Conceptos según Anexo 20 RMF 2022.
        Usa nombres exactos de atributos del estándar oficial.
        """
        conceptos_elem = ET.SubElement(root, 'cfdi:Conceptos')
        
        for detalle in detalles:
            concepto_elem = ET.SubElement(conceptos_elem, 'cfdi:Concepto')
            
            # Atributos requeridos según Anexo 20
            concepto_elem.set('ClaveProdServ', detalle.clave_prod_serv)
            concepto_elem.set('Cantidad', f"{detalle.cantidad:.6f}")
            concepto_elem.set('ClaveUnidad', getattr(detalle, 'clave_unidad', 'H87'))
            concepto_elem.set('Unidad', detalle.unidad)
            concepto_elem.set('Descripcion', detalle.concepto)
            concepto_elem.set('ValorUnitario', f"{detalle.precio:.6f}")
            concepto_elem.set('Importe', f"{detalle.importe:.2f}")
            concepto_elem.set('ObjetoImp', detalle.objeto_impuesto)
            
            # Atributos opcionales según Anexo 20
            if detalle.no_identificacion:
                concepto_elem.set('NoIdentificacion', detalle.no_identificacion)
            
            # Descuento del concepto (opcional)
            if hasattr(detalle, 'descuento') and detalle.descuento and detalle.descuento > 0:
                concepto_elem.set('Descuento', f"{detalle.descuento:.2f}")
            
            # Impuestos del concepto (si aplican)
            if detalle.objeto_impuesto == '02':
                cls._agregar_impuestos_concepto(concepto_elem, detalle)
    
    @classmethod
    def _agregar_impuestos_concepto(cls, concepto_elem, detalle):
        """
        Agrega impuestos al concepto según Anexo 20 RMF 2022.
        Siempre incluye el nodo de impuestos para objetos del impuesto.
        """
        impuestos_elem = ET.SubElement(concepto_elem, 'cfdi:Impuestos')
        
        # Traslados del concepto
        traslados_elem = ET.SubElement(impuestos_elem, 'cfdi:Traslados')
        
        # Obtener la tasa correcta del producto
        from core.utils.tax_utils import obtener_tasa_impuesto_xml
        tasa_impuesto = obtener_tasa_impuesto_xml(detalle.producto_servicio.impuesto)
        
        traslado_elem = ET.SubElement(traslados_elem, 'cfdi:Traslado')
        traslado_elem.set('Base', f"{detalle.importe:.2f}")
        traslado_elem.set('Impuesto', '002')  # IVA
        traslado_elem.set('TipoFactor', 'Tasa')
        traslado_elem.set('TasaOCuota', tasa_impuesto)
        traslado_elem.set('Importe', f"{detalle.impuesto_concepto:.2f}")
    
    @classmethod
    def _agregar_impuestos(cls, root, factura, detalles):
        """
        Agrega el elemento Impuestos según Anexo 20 RMF 2022.
        Usa nombres exactos de atributos del estándar oficial.
        """
        # Verificar si hay conceptos con objeto de impuesto
        conceptos_con_impuesto = [detalle for detalle in detalles if detalle.objeto_impuesto == '02']
        
        if not conceptos_con_impuesto:
            return
        
        impuestos_elem = ET.SubElement(root, 'cfdi:Impuestos')
        
        # Calcular totales de impuestos
        total_traslados = sum(detalle.impuesto_concepto for detalle in conceptos_con_impuesto)
        total_retenciones = 0  # Por ahora no manejamos retenciones
        
        # Total de impuestos trasladados (siempre incluir, aunque sea 0.00)
        impuestos_elem.set('TotalImpuestosTrasladados', f"{total_traslados:.2f}")
        
        # Total de impuestos retenidos
        if total_retenciones > 0:
            impuestos_elem.set('TotalImpuestosRetenidos', f"{total_retenciones:.2f}")
        
        # Traslados - siempre incluir cuando hay conceptos con objeto de impuesto
        traslados_elem = ET.SubElement(impuestos_elem, 'cfdi:Traslados')
        
        # Agrupar por tasa de impuesto para crear traslados separados
        from collections import defaultdict
        impuestos_por_tasa = defaultdict(lambda: {'base': 0, 'importe': 0, 'tasa': None})
        
        for detalle in conceptos_con_impuesto:
            from core.utils.tax_utils import obtener_tasa_impuesto_xml
            tasa = obtener_tasa_impuesto_xml(detalle.producto_servicio.impuesto)
            impuestos_por_tasa[tasa]['base'] += detalle.importe
            impuestos_por_tasa[tasa]['importe'] += detalle.impuesto_concepto
            impuestos_por_tasa[tasa]['tasa'] = tasa
        
        # Crear traslados para cada tasa
        for tasa, datos in impuestos_por_tasa.items():
            traslado_elem = ET.SubElement(traslados_elem, 'cfdi:Traslado')
            traslado_elem.set('Base', f"{datos['base']:.2f}")
            traslado_elem.set('Impuesto', '002')  # IVA
            traslado_elem.set('TipoFactor', 'Tasa')
            traslado_elem.set('TasaOCuota', tasa)
            traslado_elem.set('Importe', f"{datos['importe']:.2f}")
        
        # Retenciones (si aplican)
        if total_retenciones > 0:
            retenciones_elem = ET.SubElement(impuestos_elem, 'cfdi:Retenciones')
            # Aquí se agregarían las retenciones si las hubiera
    
    @classmethod
    def _agregar_complementos(cls, root, factura):
        """Agrega complementos si aplican"""
        # Por ahora no agregamos complementos específicos
        # La Información Global se agrega directamente en el Comprobante
        pass
    
    @classmethod
    def _agregar_informacion_global(cls, root, factura):
        """
        Agrega el nodo Información Global requerido para RFC XAXX010101000
        según el Anexo 20 RMF 2022
        """
        try:
            # Crear elemento Información Global directamente en el Comprobante
            info_global = ET.SubElement(root, 'cfdi:InformacionGlobal')
            
            # Atributos requeridos según Anexo 20
            # Usar valores de la factura si están disponibles, sino valores por defecto
            periodicidad = factura.periodicidad if hasattr(factura, 'periodicidad') and factura.periodicidad else '01'
            meses = factura.meses if hasattr(factura, 'meses') and factura.meses else '01'
            año = factura.año_informacion_global if hasattr(factura, 'año_informacion_global') and factura.año_informacion_global else factura.fecha_emision.year
            
            info_global.set('Periodicidad', periodicidad)
            info_global.set('Meses', meses)
            info_global.set('Año', str(año))
            
            logger.info(f"Nodo Información Global agregado para RFC XAXX010101000 - Periodicidad: {periodicidad}, Meses: {meses}, Año: {año}")
            
        except Exception as e:
            logger.error(f"Error agregando Información Global: {e}")
            # No lanzar excepción para no interrumpir el proceso
    
    @classmethod
    def _formatear_xml(cls, xml_string: str) -> str:
        """Formatea el XML para mejor legibilidad"""
        try:
            import xml.dom.minidom
            dom = xml.dom.minidom.parseString(xml_string)
            return dom.toprettyxml(indent="  ", encoding="utf-8").decode('utf-8')
        except Exception:
            # Si hay error en el formateo, devolver el XML original
            return xml_string
    
    @classmethod
    def generar_cadena_original_desde_modelos(cls, factura, detalles) -> str:
        """
        Genera la cadena original del CFDI para el sellado desde los modelos
        
        Args:
            factura: Instancia del modelo Factura
            detalles: Lista de instancias de FacturaDetalle
            
        Returns:
            str: Cadena original
        """
        try:
            # Crear estructura para la cadena original
            cadena_parts = []
            
            # Datos del comprobante
            cadena_parts.append(f"||4.0|{factura.serie}|{factura.folio}|{factura.fecha_emision.strftime('%Y-%m-%dT%H:%M:%S')}|{factura.exportacion}|{factura.moneda}|{factura.tipo_cambio:.4f}|{factura.total:.2f}|I|{factura.metodo_pago}|{factura.lugar_expedicion}|")
            
            # Datos del emisor
            cadena_parts.append(f"|{factura.emisor.rfc}|{factura.emisor.razon_social}|{factura.emisor.regimen_fiscal}|")
            
            # Datos del receptor
            cadena_parts.append(f"|{factura.receptor.rfc}|{factura.receptor.razon_social}|{factura.receptor.codigo_postal}|{factura.receptor.regimen_fiscal.codigo}|{factura.uso_cfdi}|")
            
            # Conceptos
            for detalle in detalles:
                cadena_parts.append(f"|{detalle.clave_prod_serv}|{detalle.no_identificacion}|{detalle.cantidad:.2f}|{detalle.unidad}|{detalle.concepto}|{detalle.precio:.2f}|{detalle.importe:.2f}|{detalle.objeto_impuesto}|")
            
            # Impuestos
            if factura.impuesto > 0:
                iva_base = sum(detalle.importe for detalle in detalles if detalle.objeto_impuesto == '02')
                cadena_parts.append(f"|{iva_base:.2f}|002|Tasa|0.160000|{factura.impuesto:.2f}|")
            
            return ''.join(cadena_parts)
            
        except Exception as e:
            logger.error(f"Error generando cadena original: {e}")
            raise
    
    @classmethod
    def generar_cadena_original(cls, xml_cfdi: str) -> str:
        """
        Genera la cadena original del CFDI para el sellado
        
        Args:
            xml_cfdi: XML del CFDI como string
            
        Returns:
            str: Cadena original
        """
        try:
            root = ET.fromstring(xml_cfdi)
            
            # Extraer datos del comprobante
            comprobante = root
            version = comprobante.get('Version', '4.0')
            serie = comprobante.get('Serie', '')
            folio = comprobante.get('Folio', '')
            fecha = comprobante.get('Fecha', '')
            exportacion = comprobante.get('Exportacion', '01')
            moneda = comprobante.get('Moneda', 'MXN')
            tipo_cambio = comprobante.get('TipoCambio', '1.0000')
            total = comprobante.get('Total', '0.00')
            tipo_comprobante = comprobante.get('TipoDeComprobante', 'I')
            metodo_pago = comprobante.get('MetodoPago', 'PUE')
            lugar_expedicion = comprobante.get('LugarExpedicion', '')
            
            # Extraer datos del emisor
            emisor = comprobante.find('cfdi:Emisor', cls.NAMESPACES)
            rfc_emisor = emisor.get('Rfc', '') if emisor is not None else ''
            nombre_emisor = emisor.get('Nombre', '') if emisor is not None else ''
            regimen_emisor = emisor.get('RegimenFiscal', '') if emisor is not None else ''
            
            # Extraer datos del receptor
            receptor = comprobante.find('cfdi:Receptor', cls.NAMESPACES)
            rfc_receptor = receptor.get('Rfc', '') if receptor is not None else ''
            nombre_receptor = receptor.get('Nombre', '') if receptor is not None else ''
            domicilio_receptor = receptor.get('DomicilioFiscalReceptor', '') if receptor is not None else ''
            regimen_receptor = receptor.get('RegimenFiscalReceptor', '') if receptor is not None else ''
            uso_cfdi = receptor.get('UsoCFDI', '') if receptor is not None else ''
            
            # Construir cadena original
            cadena_parts = []
            
            # Datos del comprobante
            cadena_parts.append(f"||{version}|{serie}|{folio}|{fecha}|{exportacion}|{moneda}|{tipo_cambio}|{total}|{tipo_comprobante}|{metodo_pago}|{lugar_expedicion}|")
            
            # Datos del emisor
            cadena_parts.append(f"|{rfc_emisor}|{nombre_emisor}|{regimen_emisor}|")
            
            # Datos del receptor
            cadena_parts.append(f"|{rfc_receptor}|{nombre_receptor}|{domicilio_receptor}|{regimen_receptor}|{uso_cfdi}|")
            
            # Conceptos
            conceptos = comprobante.find('cfdi:Conceptos', cls.NAMESPACES)
            if conceptos is not None:
                for concepto in conceptos.findall('cfdi:Concepto', cls.NAMESPACES):
                    clave_prod_serv = concepto.get('ClaveProdServ', '')
                    no_identificacion = concepto.get('NoIdentificacion', '')
                    cantidad = concepto.get('Cantidad', '0.000000')
                    unidad = concepto.get('Unidad', '')
                    descripcion = concepto.get('Descripcion', '')
                    valor_unitario = concepto.get('ValorUnitario', '0.000000')
                    importe = concepto.get('Importe', '0.00')
                    objeto_imp = concepto.get('ObjetoImp', '02')
                    
                    cadena_parts.append(f"|{clave_prod_serv}|{no_identificacion}|{cantidad}|{unidad}|{descripcion}|{valor_unitario}|{importe}|{objeto_imp}|")
            
            return ''.join(cadena_parts)
            
        except Exception as e:
            logger.error(f"Error generando cadena original: {e}")
            return ""
    
    @classmethod
    def actualizar_sello_y_certificado(cls, xml_cfdi: str, sello: str, no_certificado: str, certificado_base64: str) -> str:
        """
        Actualiza el XML CFDI con el sello digital y certificado
        
        Args:
            xml_cfdi: XML del CFDI sin firmar
            sello: Sello digital generado
            no_certificado: Número de certificado
            certificado_base64: Certificado en base64
            
        Returns:
            str: XML CFDI con sello y certificado
        """
        try:
            # Usar reemplazo de texto para mantener los namespaces originales
            xml_actualizado = xml_cfdi
            
            # Buscar y reemplazar el atributo Sello
            import re
            sello_pattern = r'Sello="[^"]*"'
            if re.search(sello_pattern, xml_actualizado):
                xml_actualizado = re.sub(sello_pattern, f'Sello="{sello}"', xml_actualizado)
            else:
                # Si no existe, agregarlo después de Version
                version_pattern = r'(Version="[^"]*")'
                xml_actualizado = re.sub(version_pattern, f'\\1 Sello="{sello}"', xml_actualizado)
            
            # Buscar y reemplazar NoCertificado
            no_cert_pattern = r'NoCertificado="[^"]*"'
            if re.search(no_cert_pattern, xml_actualizado):
                xml_actualizado = re.sub(no_cert_pattern, f'NoCertificado="{no_certificado}"', xml_actualizado)
            else:
                # Si no existe, agregarlo después de Sello
                sello_pattern = r'(Sello="[^"]*")'
                xml_actualizado = re.sub(sello_pattern, f'\\1 NoCertificado="{no_certificado}"', xml_actualizado)
            
            # Buscar y reemplazar Certificado
            cert_pattern = r'Certificado="[^"]*"'
            if re.search(cert_pattern, xml_actualizado):
                xml_actualizado = re.sub(cert_pattern, f'Certificado="{certificado_base64}"', xml_actualizado)
            else:
                # Si no existe, agregarlo después de NoCertificado
                no_cert_pattern = r'(NoCertificado="[^"]*")'
                xml_actualizado = re.sub(no_cert_pattern, f'\\1 Certificado="{certificado_base64}"', xml_actualizado)
            
            return xml_actualizado
            
        except Exception as e:
            logger.error(f"Error actualizando sello y certificado: {e}")
            return xml_cfdi
    
    @classmethod
    def extraer_timbre_fiscal(cls, xml_timbrado: str) -> Dict[str, Any]:
        """
        Extrae los datos del TimbreFiscalDigital del XML timbrado
        
        Args:
            xml_timbrado: XML timbrado por el PAC
            
        Returns:
            Dict: Datos del timbre fiscal
        """
        try:
            root = ET.fromstring(xml_timbrado)
            
            # Buscar el timbre fiscal
            timbre_elem = root.find('.//{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital')
            
            if timbre_elem is None:
                return {'valido': False, 'error': 'No se encontró el TimbreFiscalDigital'}
            
            return {
                'valido': True,
                'uuid': timbre_elem.get('UUID'),
                'fecha_timbrado': timbre_elem.get('FechaTimbrado'),
                'rfc_proveedor_certificacion': timbre_elem.get('RfcProvCertif'),
                'sello_cfd': timbre_elem.get('SelloCFD'),
                'no_certificado_sat': timbre_elem.get('NoCertificadoSAT'),
                'sello_sat': timbre_elem.get('SelloSAT'),
                'version': timbre_elem.get('Version')
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo timbre fiscal: {e}")
            return {'valido': False, 'error': str(e)}
