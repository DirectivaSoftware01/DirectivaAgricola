from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.conf import settings
import os
import shutil


class Command(BaseCommand):
    help = 'Comando para crear empresa con configuración básica'

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
            self._insertar_datos_basicos(razon_social, rfc, direccion, telefono, ciclo_actual)

            self.stdout.write(
                self.style.SUCCESS(f'Base de datos {db_name} inicializada correctamente')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al inicializar la base de datos: {str(e)}')
            )
            import traceback
            traceback.print_exc()
            # Limpiar en caso de error
            if os.path.exists(db_path):
                os.remove(db_path)
        finally:
            # Restaurar configuración original
            settings.DATABASES = original_databases

    def _insertar_datos_basicos(self, razon_social, rfc, direccion, telefono, ciclo_actual):
        """Inserta los datos básicos en la nueva base de datos"""
        
        # Conectar a la nueva base de datos
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Insertar configuración del sistema usando SQL directo
            sql_config = f"""
                INSERT OR REPLACE INTO configuracion_sistema 
                (ciclo_actual, nombre_pac, contrato, usuario_pac, password_pac, password_llave, 
                 direccion, razon_social, rfc, telefono, fecha_creacion, fecha_modificacion)
                VALUES ('{ciclo_actual}', 'Prodigia', 'PRODIGIA_CONTRATO', 'prodigia_usuario', 
                        'prodigia_password', 'prodigia_llave_password', '{direccion}', 
                        '{razon_social}', '{rfc}', '{telefono}', datetime('now'), datetime('now'))
            """
            cursor.execute(sql_config)

        self.stdout.write('Configuración del sistema insertada correctamente')
