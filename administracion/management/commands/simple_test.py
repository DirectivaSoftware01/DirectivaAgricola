from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.conf import settings
import os
import shutil


class Command(BaseCommand):
    help = 'Comando simple para crear empresa'

    def add_arguments(self, parser):
        parser.add_argument('db_name', type=str, help='Nombre de la base de datos')

    def handle(self, *args, **options):
        db_name = options['db_name']
        
        # Crear la base de datos SQLite
        db_path = os.path.join(settings.BASE_DIR, f'{db_name}.sqlite3')
        
        if os.path.exists(db_path):
            self.stdout.write(
                self.style.WARNING(f'La base de datos {db_name} ya existe')
            )
            return

        # Copiar la base de datos principal como plantilla
        template_db = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        if os.path.exists(template_db):
            shutil.copy2(template_db, db_path)
            self.stdout.write(f'Base de datos {db_name} creada desde plantilla')
        else:
            self.stdout.write(
                self.style.ERROR('No se encontró la base de datos plantilla')
            )
            return

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

        try:
            # Ejecutar migraciones en la nueva base de datos
            from django.core.management import call_command
            call_command('migrate', database='default', verbosity=0)

            # Insertar datos básicos
            self._insertar_datos_basicos()

            self.stdout.write(
                self.style.SUCCESS(f'Base de datos {db_name} inicializada correctamente')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al inicializar la base de datos: {str(e)}')
            )
            # Limpiar en caso de error
            if os.path.exists(db_path):
                os.remove(db_path)
        finally:
            # Restaurar configuración original
            settings.DATABASES = original_databases

    def _insertar_datos_basicos(self):
        """Inserta los datos básicos en la nueva base de datos"""
        
        # Conectar a la nueva base de datos
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Insertar configuración del sistema
            cursor.execute("""
                INSERT OR REPLACE INTO configuracion_sistema 
                (razon_social, rfc, direccion, telefono, ciclo_actual, fecha_creacion, fecha_modificacion)
                VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, ('Empresa Test', 'TEST123456789', 'Dirección Test', '555-1234', '2024-2025'))

            # Crear usuario supervisor usando SQL directo
            from django.contrib.auth.hashers import make_password
            supervisor_password = make_password('Directivasbmj1')
            
            # Insertar en auth_user
            cursor.execute("""
                INSERT OR IGNORE INTO auth_user 
                (username, first_name, last_name, email, password, is_staff, is_active, is_superuser, date_joined)
                VALUES ('supervisor', 'SUPERVISOR', 'SISTEMA', 'supervisor@directiva.com', ?, 1, 1, 1, datetime('now'))
            """, [supervisor_password])

            # Insertar en core_usuario
            cursor.execute("""
                INSERT OR IGNORE INTO core_usuario 
                (nombre, usuario, password_hash, tipo_usuario, activo, fecha_creacion)
                VALUES ('SUPERVISOR SISTEMA', 'supervisor', ?, 'administrador', 1, datetime('now'))
            """, [supervisor_password])

        self.stdout.write('Datos básicos y usuario supervisor insertados correctamente')
