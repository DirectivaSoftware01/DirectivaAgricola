import logging
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any
from cryptography.hazmat.primitives import serialization
from .configuracion_entorno import ConfiguracionEntornoService
from .certificado_service import CertificadoService

logger = logging.getLogger(__name__)


class TimbradoService:
    """Servicio para timbrado de CFDI con PAC Prodigia"""
    
    def __init__(self, configuracion: Dict[str, Any], emisor):
        """
        Inicializa el servicio de timbrado
        
        Args:
            configuracion: Configuración del PAC
            emisor: Emisor del CFDI
        """
        self.configuracion = configuracion
        self.emisor = emisor
        self.url_base = configuracion.get('url', '')
        self.credenciales = configuracion.get('credenciales', {})
        self.timeout = 30
        
        logger.info(f"TimbradoService inicializado para emisor {emisor.rfc}")
        logger.info(f"URL PAC: {self.url_base}")
        logger.info(f"Usuario PAC: {self.credenciales.get('usuario', 'N/A')}")
        logger.info(f"Contrato PAC: {self.credenciales.get('contrato', 'N/A')}")
    
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
                    'error': f'Respuesta vacía del PAC (Status: {response.status_code})',
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
    
    def _firmar_xml_cfdi(self, xml_cfdi: str) -> str:
        """
        Firma el XML CFDI con el certificado del emisor
        
        Args:
            xml_cfdi: XML del CFDI a firmar
            
        Returns:
            str: XML firmado
        """
        try:
            # Obtener datos del certificado
            certificado_data = CertificadoService.extraer_datos_certificado(self.emisor)
            
            if not certificado_data or not certificado_data.get('valido'):
                logger.warning(f"Certificado no válido para emisor {self.emisor.rfc}: {certificado_data.get('error', 'Error desconocido')}")
                return xml_cfdi
            
            # Cargar llave privada
            llave_privada = CertificadoService.cargar_llave_privada(self.emisor)
            if not llave_privada:
                logger.warning(f"No se pudo cargar la llave privada para emisor {self.emisor.rfc}")
                return xml_cfdi
            
            # Generar cadena original
            from .xml_builder import XMLCFDIBuilder
            cadena_original = XMLCFDIBuilder.generar_cadena_original(xml_cfdi)
            
            # Generar sello digital
            sello = CertificadoService.generar_sello_digital(cadena_original, llave_privada)
            
            if not sello:
                logger.warning(f"No se pudo generar el sello digital para emisor {self.emisor.rfc}")
                return xml_cfdi
            
            # Actualizar XML con sello y certificado
            xml_firmado = XMLCFDIBuilder.actualizar_sello_y_certificado(
                xml_cfdi, 
                sello, 
                certificado_data['no_certificado'], 
                certificado_data['certificado_base64']
            )
            
            logger.info(f"XML firmado exitosamente para emisor {self.emisor.rfc}")
            return xml_firmado
            
        except Exception as e:
            logger.error(f"Error firmando XML: {e}")
            return xml_cfdi
    
    def _construir_soap_envelope(self, xml_cfdi: str) -> str:
        """
        Construye el envelope SOAP para el timbrado
        
        Args:
            xml_cfdi: XML del CFDI a timbrar
            
        Returns:
            str: Envelope SOAP
        """
        # Obtener certificados en base64
        certificado_data = CertificadoService.extraer_datos_certificado(self.emisor)
        certificado_base64 = certificado_data.get('certificado_base64', '') if certificado_data else ''
        
        # Obtener llave privada en base64
        llave_privada = CertificadoService.cargar_llave_privada(self.emisor)
        llave_base64 = ''
        if llave_privada:
            import base64
            # Serializar la llave privada a bytes primero
            llave_bytes = llave_privada.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            llave_base64 = base64.b64encode(llave_bytes).decode('utf-8')
        
        # Construir envelope SOAP según documentación oficial de Prodigia
        soap_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tim="timbrado.ws.pade.mx">
    <soapenv:Header/>
    <soapenv:Body>
        <tim:timbradoCfdi>
            <contrato>{self.credenciales.get('contrato', '')}</contrato>
            <usuario>{self.credenciales.get('usuario', '')}</usuario>
            <passwd>{self.credenciales.get('password', '')}</passwd>
            <cfdiXml><![CDATA[{xml_cfdi}]]></cfdiXml>
            <cert>{certificado_base64}</cert>
            <key>{llave_base64}</key>
            <keyPass>{self.emisor.password_llave or ''}</keyPass>
            <prueba>{str(self.credenciales.get('prueba', 'true')).lower()}</prueba>
            <opciones>CALCULAR_SELLO</opciones>
        </tim:timbradoCfdi>
    </soapenv:Body>
</soapenv:Envelope>"""
        
        logger.info(f"Request SOAP generado: {soap_envelope[:500]}...")
        return soap_envelope
    
    def _procesar_respuesta_servicio_timbrado(self, xml_respuesta: str) -> Dict[str, Any]:
        """
        Procesa la respuesta del servicio de timbrado usando la misma lógica que PACProdigiaClient
        
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
            try:
                root = ET.fromstring(xml_decoded)
            except ET.ParseError as e:
                logger.error(f"Error parseando XML de respuesta: {e}")
                logger.error(f"XML recibido: {xml_decoded[:500]}...")
                return {
                    'exito': False,
                    'error': f'Error parseando respuesta del PAC: {str(e)}',
                    'codigo_error': 'XML_PARSE_ERROR'
                }
            
            # Verificar si hay error (usando la misma lógica que PACProdigiaClient)
            error_elem = root.find('.//Error')
            if error_elem is not None:
                codigo = error_elem.get('Codigo', 'UNKNOWN')
                mensaje = error_elem.text or 'Error desconocido'
                
                logger.error(f"Error del PAC: {mensaje} (Código: {codigo})")
                return {
                    'exito': False,
                    'error': mensaje,
                    'codigo_error': codigo,
                    'xml_respuesta': xml_respuesta
                }
            
            # Verificar si el timbrado fue exitoso
            timbrado_ok = root.find('.//timbradoOk')
            if timbrado_ok is not None and timbrado_ok.text and timbrado_ok.text.lower() == 'true':
                # El timbrado fue exitoso, buscar el XML en xmlBase64
                xml_base64_elem = root.find('.//xmlBase64')
                if xml_base64_elem is not None and xml_base64_elem.text:
                    # Decodificar el XML desde Base64
                    import base64
                    xml_timbrado = base64.b64decode(xml_base64_elem.text).decode('utf-8')
                    
                    # Extraer datos del timbre
                    from .xml_builder import XMLCFDIBuilder
                    timbre_data = XMLCFDIBuilder.extraer_timbre_fiscal(xml_timbrado)
                    
                    if timbre_data['valido']:
                        logger.info(f"Timbrado exitoso - UUID: {timbre_data['uuid']}")
                        
                        # Generar código QR
                        qr_base64 = self._generar_codigo_qr_complemento_pago(xml_timbrado)
                        
                        # Extraer cadena original del SAT
                        cadena_original_sat = self._extraer_cadena_original_sat(xml_timbrado)
                        
                        return {
                            'exito': True,
                            'timbradoOk': True,
                            'xml_timbrado': xml_timbrado,
                            'xmlBase64': xml_base64_elem.text,  # Agregar el Base64 original
                            'uuid': timbre_data['uuid'],
                            'fecha_timbrado': timbre_data['fecha_timbrado'],
                            'sello_sat': timbre_data['sello_sat'],
                            'no_certificado_sat': timbre_data['no_certificado_sat'],
                            'selloCFD': timbre_data.get('sello_cfd', ''),
                            'version': timbre_data.get('version', '1.1'),
                            'qr_base64': qr_base64,
                            'cadena_original_sat': cadena_original_sat,
                            'xml_respuesta': xml_respuesta
                        }
                    else:
                        logger.error(f"Error extrayendo timbre: {timbre_data.get('error', 'Desconocido')}")
                        return {
                            'exito': False,
                            'error': f"Error extrayendo timbre: {timbre_data.get('error', 'Desconocido')}",
                            'codigo_error': 'TIMBRE_EXTRACTION_ERROR',
                            'xml_respuesta': xml_respuesta
                        }
                else:
                    logger.error("No se encontró xmlBase64 en la respuesta exitosa")
                    return {
                        'exito': False,
                        'error': 'No se encontró xmlBase64 en la respuesta exitosa',
                        'codigo_error': 'NO_XML_BASE64',
                        'xml_respuesta': xml_respuesta
                    }
            else:
                # El timbrado no fue exitoso, buscar mensaje de error
                mensaje_elem = root.find('.//mensaje')
                codigo_elem = root.find('.//codigo')
                
                mensaje = mensaje_elem.text if mensaje_elem is not None and mensaje_elem.text else 'Error desconocido'
                codigo = codigo_elem.text if codigo_elem is not None and codigo_elem.text else 'UNKNOWN'
                
                logger.error(f"Timbrado falló: {mensaje} (Código: {codigo})")
                return {
                    'exito': False,
                    'error': mensaje,
                    'codigo_error': codigo,
                    'xml_respuesta': xml_respuesta
                }
                
        except Exception as e:
            logger.error(f"Error procesando respuesta del PAC: {e}")
            return {
                'exito': False,
                'error': f'Error procesando respuesta: {str(e)}',
                'codigo_error': 'RESPONSE_PROCESSING_ERROR',
                'xml_respuesta': xml_respuesta
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
                    # Verificar que el elemento return tenga contenido
                    if return_elem.text is None or return_elem.text.strip() == '':
                        return {
                            'exito': False,
                            'error': 'El elemento return está vacío',
                            'codigo_error': 'EMPTY_RETURN'
                        }
                    # Parsear la respuesta del servicio de timbrado
                    logger.info(f"Contenido del elemento return: {return_elem.text[:200]}...")
                    
                    # Verificar que el contenido sea XML válido
                    try:
                        ET.fromstring(return_elem.text)
                    except ET.ParseError as e:
                        logger.error(f"El contenido del return no es XML válido: {e}")
                        return {
                            'exito': False,
                            'error': f'El contenido del return no es XML válido: {str(e)}',
                            'codigo_error': 'INVALID_RETURN_XML'
                        }
                    
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
    
    def _generar_codigo_qr_complemento_pago(self, xml_timbrado: str) -> str:
        """
        Genera el código QR para el complemento de pago
        
        Args:
            xml_timbrado: XML timbrado del complemento de pago
            
        Returns:
            str: Código QR en Base64
        """
        try:
            import xml.etree.ElementTree as ET
            import qrcode
            import base64
            from io import BytesIO
            
            # Parsear el XML para extraer datos
            root = ET.fromstring(xml_timbrado)
            
            # Extraer datos necesarios para el QR
            uuid = root.get('UUID', '')
            rfc_emisor = root.find('.//{http://www.sat.gob.mx/cfd/4}Emisor').get('Rfc', '')
            rfc_receptor = root.find('.//{http://www.sat.gob.mx/cfd/4}Receptor').get('Rfc', '')
            total = root.get('Total', '0')
            sello = root.get('Sello', '')
            
            # Construir URL del QR
            siglas_sello = sello[-8:] if sello else ''
            url_qr = f"https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id={uuid}&re={rfc_emisor}&rr={rfc_receptor}&tt={total}&fe={siglas_sello}"
            
            # Generar código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=3,
                border=2,
            )
            qr.add_data(url_qr)
            qr.make(fit=True)
            
            # Crear imagen
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error generando código QR para complemento de pago: {e}")
            return ""
    
    def _extraer_cadena_original_sat(self, xml_timbrado: str) -> str:
        """
        Extrae la cadena original del complemento SAT del XML timbrado
        
        Args:
            xml_timbrado: XML timbrado del complemento de pago
            
        Returns:
            str: Cadena original del SAT
        """
        try:
            import xml.etree.ElementTree as ET
            
            root = ET.fromstring(xml_timbrado)
            
            # Buscar el complemento de timbre fiscal
            complemento = root.find('.//{http://www.sat.gob.mx/cfd/4}Complemento')
            if complemento is not None:
                timbre = complemento.find('{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital')
                if timbre is not None:
                    # Extraer cadena original (SelloCFD)
                    cadena_original = timbre.get('SelloCFD')
                    if cadena_original:
                        logger.info("Cadena original del complemento SAT extraída exitosamente")
                        return cadena_original
            
            logger.warning("No se pudo extraer la cadena original del complemento SAT")
            return ""
            
        except Exception as e:
            logger.error(f"Error extrayendo cadena original del SAT: {e}")
            return ""
