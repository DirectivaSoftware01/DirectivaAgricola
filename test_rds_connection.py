#!/usr/bin/env python3
"""
Script para verificar conectividad con RDS PostgreSQL
"""

import psycopg2
import sys
import os

# Configuración de RDS
RDS_HOSTNAME = "directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com"
RDS_PORT = "5432"
RDS_USERNAME = "postgres"
RDS_PASSWORD = "Directiva2024!"

def test_connection():
    """Probar conexión a RDS"""
    print("🔍 Probando conectividad con RDS PostgreSQL...")
    print(f"   Host: {RDS_HOSTNAME}")
    print(f"   Puerto: {RDS_PORT}")
    print(f"   Usuario: {RDS_USERNAME}")
    
    try:
        # Intentar conectar
        conn = psycopg2.connect(
            host=RDS_HOSTNAME,
            port=RDS_PORT,
            user=RDS_USERNAME,
            password=RDS_PASSWORD,
            database="postgres",
            connect_timeout=10
        )
        
        print("✅ Conexión exitosa a RDS!")
        
        # Probar consulta
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"📊 Versión de PostgreSQL: {version}")
        
        # Listar bases de datos existentes
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = cursor.fetchall()
        print("🗄️ Bases de datos existentes:")
        for db in databases:
            print(f"   - {db[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Error de conexión: {e}")
        print("\n💡 Posibles soluciones:")
        print("   1. Verificar que RDS esté ejecutándose")
        print("   2. Verificar Security Groups (puerto 5432)")
        print("   3. Verificar credenciales")
        print("   4. Verificar conectividad de red")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def create_databases():
    """Crear bases de datos necesarias"""
    print("\n🏗️ Creando bases de datos...")
    
    try:
        conn = psycopg2.connect(
            host=RDS_HOSTNAME,
            port=RDS_PORT,
            user=RDS_USERNAME,
            password=RDS_PASSWORD,
            database="postgres"
        )
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Crear base de datos de administración
        try:
            cursor.execute("CREATE DATABASE directiva_administracion;")
            print("✅ Base de datos 'directiva_administracion' creada")
        except psycopg2.errors.DuplicateDatabase:
            print("ℹ️  Base de datos 'directiva_administracion' ya existe")
        
        # Crear base de datos principal
        try:
            cursor.execute("CREATE DATABASE directiva_agricola;")
            print("✅ Base de datos 'directiva_agricola' creada")
        except psycopg2.errors.DuplicateDatabase:
            print("ℹ️  Base de datos 'directiva_agricola' ya existe")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando bases de datos: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Verificador de conectividad RDS PostgreSQL")
    print("=" * 50)
    
    # Probar conexión
    if not test_connection():
        sys.exit(1)
    
    # Crear bases de datos
    if not create_databases():
        sys.exit(1)
    
    print("\n✅ Verificación completada exitosamente!")
    print("🎯 RDS está listo para el despliegue")

if __name__ == "__main__":
    main()
