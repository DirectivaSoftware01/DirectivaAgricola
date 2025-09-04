from django import template
from django.templatetags.static import static
import time

register = template.Library()

@register.simple_tag
def static_with_timestamp(path):
    """
    Genera una URL estática con timestamp para evitar cache
    """
    static_url = static(path)
    timestamp = str(int(time.time()))
    separator = '&' if '?' in static_url else '?'
    return f"{static_url}{separator}v={timestamp}"

@register.simple_tag
def current_timestamp():
    """
    Retorna el timestamp actual para usar en URLs
    """
    return str(int(time.time()))

@register.simple_tag
def cache_buster():
    """
    Genera un valor único para evitar cache
    """
    return str(int(time.time() * 1000))  # Milisegundos para mayor precisión

