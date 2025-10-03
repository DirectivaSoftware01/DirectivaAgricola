#!/usr/bin/env python3
"""
Genera un script SQL con la ESTRUCTURA (schema) de una base de datos de empresa
por defecto toma Directiva_DEMO250901XXX.sqlite3 en la raíz del proyecto y
guarda el resultado en scripts_bd/estructura_empresa_limpia.sql
"""
import sqlite3
from pathlib import Path


def generar_estructura_desde_sqlite(db_path: Path, out_path: Path) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"No existe la base de datos: {db_path}")

    connection = sqlite3.connect(str(db_path))
    cursor = connection.cursor()

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("-- Estructura limpia de base de datos de empresa\n")
        f.write("-- Generado automaticamente desde {0}\n\n".format(db_path.name))

        # Obtener objetos tipo tabla e indices definidos por el usuario (excluyendo sqlite_*)
        cursor.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE sql IS NOT NULL
              AND name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            """
        )
        objects = cursor.fetchall()

        for obj_type, name, sql in objects:
            # Solo escribir CREATE statements (tablas, índices, triggers, views si existieran)
            if sql and sql.strip().upper().startswith("CREATE"):
                f.write(f"-- {obj_type.upper()}: {name}\n")
                f.write(sql.strip())
                if not sql.strip().endswith(";"):
                    f.write(";")
                f.write("\n\n")

    connection.close()


def main():
    project_root = Path(__file__).resolve().parents[1]
    default_db = project_root / "Directiva_DEMO250901XXX.sqlite3"
    out_file = project_root / "scripts_bd" / "estructura_empresa_limpia.sql"

    print(f"Leyendo BD de empresa desde: {default_db}")
    print(f"Escribiendo estructura en: {out_file}")

    generar_estructura_desde_sqlite(default_db, out_file)
    print("Listo.")


if __name__ == "__main__":
    main()


