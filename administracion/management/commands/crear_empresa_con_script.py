from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.conf import settings
import os
import sqlite3
from pathlib import Path


class Command(BaseCommand):
    help = 'Crear empresa usando script de base de datos principal'

    def add_arguments(self, parser):
        parser.add_argument('db_name', type=str, help='Nombre de la base de datos')
        parser.add_argument('--razon_social', type=str, required=True, help='Razón social de la empresa')
        parser.add_argument('--rfc', type=str, required=True, help='RFC de la empresa')
        parser.add_argument('--direccion', type=str, required=True, help='Dirección de la empresa')
        parser.add_argument('--telefono', type=str, required=True, help='Teléfono de la empresa')
        parser.add_argument('--ciclo_actual', type=str, required=True, help='Ciclo actual')

    def handle(self, *args, **options):
        db_name = options['db_name']
        razon_social = options['razon_social']
        rfc = options['rfc']
        direccion = options['direccion']
        telefono = options['telefono']
        ciclo_actual = options['ciclo_actual']

        # Crear la base de datos SQLite
        db_path = os.path.join(settings.BASE_DIR, f'{db_name}.sqlite3')
        
        if os.path.exists(db_path):
            self.stdout.write(
                self.style.WARNING(f'La base de datos {db_name} ya existe')
            )
            return

        # Ruta del script SQL
        script_path = Path(settings.BASE_DIR) / 'scripts_bd' / 'base_datos_principal.sql'
        
        if not script_path.exists():
            self.stdout.write(
                self.style.ERROR(f'No se encontró el script: {script_path}')
            )
            return

        try:
            # Crear la nueva base de datos usando el script
            self._crear_bd_desde_script(db_path, script_path)
            
            # Configurar la nueva base de datos
            new_db_config = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': db_path,
                }
            }

            # Agregar la nueva base de datos a la configuración temporalmente
            original_databases = settings.DATABASES.copy()
            settings.DATABASES.update(new_db_config)

            # Insertar datos específicos de la empresa
            self._insertar_datos_empresa(razon_social, rfc, direccion, telefono, ciclo_actual)

            self.stdout.write(
                self.style.SUCCESS(f'Base de datos {db_name} creada exitosamente')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear la base de datos: {str(e)}')
            )
            import traceback
            traceback.print_exc()
            # Limpiar en caso de error
            if os.path.exists(db_path):
                os.remove(db_path)
        finally:
            # Restaurar configuración original
            settings.DATABASES = original_databases

    def _crear_bd_desde_script(self, db_path, script_path):
        """Crear la base de datos desde el script SQL"""
        # Crear nueva base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Leer y ejecutar el script
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
            
        # Dividir el script en statements individuales
        statements = [stmt.strip() for stmt in script_content.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except sqlite3.Error as e:
                    self.stdout.write(f"Advertencia: {e} - Statement: {statement[:100]}...")
        
        conn.commit()
        conn.close()
        
        self.stdout.write(f'Base de datos creada desde script: {db_path}')

    def _insertar_datos_empresa(self, razon_social, rfc, direccion, telefono, ciclo_actual):
        """Insertar datos específicos de la empresa"""
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Actualizar configuración del sistema
            sql_config = f"""
                UPDATE configuracion_sistema SET
                    razon_social = '{razon_social}',
                    rfc = '{rfc}',
                    direccion = '{direccion}',
                    telefono = '{telefono}',
                    ciclo_actual = '{ciclo_actual}',
                    nombre_pac = 'Prodigia',
                    contrato = 'PRODIGIA_CONTRATO',
                    usuario_pac = 'prodigia_usuario',
                    password_pac = 'prodigia_password',
                    password_llave = 'prodigia_llave_password',
                    fecha_modificacion = datetime('now')
                WHERE id = 1
            """
            cursor.execute(sql_config)

            # Crear usuario supervisor
            from django.contrib.auth.hashers import make_password
            supervisor_password = make_password('Directivasbmj1')
            
            # Insertar usuario supervisor en la tabla usuarios
            sql_usuario = f"""
                INSERT OR REPLACE INTO usuarios 
                (username, password, first_name, last_name, email, is_staff, is_active, is_superuser, 
                 date_joined, nombre, puesto, is_admin)
                VALUES ('supervisor', '{supervisor_password}', 'SUPERVISOR', 'SISTEMA', 
                        'supervisor@directiva.com', 1, 1, 1, datetime('now'), 
                        'SUPERVISOR SISTEMA', 'Administrador', 1)
            """
            cursor.execute(sql_usuario)

        self.stdout.write('Datos de la empresa y usuario supervisor insertados correctamente')
