from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.conf import settings
import os
import sqlite3


class Command(BaseCommand):
    help = 'Comando para crear empresa con base de datos limpia'

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

            # Insertar regímenes fiscales
            regimenes_fiscales = [
                ('601', 'General de Ley Personas Morales'),
                ('603', 'Personas Morales con Fines no Lucrativos'),
                ('605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios'),
                ('606', 'Arrendamiento'),
                ('608', 'Demás ingresos'),
                ('610', 'Residentes en el Extranjero sin Establecimiento Permanente en México'),
                ('611', 'Ingresos por Dividendos (socios y accionistas)'),
                ('612', 'Personas Físicas con Actividades Empresariales y Profesionales'),
                ('614', 'Ingresos por intereses'),
                ('615', 'Régimen de los ingresos por obtención de premios'),
                ('616', 'Sin obligaciones fiscales'),
                ('620', 'Sociedades Cooperativas de Producción que optan por diferir sus ingresos'),
                ('621', 'Incorporación Fiscal'),
                ('622', 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras'),
                ('623', 'Opcional para Grupos de Sociedades'),
                ('624', 'Coordinados'),
                ('625', 'Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas'),
                ('626', 'Régimen Simplificado de Confianza'),
                ('628', 'Hidrocarburos'),
                ('629', 'De los Regímenes Fiscales Preferentes y de las Empresas Multinacionales'),
                ('630', 'Enajenación de acciones en bolsa de valores'),
            ]

            for codigo, descripcion in regimenes_fiscales:
                sql_regimen = f"""
                    INSERT OR IGNORE INTO regimen_fiscal (codigo, descripcion, activo, fecha_creacion)
                    VALUES ('{codigo}', '{descripcion}', 1, datetime('now'))
                """
                cursor.execute(sql_regimen)

            # Insertar tipos de impuestos
            tipos_impuestos = [
                ('002', 'IVA', 'Impuesto al Valor Agregado', 16.0),
                ('003', 'IEPS', 'Impuesto Especial sobre Producción y Servicios', 0.0),
                ('001', 'ISR', 'Impuesto Sobre la Renta', 0.0),
                ('004', 'ISH', 'Impuesto Sobre Hospedaje', 3.0),
            ]

            for clave, nombre, descripcion, porcentaje in tipos_impuestos:
                sql_impuesto = f"""
                    INSERT OR IGNORE INTO tipo_impuesto 
                    (clave, nombre, descripcion, porcentaje, activo, fecha_creacion)
                    VALUES ('{clave}', '{nombre}', '{descripcion}', {porcentaje}, 1, datetime('now'))
                """
                cursor.execute(sql_impuesto)

            # Insertar formas de pago
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

            for clave, descripcion in formas_pago:
                sql_forma = f"""
                    INSERT OR IGNORE INTO forma_pago 
                    (clave, descripcion, activo, fecha_creacion)
                    VALUES ('{clave}', '{descripcion}', 1, datetime('now'))
                """
                cursor.execute(sql_forma)

            # Insertar métodos de pago
            metodos_pago = [
                ('PUE', 'Pago en una sola exhibición'),
                ('PPD', 'Pago en parcialidades o diferido'),
            ]

            for clave, descripcion in metodos_pago:
                sql_metodo = f"""
                    INSERT OR IGNORE INTO metodo_pago 
                    (clave, descripcion, activo, fecha_creacion)
                    VALUES ('{clave}', '{descripcion}', 1, datetime('now'))
                """
                cursor.execute(sql_metodo)

            # Insertar usos de CFDI
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

            for clave, descripcion in usos_cfdi:
                sql_uso = f"""
                    INSERT OR IGNORE INTO uso_cfdi 
                    (clave, descripcion, activo, fecha_creacion)
                    VALUES ('{clave}', '{descripcion}', 1, datetime('now'))
                """
                cursor.execute(sql_uso)

            # Crear usuario supervisor usando SQL directo
            from django.contrib.auth.hashers import make_password
            supervisor_password = make_password('Directivasbmj1')
            
            # Insertar en core_usuario usando SQL directo
            sql_usuario = f"""
                INSERT OR IGNORE INTO core_usuario 
                (nombre, usuario, password_hash, tipo_usuario, activo, fecha_creacion)
                VALUES ('SUPERVISOR SISTEMA', 'supervisor', '{supervisor_password}', 'administrador', 1, datetime('now'))
            """
            cursor.execute(sql_usuario)

        self.stdout.write('Datos básicos, catálogos y usuario supervisor insertados correctamente')
