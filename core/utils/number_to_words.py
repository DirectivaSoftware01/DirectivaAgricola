"""
Utilidades para convertir números a texto en español
"""

def number_to_words_spanish(number):
    """
    Convierte un número a texto en español
    
    Args:
        number: Número decimal (float o Decimal)
        
    Returns:
        str: Número convertido a texto en español
    """
    # Convertir a entero si es decimal
    if isinstance(number, float):
        number = int(number)
    
    # Nombres de números
    units = ['', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve']
    teens = ['diez', 'once', 'doce', 'trece', 'catorce', 'quince', 'dieciséis', 'diecisiete', 'dieciocho', 'diecinueve']
    tens = ['', '', 'veinte', 'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa']
    hundreds = ['', 'ciento', 'doscientos', 'trescientos', 'cuatrocientos', 'quinientos', 'seiscientos', 'setecientos', 'ochocientos', 'novecientos']
    
    if number == 0:
        return 'cero'
    
    if number < 0:
        return 'menos ' + number_to_words_spanish(-number)
    
    if number < 10:
        return units[number]
    
    if number < 20:
        return teens[number - 10]
    
    if number < 100:
        if number % 10 == 0:
            return tens[number // 10]
        elif number < 30:
            if number == 21:
                return 'veintiuno'
            elif number == 22:
                return 'veintidós'
            elif number == 23:
                return 'veintitrés'
            elif number == 26:
                return 'veintiséis'
            elif number == 27:
                return 'veintisiete'
            else:
                return 'veinti' + units[number % 10]
        else:
            return tens[number // 10] + ' y ' + units[number % 10]
    
    if number < 1000:
        if number == 100:
            return 'cien'
        elif number % 100 == 0:
            return hundreds[number // 100]
        else:
            return hundreds[number // 100] + ' ' + number_to_words_spanish(number % 100)
    
    if number < 1000000:
        if number < 2000:
            return 'mil ' + number_to_words_spanish(number % 1000) if number % 1000 != 0 else 'mil'
        else:
            return number_to_words_spanish(number // 1000) + ' mil' + (' ' + number_to_words_spanish(number % 1000) if number % 1000 != 0 else '')
    
    if number < 1000000000:
        if number < 2000000:
            return 'un millón ' + number_to_words_spanish(number % 1000000) if number % 1000000 != 0 else 'un millón'
        else:
            return number_to_words_spanish(number // 1000000) + ' millones' + (' ' + number_to_words_spanish(number % 1000000) if number % 1000000 != 0 else '')
    
    return str(number)  # Para números muy grandes, devolver como string


def format_currency_in_words(amount):
    """
    Formatea una cantidad monetaria en palabras
    
    Args:
        amount: Cantidad decimal (float o Decimal)
        
    Returns:
        str: Cantidad en palabras con formato monetario
    """
    # Separar parte entera y decimal
    integer_part = int(amount)
    decimal_part = int((amount - integer_part) * 100)
    
    # Convertir parte entera a palabras
    if integer_part == 1:
        integer_words = 'un peso'
    else:
        integer_words = number_to_words_spanish(integer_part) + ' pesos'
    
    # Agregar centavos si existen
    if decimal_part > 0:
        if decimal_part == 1:
            decimal_words = 'un centavo'
        else:
            decimal_words = number_to_words_spanish(decimal_part) + ' centavos'
        return integer_words + ' con ' + decimal_words
    
    return integer_words
