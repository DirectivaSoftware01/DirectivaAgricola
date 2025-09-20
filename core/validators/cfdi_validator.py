"""
Validadores SAT para CFDI 4.0
Implementa todas las validaciones requeridas por el SAT antes del timbrado
"""

import re
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any, Optional
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class CFDIValidator:
    """
    Validador principal para CFDI 4.0 según Anexo 20 RMF 2022.
    Implementa validaciones adicionales del estándar oficial.
    """
    
    # Catálogos SAT según Anexo 20 (versión actualizada)
    REGIMENES_FISCALES = {
        '601', '603', '605', '606', '608', '610', '611', '612', '614', '615',
        '616', '620', '621', '622', '623', '624', '625', '626', '628', '629', '630'
    }
    
    USOS_CFDI = {
        'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07',
        'I08', 'D01', 'D02', 'D03', 'D04', 'D05', 'D06', 'D07', 'D08', 'D09', 'D10', 'P01'
    }
    
    FORMAS_PAGO = {
        '01', '02', '03', '04', '05', '06', '08', '12', '13', '14', '15', '17',
        '23', '24', '25', '26', '27', '28', '29', '30', '31', '99'
    }
    
    METODOS_PAGO = {'PUE', 'PPD'}
    
    MONEDAS = {'MXN', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'INR'}
    
    EXPORTACION_VALORES = {'01', '02', '03'}
    
    OBJETO_IMPUESTO_VALORES = {'01', '02', '03'}
    
    # Valores válidos según Anexo 20
    TIPO_COMPROBANTE_VALORES = {'I', 'E', 'T', 'N', 'P'}
    
    # Validaciones específicas del Anexo 20
    @classmethod
    def validar_anexo_20_estructura(cls, factura, detalles) -> List[str]:
        """
        Valida la estructura del CFDI según Anexo 20 RMF 2022.
        
        Args:
            factura: Instancia del modelo Factura
            detalles: Lista de instancias de FacturaDetalle
            
        Returns:
            List[str]: Lista de errores encontrados
        """
        errores = []
        
        # Validar versión CFDI
        if not hasattr(factura, 'version') or factura.version != '4.0':
            errores.append("La versión del CFDI debe ser 4.0 según Anexo 20")
        
        # Validar tipo de comprobante
        if hasattr(factura, 'tipo_comprobante'):
            if factura.tipo_comprobante not in cls.TIPO_COMPROBANTE_VALORES:
                errores.append(f"Tipo de comprobante inválido: {factura.tipo_comprobante}")
        
        # Validar exportación
        if factura.exportacion not in cls.EXPORTACION_VALORES:
            errores.append(f"Valor de exportación inválido: {factura.exportacion}")
        
        # Validar método de pago
        if factura.metodo_pago not in cls.METODOS_PAGO:
            errores.append(f"Método de pago inválido: {factura.metodo_pago}")
        
        # Validar forma de pago (condicional)
        if factura.forma_pago and factura.forma_pago not in cls.FORMAS_PAGO:
            errores.append(f"Forma de pago inválida: {factura.forma_pago}")
        
        # Validar uso CFDI
        if factura.uso_cfdi not in cls.USOS_CFDI:
            errores.append(f"Uso CFDI inválido: {factura.uso_cfdi}")
        
        # Validar moneda
        if factura.moneda not in cls.MONEDAS:
            errores.append(f"Moneda inválida: {factura.moneda}")
        
        # Validar tipo de cambio (condicional)
        if factura.moneda != 'MXN' and not factura.tipo_cambio:
            errores.append("Tipo de cambio es requerido para monedas diferentes a MXN")
        
        # Validar lugar de expedición (código postal)
        if not re.match(r'^\d{5}$', factura.lugar_expedicion):
            errores.append("Lugar de expedición debe ser un código postal de 5 dígitos")
        
        return errores
    
    @classmethod
    def validar_factura_completa(cls, factura, detalles) -> Dict[str, Any]:
        """
        Valida una factura completa con todos sus detalles
        
        Args:
            factura: Instancia del modelo Factura
            detalles: Lista de instancias de FacturaDetalle
            
        Returns:
            Dict: Resultado de la validación
        """
        errores = []
        advertencias = []
        
        try:
            # Validar estructura básica
            errores.extend(cls._validar_estructura_basica(factura))
            
            # Validar emisor
            errores.extend(cls._validar_emisor(factura.emisor))
            
            # Validar receptor
            errores.extend(cls._validar_receptor(factura.receptor))
            
            # Validar conceptos
            errores.extend(cls._validar_conceptos(detalles))
            
            # Validar totales
            errores.extend(cls._validar_totales(factura, detalles))
            
            # Validar forma y método de pago
            errores.extend(cls._validar_forma_metodo_pago(factura))
            
            # Validar moneda y tipo de cambio
            errores.extend(cls._validar_moneda_tipo_cambio(factura))
            
            # Validar exportación
            errores.extend(cls._validar_exportacion(factura))
            
            # Validar unicidad de folio
            errores.extend(cls._validar_unicidad_folio(factura))
            
            return {
                'valido': len(errores) == 0,
                'errores': errores,
                'advertencias': advertencias
            }
            
        except Exception as e:
            logger.error(f"Error validando factura completa: {e}")
            return {
                'valido': False,
                'errores': [f"Error inesperado en validación: {str(e)}"],
                'advertencias': advertencias
            }
    
    @classmethod
    def _validar_estructura_basica(cls, factura) -> List[str]:
        """Valida la estructura básica del CFDI"""
        errores = []
        
        # Versión debe ser 4.0
        if not factura.serie:
            errores.append("La serie es obligatoria")
        
        if not factura.folio:
            errores.append("El folio es obligatorio")
        
        # Fecha de emisión
        if not factura.fecha_emision:
            errores.append("La fecha de emisión es obligatoria")
        else:
            # Verificar que no sea futura (usando zona horaria de México)
            from django.utils import timezone as django_timezone
            ahora = django_timezone.now()
            if factura.fecha_emision > ahora:
                errores.append("La fecha de emisión no puede ser futura")
        
        # Lugar de expedición
        if not factura.lugar_expedicion:
            errores.append("El lugar de expedición es obligatorio")
        elif not re.match(r'^\d{5}$', factura.lugar_expedicion):
            errores.append("El lugar de expedición debe ser un código postal de 5 dígitos")
        
        return errores
    
    @classmethod
    def _validar_emisor(cls, emisor) -> List[str]:
        """Valida los datos del emisor"""
        errores = []
        
        if not emisor.rfc:
            errores.append("El RFC del emisor es obligatorio")
        elif not cls._validar_rfc(emisor.rfc):
            errores.append("El RFC del emisor no tiene un formato válido")
        
        if not emisor.razon_social:
            errores.append("La razón social del emisor es obligatoria")
        elif '&' in emisor.razon_social:
            errores.append("La razón social no puede contener el carácter '&' (usar '&amp;' en XML)")
        
        if not emisor.regimen_fiscal:
            errores.append("El régimen fiscal del emisor es obligatorio")
        elif emisor.regimen_fiscal not in cls.REGIMENES_FISCALES:
            errores.append(f"El régimen fiscal '{emisor.regimen_fiscal}' no es válido")
        
        return errores
    
    @classmethod
    def _validar_receptor(cls, receptor) -> List[str]:
        """Valida los datos del receptor"""
        errores = []
        
        if not receptor.rfc:
            errores.append("El RFC del receptor es obligatorio")
        elif not cls._validar_rfc(receptor.rfc, permitir_genericos=True):
            errores.append("El RFC del receptor no tiene un formato válido")
        
        if not receptor.razon_social:
            errores.append("El nombre del receptor es obligatorio")
        elif '&' in receptor.razon_social:
            errores.append("El nombre del receptor no puede contener el carácter '&' (usar '&amp;' en XML)")
        
        if not receptor.codigo_postal:
            errores.append("El código postal del receptor es obligatorio")
        elif not re.match(r'^\d{5}$', receptor.codigo_postal):
            errores.append("El código postal del receptor debe ser de 5 dígitos")
        
        if not receptor.regimen_fiscal:
            errores.append("El régimen fiscal del receptor es obligatorio")
        elif receptor.regimen_fiscal.codigo not in cls.REGIMENES_FISCALES:
            errores.append(f"El régimen fiscal del receptor '{receptor.regimen_fiscal.codigo}' no es válido")
        
        return errores
    
    @classmethod
    def _validar_conceptos(cls, detalles) -> List[str]:
        """Valida los conceptos de la factura"""
        errores = []
        
        if not detalles:
            errores.append("Debe haber al menos un concepto en la factura")
            return errores
        
        for i, detalle in enumerate(detalles, 1):
            # Validar cantidad
            if detalle.cantidad <= 0:
                errores.append(f"Concepto {i}: La cantidad debe ser mayor a 0")
            
            # Validar precio
            if detalle.precio < 0:
                errores.append(f"Concepto {i}: El precio no puede ser negativo")
            
            # Validar clave de producto/servicio
            if not detalle.clave_prod_serv:
                errores.append(f"Concepto {i}: La clave de producto/servicio es obligatoria")
            
            # Validar unidad
            if not detalle.unidad:
                errores.append(f"Concepto {i}: La unidad es obligatoria")
            
            # Validar objeto de impuesto
            if detalle.objeto_impuesto not in cls.OBJETO_IMPUESTO_VALORES:
                errores.append(f"Concepto {i}: El objeto de impuesto '{detalle.objeto_impuesto}' no es válido")
            
            # Validar descripción
            if not detalle.concepto:
                errores.append(f"Concepto {i}: La descripción del concepto es obligatoria")
            elif len(detalle.concepto) > 1000:
                errores.append(f"Concepto {i}: La descripción no puede exceder 1000 caracteres")
        
        return errores
    
    @classmethod
    def _validar_totales(cls, factura, detalles) -> List[str]:
        """Valida los totales de la factura"""
        errores = []
        
        # Calcular subtotal
        subtotal_calculado = sum(detalle.importe for detalle in detalles) or Decimal('0.00')
        subtotal_calculado = subtotal_calculado.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Calcular impuestos
        impuesto_calculado = sum(detalle.impuesto_concepto for detalle in detalles) or Decimal('0.00')
        impuesto_calculado = impuesto_calculado.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Calcular total
        total_calculado = subtotal_calculado + impuesto_calculado
        total_calculado = total_calculado.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Validar subtotal
        if abs(factura.subtotal - subtotal_calculado) > Decimal('0.01'):
            errores.append(f"El subtotal no coincide. Calculado: {subtotal_calculado}, Registrado: {factura.subtotal}")
        
        # Validar impuesto
        if abs(factura.impuesto - impuesto_calculado) > Decimal('0.01'):
            errores.append(f"El impuesto no coincide. Calculado: {impuesto_calculado}, Registrado: {factura.impuesto}")
        
        # Validar total
        if abs(factura.total - total_calculado) > Decimal('0.01'):
            errores.append(f"El total no coincide. Calculado: {total_calculado}, Registrado: {factura.total}")
        
        # Validar que no haya valores negativos
        if factura.subtotal < 0:
            errores.append("El subtotal no puede ser negativo")
        
        if factura.impuesto < 0:
            errores.append("El impuesto no puede ser negativo")
        
        if factura.total < 0:
            errores.append("El total no puede ser negativo")
        
        return errores
    
    @classmethod
    def _validar_forma_metodo_pago(cls, factura) -> List[str]:
        """Valida forma y método de pago"""
        errores = []
        
        # Validar forma de pago
        if not factura.forma_pago:
            errores.append("La forma de pago es obligatoria")
        elif factura.forma_pago not in cls.FORMAS_PAGO:
            errores.append(f"La forma de pago '{factura.forma_pago}' no es válida")
        
        # Validar método de pago
        if not factura.metodo_pago:
            errores.append("El método de pago es obligatorio")
        elif factura.metodo_pago not in cls.METODOS_PAGO:
            errores.append(f"El método de pago '{factura.metodo_pago}' no es válido")
        
        # Validar congruencia entre forma y método de pago
        if factura.metodo_pago == 'PUE' and factura.forma_pago in ['99']:
            errores.append("Si el método de pago es PUE, la forma de pago debe ser específica (no 'Por definir')")
        
        return errores
    
    @classmethod
    def _validar_moneda_tipo_cambio(cls, factura) -> List[str]:
        """Valida moneda y tipo de cambio"""
        errores = []
        
        # Validar moneda
        if not factura.moneda:
            errores.append("La moneda es obligatoria")
        elif factura.moneda not in cls.MONEDAS:
            errores.append(f"La moneda '{factura.moneda}' no es válida")
        
        # Validar tipo de cambio
        if factura.moneda == 'MXN':
            if factura.tipo_cambio != Decimal('1.0000'):
                errores.append("Para moneda MXN, el tipo de cambio debe ser 1.0000")
        else:
            if factura.tipo_cambio <= 0:
                errores.append("El tipo de cambio debe ser mayor a 0 para monedas extranjeras")
            elif factura.tipo_cambio > Decimal('999999.9999'):
                errores.append("El tipo de cambio excede el límite permitido")
        
        return errores
    
    @classmethod
    def _validar_exportacion(cls, factura) -> List[str]:
        """Valida el campo de exportación"""
        errores = []
        
        if not factura.exportacion:
            errores.append("El campo exportación es obligatorio")
        elif factura.exportacion not in cls.EXPORTACION_VALORES:
            errores.append(f"El valor de exportación '{factura.exportacion}' no es válido")
        
        return errores
    
    @classmethod
    def _validar_unicidad_folio(cls, factura) -> List[str]:
        """Valida unicidad de serie+folio"""
        errores = []
        
        # Esta validación se haría a nivel de base de datos
        # Aquí solo verificamos que los campos estén presentes
        if not factura.serie or not factura.folio:
            errores.append("La serie y folio son obligatorios para validar unicidad")
        
        return errores
    
    @classmethod
    def _validar_conceptos_anexo_20(cls, detalles) -> List[str]:
        """
        Valida los conceptos según especificaciones del Anexo 20 RMF 2022.
        
        Args:
            detalles: Lista de instancias de FacturaDetalle
            
        Returns:
            List[str]: Lista de errores encontrados
        """
        errores = []
        
        for detalle in detalles:
            # Validar cantidad (hasta 6 decimales según Anexo 20)
            if detalle.cantidad <= 0:
                errores.append(f"Cantidad debe ser mayor a 0 en concepto: {detalle.concepto}")
            
            # Validar valor unitario (hasta 6 decimales según Anexo 20)
            if detalle.precio <= 0:
                errores.append(f"Valor unitario debe ser mayor a 0 en concepto: {detalle.concepto}")
            
            # Validar importe
            if detalle.importe <= 0:
                errores.append(f"Importe debe ser mayor a 0 en concepto: {detalle.concepto}")
            
            # Validar clave de unidad (3 caracteres según Anexo 20)
            if not hasattr(detalle, 'clave_unidad') or not detalle.clave_unidad:
                errores.append(f"Clave de unidad es requerida en concepto: {detalle.concepto}")
            elif len(detalle.clave_unidad) != 3:
                errores.append(f"Clave de unidad debe tener 3 caracteres en concepto: {detalle.concepto}")
            
            # Validar unidad (requerido según Anexo 20)
            if not detalle.unidad:
                errores.append(f"Unidad es requerida en concepto: {detalle.concepto}")
            
            # Validar clave de producto/servicio (hasta 20 caracteres según Anexo 20)
            if not detalle.clave_prod_serv:
                errores.append(f"Clave de producto/servicio es requerida en concepto: {detalle.concepto}")
            elif len(detalle.clave_prod_serv) > 20:
                errores.append(f"Clave de producto/servicio no puede exceder 20 caracteres en concepto: {detalle.concepto}")
            
            # Validar descripción (hasta 1000 caracteres según Anexo 20)
            if not detalle.concepto:
                errores.append(f"Descripción es requerida en concepto")
            elif len(detalle.concepto) > 1000:
                errores.append(f"Descripción no puede exceder 1000 caracteres en concepto: {detalle.concepto}")
            
            # Validar objeto de impuesto
            if detalle.objeto_impuesto not in cls.OBJETO_IMPUESTO_VALORES:
                errores.append(f"Objeto de impuesto inválido en concepto: {detalle.concepto}")
            
            # Validar número de identificación (hasta 50 caracteres según Anexo 20)
            if hasattr(detalle, 'no_identificacion') and detalle.no_identificacion:
                if len(detalle.no_identificacion) > 50:
                    errores.append(f"Número de identificación no puede exceder 50 caracteres en concepto: {detalle.concepto}")
        
        return errores
    
    @classmethod
    def _validar_rfc(cls, rfc: str, permitir_genericos: bool = False) -> bool:
        """
        Valida el formato del RFC
        
        Args:
            rfc: RFC a validar
            permitir_genericos: Si permite RFCs genéricos (XAXX010101000, XEXE010101000)
            
        Returns:
            bool: True si es válido
        """
        if not rfc:
            return False
        
        rfc = rfc.strip().upper()
        
        # RFCs genéricos
        if permitir_genericos and rfc in ['XAXX010101000', 'XEXE010101000']:
            return True
        
        # Patrones de RFC
        patron_persona_fisica = r'^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$'
        patron_persona_moral = r'^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$'
        
        return bool(re.match(patron_persona_fisica, rfc) or re.match(patron_persona_moral, rfc))
    
    @classmethod
    def validar_uso_cfdi_por_regimen(cls, uso_cfdi: str, regimen_fiscal: str) -> bool:
        """
        Valida que el uso CFDI sea válido para el régimen fiscal
        
        Args:
            uso_cfdi: Uso CFDI a validar
            regimen_fiscal: Régimen fiscal del receptor
            
        Returns:
            bool: True si es válido
        """
        # Reglas básicas de validación (simplificadas)
        # Usos CFDI válidos por régimen fiscal
        usos_por_regimen = {
            # Personas morales con fines no lucrativos
            '601': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas morales del régimen general
            '603': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con actividades empresariales
            '605': {'G01', 'G02', 'G03', 'D01', 'D02', 'D03', 'D04', 'D05', 'D06', 'D07', 'D08', 'D09', 'D10', 'S01', 'P01'},
            # Sueldos y salarios e ingresos asimilados a salarios
            '606': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Régimen de incorporación fiscal
            '608': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por dividendos
            '610': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por intereses
            '611': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por obtención de premios
            '612': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por arrendamiento
            '614': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por regalías
            '615': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Sin obligaciones fiscales (incluye S01 - Sin efectos fiscales)
            '616': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por regalías
            '620': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por regalías
            '621': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por regalías
            '622': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por regalías
            '623': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por regalías
            '624': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por regalías
            '625': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Sin obligaciones fiscales (incluye S01 - Sin efectos fiscales)
            '626': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por regalías
            '628': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por regalías
            '629': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
            # Personas físicas con ingresos por regalías
            '630': {'G01', 'G02', 'G03', 'I01', 'I02', 'I03', 'I04', 'I05', 'I06', 'I07', 'I08', 'S01', 'P01'},
        }
        
        usos_permitidos = usos_por_regimen.get(regimen_fiscal, set())
        return uso_cfdi in usos_permitidos
