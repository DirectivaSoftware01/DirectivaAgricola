from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.management import call_command
from django.contrib.auth.hashers import make_password
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

class Command(BaseCommand):
    help = 'Crear una nueva empresa con base de datos PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument('--razon-social', type=str, required=True, help='Razón social de la empresa')
        parser.add_argument('--rfc', type=str, required=True, help='RFC de la empresa')
        parser.add_argument('--direccion', type=str, default='', help='Dirección de la empresa')
        parser.add_argument('--telefono', type=str, default='', help='Teléfono de la empresa')
        parser.add_argument('--email', type=str, default='', help='Email de la empresa')
        parser.add_argument('--ciclo-actual', type=str, default='2025', help='Ciclo fiscal actual')

    def handle(self, *args, **options):
        razon_social = options['razon_social']
        rfc = options['rfc']
        direccion = options['direccion']
        telefono = options['telefono']
        email = options['email']
        ciclo_actual = options['ciclo_actual']

        # Nombre de la base de datos de la empresa
        db_name = f"directiva_{rfc.lower()}"

        self.stdout.write(f'🏢 Creando empresa: {razon_social} ({rfc})')
        self.stdout.write(f'🗄️ Base de datos: {db_name}')

        try:
            # 1. Verificar si la empresa ya existe en administración
            from administracion.models import Empresa
            if Empresa.objects.using('administracion').filter(rfc=rfc).exists():
                raise CommandError(f'❌ La empresa con RFC {rfc} ya existe')

            # 2. Crear base de datos PostgreSQL
            self.stdout.write('🔄 Creando base de datos PostgreSQL...')
            self._crear_base_datos_postgresql(db_name)

            # 3. Configurar base de datos temporalmente
            self.stdout.write('⚙️ Configurando base de datos...')
            original_databases = settings.DATABASES.copy()
            
            # Configurar nueva base de datos
            new_db_config = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_name,
                'USER': os.environ.get('RDS_USERNAME', 'postgres'),
                'PASSWORD': os.environ.get('RDS_PASSWORD', 'Directiva2024!'),
                'HOST': os.environ.get('RDS_HOSTNAME', 'directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com'),
                'PORT': os.environ.get('RDS_PORT', '5432'),
                'ATOMIC_REQUESTS': True,
                'TIME_ZONE': 'America/Mexico_City',
                'OPTIONS': {},
                'CONN_MAX_AGE': 0,
                'AUTOCOMMIT': True,
                'CONN_HEALTH_CHECKS': False,
                'TEST': {
                    'CHARSET': None,
                    'COLLATION': None,
                    'MIGRATE': True,
                    'MIRROR': None,
                    'NAME': None
                },
            }
            
            settings.DATABASES['default'] = new_db_config

            # 4. Crear estructura de base de datos
            self.stdout.write('🏗️ Creando estructura de base de datos...')
            self._ejecutar_script_sql(db_name, 'scripts_bd/postgresql/estructura_empresa_postgresql.sql')

            # 5. Insertar datos básicos
            self.stdout.write('📊 Insertando datos básicos...')
            self._ejecutar_script_sql(db_name, 'scripts_bd/postgresql/datos_basicos_empresa_postgresql.sql')

            # 6. Crear usuario supervisor
            self.stdout.write('👤 Creando usuario supervisor...')
            self._crear_usuario_supervisor(db_name)

            # 7. Insertar datos específicos de la empresa
            self._insertar_datos_empresa(db_name, razon_social, rfc, direccion, telefono, email, ciclo_actual)

            # 8. Restaurar configuración original
            settings.DATABASES = original_databases

            # 9. Registrar empresa en base de administración
            self.stdout.write('📝 Registrando empresa en administración...')
            self._registrar_empresa(razon_social, rfc, direccion, telefono, email, db_name)

            self.stdout.write(
                self.style.SUCCESS(f'✅ Empresa "{razon_social}" creada exitosamente!')
            )
            self.stdout.write(f'🔑 Usuario: supervisor')
            self.stdout.write(f'🔑 Contraseña: Directivasbmj1*')
            self.stdout.write(f'🗄️ Base de datos: {db_name}')

        except Exception as e:
            # Restaurar configuración en caso de error
            settings.DATABASES = original_databases
            raise CommandError(f'❌ Error creando empresa: {str(e)}')

    def _crear_base_datos_postgresql(self, db_name):
        """Crear base de datos PostgreSQL"""
        try:
            # Conectar a PostgreSQL como superusuario
            conn = psycopg2.connect(
                host=os.environ.get('RDS_HOSTNAME', 'directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com'),
                port=os.environ.get('RDS_PORT', '5432'),
                user=os.environ.get('RDS_USERNAME', 'postgres'),
                password=os.environ.get('RDS_PASSWORD', 'Directiva2024!'),
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Verificar si la base de datos existe
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone()

            if exists:
                self.stdout.write(f'ℹ️  La base de datos "{db_name}" ya existe')
            else:
                # Crear la base de datos
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                self.stdout.write(f'✅ Base de datos "{db_name}" creada exitosamente')

            cursor.close()
            conn.close()

        except Exception as e:
            raise CommandError(f'Error creando base de datos PostgreSQL: {str(e)}')

    def _ejecutar_script_sql(self, db_name, script_path):
        """Ejecutar script SQL en la base de datos"""
        try:
            # Leer script SQL
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Conectar a la base de datos de la empresa
            conn = psycopg2.connect(
                host=os.environ.get('RDS_HOSTNAME', 'directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com'),
                port=os.environ.get('RDS_PORT', '5432'),
                user=os.environ.get('RDS_USERNAME', 'postgres'),
                password=os.environ.get('RDS_PASSWORD', 'Directiva2024!'),
                database=db_name
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Ejecutar script SQL
            cursor.execute(sql_content)
            self.stdout.write(f'✅ Script {script_path} ejecutado exitosamente')

            cursor.close()
            conn.close()

        except Exception as e:
            raise CommandError(f'Error ejecutando script SQL: {str(e)}')

    def _crear_usuario_supervisor(self, db_name):
        """Crear usuario supervisor en la base de datos"""
        try:
            conn = psycopg2.connect(
                host=os.environ.get('RDS_HOSTNAME', 'directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com'),
                port=os.environ.get('RDS_PORT', '5432'),
                user=os.environ.get('RDS_USERNAME', 'postgres'),
                password=os.environ.get('RDS_PASSWORD', 'Directiva2024!'),
                database=db_name
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Crear hash de contraseña
            password_hash = make_password('Directivasbmj1*')

            # Insertar usuario supervisor
            cursor.execute("""
                INSERT INTO usuarios (username, password, first_name, last_name, email, is_superuser, is_staff, is_active, date_joined)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (username) DO UPDATE SET
                    password = EXCLUDED.password,
                    is_superuser = EXCLUDED.is_superuser,
                    is_staff = EXCLUDED.is_staff,
                    is_active = EXCLUDED.is_active
            """, (
                'supervisor',
                password_hash,
                'Supervisor',
                'Sistema',
                'supervisor@directiva.com',
                True,
                True,
                True
            ))

            self.stdout.write('✅ Usuario supervisor creado exitosamente')
            cursor.close()
            conn.close()

        except Exception as e:
            raise CommandError(f'Error creando usuario supervisor: {str(e)}')

    def _insertar_datos_empresa(self, db_name, razon_social, rfc, direccion, telefono, email, ciclo_actual):
        """Insertar datos específicos de la empresa"""
        try:
            conn = psycopg2.connect(
                host=os.environ.get('RDS_HOSTNAME', 'directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com'),
                port=os.environ.get('RDS_PORT', '5432'),
                user=os.environ.get('RDS_USERNAME', 'postgres'),
                password=os.environ.get('RDS_PASSWORD', 'Directiva2024!'),
                database=db_name
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Actualizar configuración del sistema
            cursor.execute("""
                INSERT INTO configuracion_sistema (clave, valor, descripcion)
                VALUES (%s, %s, %s)
                ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor
            """, ('ciclo_actual', ciclo_actual, 'Ciclo fiscal actual'))

            # Insertar emisor por defecto
            cursor.execute("""
                INSERT INTO emisores (razon_social, rfc, direccion, telefono, email, serie, lugar_expedicion, modo_pruebas, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (rfc) DO NOTHING
            """, (razon_social, rfc, direccion, telefono, email, 'A', 'México', True, True))

            self.stdout.write('✅ Datos específicos de la empresa insertados')
            cursor.close()
            conn.close()

        except Exception as e:
            raise CommandError(f'Error insertando datos de la empresa: {str(e)}')

    def _registrar_empresa(self, razon_social, rfc, direccion, telefono, email, db_name):
        """Registrar empresa en la base de datos de administración"""
        try:
            from administracion.models import Empresa
            
            empresa = Empresa.objects.using('administracion').create(
                nombre=razon_social,
                rfc=rfc,
                direccion=direccion,
                telefono=telefono,
                email=email,
                db_name=db_name,
                activo=True,
                suspendido=False
            )
            
            self.stdout.write(f'✅ Empresa registrada en administración con ID: {empresa.id}')

        except Exception as e:
            raise CommandError(f'Error registrando empresa en administración: {str(e)}')
