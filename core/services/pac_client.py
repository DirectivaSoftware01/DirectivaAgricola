"""
Cliente para PAC Prodigia (PADE)
Maneja la comunicación con el webservice del PAC para timbrado y cancelación
"""

import requests
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class PACProdigiaClient:
    """Cliente para PAC Prodigia (PADE)"""
    
    def __init__(self, configuracion: Dict[str, Any]):
        """
        Inicializa el cliente PAC
        
        Args:
            configuracion: Configuración del PAC obtenida de ConfiguracionEntornoService
        """
        self.configuracion = configuracion
        self.url_base = configuracion['url']
        self.credenciales = configuracion['credenciales']
        self.timeout = configuracion.get('timeout', 30)
        self.max_retries = configuracion.get('max_retries', 3)
        self.retry_delay = configuracion.get('retry_delay', 1)
        self.backoff_factor = configuracion.get('backoff_factor', 2)
    
    def timbrar_cfdi(self, xml_cfdi: str) -> Dict[str, Any]:
        """
        Timbra un CFDI con el PAC
        
        Args:
            xml_cfdi: XML del CFDI a timbrar
            
        Returns:
            Dict: Resultado del timbrado
        """
        try:
            # Preparar petición
            endpoint = f"{self.url_base}/wsTimbradoCFDI"
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml',
                'SOAPAction': 'http://tempuri.org/ITimbradoCFDI/TimbrarCFDI'
            }
            
            # Parámetros de autenticación
            params = {
                'usuario': self.credenciales['usuario'],
                'password': self.credenciales['password'],
                'contrato': self.credenciales['contrato']
            }
            
            # Realizar petición con reintentos
            for intento in range(self.max_retries):
                try:
                    logger.info(f"Intentando timbrar CFDI (intento {intento + 1}/{self.max_retries})")
                    
                    response = requests.post(
                        endpoint,
                        data=xml_cfdi,
                        headers=headers,
                        params=params,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        return self._procesar_respuesta_timbrado(response.text)
                    else:
                        error_msg = f"Error HTTP {response.status_code}: {response.text}"
                        logger.warning(f"Intento {intento + 1} falló: {error_msg}")
                        
                        if intento < self.max_retries - 1:
                            delay = self.retry_delay * (self.backoff_factor ** intento)
                            logger.info(f"Esperando {delay} segundos antes del siguiente intento")
                            time.sleep(delay)
                        else:
                            return {
                                'exito': False,
                                'error': error_msg,
                                'codigo_error': response.status_code
                            }
                
                except requests.exceptions.Timeout:
                    error_msg = f"Timeout en intento {intento + 1}"
                    logger.warning(error_msg)
                    
                    if intento < self.max_retries - 1:
                        delay = self.retry_delay * (self.backoff_factor ** intento)
                        time.sleep(delay)
                    else:
                        return {
                            'exito': False,
                            'error': 'Timeout después de todos los intentos',
                            'codigo_error': 'TIMEOUT'
                        }
                
                except requests.exceptions.RequestException as e:
                    error_msg = f"Error de conexión en intento {intento + 1}: {str(e)}"
                    logger.warning(error_msg)
                    
                    if intento < self.max_retries - 1:
                        delay = self.retry_delay * (self.backoff_factor ** intento)
                        time.sleep(delay)
                    else:
                        return {
                            'exito': False,
                            'error': f'Error de conexión: {str(e)}',
                            'codigo_error': 'CONNECTION_ERROR'
                        }
            
            return {
                'exito': False,
                'error': 'Se agotaron todos los intentos',
                'codigo_error': 'MAX_RETRIES_EXCEEDED'
            }
            
        except Exception as e:
            logger.error(f"Error inesperado en timbrado: {e}")
            return {
                'exito': False,
                'error': f'Error inesperado: {str(e)}',
                'codigo_error': 'UNEXPECTED_ERROR'
            }
    
    def _procesar_respuesta_timbrado(self, xml_respuesta: str) -> Dict[str, Any]:
        """
        Procesa la respuesta del PAC
        
        Args:
            xml_respuesta: XML de respuesta del PAC
            
        Returns:
            Dict: Resultado procesado
        """
        try:
            import xml.etree.ElementTree as ET
            
            root = ET.fromstring(xml_respuesta)
            
            # Verificar si hay error
            error_elem = root.find('.//Error')
            if error_elem is not None:
                codigo = error_elem.get('Codigo', 'UNKNOWN')
                mensaje = error_elem.text or 'Error desconocido'
                
                return {
                    'exito': False,
                    'error': mensaje,
                    'codigo_error': codigo,
                    'xml_respuesta': xml_respuesta
                }
            
            # Buscar CFDI timbrado
            cfdi_elem = root.find('.//CFDI')
            if cfdi_elem is not None:
                xml_timbrado = ET.tostring(cfdi_elem, encoding='unicode')
                
                # Extraer datos del timbre
                from .xml_builder import XMLCFDIBuilder
                timbre_data = XMLCFDIBuilder.extraer_timbre_fiscal(xml_timbrado)
                
                if timbre_data['valido']:
                    return {
                        'exito': True,
                        'xml_timbrado': xml_timbrado,
                        'uuid': timbre_data['uuid'],
                        'fecha_timbrado': timbre_data['fecha_timbrado'],
                        'sello_sat': timbre_data['sello_sat'],
                        'no_cert_sat': timbre_data['no_certificado_sat'],
                        'xml_respuesta': xml_respuesta
                    }
                else:
                    return {
                        'exito': False,
                        'error': f"Error extrayendo timbre: {timbre_data.get('error', 'Desconocido')}",
                        'codigo_error': 'TIMBRE_EXTRACTION_ERROR',
                        'xml_respuesta': xml_respuesta
                    }
            else:
                return {
                    'exito': False,
                    'error': 'No se encontró CFDI en la respuesta',
                    'codigo_error': 'NO_CFDI_IN_RESPONSE',
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
    
    def cancelar_cfdi(self, uuid: str, motivo: str, folio_sustitucion: str = None) -> Dict[str, Any]:
        """
        Cancela un CFDI
        
        Args:
            uuid: UUID del CFDI a cancelar
            motivo: Motivo de la cancelación
            folio_sustitucion: Folio del CFDI que sustituye (opcional)
            
        Returns:
            Dict: Resultado de la cancelación
        """
        try:
            endpoint = f"{self.url_base}/api/cancelacion"
            
            # Preparar datos de cancelación
            datos_cancelacion = {
                'uuid': uuid,
                'motivo': motivo,
                'usuario': self.credenciales['usuario'],
                'password': self.credenciales['password'],
                'contrato': self.credenciales['contrato']
            }
            
            if folio_sustitucion:
                datos_cancelacion['folio_sustitucion'] = folio_sustitucion
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                endpoint,
                json=datos_cancelacion,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return self._procesar_respuesta_cancelacion(response.json())
            else:
                return {
                    'exito': False,
                    'error': f"Error HTTP {response.status_code}: {response.text}",
                    'codigo_error': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error cancelando CFDI: {e}")
            return {
                'exito': False,
                'error': f'Error cancelando CFDI: {str(e)}',
                'codigo_error': 'CANCELATION_ERROR'
            }
    
    def _procesar_respuesta_cancelacion(self, json_respuesta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa la respuesta de cancelación
        
        Args:
            json_respuesta: JSON de respuesta del PAC
            
        Returns:
            Dict: Resultado procesado
        """
        try:
            if json_respuesta.get('exito', False):
                return {
                    'exito': True,
                    'acuse_cancelacion': json_respuesta.get('acuse'),
                    'fecha_cancelacion': json_respuesta.get('fecha_cancelacion'),
                    'estado': json_respuesta.get('estado')
                }
            else:
                return {
                    'exito': False,
                    'error': json_respuesta.get('mensaje', 'Error desconocido'),
                    'codigo_error': json_respuesta.get('codigo', 'UNKNOWN')
                }
                
        except Exception as e:
            logger.error(f"Error procesando respuesta de cancelación: {e}")
            return {
                'exito': False,
                'error': f'Error procesando respuesta: {str(e)}',
                'codigo_error': 'RESPONSE_PROCESSING_ERROR'
            }
    
    def consultar_estatus(self, uuid: str) -> Dict[str, Any]:
        """
        Consulta el estatus de un CFDI
        
        Args:
            uuid: UUID del CFDI
            
        Returns:
            Dict: Estatus del CFDI
        """
        try:
            endpoint = f"{self.url_base}/api/estatus"
            
            params = {
                'uuid': uuid,
                'usuario': self.credenciales['usuario'],
                'password': self.credenciales['password'],
                'contrato': self.credenciales['contrato']
            }
            
            response = requests.get(
                endpoint,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return self._procesar_respuesta_estatus(response.json())
            else:
                return {
                    'exito': False,
                    'error': f"Error HTTP {response.status_code}: {response.text}",
                    'codigo_error': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error consultando estatus: {e}")
            return {
                'exito': False,
                'error': f'Error consultando estatus: {str(e)}',
                'codigo_error': 'STATUS_QUERY_ERROR'
            }
    
    def _procesar_respuesta_estatus(self, json_respuesta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa la respuesta de estatus
        
        Args:
            json_respuesta: JSON de respuesta del PAC
            
        Returns:
            Dict: Estatus procesado
        """
        try:
            return {
                'exito': True,
                'estado': json_respuesta.get('estado'),
                'fecha_consulta': json_respuesta.get('fecha_consulta'),
                'mensaje': json_respuesta.get('mensaje'),
                'vigente': json_respuesta.get('vigente', False)
            }
            
        except Exception as e:
            logger.error(f"Error procesando respuesta de estatus: {e}")
            return {
                'exito': False,
                'error': f'Error procesando respuesta: {str(e)}',
                'codigo_error': 'RESPONSE_PROCESSING_ERROR'
            }
    
    def probar_conexion(self) -> Dict[str, Any]:
        """
        Prueba la conexión con el PAC
        
        Returns:
            Dict: Resultado de la prueba
        """
        try:
            # Usar el endpoint de timbrado para probar la conexión
            endpoint = f"{self.url_base}/servicio/Timbrado4.0"
            
            # Crear un XML de prueba simple
            xml_prueba = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <TimbradoCfdi xmlns="http://tempuri.org/">
            <contrato>{contrato}</contrato>
            <usuario>{usuario}</usuario>
            <password>{password}</password>
            <xml>test</xml>
            <prueba>true</prueba>
        </TimbradoCfdi>
    </soap:Body>
</soap:Envelope>""".format(
                contrato=self.credenciales['contrato'],
                usuario=self.credenciales['usuario'],
                password=self.credenciales['password']
            )
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/ITimbrado4_0/TimbradoCfdi'
            }
            
            response = requests.post(
                endpoint,
                data=xml_prueba,
                headers=headers,
                timeout=self.timeout
            )
            
            # Si recibimos una respuesta (aunque sea de error), significa que el servicio está disponible
            if response.status_code in [200, 400, 500]:
                return {
                    'exito': True,
                    'mensaje': 'Conexión exitosa con el PAC (servicio disponible)',
                    'tiempo_respuesta': response.elapsed.total_seconds(),
                    'status_code': response.status_code
                }
            else:
                return {
                    'exito': False,
                    'error': f"Error HTTP {response.status_code}: {response.text}",
                    'codigo_error': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error probando conexión: {e}")
            return {
                'exito': False,
                'error': f'Error probando conexión: {str(e)}',
                'codigo_error': 'CONNECTION_TEST_ERROR'
            }
