from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections, transaction
from django.conf import settings
import os
import sqlite3
from pathlib import Path
import shutil


class Command(BaseCommand):
    help = 'Crear empresa copiando base de datos principal y configurando datos'

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

        # Crear la base de datos SQLite copiando la principal
        db_path = os.path.join(settings.BASE_DIR, f'{db_name}.sqlite3')
        main_db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        
        if os.path.exists(db_path):
            self.stdout.write(
                self.style.WARNING(f'La base de datos {db_name} ya existe')
            )
            return

        try:
            # Copiar la base de datos principal
            shutil.copy2(main_db_path, db_path)
            self.stdout.write(f'Base de datos copiada: {db_path}')

            # Configurar la nueva base de datos
            new_db_config = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': db_path,
                    'ATOMIC_REQUESTS': True,
                }
            }

            # Agregar la nueva base de datos a la configuración temporalmente
            original_databases = settings.DATABASES.copy()
            settings.DATABASES.update(new_db_config)

            # Configurar la empresa
            self._configurar_empresa(razon_social, rfc, direccion, telefono, ciclo_actual)

            self.stdout.write(
                self.style.SUCCESS(f'Base de datos {db_name} creada y configurada exitosamente')
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

    def _configurar_empresa(self, razon_social, rfc, direccion, telefono, ciclo_actual):
        """Configurar datos específicos de la empresa"""
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Desactivar restricciones de clave foránea temporalmente
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Limpiar datos de la base de datos principal (mantener solo estructura y catálogos)
            self._limpiar_datos_empresa(cursor)
            
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
            
            # Limpiar usuarios existentes y crear supervisor
            cursor.execute("DELETE FROM usuarios")
            
            # Insertar usuario supervisor
            sql_usuario = f"""
                INSERT INTO usuarios 
                (id, username, password, first_name, last_name, email, is_staff, is_active, is_superuser, 
                 date_joined, nombre, puesto, is_admin, last_login)
                VALUES (1, 'supervisor', '{supervisor_password}', 'SUPERVISOR', 'SISTEMA', 
                        'supervisor@directiva.com', 1, 1, 1, datetime('now'), 
                        'SUPERVISOR SISTEMA', 'Administrador', 1, NULL)
            """
            cursor.execute(sql_usuario)
            
            # Reactivar restricciones de clave foránea
            cursor.execute("PRAGMA foreign_keys = ON")

        self.stdout.write('Datos de la empresa y usuario supervisor configurados correctamente')

    def _limpiar_datos_empresa(self, cursor):
        """Limpiar datos específicos de la empresa pero mantener catálogos"""
        # Tablas a limpiar (datos específicos de la empresa)
        tablas_a_limpiar = [
            'clientes',
            'proveedores', 
            'transportistas',
            'lotes_origen',
            'centros_costo',
            'clasificaciones_gasto',
            'productos_servicios',
            'cultivos',
            'remisiones',
            'remisiones_detalles',
            'cuentas_bancarias',
            'core_pagoremision',
            'presupuestos_gasto',
            'presupuestos',
            'presupuesto_detalles',
            'gastos',
            'gasto_detalles',
            'emisores',
            'facturas',
            'factura_detalles',
            'pagos_factura'
        ]
        
        for tabla in tablas_a_limpiar:
            try:
                cursor.execute(f"DELETE FROM {tabla}")
                self.stdout.write(f'Datos limpiados de: {tabla}')
            except sqlite3.Error as e:
                self.stdout.write(f'Advertencia: No se pudo limpiar {tabla}: {e}')
        
        # Mantener catálogos importantes
        self.stdout.write('Catálogos mantenidos: regimen_fiscal, tipo_impuesto, forma_pago, metodo_pago, uso_cfdi')