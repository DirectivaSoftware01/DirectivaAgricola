from django import template
import os

register = template.Library()

@register.filter
def basename(value):
    """Extrae el nombre del archivo de una ruta"""
    if value:
        return os.path.basename(str(value))
    return ''
