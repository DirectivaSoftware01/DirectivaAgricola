# Configuración de Gunicorn para Directiva Agrícola
# Usar con: gunicorn --config gunicorn_config.py directiva_agricola.wsgi:application

import multiprocessing

# Configuración del servidor
bind = "unix:/var/www/directiva_agricola/directiva_agricola.sock"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Configuración de procesos
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Configuración de logging
accesslog = "/var/log/directiva_agricola/gunicorn_access.log"
errorlog = "/var/log/directiva_agricola/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configuración de usuario
user = "www-data"
group = "www-data"

# Configuración de seguridad
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configuración de SSL (si se usa HTTPS directo)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Configuración de desarrollo (comentar en producción)
# reload = True
# debug = True
