import os
import sqlite3
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.hashers import make_password
from administracion.models import Empresa


class Command(BaseCommand):
    help = 'Crea una nueva empresa usando scripts SQL predefinidos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--razon-social',
            type=str,
            required=True,
            help='Razón social de la empresa'
        )
        parser.add_argument(
            '--rfc',
            type=str,
            required=True,
            help='RFC de la empresa'
        )
        parser.add_argument(
            '--direccion',
            type=str,
            default='',
            help='Dirección de la empresa'
        )
        parser.add_argument(
            '--telefono',
            type=str,
            default='',
            help='Teléfono de la empresa'
        )
        parser.add_argument(
            '--ciclo-actual',
            type=str,
            default='2025',
            help='Ciclo actual de la empresa'
        )

    def handle(self, *args, **options):
        razon_social = options['razon_social']
        rfc = options['rfc']
        direccion = options['direccion']
        telefono = options['telefono']
        ciclo_actual = options['ciclo_actual']

        # Generar nombre de base de datos
        db_name = f"Directiva_{rfc}"
        db_path = Path(settings.BASE_DIR) / f"{db_name}.sqlite3"

        self.stdout.write(f'🏢 Creando empresa: {razon_social} (RFC: {rfc})')
        self.stdout.write(f'📁 Base de datos: {db_name}.sqlite3')

        # Inicializar variable para manejo de errores
        original_databases = None
        
        try:
            # 1. Verificar si la empresa ya existe
            if Empresa.objects.using('administracion').filter(rfc=rfc).exists():
                raise CommandError(f'❌ La empresa con RFC {rfc} ya existe')

            # 2. Crear la base de datos vacía
            if db_path.exists():
                self.stdout.write(f'⚠️  La base de datos {db_name}.sqlite3 ya existe, eliminándola...')
                db_path.unlink()

            # Crear base de datos vacía
            conn = sqlite3.connect(str(db_path))
            conn.close()

            # 3. Configurar Django para usar la nueva base de datos
            new_db_config = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': str(db_path),
                    'ATOMIC_REQUESTS': True,
                    'TIME_ZONE': 'America/Mexico_City',
                    'OPTIONS': {},
                    'CONN_MAX_AGE': 0,
                    'AUTOCOMMIT': True,
                    'CONN_HEALTH_CHECKS': False,
                    'HOST': '',
                    'PASSWORD': '',
                    'PORT': '',
                    'USER': '',
                    'TEST': {
                        'CHARSET': None,
                        'COLLATION': None,
                        'MIGRATE': True,
                        'MIRROR': None,
                        'NAME': None
                    },
                }
            }

            # Actualizar configuración temporalmente
            original_databases = settings.DATABASES.copy()
            settings.DATABASES.update(new_db_config)

            # 4. Crear estructura usando script SQL
            self.stdout.write('🏗️  Creando estructura de base de datos...')
            self._ejecutar_script_sql(db_path, 'scripts_bd/estructura_empresa_limpia.sql')

            # 5. Insertar datos básicos
            self.stdout.write('📊 Insertando catálogos básicos...')
            self._ejecutar_script_sql(db_path, 'scripts_bd/datos_basicos_empresa.sql')

            # 6. Insertar datos específicos de la empresa
            self._insertar_datos_empresa(db_path, razon_social, rfc, direccion, telefono, ciclo_actual)

            # 7. Restaurar configuración original
            settings.DATABASES = original_databases

            # 8. Registrar empresa en base de administración
            self._registrar_empresa(razon_social, rfc, db_name)

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ ¡Empresa creada exitosamente!'))
            self.stdout.write(f'📁 Base de datos: {db_name}.sqlite3')
            self.stdout.write(f'👤 Usuario: supervisor')
            self.stdout.write(f'🔑 Contraseña: Directivasbmj1*')
            self.stdout.write('')
            self.stdout.write('🚀 La empresa está lista para usar inmediatamente')

        except Exception as e:
            # Restaurar configuración en caso de error
            settings.DATABASES = original_databases
            if db_path.exists():
                db_path.unlink()
            raise CommandError(f'❌ Error creando empresa: {str(e)}')

    def _ejecutar_script_sql(self, db_path, script_path):
        """Ejecutar un script SQL en la base de datos"""
        script_file = Path(settings.BASE_DIR) / script_path
        
        if not script_file.exists():
            raise CommandError(f'❌ Script no encontrado: {script_path}')

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Ejecutar el script
            cursor.executescript(script_content)
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise CommandError(f'❌ Error ejecutando script {script_path}: {str(e)}')
        finally:
            conn.close()

    def _insertar_datos_empresa(self, db_path, razon_social, rfc, direccion, telefono, ciclo_actual):
        """Insertar datos específicos de la empresa"""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        try:
            # 1. Actualizar usuario supervisor con contraseña correcta
            supervisor_password = make_password('Directivasbmj1*')
            cursor.execute("""
                UPDATE usuarios 
                SET password = ? 
                WHERE username = 'supervisor'
            """, (supervisor_password,))

            # 2. Actualizar configuración del sistema
            cursor.execute("""
                UPDATE configuracion_sistema 
                SET razon_social = ?, rfc = ?, direccion = ?, telefono = ?, ciclo_actual = ?
                WHERE id = 1
            """, (razon_social, rfc, direccion, telefono, ciclo_actual))

            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise CommandError(f'❌ Error insertando datos de empresa: {str(e)}')
        finally:
            conn.close()

    def _registrar_empresa(self, razon_social, rfc, db_name):
        """Registrar la empresa en la base de datos de administración"""
        self.stdout.write('📝 Registrando empresa en administración...')
        
        empresa = Empresa.objects.using('administracion').create(
            nombre=razon_social,
            rfc=rfc,
            db_name=db_name,
            activo=True,
            suspendido=False
        )
        
        self.stdout.write(f'✅ Empresa registrada con ID: {empresa.id}')
