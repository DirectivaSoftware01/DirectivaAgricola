"""
Utilidades para cálculo de impuestos
"""
from decimal import Decimal

def obtener_tasa_impuesto(impuesto_tipo):
    """
    Obtiene la tasa de impuesto decimal basada en el tipo de impuesto del producto
    
    Args:
        impuesto_tipo (str): Tipo de impuesto ('IVA_16', 'IVA_0', 'IVA_EXENTO')
        
    Returns:
        Decimal: Tasa de impuesto (0.16, 0.00, 0.00)
    """
    tasas_impuesto = {
        'IVA_16': Decimal('0.16'),
        'IVA_0': Decimal('0.00'),
        'IVA_EXENTO': Decimal('0.00')
    }
    
    return tasas_impuesto.get(impuesto_tipo, Decimal('0.00'))

def calcular_impuesto_concepto(importe, impuesto_tipo, objeto_impuesto='02'):
    """
    Calcula el impuesto de un concepto basado en el tipo de impuesto del producto
    
    Args:
        importe (Decimal): Importe del concepto
        impuesto_tipo (str): Tipo de impuesto del producto
        objeto_impuesto (str): Objeto del impuesto ('01', '02', '03')
        
    Returns:
        Decimal: Importe del impuesto calculado
    """
    if objeto_impuesto != '02':  # No objeto del impuesto
        return Decimal('0.00')
    
    tasa = obtener_tasa_impuesto(impuesto_tipo)
    return importe * tasa

def obtener_tasa_impuesto_xml(impuesto_tipo):
    """
    Obtiene la tasa de impuesto formateada para XML CFDI
    
    Args:
        impuesto_tipo (str): Tipo de impuesto del producto
        
    Returns:
        str: Tasa formateada para XML (ej: '0.160000', '0.000000')
    """
    tasa = obtener_tasa_impuesto(impuesto_tipo)
    return f"{tasa:.6f}"
