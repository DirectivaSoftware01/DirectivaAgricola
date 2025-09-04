from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
import time
import hashlib

class NoCacheMiddleware(MiddlewareMixin):
    """
    Middleware para evitar problemas de cache en navegadores
    """
    
    def process_response(self, request, response):
        # Agregar headers para evitar cache
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        # Agregar ETag único basado en timestamp
        etag = hashlib.md5(str(time.time()).encode()).hexdigest()
        response['ETag'] = f'"{etag}"'
        
        # Para formularios, agregar headers adicionales
        if request.path.startswith('/configuracion/') or request.path.startswith('/login/'):
            response['Last-Modified'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
            response['Vary'] = 'Accept-Encoding, User-Agent'
        
        return response

class StaticFilesNoCacheMiddleware(MiddlewareMixin):
    """
    Middleware específico para archivos estáticos
    """
    
    def process_response(self, request, response):
        if request.path.startswith('/static/'):
            # Para archivos estáticos, usar cache con versionado
            response['Cache-Control'] = 'public, max-age=3600'  # 1 hora
            response['Vary'] = 'Accept-Encoding'
            
            # Agregar timestamp para forzar recarga cuando sea necesario
            timestamp = str(int(time.time()))
            if '?' not in request.path:
                response['X-Timestamp'] = timestamp
        
        return response

