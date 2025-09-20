"""
Servicio de configuración de entornos para facturación electrónica
Maneja la configuración de pruebas vs producción para PAC Prodigia
"""

from django.conf import settings
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConfiguracionEntornoService:
    """Servicio para manejar configuración de entornos de facturación"""
    
    # URLs de PAC Prodigia según documentación oficial
    PAC_URLS = {
        'pruebas': 'https://timbrado.pade.mx',
        'produccion': 'https://timbrado.pade.mx',
        'simulacion': 'http://localhost:8000'  # Modo simulación para pruebas
    }
    
    # Endpoints del PAC según documentación oficial
    PAC_ENDPOINTS = {
        'timbrado': '/servicio/Timbrado4.0',
        'cancelacion': '/servicio/Cancelacion4.0',
        'consulta': '/servicio/Consulta4.0'
    }
    
    # Configuración por defecto según documentación oficial
    CONFIG_DEFAULT = {
        'timeout': 60,  # Recomendado por Prodigia
        'max_retries': 3,
        'retry_delay': 1,
        'backoff_factor': 2
    }
    
    @classmethod
    def obtener_url_pac(cls, emisor) -> str:
        """
        Obtiene la URL del PAC según el emisor
        
        Args:
            emisor: Instancia del modelo Emisor
            
        Returns:
            str: URL del PAC (pruebas o producción)
        """
        try:
            if emisor.timbrado_prueba:
                url = cls.PAC_URLS['pruebas']
                logger.info(f"Usando entorno de PRUEBAS para emisor {emisor.rfc}: {url}")
            else:
                url = cls.PAC_URLS['produccion']
                logger.info(f"Usando entorno de PRODUCCIÓN para emisor {emisor.rfc}: {url}")
            
            return url
        except Exception as e:
            logger.error(f"Error obteniendo URL PAC para emisor {emisor.rfc}: {e}")
            # Por defecto usar pruebas si hay error
            return cls.PAC_URLS['pruebas']
    
    @classmethod
    def obtener_configuracion_pac(cls, emisor) -> Dict[str, Any]:
        """
        Obtiene la configuración completa del PAC para un emisor
        
        Args:
            emisor: Instancia del modelo Emisor
            
        Returns:
            Dict: Configuración del PAC
        """
        config = cls.CONFIG_DEFAULT.copy()
        
        # URL del PAC
        config['url'] = cls.obtener_url_pac(emisor)
        
        # Credenciales del emisor
        config['credenciales'] = {
            'usuario': emisor.usuario_pac,
            'password': emisor.password_pac,
            'contrato': emisor.contrato,
            'nombre_pac': emisor.nombre_pac
        }
        
        # Archivos de certificado
        config['certificado'] = {
            'archivo_certificado': emisor.archivo_certificado,
            'archivo_llave': emisor.archivo_llave,
            'password_llave': emisor.password_llave
        }
        
        # Datos del emisor
        config['emisor'] = {
            'rfc': emisor.rfc,
            'razon_social': emisor.razon_social,
            'codigo_postal': emisor.codigo_postal,
            'regimen_fiscal': emisor.regimen_fiscal,
            'serie': emisor.serie
        }
        
        # Entorno
        config['entorno'] = 'pruebas' if emisor.timbrado_prueba else 'produccion'
        
        return config
    
    @classmethod
    def validar_configuracion_emisor(cls, emisor) -> Dict[str, Any]:
        """
        Valida que el emisor tenga toda la configuración necesaria
        
        Args:
            emisor: Instancia del modelo Emisor
            
        Returns:
            Dict: Resultado de la validación
        """
        errores = []
        advertencias = []
        
        # Validar campos obligatorios
        if not emisor.usuario_pac:
            errores.append("Usuario PAC es obligatorio")
        
        if not emisor.password_pac:
            errores.append("Contraseña PAC es obligatoria")
        
        if not emisor.contrato:
            errores.append("Contrato PAC es obligatorio")
        
        if not emisor.archivo_certificado:
            errores.append("Archivo de certificado es obligatorio")
        
        if not emisor.archivo_llave:
            errores.append("Archivo de llave es obligatorio")
        
        if not emisor.password_llave:
            errores.append("Contraseña de llave es obligatoria")
        
        # Validar datos del emisor
        if not emisor.rfc:
            errores.append("RFC del emisor es obligatorio")
        
        if not emisor.razon_social:
            errores.append("Razón social es obligatoria")
        
        if not emisor.codigo_postal:
            errores.append("Código postal es obligatorio")
        
        if not emisor.regimen_fiscal:
            errores.append("Régimen fiscal es obligatorio")
        
        if not emisor.serie:
            errores.append("Serie es obligatoria")
        
        # Advertencias
        if emisor.timbrado_prueba:
            advertencias.append("Modo de pruebas activado - No se generarán facturas válidas")
        
        return {
            'valido': len(errores) == 0,
            'errores': errores,
            'advertencias': advertencias,
            'configuracion': cls.obtener_configuracion_pac(emisor) if len(errores) == 0 else None
        }
    
    @classmethod
    def obtener_indicador_entorno(cls, emisor) -> Dict[str, str]:
        """
        Obtiene información para mostrar el indicador de entorno en la UI
        
        Args:
            emisor: Instancia del modelo Emisor
            
        Returns:
            Dict: Información del indicador
        """
        if emisor.timbrado_prueba:
            return {
                'tipo': 'pruebas',
                'texto': 'PRUEBAS',
                'clase_css': 'badge bg-warning text-dark',
                'icono': 'bi-exclamation-triangle',
                'descripcion': 'Facturas de prueba - No válidas fiscalmente'
            }
        else:
            return {
                'tipo': 'produccion',
                'texto': 'PRODUCCIÓN',
                'clase_css': 'badge bg-success',
                'icono': 'bi-check-circle',
                'descripcion': 'Facturas de producción - Válidas fiscalmente'
            }
