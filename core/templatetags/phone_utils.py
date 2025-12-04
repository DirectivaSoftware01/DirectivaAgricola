"""
Template tags para utilidades de teléfono
"""

import re
from django import template

register = template.Library()

@register.filter
def phone_format(value):
    """
    Formatea un número de teléfono al formato estándar mexicano
    
    Args:
        value: Número de teléfono (string)
        
    Returns:
        str: Número formateado como (XXX) XXX-XXXX o el valor original si no es válido
    """
    if not value:
        return value
    
    # Convertir a string y eliminar espacios, guiones, paréntesis
    phone = str(value).strip()
    
    # Si está vacío después de limpiar, devolver "No especificado"
    if not phone or phone == '':
        return "No especificado"
    
    # Extraer solo dígitos
    digits = re.sub(r'\D', '', phone)
    
    # Si no tiene dígitos, devolver el valor original
    if not digits:
        return value
    
    # Si tiene 10 dígitos (formato mexicano estándar), formatear como (XXX) XXX-XXXX
    if len(digits) == 10:
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    
    # Si tiene 12 dígitos y empieza con 52 (código de país de México), formatear
    if len(digits) == 12 and digits.startswith('52'):
        return f"+52 ({digits[2:5]}) {digits[5:8]}-{digits[8:12]}"
    
    # Si tiene 11 dígitos y empieza con 1 (código de país), formatear
    if len(digits) == 11 and digits.startswith('1'):
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    
    # Para otros formatos, devolver el valor original
    return value

