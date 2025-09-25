from functools import wraps
from django.conf import settings
from django.db import connections
from django.contrib.auth.decorators import login_required


def with_empresa_db(view_func):
    """
    Decorador que asegura que la vista use la base de datos correcta de la empresa
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Solo aplicar si el usuario está autenticado
        if hasattr(request, 'user') and request.user.is_authenticated:
            empresa_db = request.session.get('empresa_db')
            if empresa_db and empresa_db != 'default':
                try:
                    empresa_db_path = f'{empresa_db}.sqlite3'
                    
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
                    
                    # Solo actualizar si la configuración es diferente
                    current_config = settings.DATABASES.get('default', {})
                    if current_config.get('NAME') != empresa_db_path:
                        # Actualizar la configuración de la base de datos
                        settings.DATABASES['default'] = empresa_db_config
                        
                        # Registrar la conexión en el sistema de conexiones de Django
                        connections.databases['default'] = empresa_db_config
                        
                except Exception as e:
                    # Si hay error, limpiar la sesión y usar base por defecto
                    request.session.pop('empresa_db', None)
                    pass
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def login_required_with_empresa_db(view_func):
    """
    Decorador que combina login_required con with_empresa_db
    """
    return login_required(with_empresa_db(view_func))
