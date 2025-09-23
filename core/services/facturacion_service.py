"""
Servicio principal de facturación electrónica CFDI 4.0
Integra todos los componentes para el timbrado completo
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from django.db import transaction
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from .configuracion_entorno import ConfiguracionEntornoService
from .certificado_service import CertificadoService
from .xml_builder import XMLCFDIBuilder
from .timbrado_service import TimbradoService
from ..validators.cfdi_validator import CFDIValidator
from ..models import Factura, FacturaDetalle

logger = logging.getLogger(__name__)


class FacturacionService:
    """Servicio principal de facturación electrónica"""
    
    @classmethod
    def timbrar_factura(cls, factura) -> Dict[str, Any]:
        """
        Timbra una factura completa
        
        Args:
            factura: Objeto Factura a timbrar
            
        Returns:
            Dict: Resultado del timbrado
        """
        try:
            with transaction.atomic():
                # Obtener detalles de la factura
                detalles = FacturaDetalle.objects.filter(factura=factura)
                
                # Validar que la factura esté en estado pendiente
                if factura.estado_timbrado != 'PENDIENTE':
                    return {
                        'exito': False,
                        'error': f'La factura ya está en estado {factura.estado_timbrado}',
                        'codigo_error': 'INVALID_STATE'
                    }
                
                # Actualizar fecha de emisión con zona horaria correcta
                from ..utils.timezone_utils import obtener_fecha_actual_mexico
                factura.fecha_emision = obtener_fecha_actual_mexico(factura.lugar_expedicion)
                factura.save()
                
                # Validar configuración del emisor
                config_validacion = ConfiguracionEntornoService.validar_configuracion_emisor(factura.emisor)
                if not config_validacion['valido']:
                    return {
                        'exito': False,
                        'error': 'Configuración del emisor inválida',
                        'codigo_error': 'INVALID_EMISOR_CONFIG',
                        'detalles': config_validacion['errores']
                    }
                
                # Validar certificado
                cert_validacion = CertificadoService.validar_certificado_completo(factura.emisor)
                if not cert_validacion['valido']:
                    return {
                        'exito': False,
                        'error': 'Certificado inválido',
                        'codigo_error': 'INVALID_CERTIFICATE',
                        'detalles': cert_validacion['errores']
                    }
                
                # Validar CFDI
                cfdi_validacion = CFDIValidator.validar_factura_completa(factura, list(detalles))
                if not cfdi_validacion['valido']:
                    # Guardar errores de validación
                    factura.errores_validacion = '; '.join(cfdi_validacion['errores'])
                    factura.estado_timbrado = 'ERROR'
                    factura.save()
                    
                    return {
                        'exito': False,
                        'error': 'Validación CFDI fallida',
                        'codigo_error': 'CFDI_VALIDATION_FAILED',
                        'detalles': cfdi_validacion['errores']
                    }
                
                # Generar XML
                xml_result = cls._generar_xml_cfdi(factura, list(detalles), cert_validacion['datos_certificado'])
                if not xml_result['exito']:
                    return xml_result
                
                # Timbrar con PAC
                pac_result = cls._timbrar_con_pac(factura, xml_result['xml'], config_validacion['configuracion'])
                if not pac_result['exito']:
                    # Guardar error
                    factura.errores_validacion = pac_result['error']
                    factura.estado_timbrado = 'ERROR'
                    factura.intentos_timbrado += 1
                    factura.ultimo_intento = datetime.now(timezone.utc)
                    factura.save()
                    
                    return pac_result
                
                # Actualizar factura con datos del timbrado
                cls._actualizar_factura_timbrada(factura, xml_result['xml'], pac_result)
                
                return {
                    'exito': True,
                    'uuid': pac_result['uuid'],
                    'fecha_timbrado': pac_result['fecha_timbrado'],
                    'xml_timbrado': pac_result['xml_timbrado'],
                    'mensaje': 'Factura timbrada exitosamente'
                }
                
        except Factura.DoesNotExist:
            return {
                'exito': False,
                'error': 'Factura no encontrada',
                'codigo_error': 'FACTURA_NOT_FOUND'
            }
        except Exception as e:
            logger.error(f"Error inesperado timbrando factura {factura.serie}-{factura.folio}: {e}")
            return {
                'exito': False,
                'error': f'Error inesperado: {str(e)}',
                'codigo_error': 'UNEXPECTED_ERROR'
            }
    
    @classmethod
    def _generar_xml_cfdi(cls, factura, detalles, certificado_data) -> Dict[str, Any]:
        """Genera el XML del CFDI"""
        try:
            # Generar cadena original
            cadena_original = XMLCFDIBuilder.generar_cadena_original_desde_modelos(factura, detalles)
            
            # Cargar llave privada
            llave_privada = CertificadoService.cargar_llave_privada(factura.emisor)
            
            if not llave_privada:
                return {
                    'exito': False,
                    'error': 'No se pudo cargar la llave privada',
                    'codigo_error': 'PRIVATE_KEY_ERROR'
                }
            
            # Generar sello digital
            sello = CertificadoService.generar_sello_digital(cadena_original, llave_privada)
            if not sello:
                return {
                    'exito': False,
                    'error': 'No se pudo generar el sello digital',
                    'codigo_error': 'DIGITAL_SIGNATURE_ERROR'
                }
            
            # Construir XML
            xml_cfdi = XMLCFDIBuilder.construir_xml_cfdi(factura, detalles, certificado_data, sello)
            
            return {
                'exito': True,
                'xml': xml_cfdi,
                'cadena_original': cadena_original,
                'sello': sello
            }
            
        except Exception as e:
            logger.error(f"Error generando XML CFDI: {e}")
            return {
                'exito': False,
                'error': f'Error generando XML: {str(e)}',
                'codigo_error': 'XML_GENERATION_ERROR'
            }
    
    @classmethod
    def _timbrar_con_pac(cls, factura, xml_cfdi, configuracion) -> Dict[str, Any]:
        """Timbra el CFDI con el PAC"""
        try:
            # Crear servicio de timbrado con la configuración del emisor
            timbrado_service = TimbradoService(configuracion, factura.emisor)
            
            # Log de credenciales para debugging (sin mostrar contraseñas)
            logger.info(f"Timbrar CFDI para emisor {factura.emisor.rfc} con PAC {configuracion['credenciales']['nombre_pac']}")
            logger.info(f"URL PAC: {configuracion['url']}")
            logger.info(f"Usuario PAC: {configuracion['credenciales']['usuario']}")
            logger.info(f"Contrato PAC: {configuracion['credenciales']['contrato']}")
            logger.info(f"Entorno: {configuracion['entorno']}")
            
            # Timbrar
            resultado = timbrado_service.timbrar_cfdi(xml_cfdi)
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error timbrando con PAC: {e}")
            return {
                'exito': False,
                'error': f'Error timbrando con PAC: {str(e)}',
                'codigo_error': 'PAC_TIMBRADO_ERROR'
            }
    
    @classmethod
    def _actualizar_factura_timbrada(cls, factura, xml_original, pac_result):
        """Actualiza la factura con los datos del timbrado"""
        try:
            # Actualizar campos de timbrado
            factura.uuid = pac_result['uuid']
            factura.fecha_timbrado = datetime.fromisoformat(pac_result['fecha_timbrado'].replace('Z', '+00:00'))
            # Aceptar tanto snake_case como camelCase según la fuente
            factura.no_cert_sat = pac_result.get('no_cert_sat') or pac_result.get('no_certificado_sat') or pac_result.get('NoCertificadoSAT')
            factura.sello_sat = pac_result.get('sello_sat') or pac_result.get('selloSAT')
            factura.sello = pac_result.get('sello_cfd')  # Guardar sello del emisor
            factura.codigo_qr = pac_result.get('qr_base64')  # Guardar código QR del PAC
            factura.cadena_original_sat = cls._extraer_cadena_original_sat(pac_result['xml_timbrado'])  # Extraer cadena original
            factura.estado_timbrado = 'TIMBRADO'
            factura.xml_original = xml_original
            factura.xml_timbrado = pac_result['xml_timbrado']
            factura.intentos_timbrado += 1
            factura.ultimo_intento = datetime.now(timezone.utc)
            factura.errores_validacion = None  # Limpiar errores previos
            
            # Guardar archivos XML
            cls._guardar_archivos_xml(factura)
            
            factura.save()
            
        except Exception as e:
            logger.error(f"Error actualizando factura timbrada: {e}")
            raise
    
    @classmethod
    def _extraer_cadena_original_sat(cls, xml_timbrado):
        """Extrae la cadena original del complemento SAT del XML timbrado"""
        try:
            import xml.etree.ElementTree as ET
            
            # Parsear XML timbrado
            root = ET.fromstring(xml_timbrado)
            
            # Buscar complemento
            complemento = root.find('{http://www.sat.gob.mx/cfd/4}Complemento')
            if complemento is not None:
                # Buscar timbre fiscal
                timbre = complemento.find('{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital')
                if timbre is not None:
                    # Extraer cadena original (SelloCFD)
                    cadena_original = timbre.get('SelloCFD')
                    if cadena_original:
                        logger.info("Cadena original del complemento SAT extraída exitosamente")
                        return cadena_original
            
            logger.warning("No se pudo extraer la cadena original del complemento SAT")
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo cadena original del complemento SAT: {e}")
            return None
    
    @classmethod
    def _guardar_archivos_xml(cls, factura):
        """Guarda los archivos XML en el sistema de archivos"""
        try:
            # Crear directorio para la factura
            directorio = f"facturas/{factura.serie}-{factura.folio:06d}"
            
            # Guardar XML original
            if factura.xml_original:
                archivo_original = ContentFile(factura.xml_original.encode('utf-8'))
                archivo_original.name = f"{directorio}/original.xml"
                default_storage.save(archivo_original.name, archivo_original)
            
            # Guardar XML timbrado
            if factura.xml_timbrado:
                archivo_timbrado = ContentFile(factura.xml_timbrado.encode('utf-8'))
                archivo_timbrado.name = f"{directorio}/timbrado.xml"
                default_storage.save(archivo_timbrado.name, archivo_timbrado)
                
        except Exception as e:
            logger.error(f"Error guardando archivos XML: {e}")
            # No lanzar excepción para no interrumpir el timbrado
    
    @classmethod
    def cancelar_factura(cls, factura_id: int, motivo: str, folio_sustitucion: str = None) -> Dict[str, Any]:
        """
        Cancela una factura
        
        Args:
            factura_id: ID de la factura a cancelar
            motivo: Motivo de la cancelación
            folio_sustitucion: Folio del CFDI que sustituye (opcional)
            
        Returns:
            Dict: Resultado de la cancelación
        """
        try:
            with transaction.atomic():
                # Obtener factura
                factura = Factura.objects.select_related('emisor').get(folio=factura_id)
                
                # Validar que la factura esté timbrada
                if factura.estado_timbrado != 'TIMBRADO':
                    return {
                        'exito': False,
                        'error': f'La factura debe estar timbrada para cancelar. Estado actual: {factura.estado_timbrado}',
                        'codigo_error': 'INVALID_STATE_FOR_CANCELATION'
                    }
                
                # Validar configuración del emisor
                config_validacion = ConfiguracionEntornoService.validar_configuracion_emisor(factura.emisor)
                if not config_validacion['valido']:
                    return {
                        'exito': False,
                        'error': 'Configuración del emisor inválida',
                        'codigo_error': 'INVALID_EMISOR_CONFIG',
                        'detalles': config_validacion['errores']
                    }
                
                # Cancelar con PAC
                timbrado_service = TimbradoService(config_validacion['configuracion'], factura.emisor)
                resultado = timbrado_service.cancelar_cfdi(factura.uuid, motivo)
                
                if not resultado['exito']:
                    return resultado
                
                # Actualizar factura
                factura.estado_timbrado = 'CANCELADO'
                factura.cancelada = True
                factura.fecha_cancelacion = datetime.now(timezone.utc)
                factura.motivo_cancelacion = motivo
                factura.acuse_cancelacion = resultado.get('acuse_cancelacion')
                factura.save()
                
                return {
                    'exito': True,
                    'mensaje': 'Factura cancelada exitosamente',
                    'acuse_cancelacion': resultado.get('acuse_cancelacion')
                }
                
        except Factura.DoesNotExist:
            return {
                'exito': False,
                'error': 'Factura no encontrada',
                'codigo_error': 'FACTURA_NOT_FOUND'
            }
        except Exception as e:
            logger.error(f"Error cancelando factura {factura_id}: {e}")
            return {
                'exito': False,
                'error': f'Error cancelando factura: {str(e)}',
                'codigo_error': 'CANCELATION_ERROR'
            }
    
    @classmethod
    def consultar_estatus_factura(cls, factura_id: int) -> Dict[str, Any]:
        """
        Consulta el estatus de una factura en el SAT
        
        Args:
            factura_id: ID de la factura
            
        Returns:
            Dict: Estatus de la factura
        """
        try:
            # Obtener factura
            factura = Factura.objects.select_related('emisor').get(folio=factura_id)
            
            if not factura.uuid:
                return {
                    'exito': False,
                    'error': 'La factura no tiene UUID (no está timbrada)',
                    'codigo_error': 'NO_UUID'
                }
            
            # Validar configuración del emisor
            config_validacion = ConfiguracionEntornoService.validar_configuracion_emisor(factura.emisor)
            if not config_validacion['valido']:
                return {
                    'exito': False,
                    'error': 'Configuración del emisor inválida',
                    'codigo_error': 'INVALID_EMISOR_CONFIG'
                }
            
            # Consultar con PAC
            timbrado_service = TimbradoService(config_validacion['configuracion'], factura.emisor)
            resultado = timbrado_service.consultar_cfdi(factura.uuid)
            
            return resultado
            
        except Factura.DoesNotExist:
            return {
                'exito': False,
                'error': 'Factura no encontrada',
                'codigo_error': 'FACTURA_NOT_FOUND'
            }
        except Exception as e:
            logger.error(f"Error consultando estatus de factura {factura_id}: {e}")
            return {
                'exito': False,
                'error': f'Error consultando estatus: {str(e)}',
                'codigo_error': 'STATUS_QUERY_ERROR'
            }
    
    @classmethod
    def probar_conexion_pac(cls, emisor_id: int) -> Dict[str, Any]:
        """
        Prueba la conexión con el PAC para un emisor
        
        Args:
            emisor_id: ID del emisor
            
        Returns:
            Dict: Resultado de la prueba
        """
        try:
            from ..models import Emisor
            emisor = Emisor.objects.get(codigo=emisor_id)
            
            # Validar configuración
            config_validacion = ConfiguracionEntornoService.validar_configuracion_emisor(emisor)
            if not config_validacion['valido']:
                return {
                    'exito': False,
                    'error': 'Configuración del emisor inválida',
                    'codigo_error': 'INVALID_EMISOR_CONFIG',
                    'detalles': config_validacion['errores']
                }
            
            # Probar conexión
            timbrado_service = TimbradoService(config_validacion['configuracion'], emisor)
            resultado = timbrado_service.probar_conexion()
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error probando conexión PAC para emisor {emisor_id}: {e}")
            return {
                'exito': False,
                'error': f'Error probando conexión: {str(e)}',
                'codigo_error': 'CONNECTION_TEST_ERROR'
            }
