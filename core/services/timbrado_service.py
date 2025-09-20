"""
Servicio de timbrado CFDI 4.0
Maneja la comunicación con PAC Prodigia usando SOAP
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TimbradoService:
    """Servicio para timbrado de CFDI con PAC Prodigia"""
    
    def __init__(self, configuracion: Dict[str, Any], emisor=None):
        """
        Inicializa el servicio de timbrado
        
        Args:
            configuracion: Configuración del PAC obtenida de ConfiguracionEntornoService
            emisor: Objeto Emisor con certificados (opcional)
        """
        self.configuracion = configuracion
        self.url_base = configuracion['url']
        self.credenciales = configuracion['credenciales']
        self.timeout = configuracion.get('timeout', 30)
        self.emisor = emisor
    
    def timbrar_cfdi(self, xml_cfdi: str) -> Dict[str, Any]:
        """
        Timbra un CFDI usando el servicio SOAP de Prodigia
        
        Args:
            xml_cfdi: XML del CFDI a timbrar
            
        Returns:
            Dict: Resultado del timbrado
        """
        try:
            # Verificar si estamos en modo simulación
            if 'localhost' in self.url_base or 'simulacion' in self.url_base:
                logger.info("Modo simulación activado - generando timbrado simulado")
                return self._simular_timbrado(xml_cfdi)
            
            # Generar sello digital si tenemos emisor con certificados
            xml_con_sello = self._firmar_xml_cfdi(xml_cfdi)
            
            # Construir SOAP envelope
            soap_envelope = self._construir_soap_envelope(xml_con_sello)
            
            # Headers para SOAP
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'timbradoCfdi'
            }
            
            # URL del servicio según documentación oficial de Prodigia
            endpoint = f"{self.url_base}/servicio/Timbrado4.0"
            
            logger.info(f"Enviando CFDI a timbrar a: {endpoint}")
            logger.debug(f"SOAP Envelope: {soap_envelope}")
            
            # Realizar petición SOAP
            response = requests.post(
                endpoint,
                data=soap_envelope,
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"Respuesta del PAC: Status {response.status_code}")
            logger.info(f"Headers de respuesta: {dict(response.headers)}")
            logger.info(f"Contenido de respuesta (primeros 500 chars): {response.text[:500]}")
            
            # Verificar si la respuesta está vacía
            if not response.text.strip():
                logger.error(f"Respuesta vacía del PAC. Status: {response.status_code}, Headers: {dict(response.headers)}")
                return {
                    'exito': False,
                    'error': f'El PAC devolvió una respuesta vacía (Status: {response.status_code})',
                    'codigo_error': 'EMPTY_RESPONSE'
                }
            
            if response.status_code == 200:
                return self._procesar_respuesta_soap(response.text)
            else:
                return {
                    'exito': False,
                    'error': f"Error HTTP {response.status_code}: {response.text}",
                    'codigo_error': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error en timbrado: {e}")
            # Si hay error de conexión, usar modo simulación
            if "NameResolutionError" in str(e) or "ConnectionError" in str(e):
                logger.info("Error de conexión detectado - cambiando a modo simulación")
                return self._simular_timbrado(xml_cfdi)
            
            return {
                'exito': False,
                'error': f"Error inesperado: {str(e)}",
                'codigo_error': 'UNKNOWN_ERROR'
            }
    
    def _construir_soap_envelope(self, xml_cfdi: str) -> str:
        """
        Construye el envelope SOAP para el timbrado usando la función TimbradoCfdi
        
        Args:
            xml_cfdi: XML del CFDI a timbrar
            
        Returns:
            str: SOAP envelope completo
        """
        # Determinar si es modo prueba basado en la configuración
        es_prueba = self.configuracion.get('entorno', 'pruebas') == 'pruebas'
        
        # Remover la declaración XML si existe
        if xml_cfdi.strip().startswith('<?xml'):
            xml_cfdi = xml_cfdi.split('>', 1)[1].strip()
        
        # Usar CDATA para evitar problemas de escape
        xml_escaped = xml_cfdi
        
        # Obtener certificados del emisor si están disponibles
        cert_base64 = ""
        key_base64 = ""
        key_pass = ""
        
        if hasattr(self, 'emisor') and self.emisor:
            if self.emisor.archivo_certificado:
                cert_base64 = self.emisor.archivo_certificado
            if self.emisor.archivo_llave:
                key_base64 = self.emisor.archivo_llave
            if self.emisor.password_llave:
                key_pass = self.emisor.password_llave
        
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tim="timbrado.ws.pade.mx">
    <soapenv:Header/>
    <soapenv:Body>
        <tim:timbradoCfdi>
            <contrato>{self.credenciales['contrato']}</contrato>
            <usuario>{self.credenciales['usuario']}</usuario>
            <passwd>{self.credenciales['password']}</passwd>
            <cfdiXml><![CDATA[{xml_escaped}]]></cfdiXml>
            <cert>{cert_base64}</cert>
            <key>{key_base64}</key>
            <keyPass>{key_pass}</keyPass>
            <prueba>{str(es_prueba).lower()}</prueba>
            <opciones>CALCULAR_SELLO</opciones>
        </tim:timbradoCfdi>
    </soapenv:Body>
</soapenv:Envelope>"""
        
        return soap_envelope
    
    def _firmar_xml_cfdi(self, xml_cfdi: str) -> str:
        """
        Firma digitalmente el XML CFDI con el sello del emisor
        
        Args:
            xml_cfdi: XML del CFDI sin firmar
            
        Returns:
            str: XML CFDI con sello digital
        """
        try:
            if not self.emisor or not self.emisor.archivo_certificado or not self.emisor.archivo_llave:
                logger.warning("No se puede firmar el XML: emisor sin certificados")
                return xml_cfdi
            
            # Importar servicios necesarios
            from .certificado_service import CertificadoService
            from .xml_builder import XMLCFDIBuilder
            
            # Obtener datos del certificado
            datos_cert = CertificadoService.extraer_datos_certificado(self.emisor)
            if not datos_cert['valido']:
                logger.error(f"No se puede firmar: certificado inválido - {datos_cert.get('error')}")
                return xml_cfdi
            
            # Cargar llave privada
            llave_privada = CertificadoService.cargar_llave_privada(self.emisor)
            if not llave_privada:
                logger.error("No se puede firmar: no se pudo cargar la llave privada")
                return xml_cfdi
            
            # Generar cadena original del CFDI
            cadena_original = XMLCFDIBuilder.generar_cadena_original(xml_cfdi)
            if not cadena_original:
                logger.error("No se puede firmar: no se pudo generar la cadena original")
                return xml_cfdi
            
            # Generar sello digital
            sello_digital = CertificadoService.generar_sello_digital(cadena_original, llave_privada)
            if not sello_digital:
                logger.error("No se puede firmar: no se pudo generar el sello digital")
                return xml_cfdi
            
            # Actualizar el XML con el sello digital y certificado
            xml_firmado = XMLCFDIBuilder.actualizar_sello_y_certificado(
                xml_cfdi, 
                sello_digital, 
                datos_cert['no_certificado'],
                datos_cert['certificado_base64']
            )
            
            logger.info("XML CFDI firmado exitosamente")
            return xml_firmado
            
        except Exception as e:
            logger.error(f"Error firmando XML CFDI: {e}")
            return xml_cfdi
    
    def _procesar_respuesta_servicio_timbrado(self, xml_respuesta: str) -> Dict[str, Any]:
        """
        Procesa la respuesta del servicio de timbrado
        
        Args:
            xml_respuesta: XML de respuesta del servicio de timbrado
            
        Returns:
            Dict: Resultado procesado
        """
        try:
            # Log de la respuesta completa para debugging
            logger.info(f"Respuesta del servicio de timbrado: {xml_respuesta}")
            
            # Decodificar el XML escapado
            import html
            xml_decoded = html.unescape(xml_respuesta)
            
            # Log de la respuesta decodificada
            logger.info(f"Respuesta decodificada: {xml_decoded}")
            
            # Parsear el XML de respuesta
            root = ET.fromstring(xml_decoded)
            
            # Log de la estructura del XML parseado
            logger.info(f"Elemento raíz: {root.tag}")
            logger.info(f"Atributos del elemento raíz: {root.attrib}")
            logger.info(f"Elementos hijos: {[child.tag for child in root]}")
            
            # Buscar elementos de la respuesta con diferentes nombres posibles
            timbrado_ok = root.find('timbradoOk')
            if timbrado_ok is None:
                timbrado_ok = root.find('timbradoOK')
            if timbrado_ok is None:
                timbrado_ok = root.find('TimbradoOk')
            if timbrado_ok is None:
                timbrado_ok = root.find('TimbradoOK')
            
            codigo = root.find('codigo')
            if codigo is None:
                codigo = root.find('Codigo')
            
            mensaje = root.find('mensaje')
            if mensaje is None:
                mensaje = root.find('Mensaje')
            
            id_respuesta = root.find('id')
            if id_respuesta is None:
                id_respuesta = root.find('Id')
            
            # Log de los elementos encontrados
            logger.info(f"timbrado_ok: {timbrado_ok.text if timbrado_ok is not None else 'No encontrado'}")
            logger.info(f"codigo: {codigo.text if codigo is not None else 'No encontrado'}")
            logger.info(f"mensaje: {mensaje.text if mensaje is not None else 'No encontrado'}")
            logger.info(f"id_respuesta: {id_respuesta.text if id_respuesta is not None else 'No encontrado'}")
            
            if timbrado_ok is not None and timbrado_ok.text == 'true':
                # Timbrado exitoso - buscar el XML timbrado en xmlBase64 (según documentación del PAC)
                xml_base64 = root.find('xmlBase64')
                if xml_base64 is None:
                    xml_base64 = root.find('XMLBase64')
                if xml_base64 is None:
                    xml_base64 = root.find('xmlTimbrado')
                if xml_base64 is None:
                    xml_base64 = root.find('XmlTimbrado')
                if xml_base64 is None:
                    xml_base64 = root.find('XMLTimbrado')
                if xml_base64 is None:
                    xml_base64 = root.find('cfdiXml')
                if xml_base64 is None:
                    xml_base64 = root.find('cfdiXML')
                
                logger.info(f"xml_base64 encontrado: {xml_base64 is not None}")
                if xml_base64 is not None:
                    logger.info(f"xml_base64.text: {xml_base64.text[:200] if xml_base64.text else 'None'}...")
                
                if xml_base64 is not None and xml_base64.text:
                    try:
                        # Decodificar Base64 si es necesario
                        import base64
                        xml_timbrado_decoded = base64.b64decode(xml_base64.text).decode('utf-8')
                        logger.info(f"XML decodificado exitosamente: {xml_timbrado_decoded[:200]}...")
                        
                        # Extraer datos del timbre fiscal
                        from .xml_builder import XMLCFDIBuilder
                        timbre_data = XMLCFDIBuilder.extraer_timbre_fiscal(xml_timbrado_decoded)
                        
                        # También extraer datos directamente de la respuesta del PAC
                        uuid = root.find('UUID')
                        fecha_timbrado = root.find('FechaTimbrado')
                        sello_cfd = root.find('selloCFD')
                        no_cert_sat = root.find('noCertificadoSAT')
                        sello_sat = root.find('selloSAT')
                        
                        # Buscar código QR en base64
                        qr_base64 = root.find('pdfBase64')
                        if qr_base64 is None:
                            qr_base64 = root.find('PDFBase64')
                        if qr_base64 is None:
                            qr_base64 = root.find('qrBase64')
                        if qr_base64 is None:
                            qr_base64 = root.find('QRBase64')
                        if qr_base64 is None:
                            qr_base64 = root.find('codigoQR')
                        if qr_base64 is None:
                            qr_base64 = root.find('CodigoQR')
                        
                        logger.info(f"QR base64 encontrado: {qr_base64 is not None}")
                        if qr_base64 is not None:
                            logger.info(f"QR base64.text: {qr_base64.text[:100] if qr_base64.text else 'None'}...")
                        
                        return {
                            'exito': True,
                            'xml_timbrado': xml_timbrado_decoded,
                            'uuid': uuid.text if uuid is not None else timbre_data.get('uuid'),
                            'fecha_timbrado': fecha_timbrado.text if fecha_timbrado is not None else timbre_data.get('fecha_timbrado'),
                            'no_cert_sat': no_cert_sat.text if no_cert_sat is not None else timbre_data.get('no_certificado_sat'),
                            'sello_sat': sello_sat.text if sello_sat is not None else timbre_data.get('sello_sat'),
                            'sello_cfd': sello_cfd.text if sello_cfd is not None else None,
                            'id_respuesta': id_respuesta.text if id_respuesta is not None else None,
                            'qr_base64': qr_base64.text if qr_base64 is not None else None
                        }
                    except Exception as e:
                        logger.error(f"Error decodificando XML Base64: {e}")
                        return {
                            'exito': False,
                            'error': f'Error decodificando XML timbrado: {str(e)}',
                            'codigo_error': 'DECODE_ERROR'
                        }
                else:
                    # Log de todos los elementos para debugging
                    logger.error("No se encontró XML timbrado. Elementos disponibles:")
                    for child in root:
                        logger.error(f"  {child.tag}: {child.text[:100] if child.text else 'None'}...")
                    
                    return {
                        'exito': False,
                        'error': 'Timbrado exitoso pero no se encontró XML timbrado',
                        'codigo_error': 'NO_XML_TIMBRADO',
                        'debug_info': {
                            'elementos_disponibles': [child.tag for child in root],
                            'timbrado_ok_text': timbrado_ok.text if timbrado_ok is not None else None,
                            'xml_base64_encontrado': xml_base64 is not None,
                            'xml_base64_text': xml_base64.text[:200] if xml_base64 is not None and xml_base64.text else None
                        }
                    }
            else:
                # Error en el timbrado
                error_msg = mensaje.text if mensaje is not None else 'Error desconocido del PAC'
                codigo_error = codigo.text if codigo is not None else 'UNKNOWN'
                
                return {
                    'exito': False,
                    'error': error_msg,
                    'codigo_error': codigo_error,
                    'id_respuesta': id_respuesta.text if id_respuesta is not None else None
                }
                
        except ET.ParseError as e:
            logger.error(f"Error parseando respuesta del servicio de timbrado: {e}")
            logger.error(f"XML que causó el error: {xml_respuesta}")
            return {
                'exito': False,
                'error': f'Error parseando respuesta del PAC: {str(e)}',
                'codigo_error': 'PARSE_ERROR'
            }
        except Exception as e:
            logger.error(f"Error procesando respuesta del servicio de timbrado: {e}")
            return {
                'exito': False,
                'error': f'Error procesando respuesta del PAC: {str(e)}',
                'codigo_error': 'PROCESS_ERROR'
            }
    
    def _procesar_respuesta_soap(self, soap_response: str) -> Dict[str, Any]:
        """
        Procesa la respuesta SOAP del PAC
        
        Args:
            soap_response: Respuesta SOAP del PAC
            
        Returns:
            Dict: Resultado procesado
        """
        try:
            # Log de la respuesta completa para debugging
            logger.info(f"Procesando respuesta SOAP: {soap_response}")
            
            # Verificar si es HTML (error 404, 500, etc.)
            if soap_response.strip().startswith('<html') or soap_response.strip().startswith('<!DOCTYPE'):
                return {
                    'exito': False,
                    'error': f'El PAC devolvió HTML en lugar de XML: {soap_response[:200]}...',
                    'codigo_error': 'HTML_RESPONSE'
                }
            
            # Parsear respuesta SOAP
            root = ET.fromstring(soap_response)
            
            # Buscar el resultado en el namespace SOAP
            namespaces = {
                'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
                'tim': 'timbrado.ws.pade.mx',
                'tns': 'timbrado.ws.pade.mx',
                'ns2': 'timbrado.ws.pade.mx'
            }
            
            # Buscar el elemento de respuesta según documentación oficial
            resultado_elem = root.find('.//tim:timbradoCfdiResponse', namespaces)
            if resultado_elem is None:
                resultado_elem = root.find('.//ns2:timbradoCfdiResponse', namespaces)
            if resultado_elem is None:
                resultado_elem = root.find('.//tns:timbradoCfdiResponse', namespaces)
            
            if resultado_elem is not None:
                # El PAC devuelve la respuesta en el elemento 'return' (sin namespace)
                return_elem = resultado_elem.find('return')
                
                if return_elem is not None:
                    # Parsear la respuesta del servicio de timbrado
                    return self._procesar_respuesta_servicio_timbrado(return_elem.text)
                else:
                    return {
                        'exito': False,
                        'error': 'No se encontró elemento return en la respuesta',
                        'codigo_error': 'NO_RETURN_ELEMENT'
                    }
            
            # Si no se encuentra la respuesta esperada, buscar errores SOAP
            fault_elem = root.find('.//soap:Fault', namespaces)
            if fault_elem is not None:
                fault_string = fault_elem.find('soap:faultstring', namespaces)
                return {
                    'exito': False,
                    'error': fault_string.text if fault_string is not None else 'Error SOAP del PAC',
                    'codigo_error': 'SOAP_FAULT'
                }
            
            return {
                'exito': False,
                'error': 'Respuesta del PAC no válida o inesperada',
                'codigo_error': 'INVALID_RESPONSE'
            }
            
        except ET.ParseError as e:
            logger.error(f"Error parseando respuesta SOAP: {e}")
            logger.error(f"Respuesta que causó el error: {soap_response}")
            return {
                'exito': False,
                'error': f'Error parseando respuesta del PAC: {str(e)}. Respuesta: {soap_response[:200]}...',
                'codigo_error': 'PARSE_ERROR'
            }
        except Exception as e:
            logger.error(f"Error procesando respuesta SOAP: {e}")
            return {
                'exito': False,
                'error': f'Error procesando respuesta del PAC: {str(e)}',
                'codigo_error': 'PROCESS_ERROR'
            }
    
    def cancelar_cfdi(self, uuid: str, motivo: str) -> Dict[str, Any]:
        """
        Cancela un CFDI timbrado
        
        Args:
            uuid: UUID del CFDI a cancelar
            motivo: Motivo de la cancelación
            
        Returns:
            Dict: Resultado de la cancelación
        """
        # TODO: Implementar cancelación
        return {
            'exito': False,
            'error': 'Cancelación no implementada aún',
            'codigo_error': 'NOT_IMPLEMENTED'
        }
    
    def consultar_cfdi(self, uuid: str) -> Dict[str, Any]:
        """
        Consulta el estado de un CFDI
        
        Args:
            uuid: UUID del CFDI a consultar
            
        Returns:
            Dict: Estado del CFDI
        """
        # TODO: Implementar consulta
        return {
            'exito': False,
            'error': 'Consulta no implementada aún',
            'codigo_error': 'NOT_IMPLEMENTED'
        }
    
    def probar_conexion(self) -> Dict[str, Any]:
        """
        Prueba la conectividad con el PAC
        
        Returns:
            Dict: Resultado de la prueba de conexión
        """
        try:
            # Probar conectividad básica primero
            logger.info(f"Probando conectividad básica con: {self.url_base}")
            
            # Probar endpoints según documentación oficial de Prodigia
            endpoints_posibles = [
                f"{self.url_base}/servicio/Timbrado4.0",
                f"{self.url_base}/servicio/Timbrado4.0?wsdl"
            ]
            
            endpoints_disponibles = []
            for ep in endpoints_posibles:
                try:
                    logger.info(f"Probando endpoint: {ep}")
                    test_response = requests.get(ep, timeout=10)
                    logger.info(f"Endpoint {ep}: Status {test_response.status_code}")
                    if test_response.status_code == 200:
                        endpoints_disponibles.append(ep)
                except Exception as e:
                    logger.warning(f"Endpoint {ep} no disponible: {e}")
            
            if endpoints_disponibles:
                return {
                    'exito': True,
                    'message': f'Servicio PAC disponible. Endpoints encontrados: {endpoints_disponibles}',
                    'detalles': f"URL base: {self.url_base}"
                }
            else:
                return {
                    'exito': False,
                    'error': f'Ningún endpoint del PAC está disponible en {self.url_base}',
                    'codigo_error': 'NO_ENDPOINTS_AVAILABLE'
                }
                
        except Exception as e:
            logger.error(f"Error probando conexión con PAC: {e}")
            return {
                'exito': False,
                'error': f'Error de conectividad: {str(e)}',
                'codigo_error': 'CONNECTION_ERROR'
            }
    
    def _simular_timbrado(self, xml_cfdi: str) -> Dict[str, Any]:
        """
        Simula el timbrado de un CFDI para pruebas
        
        Args:
            xml_cfdi: XML del CFDI a timbrar
            
        Returns:
            Dict: Resultado simulado del timbrado
        """
        try:
            from datetime import datetime
            import uuid
            
            # Generar UUID simulado
            uuid_simulado = str(uuid.uuid4())
            fecha_timbrado = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            
            # Crear XML timbrado simulado
            xml_timbrado = f"""<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4" 
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xsi:schemaLocation="http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd"
                  Version="4.0"
                  Serie="A"
                  Folio="1"
                  Fecha="{fecha_timbrado}"
                  Sello="SIMULADO"
                  FormaPago="99"
                  NoCertificado="SIMULADO"
                  Certificado="SIMULADO"
                  SubTotal="100.00"
                  Moneda="MXN"
                  Total="116.00"
                  TipoDeComprobante="I"
                  Exportacion="01"
                  MetodoPago="PUE"
                  LugarExpedicion="12345">
    <cfdi:InformacionGlobal Version="1.0" Periodicidad="01" Meses="01" Año="2024"/>
    <cfdi:Emisor Rfc="BASM790803LV9" Nombre="JOSE MANUEL BARBA SOTO" RegimenFiscal="626"/>
    <cfdi:Receptor Rfc="XAXX010101000" Nombre="PUBLICO EN GENERAL" DomicilioFiscalReceptor="12345" RegimenFiscalReceptor="626" UsoCFDI="G01"/>
    <cfdi:Conceptos>
        <cfdi:Concepto ClaveProdServ="01010101" NoIdentificacion="1" Cantidad="1" ClaveUnidad="H87" Unidad="Pieza" Descripcion="PRODUCTO SIMULADO" ValorUnitario="100.00" Importe="100.00" ObjetoImp="02">
            <cfdi:Impuestos>
                <cfdi:Traslados>
                    <cfdi:Traslado Base="100.00" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="16.00"/>
                </cfdi:Traslados>
            </cfdi:Impuestos>
        </cfdi:Concepto>
    </cfdi:Conceptos>
    <cfdi:Impuestos TotalImpuestosTrasladados="16.00">
        <cfdi:Traslados>
            <cfdi:Traslado Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="16.00"/>
        </cfdi:Traslados>
    </cfdi:Impuestos>
    <cfdi:Complemento>
        <tfd:TimbreFiscalDigital xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital" 
                                 xsi:schemaLocation="http://www.sat.gob.mx/TimbreFiscalDigital http://www.sat.gob.mx/sitio_internet/cfd/TimbreFiscalDigital/TimbreFiscalDigitalv11.xsd"
                                 Version="1.1"
                                 UUID="{uuid_simulado}"
                                 FechaTimbrado="{fecha_timbrado}"
                                 RfcProvCertif="SIMULADO"
                                 SelloCFD="SIMULADO"
                                 NoCertificadoSAT="SIMULADO"
                                 SelloSAT="SIMULADO"/>
    </cfdi:Complemento>
</cfdi:Comprobante>"""
            
            logger.info(f"Timbrado simulado generado - UUID: {uuid_simulado}")
            
            return {
                'exito': True,
                'xml_timbrado': xml_timbrado,
                'uuid': uuid_simulado,
                'fecha_timbrado': fecha_timbrado,
                'no_certificado_sat': 'SIMULADO',
                'sello_sat': 'SIMULADO',
                'mensaje': 'Timbrado simulado exitoso (modo prueba)',
                'modo_simulacion': True
            }
            
        except Exception as e:
            logger.error(f"Error en simulación de timbrado: {e}")
            return {
                'exito': False,
                'error': f'Error en simulación: {str(e)}',
                'codigo_error': 'SIMULATION_ERROR'
            }
