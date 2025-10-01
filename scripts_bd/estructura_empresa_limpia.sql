-- Script de estructura base para nuevas empresas
-- Generado automáticamente desde Directiva_DEMO250901XXX.sqlite3
-- Fecha: 2025-01-01

PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

-- Tabla de migraciones de Django
CREATE TABLE IF NOT EXISTS "django_migrations" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "app" varchar(255) NOT NULL,
    "name" varchar(255) NOT NULL,
    "applied" datetime NOT NULL
);

-- Tabla de sesiones de Django
CREATE TABLE IF NOT EXISTS "django_session" (
    "session_key" varchar(40) NOT NULL PRIMARY KEY,
    "session_data" text NOT NULL,
    "expire_date" datetime NOT NULL
);

-- Tabla de tipos de contenido de Django
CREATE TABLE IF NOT EXISTS "django_content_type" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "app_label" varchar(100) NOT NULL,
    "model" varchar(100) NOT NULL
);

-- Tabla de permisos de Django
CREATE TABLE IF NOT EXISTS "auth_permission" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" varchar(255) NOT NULL,
    "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id"),
    "codename" varchar(100) NOT NULL
);

-- Tabla de grupos de Django
CREATE TABLE IF NOT EXISTS "auth_group" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" varchar(150) NOT NULL UNIQUE
);

-- Tabla de permisos de grupos
CREATE TABLE IF NOT EXISTS "auth_group_permissions" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "group_id" integer NOT NULL REFERENCES "auth_group" ("id"),
    "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id")
);

-- Tabla de usuarios (modelo personalizado)
CREATE TABLE IF NOT EXISTS "usuarios" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "password" varchar(128) NOT NULL,
    "last_login" datetime NULL,
    "is_superuser" bool NOT NULL,
    "username" varchar(150) NOT NULL UNIQUE,
    "first_name" varchar(150) NOT NULL,
    "last_name" varchar(150) NOT NULL,
    "email" varchar(254) NOT NULL,
    "is_staff" bool NOT NULL,
    "is_active" bool NOT NULL,
    "date_joined" datetime NOT NULL
);

-- Tabla de permisos de usuarios
CREATE TABLE IF NOT EXISTS "usuarios_user_permissions" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "usuario_id" integer NOT NULL REFERENCES "usuarios" ("id"),
    "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id")
);

-- Tabla de grupos de usuarios
CREATE TABLE IF NOT EXISTS "usuarios_groups" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "usuario_id" integer NOT NULL REFERENCES "usuarios" ("id"),
    "group_id" integer NOT NULL REFERENCES "auth_group" ("id")
);

-- Tabla de configuración del sistema
CREATE TABLE IF NOT EXISTS "configuracion_sistema" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "razon_social" varchar(255) NOT NULL,
    "rfc" varchar(13) NOT NULL,
    "direccion" text NOT NULL,
    "telefono" varchar(20) NOT NULL,
    "ciclo_actual" varchar(4) NOT NULL,
    "certificado_nombre" varchar(255) NOT NULL,
    "certificado_password" varchar(255) NOT NULL,
    "certificado_ruta" varchar(500) NOT NULL,
    "pac_usuario" varchar(100) NOT NULL,
    "pac_password" varchar(100) NOT NULL,
    "pac_url" varchar(500) NOT NULL,
    "pac_produccion" bool NOT NULL,
    "fecha_creacion" datetime NOT NULL,
    "fecha_modificacion" datetime NOT NULL
);

-- Tabla de regímenes fiscales
CREATE TABLE IF NOT EXISTS "regimen_fiscal" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "codigo" varchar(3) NOT NULL,
    "descripcion" varchar(255) NOT NULL,
    "fisica" bool NOT NULL,
    "moral" bool NOT NULL,
    "activo" bool NOT NULL,
    "fecha_creacion" datetime NOT NULL
);

-- Tabla de usos de CFDI
CREATE TABLE IF NOT EXISTS "uso_cfdi" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "codigo" varchar(3) NOT NULL,
    "descripcion" varchar(255) NOT NULL,
    "aplica_fisica" bool NOT NULL,
    "aplica_moral" bool NOT NULL,
    "activo" bool NOT NULL,
    "fecha_creacion" datetime NOT NULL
);

-- Tabla de métodos de pago
CREATE TABLE IF NOT EXISTS "metodo_pago" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "codigo" varchar(3) NOT NULL,
    "descripcion" varchar(255) NOT NULL,
    "activo" bool NOT NULL,
    "fecha_creacion" datetime NOT NULL
);

-- Tabla de formas de pago
CREATE TABLE IF NOT EXISTS "forma_pago" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "codigo" varchar(2) NOT NULL,
    "descripcion" varchar(255) NOT NULL,
    "activo" bool NOT NULL,
    "fecha_creacion" datetime NOT NULL
);

-- Tabla de tipos de impuesto
CREATE TABLE IF NOT EXISTS "tipo_impuesto" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "codigo" varchar(3) NOT NULL,
    "nombre" varchar(100) NOT NULL,
    "tasa" decimal(6,4) NOT NULL,
    "activo" bool NOT NULL,
    "fecha_creacion" datetime NOT NULL,
    "fecha_modificacion" datetime NOT NULL
);

-- Tabla de clientes
CREATE TABLE IF NOT EXISTS "cliente" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "nombre" varchar(255) NOT NULL,
    "rfc" varchar(13) NOT NULL,
    "regimen_fiscal_id" integer NOT NULL REFERENCES "regimen_fiscal" ("id"),
    "direccion" text NOT NULL,
    "ciudad" varchar(100) NOT NULL,
    "estado" varchar(100) NOT NULL,
    "codigo_postal" varchar(10) NOT NULL,
    "telefono" varchar(20) NOT NULL,
    "email" varchar(254) NOT NULL,
    "activo" bool NOT NULL,
    "fecha_creacion" datetime NOT NULL,
    "fecha_modificacion" datetime NOT NULL
);

-- Tabla de productos y servicios
CREATE TABLE IF NOT EXISTS "productos_servicios" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "clave" varchar(50) NOT NULL,
    "descripcion" varchar(255) NOT NULL,
    "unidad_medida" varchar(10) NOT NULL,
    "precio_unitario" decimal(10,2) NOT NULL,
    "impuesto_catalogo_id" integer NULL REFERENCES "tipo_impuesto" ("id"),
    "activo" bool NOT NULL,
    "fecha_creacion" datetime NOT NULL,
    "fecha_modificacion" datetime NOT NULL
);

-- Tabla de emisores
CREATE TABLE IF NOT EXISTS "emisores" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "razon_social" varchar(255) NOT NULL,
    "rfc" varchar(13) NOT NULL,
    "regimen_fiscal_id" integer NOT NULL REFERENCES "regimen_fiscal" ("id"),
    "direccion" text NOT NULL,
    "ciudad" varchar(100) NOT NULL,
    "estado" varchar(100) NOT NULL,
    "codigo_postal" varchar(10) NOT NULL,
    "telefono" varchar(20) NOT NULL,
    "email" varchar(254) NOT NULL,
    "serie" varchar(10) NOT NULL,
    "lugar_expedicion" varchar(100) NOT NULL,
    "modo_pruebas" bool NOT NULL,
    "activo" bool NOT NULL,
    "fecha_creacion" datetime NOT NULL,
    "fecha_modificacion" datetime NOT NULL
);

-- Tabla de facturas
CREATE TABLE IF NOT EXISTS "factura" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "folio" varchar(20) NOT NULL,
    "fecha" date NOT NULL,
    "emisor_id" integer NOT NULL REFERENCES "emisores" ("id"),
    "cliente_id" integer NOT NULL REFERENCES "cliente" ("id"),
    "subtotal" decimal(10,2) NOT NULL,
    "total_impuestos" decimal(10,2) NOT NULL,
    "total" decimal(10,2) NOT NULL,
    "metodo_pago_id" integer NOT NULL REFERENCES "metodo_pago" ("id"),
    "forma_pago_id" integer NOT NULL REFERENCES "forma_pago" ("id"),
    "uso_cfdi_id" integer NOT NULL REFERENCES "uso_cfdi" ("id"),
    "uuid" varchar(36) NULL,
    "fecha_timbrado" datetime NULL,
    "estado" varchar(20) NOT NULL,
    "activo" bool NOT NULL,
    "fecha_creacion" datetime NOT NULL,
    "fecha_modificacion" datetime NOT NULL
);

-- Tabla de detalles de factura
CREATE TABLE IF NOT EXISTS "factura_detalles" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "factura_id" integer NOT NULL REFERENCES "factura" ("id"),
    "producto_servicio_id" integer NOT NULL REFERENCES "productos_servicios" ("id"),
    "cantidad" decimal(10,3) NOT NULL,
    "precio_unitario" decimal(10,2) NOT NULL,
    "importe" decimal(10,2) NOT NULL,
    "impuesto_tasa" decimal(6,4) NOT NULL,
    "impuesto_importe" decimal(10,2) NOT NULL,
    "fecha_creacion" datetime NOT NULL,
    "fecha_modificacion" datetime NOT NULL
);

-- Índices para mejorar rendimiento
CREATE INDEX "idx_usuarios_username" ON "usuarios" ("username");
CREATE INDEX "idx_usuarios_email" ON "usuarios" ("email");
CREATE INDEX "idx_cliente_rfc" ON "cliente" ("rfc");
CREATE INDEX "idx_emisores_rfc" ON "emisores" ("rfc");
CREATE INDEX "idx_factura_folio" ON "factura" ("folio");
CREATE INDEX "idx_factura_uuid" ON "factura" ("uuid");
CREATE INDEX "idx_regimen_fiscal_codigo" ON "regimen_fiscal" ("codigo");
CREATE INDEX "idx_uso_cfdi_codigo" ON "uso_cfdi" ("codigo");
CREATE INDEX "idx_metodo_pago_codigo" ON "metodo_pago" ("codigo");
CREATE INDEX "idx_forma_pago_codigo" ON "forma_pago" ("codigo");
CREATE INDEX "idx_tipo_impuesto_codigo" ON "tipo_impuesto" ("codigo");

COMMIT;
