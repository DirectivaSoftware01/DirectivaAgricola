#!/usr/bin/env python3
"""
Script para crear un script SQL de la base de datos principal
"""
import sqlite3
import os
from pathlib import Path

def crear_script_bd():
    # Ruta de la base de datos principal
    db_path = Path(__file__).parent.parent / 'db.sqlite3'
    script_path = Path(__file__).parent / 'base_datos_principal.sql'
    
    print(f"Creando script desde: {db_path}")
    print(f"Guardando en: {script_path}")
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write("-- Script de la base de datos principal\n")
        f.write("-- Generado automáticamente\n\n")
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        for table_name in tables:
            table_name = table_name[0]
            
            # Obtener estructura de la tabla
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Crear CREATE TABLE statement
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            create_sql = cursor.fetchone()
            
            if create_sql and create_sql[0]:
                f.write(f"-- Tabla: {table_name}\n")
                f.write(f"{create_sql[0]};\n\n")
                
                # Obtener datos de la tabla
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                if rows:
                    # Obtener nombres de columnas
                    column_names = [col[1] for col in columns]
                    
                    f.write(f"-- Datos para {table_name}\n")
                    for row in rows:
                        # Crear INSERT statement
                        values = []
                        for value in row:
                            if value is None:
                                values.append('NULL')
                            elif isinstance(value, str):
                                # Escapar comillas simples
                                escaped_value = value.replace("'", "''")
                                values.append(f"'{escaped_value}'")
                            else:
                                values.append(str(value))
                        
                        insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(values)});"
                        f.write(f"{insert_sql}\n")
                    
                    f.write("\n")
    
    conn.close()
    print(f"Script creado exitosamente: {script_path}")
    print(f"Tamaño del archivo: {script_path.stat().st_size} bytes")

if __name__ == "__main__":
    crear_script_bd()
