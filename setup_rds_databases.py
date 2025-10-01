#!/usr/bin/env python3
"""
Script para configurar las bases de datos en RDS PostgreSQL
Crea las bases de datos de administración y principal, y aplica la estructura
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuración de RDS
RDS_HOSTNAME = "directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com"
RDS_PORT = "5432"
RDS_USERNAME = "postgres"
RDS_PASSWORD = "Directiva2024!"
RDS_ADMIN_DB_NAME = "directiva_administracion"
DS_DB_NAME = "directiva_agricola"

def connect_to_postgres():
    """Conectar a PostgreSQL como superusuario"""
    try:
        conn = psycopg2.connect(
            host=RDS_HOSTNAME,
            port=RDS_PORT,
            user=RDS_USERNAME,
            password=RDS_PASSWORD,
            database="postgres"  # Conectar a la base de datos por defecto
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        return None

def create_database(conn, db_name):
    """Crear base de datos si no existe"""
    try:
        cursor = conn.cursor()
        
        # Verificar si la base de datos existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"ℹ️  La base de datos '{db_name}' ya existe")
            return True
        
        # Crear la base de datos
        cursor.execute(f'CREATE DATABASE "{db_name}"')
        print(f"✅ Base de datos '{db_name}' creada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error creando base de datos '{db_name}': {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()

def setup_administracion_database():
    """Configurar base de datos de administración"""
    print("🏢 Configurando base de datos de administración...")
    
    try:
        # Conectar a la base de datos de administración
        conn = psycopg2.connect(
            host=RDS_HOSTNAME,
            port=RDS_PORT,
            user=RDS_USERNAME,
            password=RDS_PASSWORD,
            database=RDS_ADMIN_DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Crear tabla de empresas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS administracion_empresa (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                rfc VARCHAR(13) UNIQUE NOT NULL,
                direccion TEXT,
                telefono VARCHAR(20),
                email VARCHAR(255),
                db_name VARCHAR(100) UNIQUE NOT NULL,
                activo BOOLEAN DEFAULT TRUE,
                suspendido BOOLEAN DEFAULT FALSE,
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Crear tabla de usuarios de administración
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS administracion_usuarioadministracion (
                id SERIAL PRIMARY KEY,
                username VARCHAR(150) UNIQUE NOT NULL,
                password VARCHAR(128) NOT NULL,
                first_name VARCHAR(30),
                last_name VARCHAR(30),
                email VARCHAR(254),
                is_staff BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                date_joined TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Crear tabla de sesiones de Django
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS django_session (
                session_key VARCHAR(40) PRIMARY KEY,
                session_data TEXT NOT NULL,
                expire_date TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """)
        
        # Crear índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_empresa_rfc ON administracion_empresa(rfc);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_empresa_activo ON administracion_empresa(activo);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_expire ON django_session(expire_date);")
        
        print("✅ Base de datos de administración configurada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error configurando base de datos de administración: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def setup_main_database():
    """Configurar base de datos principal"""
    print("🏭 Configurando base de datos principal...")
    
    try:
        # Conectar a la base de datos principal
        conn = psycopg2.connect(
            host=RDS_HOSTNAME,
            port=RDS_PORT,
            user=RDS_USERNAME,
            password=RDS_PASSWORD,
            database=DS_DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Crear tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                password VARCHAR(128) NOT NULL,
                last_login TIMESTAMP WITH TIME ZONE,
                is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
                username VARCHAR(150) UNIQUE NOT NULL,
                first_name VARCHAR(30),
                last_name VARCHAR(30),
                email VARCHAR(254),
                is_staff BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Crear tabla de sesiones de Django
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS django_session (
                session_key VARCHAR(40) PRIMARY KEY,
                session_data TEXT NOT NULL,
                expire_date TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """)
        
        # Crear tabla de productos/servicios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos_servicios (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(50) UNIQUE NOT NULL,
                descripcion TEXT NOT NULL,
                precio DECIMAL(10,2) NOT NULL,
                unidad VARCHAR(20) NOT NULL,
                activo BOOLEAN DEFAULT TRUE,
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                impuesto_catalogo_id INTEGER
            );
        """)
        
        # Crear tabla de impuestos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipo_impuesto (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(3) NOT NULL,
                nombre VARCHAR(100) NOT NULL,
                tasa DECIMAL(6,4) NOT NULL,
                activo BOOLEAN DEFAULT TRUE,
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Crear tabla de régimen fiscal
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regimen_fiscal (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(10) UNIQUE NOT NULL,
                descripcion TEXT NOT NULL,
                fisica BOOLEAN DEFAULT FALSE,
                moral BOOLEAN DEFAULT FALSE,
                activo BOOLEAN DEFAULT TRUE
            );
        """)
        
        # Crear tabla de usos CFDI
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uso_cfdi (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(10) UNIQUE NOT NULL,
                descripcion TEXT NOT NULL,
                aplica_fisica BOOLEAN DEFAULT TRUE,
                aplica_moral BOOLEAN DEFAULT TRUE,
                activo BOOLEAN DEFAULT TRUE
            );
        """)
        
        # Crear tabla de métodos de pago
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metodo_pago (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(10) UNIQUE NOT NULL,
                descripcion TEXT NOT NULL,
                activo BOOLEAN DEFAULT TRUE
            );
        """)
        
        # Crear tabla de formas de pago
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forma_pago (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(10) UNIQUE NOT NULL,
                descripcion TEXT NOT NULL,
                activo BOOLEAN DEFAULT TRUE
            );
        """)
        
        # Crear tabla de configuración del sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion_sistema (
                id SERIAL PRIMARY KEY,
                clave VARCHAR(100) UNIQUE NOT NULL,
                valor TEXT NOT NULL,
                descripcion TEXT,
                fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Crear índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios(is_active);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_codigo ON productos_servicios(codigo);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos_servicios(activo);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_expire ON django_session(expire_date);")
        
        print("✅ Base de datos principal configurada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error configurando base de datos principal: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def insert_basic_data():
    """Insertar datos básicos en ambas bases de datos"""
    print("📊 Insertando datos básicos...")
    
    # Datos para base de datos de administración
    try:
        conn = psycopg2.connect(
            host=RDS_HOSTNAME,
            port=RDS_PORT,
            user=RDS_USERNAME,
            password=RDS_PASSWORD,
            database=RDS_ADMIN_DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Insertar usuario administrador
        cursor.execute("""
            INSERT INTO administracion_usuarioadministracion 
            (username, password, first_name, last_name, email, is_staff, is_active)
            VALUES ('admin', 'pbkdf2_sha256$600000$hash$hash', 'Administrador', 'Sistema', 'admin@directiva.com', TRUE, TRUE)
            ON CONFLICT (username) DO NOTHING;
        """)
        
        print("✅ Datos básicos de administración insertados")
        
    except Exception as e:
        print(f"❌ Error insertando datos de administración: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    # Datos para base de datos principal
    try:
        conn = psycopg2.connect(
            host=RDS_HOSTNAME,
            port=RDS_PORT,
            user=RDS_USERNAME,
            password=RDS_PASSWORD,
            database=DS_DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Insertar usuario supervisor
        cursor.execute("""
            INSERT INTO usuarios 
            (username, password, first_name, last_name, email, is_superuser, is_staff, is_active)
            VALUES ('supervisor', 'pbkdf2_sha256$600000$hash$hash', 'Supervisor', 'Sistema', 'supervisor@directiva.com', TRUE, TRUE, TRUE)
            ON CONFLICT (username) DO NOTHING;
        """)
        
        # Insertar impuestos básicos
        cursor.execute("""
            INSERT INTO tipo_impuesto (codigo, nombre, tasa, activo) VALUES
            ('002', 'IVA Tasa 16%', 0.1600, TRUE),
            ('002', 'IVA Tasa 0%', 0.0000, TRUE)
            ON CONFLICT DO NOTHING;
        """)
        
        # Insertar régimen fiscal básico
        cursor.execute("""
            INSERT INTO regimen_fiscal (codigo, descripcion, fisica, moral, activo) VALUES
            ('601', 'General de Ley Personas Morales', FALSE, TRUE, TRUE),
            ('603', 'Personas Morales con Fines no Lucrativos', FALSE, TRUE, TRUE)
            ON CONFLICT (codigo) DO NOTHING;
        """)
        
        # Insertar usos CFDI básicos
        cursor.execute("""
            INSERT INTO uso_cfdi (codigo, descripcion, aplica_fisica, aplica_moral, activo) VALUES
            ('G01', 'Adquisición de mercancías', TRUE, TRUE, TRUE),
            ('G02', 'Devoluciones, descuentos o bonificaciones', TRUE, TRUE, TRUE),
            ('G03', 'Gastos en general', TRUE, TRUE, TRUE)
            ON CONFLICT (codigo) DO NOTHING;
        """)
        
        # Insertar métodos de pago básicos
        cursor.execute("""
            INSERT INTO metodo_pago (codigo, descripcion, activo) VALUES
            ('PUE', 'Pago en una sola exhibición', TRUE),
            ('PPD', 'Pago en parcialidades o diferido', TRUE)
            ON CONFLICT (codigo) DO NOTHING;
        """)
        
        # Insertar formas de pago básicas
        cursor.execute("""
            INSERT INTO forma_pago (codigo, descripcion, activo) VALUES
            ('01', 'Efectivo', TRUE),
            ('03', 'Transferencia electrónica de fondos', TRUE),
            ('04', 'Tarjeta de crédito', TRUE)
            ON CONFLICT (codigo) DO NOTHING;
        """)
        
        # Insertar configuración básica
        cursor.execute("""
            INSERT INTO configuracion_sistema (clave, valor, descripcion) VALUES
            ('ciclo_actual', '2025', 'Ciclo fiscal actual'),
            ('version_sistema', '1.0.0', 'Versión del sistema')
            ON CONFLICT (clave) DO NOTHING;
        """)
        
        print("✅ Datos básicos de la base principal insertados")
        
    except Exception as e:
        print(f"❌ Error insertando datos de la base principal: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def main():
    """Función principal"""
    print("🚀 Configurando bases de datos en RDS PostgreSQL...")
    
    # Conectar a PostgreSQL
    conn = connect_to_postgres()
    if not conn:
        sys.exit(1)
    
    try:
        # Crear bases de datos
        if not create_database(conn, RDS_ADMIN_DB_NAME):
            sys.exit(1)
        
        if not create_database(conn, DS_DB_NAME):
            sys.exit(1)
        
        # Configurar bases de datos
        if not setup_administracion_database():
            sys.exit(1)
        
        if not setup_main_database():
            sys.exit(1)
        
        # Insertar datos básicos
        insert_basic_data()
        
        print("✅ Configuración de bases de datos completada exitosamente!")
        print(f"📊 Base de datos de administración: {RDS_ADMIN_DB_NAME}")
        print(f"🏭 Base de datos principal: {DS_DB_NAME}")
        print("🔑 Usuario administrador: admin")
        print("👤 Usuario supervisor: supervisor")
        
    except Exception as e:
        print(f"❌ Error en la configuración: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
