import os
import sqlite3
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.hashers import make_password
from administracion.models import Empresa


class Command(BaseCommand):
    help = 'Crea una nueva empresa con estructura completa y datos básicos'

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

        self.stdout.write(f'Creando empresa: {razon_social} (RFC: {rfc})')
        self.stdout.write(f'Base de datos: {db_name}.sqlite3')

        try:
            # 1. Verificar si la empresa ya existe
            if Empresa.objects.using('administracion').filter(rfc=rfc).exists():
                raise CommandError(f'La empresa con RFC {rfc} ya existe')

            # 2. Crear la base de datos vacía
            if db_path.exists():
                self.stdout.write(f'La base de datos {db_name}.sqlite3 ya existe, eliminándola...')
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

            # 4. Aplicar migraciones
            self.stdout.write('Aplicando migraciones...')
            call_command('migrate', '--database=default', verbosity=0)
            call_command('migrate', 'core', '--database=default', verbosity=0)

            # 5. Crear estructura y datos básicos
            self._crear_estructura_basica(db_path)
            self._insertar_datos_basicos(db_path, razon_social, rfc, direccion, telefono, ciclo_actual)

            # 6. Restaurar configuración original
            settings.DATABASES = original_databases

            # 7. Registrar empresa en base de administración
            self._registrar_empresa(razon_social, rfc, db_name)

            self.stdout.write(
                self.style.SUCCESS(f'✅ Empresa {razon_social} creada exitosamente')
            )
            self.stdout.write(f'📁 Base de datos: {db_name}.sqlite3')
            self.stdout.write(f'👤 Usuario: supervisor')
            self.stdout.write(f'🔑 Contraseña: Directivasbmj1*')

        except Exception as e:
            # Restaurar configuración en caso de error
            settings.DATABASES = original_databases
            if db_path.exists():
                db_path.unlink()
            raise CommandError(f'Error creando empresa: {str(e)}')

    def _crear_estructura_basica(self, db_path):
        """Crear estructura básica de la base de datos"""
        self.stdout.write('Creando estructura básica...')
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Crear tabla django_session si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS django_session (
                session_key varchar(40) NOT NULL PRIMARY KEY,
                session_data text NOT NULL,
                expire_date datetime NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def _insertar_datos_basicos(self, db_path, razon_social, rfc, direccion, telefono, ciclo_actual):
        """Insertar datos básicos en la nueva empresa"""
        self.stdout.write('Insertando datos básicos...')
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 1. Crear usuario supervisor
        supervisor_password = make_password('Directivasbmj1*')
        cursor.execute("""
            INSERT INTO usuarios (
                password, last_login, is_superuser, username, first_name, last_name, 
                email, is_staff, is_active, date_joined
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            supervisor_password,
            None,
            1,  # is_superuser
            'supervisor',
            'SUPERVISOR',
            'SISTEMA',
            'supervisor@sistema.com',
            1,  # is_staff
            1,  # is_active
            '2025-01-01 00:00:00'
        ))

        # 2. Insertar catálogos básicos
        self._insertar_catalogos_basicos(cursor)

        # 3. Insertar configuración del sistema
        cursor.execute("""
            INSERT INTO configuracion_sistema (
                razon_social, rfc, direccion, telefono, ciclo_actual,
                certificado_nombre, certificado_password, certificado_ruta,
                pac_usuario, pac_password, pac_url, pac_produccion,
                fecha_creacion, fecha_modificacion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            razon_social,
            rfc,
            direccion,
            telefono,
            ciclo_actual,
            '',  # certificado_nombre
            '',  # certificado_password
            '',  # certificado_ruta
            '',  # pac_usuario
            '',  # pac_password
            '',  # pac_url
            0,   # pac_produccion
            '2025-01-01 00:00:00',
            '2025-01-01 00:00:00'
        ))

        conn.commit()
        conn.close()

    def _insertar_catalogos_basicos(self, cursor):
        """Insertar catálogos básicos del sistema"""
        
        # Regímenes fiscales básicos
        regimenes = [
            ('601', 'General de Ley Personas Morales'),
            ('603', 'Personas Morales con Fines no Lucrativos'),
            ('605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios'),
            ('606', 'Arrendamiento'),
            ('608', 'Demás ingresos'),
            ('610', 'Residentes en el Extranjero sin Establecimiento Permanente en México'),
            ('611', 'Ingresos por Dividendos (socios y accionistas)'),
            ('612', 'Personas Físicas con Actividades Empresariales y Profesionales'),
            ('615', 'Régimen de los ingresos por obtención de premios'),
            ('616', 'Sin obligaciones fiscales'),
            ('620', 'Sociedades Cooperativas de Producción que optan por diferir sus ingresos'),
            ('621', 'Incorporación Fiscal'),
            ('622', 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras'),
            ('623', 'Opcional para Grupos de Sociedades'),
            ('624', 'Coordinados'),
            ('625', 'Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas'),
            ('626', 'Régimen Simplificado de Confianza'),
        ]

        for codigo, descripcion in regimenes:
            cursor.execute("""
                INSERT OR IGNORE INTO regimen_fiscal (codigo, descripcion, fisica, moral, activo, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (codigo, descripcion, 1, 1, 1, '2025-01-01 00:00:00'))

        # Usos de CFDI básicos
        usos_cfdi = [
            ('G01', 'Adquisición de mercancías'),
            ('G02', 'Devoluciones, descuentos o bonificaciones'),
            ('G03', 'Gastos en general'),
            ('I01', 'Construcciones'),
            ('I02', 'Mobilario y equipo de oficina por inversiones'),
            ('I03', 'Equipo de transporte'),
            ('I04', 'Equipo de computo y accesorios'),
            ('I05', 'Dados, troqueles, moldes, matrices y herramental'),
            ('I06', 'Comunicaciones telefónicas'),
            ('I07', 'Comunicaciones satelitales'),
            ('I08', 'Otra maquinaria y equipo'),
            ('D01', 'Honorarios médicos, dentales y gastos hospitalarios'),
            ('D02', 'Gastos médicos por incapacidad o discapacidad'),
            ('D03', 'Gastos funerales'),
            ('D04', 'Donativos'),
            ('D05', 'Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)'),
            ('D06', 'Aportaciones voluntarias al SAR'),
            ('D07', 'Primas por seguros de gastos médicos'),
            ('D08', 'Gastos de transportación escolar obligatoria'),
            ('D09', 'Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones'),
            ('D10', 'Pagos por servicios educativos (colegiaturas)'),
            ('P01', 'Por definir'),
        ]

        for codigo, descripcion in usos_cfdi:
            cursor.execute("""
                INSERT OR IGNORE INTO uso_cfdi (codigo, descripcion, aplica_fisica, aplica_moral, activo, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (codigo, descripcion, 1, 1, 1, '2025-01-01 00:00:00'))

        # Métodos de pago básicos
        metodos_pago = [
            ('PUE', 'Pago en una exhibición'),
            ('PPD', 'Pago en parcialidades o diferido'),
        ]

        for codigo, descripcion in metodos_pago:
            cursor.execute("""
                INSERT OR IGNORE INTO metodo_pago (codigo, descripcion, activo, fecha_creacion)
                VALUES (?, ?, ?, ?)
            """, (codigo, descripcion, 1, '2025-01-01 00:00:00'))

        # Formas de pago básicas
        formas_pago = [
            ('01', 'Efectivo'),
            ('02', 'Cheque nominativo'),
            ('03', 'Transferencia electrónica de fondos'),
            ('04', 'Tarjeta de crédito'),
            ('05', 'Monedero electrónico'),
            ('06', 'Dinero electrónico'),
            ('08', 'Vales de despensa'),
            ('12', 'Dación en pago'),
            ('13', 'Pago por subrogación'),
            ('14', 'Pago por consignación'),
            ('15', 'Condonación'),
            ('17', 'Compensación'),
            ('23', 'Novación'),
            ('24', 'Confusión'),
            ('25', 'Remisión de deuda'),
            ('26', 'Prescripción o caducidad'),
            ('27', 'A satisfacción del acreedor'),
            ('28', 'Tarjeta de débito'),
            ('29', 'Tarjeta de servicios'),
            ('30', 'Aplicación de anticipos'),
            ('31', 'Intermediario pagos'),
            ('99', 'Por definir'),
        ]

        for codigo, descripcion in formas_pago:
            cursor.execute("""
                INSERT OR IGNORE INTO forma_pago (codigo, descripcion, activo, fecha_creacion)
                VALUES (?, ?, ?, ?)
            """, (codigo, descripcion, 1, '2025-01-01 00:00:00'))

        # Impuestos básicos
        impuestos = [
            ('002', 'IVA Tasa 16%', 0.16),
            ('003', 'IVA Tasa 0%', 0.00),
        ]

        for codigo, nombre, tasa in impuestos:
            cursor.execute("""
                INSERT OR IGNORE INTO tipo_impuesto (codigo, nombre, tasa, activo, fecha_creacion)
                VALUES (?, ?, ?, ?, ?)
            """, (codigo, nombre, tasa, 1, '2025-01-01 00:00:00'))

    def _registrar_empresa(self, razon_social, rfc, db_name):
        """Registrar la empresa en la base de datos de administración"""
        self.stdout.write('Registrando empresa en administración...')
        
        empresa = Empresa.objects.using('administracion').create(
            nombre=razon_social,
            rfc=rfc,
            db_name=db_name,
            activo=True,
            suspendido=False
        )
        
        self.stdout.write(f'✅ Empresa registrada con ID: {empresa.id}')
