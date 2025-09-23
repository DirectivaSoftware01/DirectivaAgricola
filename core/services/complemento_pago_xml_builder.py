"""
Constructor de XML para Complemento de Pago CFDI 4.0
Genera el XML del complemento de pago con estructura pago20:Pagos
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from ..utils.timezone_utils import obtener_fecha_actual_mexico, formatear_fecha_cfdi
from decimal import Decimal
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ComplementoPagoXMLBuilder:
    """
    Constructor de XML para Complemento de Pago CFDI 4.0 según Anexo 20 RMF 2022.
    Genera XML válido con namespace correcto y validación XSD oficial.
    """
    
    # Namespaces CFDI 4.0 y Pagos 2.0
    NAMESPACES = {
        'cfdi': 'http://www.sat.gob.mx/cfd/4',
        'pago20': 'http://www.sat.gob.mx/Pagos20',
        'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    # Schema locations según Anexo 20
    SCHEMA_LOCATIONS = {
        'http://www.sat.gob.mx/cfd/4': 'http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd',
        'http://www.sat.gob.mx/Pagos20': 'http://www.sat.gob.mx/sitio_internet/cfd/Pagos/Pagos20.xsd',
        'http://www.sat.gob.mx/TimbreFiscalDigital': 'http://www.sat.gob.mx/sitio_internet/cfd/TimbreFiscalDigital/TimbreFiscalDigitalv11.xsd'
    }
    
    # Versión CFDI según Anexo 20
    CFDI_VERSION = "4.0"
    PAGOS_VERSION = "2.0"
    
    @classmethod
    def construir_xml_complemento_pago(cls, factura, pago_data: Dict[str, Any], certificado_data: Dict[str, Any], sello: str) -> str:
        """
        Construye el XML completo del Complemento de Pago CFDI 4.0
        
        Args:
            factura: Instancia del modelo Factura (factura PPD)
            pago_data: Datos del pago del formulario
            certificado_data: Datos del certificado
            sello: Sello digital generado
            
        Returns:
            str: XML del Complemento de Pago como string
        """
        try:
            # Crear elemento raíz con namespace correcto
            root = ET.Element('{http://www.sat.gob.mx/cfd/4}Comprobante')
            
            # Agregar namespaces (en el orden correcto según la estructura proporcionada)
            root.set('xmlns:cfdi', cls.NAMESPACES['cfdi'])
            root.set('xmlns:xsi', cls.NAMESPACES['xsi'])
            root.set('xmlns:pago20', cls.NAMESPACES['pago20'])
            
            # Schema locations (solo los necesarios para complemento de pago)
            schema_locations = [
                f"{cls.NAMESPACES['cfdi']} http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd",
                f"{cls.NAMESPACES['pago20']} http://www.sat.gob.mx/sitio_internet/cfd/Pagos/Pagos20.xsd"
            ]
            root.set('xsi:schemaLocation', ' '.join(schema_locations))
            
            # Atributos del comprobante (en el orden correcto según la estructura proporcionada)
            root.set('Sello', sello)
            root.set('Certificado', certificado_data.get('certificado_base64', ''))
            root.set('LugarExpedicion', pago_data.get('lugar_expedicion', '85140'))
            root.set('Folio', pago_data.get('folio', '24A'))
            root.set('TipoDeComprobante', 'P')  # P - Pago
            root.set('Exportacion', '01')  # 01 - No aplica
            root.set('Total', '0')
            root.set('Serie', pago_data.get('serie', 'A'))
            root.set('Moneda', 'XXX')  # Siempre XXX para complementos de pago
            root.set('SubTotal', '0')
            root.set('NoCertificado', certificado_data.get('no_certificado', ''))
            # Usar fecha actual en zona horaria de México (como en facturación)
            fecha_actual = obtener_fecha_actual_mexico(factura.lugar_expedicion)
            root.set('Fecha', formatear_fecha_cfdi(fecha_actual))
            root.set('Version', cls.CFDI_VERSION)
            
            # Debug: verificar certificado
            logger.info(f"Certificado data recibido: {certificado_data}")
            logger.info(f"Certificado a usar: {certificado_data.get('certificado_base64', '')[:100]}...")
            
            # Emisor
            emisor = ET.SubElement(root, '{http://www.sat.gob.mx/cfd/4}Emisor')
            emisor.set('Rfc', factura.emisor.rfc)
            emisor.set('Nombre', factura.emisor.razon_social)
            emisor.set('RegimenFiscal', str(factura.emisor.regimen_fiscal) if factura.emisor.regimen_fiscal else '')
            
            # Receptor
            receptor = ET.SubElement(root, '{http://www.sat.gob.mx/cfd/4}Receptor')
            receptor.set('Rfc', factura.receptor.rfc)
            receptor.set('Nombre', factura.receptor.razon_social)
            receptor.set('DomicilioFiscalReceptor', factura.receptor.codigo_postal)
            receptor.set('RegimenFiscalReceptor', factura.receptor.regimen_fiscal.codigo if factura.receptor.regimen_fiscal else '')
            receptor.set('UsoCFDI', 'CP01')  # CP01 es obligatorio para complementos de pago
            
            # Conceptos (obligatorio para CFDI de pago)
            conceptos = ET.SubElement(root, '{http://www.sat.gob.mx/cfd/4}Conceptos')
            concepto = ET.SubElement(conceptos, '{http://www.sat.gob.mx/cfd/4}Concepto')
            concepto.set('ClaveProdServ', '84111506')  # Servicios de pago
            # NoIdentificacion y Unidad no se deben registrar en complementos de pago
            concepto.set('Cantidad', '1')
            concepto.set('ClaveUnidad', 'ACT')
            concepto.set('Descripcion', 'Pago')
            concepto.set('ValorUnitario', '0')
            concepto.set('Importe', '0')
            concepto.set('ObjetoImp', '01')  # 01 - No objeto del impuesto
            
            # Complemento - Pagos
            complemento = ET.SubElement(root, '{http://www.sat.gob.mx/cfd/4}Complemento')
            pagos = ET.SubElement(complemento, '{http://www.sat.gob.mx/Pagos20}Pagos')
            pagos.set('Version', cls.PAGOS_VERSION)
            
            # Totales de pagos
            totales = ET.SubElement(pagos, '{http://www.sat.gob.mx/Pagos20}Totales')
            totales.set('MontoTotalPagos', str(pago_data.get('monto', 0)))

            # Calcular totales de impuestos - siempre incluir al menos uno de los campos requeridos
            base_imp = float(pago_data.get('base', 0))
            importe_imp = float(pago_data.get('importe', 0))
            tipo_factor = pago_data.get('tipo_factor', 'Tasa')
            tasa = float(pago_data.get('tasa', 0.16))
            
            logger.info(f"Base impuesto: {base_imp}, Importe impuesto: {importe_imp}, Tipo factor: {tipo_factor}, Tasa: {tasa}")
            
            # Determinar qué campo de total usar según el tipo de impuesto
            if base_imp > 0:
                if tipo_factor == 'Exento':
                    totales.set('TotalTrasladosBaseIVAExento', str(base_imp))
                    logger.info(f"TotalTrasladosBaseIVAExento agregado: {base_imp}")
                elif tipo_factor == 'Tasa0' or tasa == 0.0:  # Tasa Cero
                    totales.set('TotalTrasladosBaseIVA0', str(base_imp))
                    totales.set('TotalTrasladosImpuestoIVA0', str(importe_imp))
                    logger.info(f"TotalTrasladosBaseIVA0 agregado: {base_imp}, TotalTrasladosImpuestoIVA0: {importe_imp}")
                elif tipo_factor == 'Tasa' and tasa == 0.08:  # IVA 8%
                    totales.set('TotalTrasladosBaseIVA8', str(base_imp))
                    totales.set('TotalTrasladosImpuestoIVA8', str(importe_imp))
                    logger.info(f"TotalTrasladosBaseIVA8 agregado: {base_imp}, TotalTrasladosImpuestoIVA8: {importe_imp}")
                elif tipo_factor == 'Tasa' and tasa == 0.16:  # IVA 16%
                    totales.set('TotalTrasladosBaseIVA16', str(base_imp))
                    totales.set('TotalTrasladosImpuestoIVA16', str(importe_imp))
                    logger.info(f"TotalTrasladosBaseIVA16 agregado: {base_imp}, TotalTrasladosImpuestoIVA16: {importe_imp}")
                else:  # Por defecto (IVA 16%)
                    totales.set('TotalTrasladosBaseIVA16', str(base_imp))
                    totales.set('TotalTrasladosImpuestoIVA16', str(importe_imp))
                    logger.info(f"TotalTrasladosBaseIVA16 agregado (por defecto): {base_imp}, TotalTrasladosImpuestoIVA16: {importe_imp}")
            else:
                # Si no hay base, agregar al menos un campo con valor 0 para cumplir con la validación
                totales.set('TotalTrasladosBaseIVA16', '0')
                totales.set('TotalTrasladosImpuestoIVA16', '0')
                logger.info("Campos de totales agregados con valor 0 para cumplir validación")
            
            # Pago individual
            pago = ET.SubElement(pagos, '{http://www.sat.gob.mx/Pagos20}Pago')
            # Usar fecha de pago en zona horaria de México
            if 'fecha_pago' in pago_data and pago_data['fecha_pago']:
                # Si viene fecha del formulario, usar esa fecha pero en zona horaria de México
                fecha_pago_str = pago_data['fecha_pago']
                if 'T' not in fecha_pago_str:
                    fecha_pago_str += 'T00:00:00'
                # Convertir a datetime y aplicar zona horaria de México
                fecha_pago_dt = datetime.fromisoformat(fecha_pago_str.replace('Z', '+00:00'))
                zona_horaria = obtener_fecha_actual_mexico(factura.lugar_expedicion).tzinfo
                fecha_pago_dt = fecha_pago_dt.replace(tzinfo=zona_horaria)
                fecha_pago = formatear_fecha_cfdi(fecha_pago_dt)
            else:
                # Si no hay fecha, usar fecha actual en zona horaria de México
                fecha_pago = formatear_fecha_cfdi(obtener_fecha_actual_mexico(factura.lugar_expedicion))
            pago.set('FechaPago', fecha_pago)
            pago.set('FormaDePagoP', pago_data.get('forma_pago', '03'))
            pago.set('MonedaP', pago_data.get('moneda_p', 'MXN'))
            pago.set('TipoCambioP', str(pago_data.get('tipo_cambio', 1)))
            pago.set('Monto', str(pago_data.get('monto', 0)))
            
            # Documento relacionado
            docto_rel = ET.SubElement(pago, '{http://www.sat.gob.mx/Pagos20}DoctoRelacionado')
            docto_rel.set('IdDocumento', pago_data.get('id_documento', ''))
            docto_rel.set('Serie', pago_data.get('serie_dr', ''))
            docto_rel.set('Folio', pago_data.get('folio_dr', ''))
            docto_rel.set('MonedaDR', pago_data.get('moneda_dr', 'MXN'))
            docto_rel.set('EquivalenciaDR', str(pago_data.get('equivalencia_dr', 1)))
            docto_rel.set('NumParcialidad', str(pago_data.get('num_parcialidad', 1)))
            docto_rel.set('ImpSaldoAnt', str(pago_data.get('imp_saldo_ant', 0)))
            docto_rel.set('ImpPagado', str(pago_data.get('imp_pagado', 0)))
            docto_rel.set('ImpSaldoInsoluto', str(pago_data.get('imp_saldo_insoluto', 0)))
            docto_rel.set('ObjetoImpDR', pago_data.get('objeto_imp_dr', '02'))
            
            # Impuestos del documento relacionado (siempre se incluyen, incluso si es tasa cero)
            if base_imp > 0:  # Solo verificamos que haya base, no importe
                tipo_factor = pago_data.get('tipo_factor', 'Tasa')
                tasa = pago_data.get('tasa', 0.16)
                
                # Para tasa cero, usar 'Tasa' con tasa 0.000000 (no 'Tasa0')
                if tipo_factor == 'Tasa0':
                    tipo_factor = 'Tasa'
                    tasa = 0.000000
                
                logger.info(f"Agregando ImpuestosDR: Base={base_imp}, Impuesto={pago_data.get('impuesto', '002')}, TipoFactor={tipo_factor}, Tasa={tasa}, Importe={importe_imp}")
                impuestos_dr = ET.SubElement(docto_rel, '{http://www.sat.gob.mx/Pagos20}ImpuestosDR')
                traslados_dr = ET.SubElement(impuestos_dr, '{http://www.sat.gob.mx/Pagos20}TrasladosDR')
                traslado_dr = ET.SubElement(traslados_dr, '{http://www.sat.gob.mx/Pagos20}TrasladoDR')
                traslado_dr.set('BaseDR', str(base_imp))
                traslado_dr.set('ImpuestoDR', pago_data.get('impuesto', '002'))
                traslado_dr.set('TipoFactorDR', tipo_factor)
                traslado_dr.set('TasaOCuotaDR', f"{tasa:.6f}")
                traslado_dr.set('ImporteDR', str(importe_imp))
            else:
                logger.info("No se agregaron ImpuestosDR porque base_imp es 0")
            
            # Impuestos del pago (siempre se incluyen, incluso si es tasa cero)
            if base_imp > 0:  # Solo verificamos que haya base, no importe
                tipo_factor = pago_data.get('tipo_factor', 'Tasa')
                tasa = pago_data.get('tasa', 0.16)
                
                # Para tasa cero, usar 'Tasa' con tasa 0.000000 (no 'Tasa0')
                if tipo_factor == 'Tasa0':
                    tipo_factor = 'Tasa'
                    tasa = 0.000000
                
                logger.info(f"Agregando ImpuestosP: Base={base_imp}, Impuesto={pago_data.get('impuesto', '002')}, TipoFactor={tipo_factor}, Tasa={tasa}, Importe={importe_imp}")
                impuestos_p = ET.SubElement(pago, '{http://www.sat.gob.mx/Pagos20}ImpuestosP')
                traslados_p = ET.SubElement(impuestos_p, '{http://www.sat.gob.mx/Pagos20}TrasladosP')
                traslado_p = ET.SubElement(traslados_p, '{http://www.sat.gob.mx/Pagos20}TrasladoP')
                traslado_p.set('BaseP', str(base_imp))
                traslado_p.set('ImpuestoP', pago_data.get('impuesto', '002'))
                traslado_p.set('TipoFactorP', tipo_factor)
                traslado_p.set('TasaOCuotaP', f"{tasa:.6f}")
                traslado_p.set('ImporteP', str(importe_imp))
            else:
                logger.info("No se agregaron ImpuestosP porque base_imp es 0")
            
            # Convertir a string con formato
            xml_str = ET.tostring(root, encoding='unicode', method='xml')
            
            # Reemplazar los namespaces para que aparezcan correctamente
            # Solo reemplazar si existen los namespaces ns0, ns1, etc.
            if 'ns0:' in xml_str:
                xml_str = xml_str.replace('ns0:', 'cfdi:')
            if 'ns1:' in xml_str:
                xml_str = xml_str.replace('ns1:', 'pago20:')
            if 'ns2:' in xml_str:
                xml_str = xml_str.replace('ns2:', 'tfd:')
            
            # Remover namespaces duplicados si existen
            import re
            # Remover xmlns:ns0 y xmlns:ns1 si existen
            xml_str = re.sub(r'\s+xmlns:ns\d+="[^"]*"', '', xml_str)
            
            # Formatear XML con indentación
            from xml.dom import minidom
            dom = minidom.parseString(xml_str)
            xml_formateado = dom.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')
            
            # Remover línea vacía del inicio
            lines = xml_formateado.split('\n')
            xml_final = '\n'.join([line for line in lines if line.strip()])
            
            # Log del XML generado para debugging
            logger.info(f"XML generado completo: {xml_final}")
            
            logger.info(f"XML de complemento de pago generado exitosamente para factura {factura.folio}")
            logger.debug(f"XML generado: {xml_final[:1000]}...")
            return xml_final
            
        except Exception as e:
            logger.error(f"Error al generar XML de complemento de pago: {str(e)}")
            raise
    
    @classmethod
    def validar_datos_pago(cls, pago_data: Dict[str, Any]) -> List[str]:
        """
        Valida los datos del pago antes de generar el XML
        
        Args:
            pago_data: Datos del pago
            
        Returns:
            List[str]: Lista de errores encontrados
        """
        errores = []
        
        # Validar campos requeridos
        campos_requeridos = [
            'monto', 'fecha_pago', 'forma_pago', 'id_documento',
            'serie_dr', 'folio_dr', 'num_parcialidad'
        ]
        
        for campo in campos_requeridos:
            if not pago_data.get(campo):
                errores.append(f"El campo {campo} es requerido")
        
        # Validar monto
        try:
            monto = float(pago_data.get('monto', 0))
            if monto <= 0:
                errores.append("El monto debe ser mayor a cero")
        except (ValueError, TypeError):
            errores.append("El monto debe ser un número válido")
        
        # Validar fecha
        try:
            datetime.fromisoformat(pago_data.get('fecha_pago', '').replace('Z', '+00:00'))
        except (ValueError, TypeError):
            errores.append("La fecha de pago debe tener formato válido")
        
        return errores
    
    @classmethod
    def generar_cadena_original_desde_modelos(cls, factura, pago_data: Dict[str, Any]) -> str:
        """
        Genera la cadena original del complemento de pago desde los modelos
        (similar a como se hace en facturación)

        Args:
            factura: Instancia del modelo Factura
            pago_data: Datos del pago

        Returns:
            str: Cadena original
        """
        try:
            # Construir la cadena original según el Anexo 20 para complemento de pago
            cadena_parts = []

            # Datos del comprobante (usando datos de la factura, no del formulario)
            fecha_actual = formatear_fecha_cfdi(obtener_fecha_actual_mexico(factura.lugar_expedicion))
            cadena_parts.append(f"||{cls.CFDI_VERSION}")
            cadena_parts.append(f"|{factura.serie}")
            cadena_parts.append(f"|{factura.folio}")
            cadena_parts.append(f"|{fecha_actual}")
            cadena_parts.append(f"|P")  # TipoDeComprobante = P (Pago)
            cadena_parts.append(f"|01")  # Exportacion
            cadena_parts.append(f"|0")  # Total
            cadena_parts.append(f"|XXX")  # Moneda siempre XXX para complementos
            cadena_parts.append(f"|0")  # SubTotal
            cadena_parts.append(f"|{factura.lugar_expedicion}")
            cadena_parts.append(f"|")  # Sello (se llenará después)
            cadena_parts.append(f"|")  # NoCertificado (se llenará después)
            cadena_parts.append(f"|")  # Certificado (se llenará después)

            # Emisor (usando datos de la factura)
            cadena_parts.append(f"|{factura.emisor.rfc}")
            cadena_parts.append(f"|{factura.emisor.razon_social}")
            cadena_parts.append(f"|{str(factura.emisor.regimen_fiscal) if factura.emisor.regimen_fiscal else ''}")

            # Receptor (usando datos de la factura)
            cadena_parts.append(f"|{factura.receptor.rfc}")
            cadena_parts.append(f"|{factura.receptor.razon_social}")
            cadena_parts.append(f"|{factura.receptor.codigo_postal}")
            cadena_parts.append(f"|{factura.receptor.regimen_fiscal.codigo if factura.receptor.regimen_fiscal else ''}")
            cadena_parts.append(f"|CP01")  # CP01 es obligatorio para complementos de pago

            # Conceptos (fijos para complemento de pago)
            cadena_parts.append(f"|84111506")  # ClaveProdServ
            cadena_parts.append(f"|")  # NoIdentificacion (vacío para complementos de pago)
            cadena_parts.append(f"|1")  # Cantidad
            cadena_parts.append(f"|ACT")  # ClaveUnidad
            cadena_parts.append(f"|")  # Unidad (vacío para complementos de pago)
            cadena_parts.append(f"|Pago")  # Descripcion
            cadena_parts.append(f"|0")  # ValorUnitario
            cadena_parts.append(f"|0")  # Importe
            cadena_parts.append(f"|01")  # ObjetoImp

            # Complemento - Pagos
            cadena_parts.append(f"|{cls.PAGOS_VERSION}")  # Version de Pagos

            # Totales
            monto_total = pago_data.get('monto', 0)
            cadena_parts.append(f"|{monto_total}")  # MontoTotalPagos

            # Calcular totales de impuestos - usar la misma lógica que en el XML
            base_imp = float(pago_data.get('base', 0))
            importe_imp = float(pago_data.get('importe', 0))
            tipo_factor = pago_data.get('tipo_factor', 'Tasa')
            tasa = float(pago_data.get('tasa', 0.16))
            
            if base_imp > 0:
                if tipo_factor == 'Exento':
                    cadena_parts.append(f"|{base_imp}")  # TotalTrasladosBaseIVAExento
                elif tipo_factor == 'Tasa0' or tasa == 0.0:  # Tasa Cero
                    cadena_parts.append(f"|{base_imp}")  # TotalTrasladosBaseIVA0
                    cadena_parts.append(f"|{importe_imp}")  # TotalTrasladosImpuestoIVA0
                elif tipo_factor == 'Tasa' and tasa == 0.08:  # IVA 8%
                    cadena_parts.append(f"|{base_imp}")  # TotalTrasladosBaseIVA8
                    cadena_parts.append(f"|{importe_imp}")  # TotalTrasladosImpuestoIVA8
                elif tipo_factor == 'Tasa' and tasa == 0.16:  # IVA 16%
                    cadena_parts.append(f"|{base_imp}")  # TotalTrasladosBaseIVA16
                    cadena_parts.append(f"|{importe_imp}")  # TotalTrasladosImpuestoIVA16
                else:  # Por defecto (IVA 16%)
                    cadena_parts.append(f"|{base_imp}")  # TotalTrasladosBaseIVA16
                    cadena_parts.append(f"|{importe_imp}")  # TotalTrasladosImpuestoIVA16
            else:
                # Si no hay base, agregar valores 0 para cumplir con la validación
                cadena_parts.append(f"|0")  # TotalTrasladosBaseIVA16
                cadena_parts.append(f"|0")  # TotalTrasladosImpuestoIVA16

            # Pago individual - usar la misma lógica de fecha que en el XML
            if 'fecha_pago' in pago_data and pago_data['fecha_pago']:
                fecha_pago_str = pago_data['fecha_pago']
                if 'T' not in fecha_pago_str:
                    fecha_pago_str += 'T00:00:00'
                fecha_pago_dt = datetime.fromisoformat(fecha_pago_str.replace('Z', '+00:00'))
                zona_horaria = obtener_fecha_actual_mexico(factura.lugar_expedicion).tzinfo
                fecha_pago_dt = fecha_pago_dt.replace(tzinfo=zona_horaria)
                fecha_pago = formatear_fecha_cfdi(fecha_pago_dt)
            else:
                fecha_pago = formatear_fecha_cfdi(obtener_fecha_actual_mexico(factura.lugar_expedicion))
            cadena_parts.append(f"|{fecha_pago}")
            cadena_parts.append(f"|{pago_data.get('forma_pago', '03')}")
            cadena_parts.append(f"|{pago_data.get('moneda_p', 'MXN')}")
            cadena_parts.append(f"|{pago_data.get('tipo_cambio', 1)}")
            cadena_parts.append(f"|{monto_total}")

            # Documento relacionado (usando datos de la factura)
            cadena_parts.append(f"|{factura.uuid}")  # IdDocumento = UUID de la factura
            cadena_parts.append(f"|{factura.serie}")  # Serie de la factura
            cadena_parts.append(f"|{factura.folio}")  # Folio de la factura
            cadena_parts.append(f"|{factura.moneda}")  # Moneda de la factura
            cadena_parts.append(f"|{pago_data.get('equivalencia_dr', 1)}")
            cadena_parts.append(f"|{pago_data.get('num_parcialidad', 1)}")
            cadena_parts.append(f"|{pago_data.get('imp_saldo_ant', 0)}")
            cadena_parts.append(f"|{pago_data.get('imp_pagado', 0)}")
            cadena_parts.append(f"|{pago_data.get('imp_saldo_insoluto', 0)}")
            cadena_parts.append(f"|{pago_data.get('objeto_imp_dr', '02')}")

            # Impuestos del documento relacionado
            if base_imp > 0:
                cadena_parts.append(f"|{base_imp}")  # BaseDR
                cadena_parts.append(f"|{pago_data.get('impuesto', '002')}")  # ImpuestoDR
                cadena_parts.append(f"|{pago_data.get('tipo_factor', 'Tasa')}")  # TipoFactorDR
                cadena_parts.append(f"|{pago_data.get('tasa', 0.16)}")  # TasaOCuotaDR
                cadena_parts.append(f"|{importe_imp}")  # ImporteDR

            # Impuestos del pago
            if base_imp > 0:
                cadena_parts.append(f"|{base_imp}")  # BaseP
                cadena_parts.append(f"|{pago_data.get('impuesto', '002')}")  # ImpuestoP
                cadena_parts.append(f"|{pago_data.get('tipo_factor', 'Tasa')}")  # TipoFactorP
                cadena_parts.append(f"|{pago_data.get('tasa', 0.16)}")  # TasaOCuotaP
                cadena_parts.append(f"|{importe_imp}")  # ImporteP

            # Unir todas las partes
            cadena_original = ''.join(cadena_parts)

            logger.info(f"Cadena original generada desde modelos: {cadena_original[:200]}...")
            return cadena_original

        except Exception as e:
            logger.error(f"Error generando cadena original desde modelos: {e}")
            return ""
    
    @classmethod
    def generar_cadena_original(cls, xml_cfdi: str) -> str:
        """
        Genera la cadena original del XML CFDI para el sello digital
        
        Args:
            xml_cfdi: XML del CFDI como string
            
        Returns:
            str: Cadena original para el sello digital
        """
        try:
            # Parsear el XML
            root = ET.fromstring(xml_cfdi)
            
            # Extraer elementos en el orden requerido para la cadena original
            cadena_parts = []
            
            # Información del comprobante
            cadena_parts.append(f"||{root.get('Version', '')}")
            cadena_parts.append(f"|{root.get('Serie', '')}")
            cadena_parts.append(f"|{root.get('Folio', '')}")
            cadena_parts.append(f"|{root.get('Fecha', '')}")
            cadena_parts.append(f"|{root.get('Sello', '')}")
            cadena_parts.append(f"|{root.get('FormaPago', '')}")
            cadena_parts.append(f"|{root.get('NoCertificado', '')}")
            cadena_parts.append(f"|{root.get('SubTotal', '')}")
            cadena_parts.append(f"|{root.get('Descuento', '')}")
            cadena_parts.append(f"|{root.get('Moneda', '')}")
            cadena_parts.append(f"|{root.get('TipoCambio', '')}")
            cadena_parts.append(f"|{root.get('Total', '')}")
            cadena_parts.append(f"|{root.get('TipoDeComprobante', '')}")
            cadena_parts.append(f"|{root.get('Exportacion', '')}")
            cadena_parts.append(f"|{root.get('MetodoPago', '')}")
            cadena_parts.append(f"|{root.get('LugarExpedicion', '')}")
            cadena_parts.append(f"|{root.get('Confirmacion', '')}")
            
            # Información del emisor
            emisor = root.find('.//{http://www.sat.gob.mx/cfd/4}Emisor')
            if emisor is not None:
                cadena_parts.append(f"|{emisor.get('Rfc', '')}")
                cadena_parts.append(f"|{emisor.get('Nombre', '')}")
                cadena_parts.append(f"|{emisor.get('RegimenFiscal', '')}")
            
            # Información del receptor
            receptor = root.find('.//{http://www.sat.gob.mx/cfd/4}Receptor')
            if receptor is not None:
                cadena_parts.append(f"|{receptor.get('Rfc', '')}")
                cadena_parts.append(f"|{receptor.get('Nombre', '')}")
                cadena_parts.append(f"|{receptor.get('DomicilioFiscalReceptor', '')}")
                cadena_parts.append(f"|{receptor.get('RegimenFiscalReceptor', '')}")
                cadena_parts.append(f"|{receptor.get('UsoCFDI', '')}")
            
            # Conceptos
            conceptos = root.find('.//{http://www.sat.gob.mx/cfd/4}Conceptos')
            if conceptos is not None:
                for concepto in conceptos.findall('.//{http://www.sat.gob.mx/cfd/4}Concepto'):
                    cadena_parts.append(f"|{concepto.get('ClaveProdServ', '')}")
                    cadena_parts.append(f"|{concepto.get('NoIdentificacion', '')}")
                    cadena_parts.append(f"|{concepto.get('Cantidad', '')}")
                    cadena_parts.append(f"|{concepto.get('ClaveUnidad', '')}")
                    cadena_parts.append(f"|{concepto.get('Unidad', '')}")
                    cadena_parts.append(f"|{concepto.get('Descripcion', '')}")
                    cadena_parts.append(f"|{concepto.get('ValorUnitario', '')}")
                    cadena_parts.append(f"|{concepto.get('Importe', '')}")
                    cadena_parts.append(f"|{concepto.get('Descuento', '')}")
                    cadena_parts.append(f"|{concepto.get('ObjetoImp', '')}")
            
            # Complemento de pagos
            pagos = root.find('.//{http://www.sat.gob.mx/Pagos20}Pagos')
            if pagos is not None:
                cadena_parts.append(f"|{pagos.get('Version', '')}")
                
                # Totales
                totales = pagos.find('.//{http://www.sat.gob.mx/Pagos20}Totales')
                if totales is not None:
                    cadena_parts.append(f"|{totales.get('TotalTrasladosImpuestoIVA16', '')}")
                    cadena_parts.append(f"|{totales.get('TotalTrasladosBaseIVA16', '')}")
                    cadena_parts.append(f"|{totales.get('MontoTotalPagos', '')}")
                
                # Pagos individuales
                for pago in pagos.findall('.//{http://www.sat.gob.mx/Pagos20}Pago'):
                    cadena_parts.append(f"|{pago.get('FechaPago', '')}")
                    cadena_parts.append(f"|{pago.get('FormaDePagoP', '')}")
                    cadena_parts.append(f"|{pago.get('MonedaP', '')}")
                    cadena_parts.append(f"|{pago.get('TipoCambioP', '')}")
                    cadena_parts.append(f"|{pago.get('Monto', '')}")
                    
                    # Documentos relacionados
                    for docto in pago.findall('.//{http://www.sat.gob.mx/Pagos20}DoctoRelacionado'):
                        cadena_parts.append(f"|{docto.get('IdDocumento', '')}")
                        cadena_parts.append(f"|{docto.get('Serie', '')}")
                        cadena_parts.append(f"|{docto.get('Folio', '')}")
                        cadena_parts.append(f"|{docto.get('MonedaDR', '')}")
                        cadena_parts.append(f"|{docto.get('EquivalenciaDR', '')}")
                        cadena_parts.append(f"|{docto.get('NumParcialidad', '')}")
                        cadena_parts.append(f"|{docto.get('ImpSaldoAnt', '')}")
                        cadena_parts.append(f"|{docto.get('ImpPagado', '')}")
                        cadena_parts.append(f"|{docto.get('ImpSaldoInsoluto', '')}")
                        cadena_parts.append(f"|{docto.get('ObjetoImpDR', '')}")
            
            # Unir todas las partes
            cadena_original = ''.join(cadena_parts)
            
            return cadena_original
            
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
            # Parsear el XML
            root = ET.fromstring(xml_cfdi)
            
            # Actualizar sello y certificado
            root.set('Sello', sello)
            root.set('Certificado', certificado_base64)
            root.set('NoCertificado', no_certificado)
            
            # Convertir de vuelta a string
            return ET.tostring(root, encoding='unicode', xml_declaration=True)
            
        except Exception as e:
            logger.error(f"Error actualizando sello y certificado: {e}")
            return xml_cfdi
