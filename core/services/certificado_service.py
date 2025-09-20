"""
Servicio para manejo de certificados y sellado digital
Maneja la extracción de datos del certificado, validación de vigencia y generación de sellos
"""

import os
import base64
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import pkcs12
from django.core.files.base import ContentFile
from django.conf import settings

logger = logging.getLogger(__name__)


class CertificadoService:
    """Servicio para manejo de certificados digitales"""
    
    @classmethod
    def extraer_datos_certificado(cls, emisor) -> Dict[str, Any]:
        """
        Extrae datos del certificado .cer
        
        Args:
            emisor: Objeto Emisor con archivo de certificado
            
        Returns:
            Dict: Datos extraídos del certificado
        """
        try:
            # Obtener el certificado en base64
            if not emisor.archivo_certificado:
                raise ValueError("No se ha cargado un archivo de certificado para este emisor")
            
            # Validar que sea base64 válido
            try:
                certificado_data = base64.b64decode(emisor.archivo_certificado)
            except Exception as e:
                raise ValueError(f"El certificado no es un base64 válido: {str(e)}")
            
            # Validar que el certificado tenga el tamaño mínimo esperado
            if len(certificado_data) < 100:
                raise ValueError("El certificado parece estar corrupto o incompleto")
            
            # Intentar cargar el certificado como DER
            try:
                certificado = x509.load_der_x509_certificate(certificado_data)
            except Exception as e:
                # Si falla como DER, intentar como PEM
                try:
                    # Convertir DER a PEM si es necesario
                    pem_data = base64.b64encode(certificado_data).decode('utf-8')
                    pem_cert = f"-----BEGIN CERTIFICATE-----\n{pem_data}\n-----END CERTIFICATE-----"
                    certificado = x509.load_pem_x509_certificate(pem_cert.encode('utf-8'))
                except Exception as pem_error:
                    raise ValueError(f"No se pudo cargar el certificado como DER o PEM: {str(e)} | PEM: {str(pem_error)}")
            
            # Extraer datos
            numero_certificado = certificado.serial_number
            rfc_emisor = None
            razon_social = None
            
            # Extraer RFC y razón social del subject
            for attribute in certificado.subject:
                if attribute.oid == x509.NameOID.COUNTRY_NAME:
                    continue
                elif attribute.oid == x509.NameOID.STATE_OR_PROVINCE_NAME:
                    continue
                elif attribute.oid == x509.NameOID.LOCALITY_NAME:
                    continue
                elif attribute.oid == x509.NameOID.ORGANIZATION_NAME:
                    razon_social = attribute.value
                elif attribute.oid == x509.NameOID.COMMON_NAME:
                    # El RFC puede estar en el CN
                    if len(attribute.value) == 13:  # RFC de persona moral
                        rfc_emisor = attribute.value
                    elif len(attribute.value) == 12:  # RFC de persona física
                        rfc_emisor = attribute.value
            
            # Fechas de vigencia
            fecha_inicio = certificado.not_valid_before_utc
            fecha_fin = certificado.not_valid_after_utc
            
            # Verificar si es FIEL
            es_fiel = cls._es_certificado_fiel(certificado)
            
            return {
                'valido': True,
                'no_certificado': str(numero_certificado),
                'rfc_emisor': rfc_emisor,
                'razon_social': razon_social,
                'fecha_inicio': fecha_inicio.isoformat() if fecha_inicio else None,
                'fecha_fin': fecha_fin.isoformat() if fecha_fin else None,
                'es_fiel': es_fiel,
                'vigente': cls._verificar_vigencia(fecha_inicio, fecha_fin),
                'certificado_base64': base64.b64encode(certificado_data).decode('utf-8')
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo datos del certificado: {e}")
            return {
                'valido': False,
                'error': str(e)
            }
    
    @classmethod
    def _verificar_vigencia(cls, fecha_inicio, fecha_fin) -> bool:
        """
        Verifica si el certificado está vigente
        
        Args:
            fecha_inicio: Fecha de inicio de vigencia
            fecha_fin: Fecha de fin de vigencia
            
        Returns:
            bool: True si está vigente, False si no
        """
        ahora = datetime.now()
        # Convertir fechas a timezone-aware si es necesario
        if fecha_inicio.tzinfo is None:
            fecha_inicio = fecha_inicio.replace(tzinfo=timezone.utc)
        if fecha_fin.tzinfo is None:
            fecha_fin = fecha_fin.replace(tzinfo=timezone.utc)
        if ahora.tzinfo is None:
            ahora = ahora.replace(tzinfo=timezone.utc)
        
        return fecha_inicio <= ahora <= fecha_fin
    
    @classmethod
    def _es_certificado_fiel(cls, certificado) -> bool:
        """
        Verifica si el certificado es FIEL (Firma Electrónica Avanzada)
        
        Args:
            certificado: Objeto del certificado
            
        Returns:
            bool: True si es FIEL, False si es CSD
        """
        try:
            # Verificar el Subject Alternative Name (SAN) para detectar FIEL
            for extension in certificado.extensions:
                if extension.oid == x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME:
                    san = extension.value
                    for name in san:
                        if isinstance(name, x509.RFC822Name):
                            # FIEL típicamente tiene emails en SAN
                            email = name.value.lower()
                            if 'fiel' in email or 'autenticacion' in email:
                                return True
                
                # Verificar Extended Key Usage para FIEL
                elif extension.oid == x509.ExtensionOID.EXTENDED_KEY_USAGE:
                    eku = extension.value
                    # FIEL tiene clientAuthentication y emailProtection
                    if (x509.ExtendedKeyUsageOID.CLIENT_AUTH in eku and 
                        x509.ExtendedKeyUsageOID.EMAIL_PROTECTION in eku):
                        return True
            
            # Verificar el Common Name (CN) del subject
            for attribute in certificado.subject:
                if attribute.oid == x509.NameOID.COMMON_NAME:
                    cn = attribute.value.lower()
                    if 'fiel' in cn or 'autenticacion' in cn:
                        return True
            
            # Si no se encuentra evidencia de FIEL, asumir que es CSD
            return False
            
        except Exception as e:
            logger.warning(f"Error verificando tipo de certificado: {e}")
            # En caso de error, asumir que es CSD (más seguro para facturación)
            return False
    
    @classmethod
    def validar_vigencia_certificado(cls, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """
        Valida la vigencia del certificado
        
        Args:
            fecha_inicio: Fecha de inicio de vigencia
            fecha_fin: Fecha de fin de vigencia
            
        Returns:
            Dict: Resultado de la validación
        """
        ahora = datetime.now(timezone.utc)
        
        # Ajustar fechas a UTC si no tienen timezone
        if fecha_inicio.tzinfo is None:
            fecha_inicio = fecha_inicio.replace(tzinfo=timezone.utc)
        if fecha_fin.tzinfo is None:
            fecha_fin = fecha_fin.replace(tzinfo=timezone.utc)
        
        if ahora < fecha_inicio:
            return {
                'valido': False,
                'estado': 'no_vigente',
                'mensaje': 'El certificado aún no es válido',
                'dias_restantes': (fecha_inicio - ahora).days
            }
        elif ahora > fecha_fin:
            return {
                'valido': False,
                'estado': 'vencido',
                'mensaje': 'El certificado ha vencido',
                'dias_vencido': (ahora - fecha_fin).days
            }
        else:
            dias_restantes = (fecha_fin - ahora).days
            return {
                'valido': True,
                'estado': 'vigente',
                'mensaje': 'El certificado es válido',
                'dias_restantes': dias_restantes,
                'advertencia': dias_restantes < 30  # Advertencia si vence en menos de 30 días
            }
    
    @classmethod
    def cargar_llave_privada(cls, emisor) -> Optional[Any]:
        """
        Carga la llave privada del emisor
        
        Args:
            emisor: Objeto Emisor con archivo de llave y contraseña
            
        Returns:
            Llave privada o None si hay error
        """
        try:
            # Decodificar la llave desde base64
            if not emisor.archivo_llave:
                raise ValueError("No se ha cargado un archivo de llave para este emisor")
            
            llave_data = base64.b64decode(emisor.archivo_llave)
            
            # Intentar cargar como PEM
            try:
                llave_privada = serialization.load_pem_private_key(
                    llave_data,
                    password=emisor.password_llave.encode('utf-8') if emisor.password_llave else None
                )
                return llave_privada
            except Exception:
                # Intentar cargar como DER
                llave_privada = serialization.load_der_private_key(
                    llave_data,
                    password=emisor.password_llave.encode('utf-8') if emisor.password_llave else None
                )
                return llave_privada
                
        except Exception as e:
            logger.error(f"Error cargando llave privada: {e}")
            return None
    
    @classmethod
    def generar_sello_digital(cls, cadena_original: str, llave_privada: Any) -> Optional[str]:
        """
        Genera el sello digital de la cadena original
        
        Args:
            cadena_original: Cadena original del CFDI
            llave_privada: Llave privada para firmar
            
        Returns:
            str: Sello digital en base64 o None si hay error
        """
        try:
            # Convertir cadena a bytes
            cadena_bytes = cadena_original.encode('utf-8')
            
            # Firmar con SHA256 y RSA
            firma = llave_privada.sign(
                cadena_bytes,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            # Convertir a base64
            sello_base64 = base64.b64encode(firma).decode('utf-8')
            
            return sello_base64
            
        except Exception as e:
            logger.error(f"Error generando sello digital: {e}")
            return None
    
    @classmethod
    def validar_certificado_completo(cls, emisor) -> Dict[str, Any]:
        """
        Valida completamente el certificado de un emisor
        
        Args:
            emisor: Instancia del modelo Emisor
            
        Returns:
            Dict: Resultado de la validación completa
        """
        errores = []
        advertencias = []
        
        try:
            # Extraer datos del certificado
            datos_cert = cls.extraer_datos_certificado(emisor)
            
            if not datos_cert['valido']:
                errores.append(f"Error en certificado: {datos_cert.get('error', 'Desconocido')}")
                return {
                    'valido': False,
                    'errores': errores,
                    'advertencias': advertencias
                }
            
            # Validar vigencia (convertir strings ISO de vuelta a datetime)
            from datetime import datetime
            fecha_inicio = datetime.fromisoformat(datos_cert['fecha_inicio']) if datos_cert['fecha_inicio'] else None
            fecha_fin = datetime.fromisoformat(datos_cert['fecha_fin']) if datos_cert['fecha_fin'] else None
            
            vigencia = cls.validar_vigencia_certificado(fecha_inicio, fecha_fin)
            
            if not vigencia['valido']:
                errores.append(vigencia['mensaje'])
            elif vigencia.get('advertencia'):
                advertencias.append(f"El certificado vence en {vigencia['dias_restantes']} días")
            
            # Verificar si es FIEL
            if datos_cert['es_fiel']:
                errores.append("No se puede usar certificado FIEL para facturación")
            
            # Verificar RFC
            if datos_cert['rfc_emisor'] and datos_cert['rfc_emisor'] != emisor.rfc:
                errores.append(f"RFC del certificado ({datos_cert['rfc_emisor']}) no coincide con el emisor ({emisor.rfc})")
            
            # Probar carga de llave privada
            try:
                llave_privada = cls.cargar_llave_privada(emisor)
                llave_cargada = True
            except Exception as e:
                errores.append(f"No se pudo cargar la llave privada: {str(e)}")
                llave_cargada = False
            
            return {
                'valido': len(errores) == 0,
                'errores': errores,
                'advertencias': advertencias,
                'datos_certificado': datos_cert,
                'vigencia': vigencia,
                'llave_cargada': llave_cargada
            }
            
        except Exception as e:
            logger.error(f"Error validando certificado completo: {e}")
            return {
                'valido': False,
                'errores': [f"Error inesperado: {str(e)}"],
                'advertencias': advertencias
            }
