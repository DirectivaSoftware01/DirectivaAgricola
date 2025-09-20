"""
Utilidades para manejo de zonas horarias en México
Mapea códigos postales mexicanos a sus zonas horarias correspondientes
"""

import pytz
from datetime import datetime
from typing import Optional


def obtener_zona_horaria_mexico(codigo_postal: str) -> str:
    """
    Obtiene la zona horaria de México según el código postal
    
    Args:
        codigo_postal: Código postal de 5 dígitos
        
    Returns:
        str: Zona horaria de México (America/Mexico_City, America/Tijuana, America/Cancun, America/Hermosillo)
    """
    if not codigo_postal or len(codigo_postal) != 5:
        return "America/Mexico_City"  # Zona horaria por defecto
    
    cp = int(codigo_postal)
    
    # Zona horaria de Tijuana (UTC-8)
    if 21000 <= cp <= 22999:  # Baja California
        return "America/Tijuana"
    
    # Zona horaria de Hermosillo/Sonora (UTC-7) - Mexican Pacific Standard Time
    elif 83000 <= cp <= 85999:  # Sonora
        return "America/Hermosillo"
    
    # Zona horaria de Cancún (UTC-5)
    elif 77000 <= cp <= 77999:  # Quintana Roo
        return "America/Cancun"
    
    # Zona horaria de México (UTC-6)
    else:
        return "America/Mexico_City"


def obtener_fecha_actual_mexico(codigo_postal: str) -> datetime:
    """
    Obtiene la fecha y hora actual en la zona horaria correspondiente al código postal
    
    Args:
        codigo_postal: Código postal de 5 dígitos
        
    Returns:
        datetime: Fecha y hora actual en la zona horaria correspondiente
    """
    zona_horaria = obtener_zona_horaria_mexico(codigo_postal)
    tz = pytz.timezone(zona_horaria)
    
    # Obtener la fecha actual en la zona horaria correspondiente
    fecha_actual = datetime.now(tz)
    
    return fecha_actual


def formatear_fecha_cfdi(fecha: datetime) -> str:
    """
    Formatea la fecha para el CFDI en formato AAAA-MM-DDThh:mm:ss
    
    Args:
        fecha: Fecha datetime con zona horaria
        
    Returns:
        str: Fecha formateada para CFDI
    """
    return fecha.strftime('%Y-%m-%dT%H:%M:%S')
