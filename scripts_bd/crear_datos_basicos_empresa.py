#!/usr/bin/env python3
"""
Genera un script SQL con los DATOS BÁSICOS de una base de datos de empresa.

Origen: Directiva_DEMO250901XXX.sqlite3 en la raíz del proyecto
Destino: scripts_bd/datos_basicos_empresa.sql

Estrategia:
- Excluir objetos internos de SQLite (sqlite_*) y tablas de Django típicas.
- Excluir tablas de sesiones/migraciones.
- Por defecto, incluye todas las tablas restantes cuyo volumen sea razonable (<= 1000 filas),
  que suele cubrir catálogos y configuración, además de usuarios.
"""
import sqlite3
from pathlib import Path


EXCLUDE_TABLE_PREFIXES = (
    "sqlite_",
)

EXCLUDE_TABLES = {
    # Django internals y no requeridas para datos base
    "django_migrations",
    "django_session",
    "django_content_type",
    "django_admin_log",
}

MAX_ROWS_PER_TABLE = 1000


def escape_value(value):
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    # tratar como texto
    text = str(value).replace("'", "''")
    return f"'{text}'"


def generar_datos_basicos(db_path: Path, out_path: Path) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"No existe la base de datos: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("-- Datos básicos de empresa\n")
        f.write("-- Generado automaticamente desde {0}\n\n".format(db_path.name))

        # Listar tablas
        cur.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        tables = [row[0] for row in cur.fetchall()]

        for table in tables:
            if table in EXCLUDE_TABLES:
                continue
            if any(table.startswith(pref) for pref in EXCLUDE_TABLE_PREFIXES):
                continue

            # Columnas
            cur.execute(f"PRAGMA table_info({table})")
            cols = cur.fetchall()
            column_names = [c[1] for c in cols]
            if not column_names:
                continue

            # Conteo/lectura filas
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            total = cur.fetchone()[0]

            if total == 0:
                continue

            limit = min(total, MAX_ROWS_PER_TABLE)
            cur.execute(f"SELECT * FROM {table} LIMIT {limit}")
            rows = cur.fetchall()

            f.write(f"-- Tabla: {table} (filas exportadas: {len(rows)} de {total})\n")
            for row in rows:
                values = ", ".join(escape_value(v) for v in row)
                insert_sql = f"INSERT INTO {table} ({', '.join(column_names)}) VALUES ({values});"
                f.write(insert_sql + "\n")
            f.write("\n")

    conn.close()


def main():
    project_root = Path(__file__).resolve().parents[1]
    default_db = project_root / "Directiva_DEMO250901XXX.sqlite3"
    out_file = project_root / "scripts_bd" / "datos_basicos_empresa.sql"

    print(f"Leyendo datos base desde: {default_db}")
    print(f"Escribiendo datos en: {out_file}")
    generar_datos_basicos(default_db, out_file)
    print("Listo.")


if __name__ == "__main__":
    main()


