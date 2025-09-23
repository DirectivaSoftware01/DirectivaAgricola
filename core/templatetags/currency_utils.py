"""
Template tags para utilidades de moneda
"""

from django import template
from decimal import Decimal
from ..utils.number_to_words import format_currency_in_words

register = template.Library()

@register.filter
def currency_in_words(value):
    """
    Convierte una cantidad monetaria a palabras en español
    
    Args:
        value: Cantidad decimal (float, Decimal o string)
        
    Returns:
        str: Cantidad en palabras
    """
    try:
        # Convertir a Decimal para manejo preciso
        if isinstance(value, str):
            amount = Decimal(value)
        elif isinstance(value, (int, float)):
            amount = Decimal(str(value))
        else:
            amount = value
            
        return format_currency_in_words(amount)
    except (ValueError, TypeError, AttributeError):
        return str(value)  # Devolver valor original si hay error

@register.filter
def currency_format(value):
    """
    Formatea una cantidad monetaria con separadores de miles
    
    Args:
        value: Cantidad decimal (float, Decimal o string)
        
    Returns:
        str: Cantidad formateada como $ ###,###,###,##0.00
    """
    try:
        # Convertir a Decimal para manejo preciso
        if isinstance(value, str):
            amount = Decimal(value)
        elif isinstance(value, (int, float)):
            amount = Decimal(str(value))
        else:
            amount = value
            
        # Formatear con 2 decimales
        formatted = f"{amount:,.2f}"
        return f"${formatted}"
    except (ValueError, TypeError, AttributeError):
        return str(value)  # Devolver valor original si hay error

