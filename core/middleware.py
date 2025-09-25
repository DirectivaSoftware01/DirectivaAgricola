from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
import time
import hashlib
from directiva_agricola.db_router import set_current_company_db
from django.middleware.csrf import get_token

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


class EmpresaDbMiddleware(MiddlewareMixin):
    """Middleware simplificado que solo mantiene la configuración de base de datos"""

    def process_request(self, request):
        # No aplicar middleware a URLs de administración
        if request.path.startswith('/admin-empresas/'):
            return None
            
        # Solo mantener la configuración si ya está establecida
        empresa_db = request.session.get('empresa_db')
        if empresa_db and empresa_db != 'default':
            try:
                from django.conf import settings
                from django.db import connections
                
                empresa_db_path = f'{empresa_db}.sqlite3'
                
                # Solo actualizar si la configuración es diferente
                current_config = settings.DATABASES.get('default', {})
                if current_config.get('NAME') != empresa_db_path:
                    # Crear configuración completa de la base de datos
                    empresa_db_config = {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': empresa_db_path,
                        'ATOMIC_REQUESTS': True,
                        'AUTOCOMMIT': True,
                        'CONN_HEALTH_CHECKS': False,
                        'CONN_MAX_AGE': 0,
                        'HOST': '',
                        'OPTIONS': {},
                        'PASSWORD': '',
                        'PORT': '',
                        'TEST': {
                            'CHARSET': None,
                            'COLLATION': None,
                            'MIGRATE': True,
                            'MIRROR': None,
                            'NAME': None
                        },
                        'TIME_ZONE': None,
                        'USER': ''
                    }
                    
                    # Actualizar la configuración de la base de datos
                    settings.DATABASES['default'] = empresa_db_config
                    
                    # Registrar la conexión en el sistema de conexiones de Django
                    connections.databases['default'] = empresa_db_config
                    
            except Exception as e:
                # Si hay error, limpiar la sesión y usar base por defecto
                request.session.pop('empresa_db', None)
                pass
                    
        return None


class CSRFRefreshMiddleware(MiddlewareMixin):
    """Middleware para manejar el CSRF con bases de datos dinámicas"""

    def process_request(self, request):
        # Solo procesar si el usuario está autenticado y hay una empresa configurada
        if (request.user.is_authenticated and 
            request.session.get('empresa_db') and 
            request.session.get('empresa_db') != 'default'):
            
            # Forzar la regeneración del token CSRF para la nueva base de datos
            try:
                from django.middleware.csrf import get_token
                get_token(request)
            except Exception:
                # Si hay error, no hacer nada
                pass
                
        return None

    def process_response(self, request, response):
        # Solo procesar si el usuario está autenticado y hay una empresa configurada
        if (request.user.is_authenticated and 
            request.session.get('empresa_db') and 
            request.session.get('empresa_db') != 'default'):
            
            # Asegurar que el token CSRF esté presente en la respuesta
            try:
                csrf_token = get_token(request)
                if csrf_token and response.get('Content-Type', '').startswith('text/html'):
                    # Agregar el token CSRF como meta tag si no existe
                    content = response.content.decode('utf-8')
                    if 'csrfmiddlewaretoken' not in content and 'name="csrf-token"' not in content:
                        # Agregar meta tag CSRF en el head
                        if '<head>' in content:
                            content = content.replace(
                                '<head>',
                                f'<head>\n    <meta name="csrf-token" content="{csrf_token}">'
                            )
                            response.content = content.encode('utf-8')
            except Exception:
                # Si hay error, no hacer nada
                pass
                
        return response

