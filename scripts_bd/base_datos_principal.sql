-- Script de la base de datos principal
-- Generado automáticamente

-- Tabla: auth_group
CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);

-- Tabla: auth_group_permissions
CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: auth_permission
CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);

-- Datos para auth_permission
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (1, 1, 'add_logentry', 'Can add log entry');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (2, 1, 'change_logentry', 'Can change log entry');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (3, 1, 'delete_logentry', 'Can delete log entry');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (4, 1, 'view_logentry', 'Can view log entry');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (5, 2, 'add_permission', 'Can add permission');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (6, 2, 'change_permission', 'Can change permission');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (7, 2, 'delete_permission', 'Can delete permission');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (8, 2, 'view_permission', 'Can view permission');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (9, 3, 'add_group', 'Can add group');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (10, 3, 'change_group', 'Can change group');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (11, 3, 'delete_group', 'Can delete group');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (12, 3, 'view_group', 'Can view group');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (13, 4, 'add_contenttype', 'Can add content type');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (14, 4, 'change_contenttype', 'Can change content type');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (15, 4, 'delete_contenttype', 'Can delete content type');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (16, 4, 'view_contenttype', 'Can view content type');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (17, 5, 'add_session', 'Can add session');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (18, 5, 'change_session', 'Can change session');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (19, 5, 'delete_session', 'Can delete session');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (20, 5, 'view_session', 'Can view session');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (21, 6, 'add_usuario', 'Can add Usuario');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (22, 6, 'change_usuario', 'Can change Usuario');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (23, 6, 'delete_usuario', 'Can delete Usuario');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (24, 6, 'view_usuario', 'Can view Usuario');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (25, 7, 'add_regimenfiscal', 'Can add Régimen Fiscal');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (26, 7, 'change_regimenfiscal', 'Can change Régimen Fiscal');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (27, 7, 'delete_regimenfiscal', 'Can delete Régimen Fiscal');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (28, 7, 'view_regimenfiscal', 'Can view Régimen Fiscal');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (29, 8, 'add_cliente', 'Can add Cliente');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (30, 8, 'change_cliente', 'Can change Cliente');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (31, 8, 'delete_cliente', 'Can delete Cliente');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (32, 8, 'view_cliente', 'Can view Cliente');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (33, 9, 'add_proveedor', 'Can add Proveedor');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (34, 9, 'change_proveedor', 'Can change Proveedor');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (35, 9, 'delete_proveedor', 'Can delete Proveedor');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (36, 9, 'view_proveedor', 'Can view Proveedor');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (37, 10, 'add_transportista', 'Can add Transportista');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (38, 10, 'change_transportista', 'Can change Transportista');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (39, 10, 'delete_transportista', 'Can delete Transportista');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (40, 10, 'view_transportista', 'Can view Transportista');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (41, 11, 'add_loteorigen', 'Can add Lote de Origen');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (42, 11, 'change_loteorigen', 'Can change Lote de Origen');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (43, 11, 'delete_loteorigen', 'Can delete Lote de Origen');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (44, 11, 'view_loteorigen', 'Can view Lote de Origen');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (45, 12, 'add_clasificaciongasto', 'Can add Clasificación de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (46, 12, 'change_clasificaciongasto', 'Can change Clasificación de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (47, 12, 'delete_clasificaciongasto', 'Can delete Clasificación de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (48, 12, 'view_clasificaciongasto', 'Can view Clasificación de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (49, 13, 'add_centrocosto', 'Can add Centro de Costo');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (50, 13, 'change_centrocosto', 'Can change Centro de Costo');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (51, 13, 'delete_centrocosto', 'Can delete Centro de Costo');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (52, 13, 'view_centrocosto', 'Can view Centro de Costo');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (53, 14, 'add_productoservicio', 'Can add Producto o Servicio');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (54, 14, 'change_productoservicio', 'Can change Producto o Servicio');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (55, 14, 'delete_productoservicio', 'Can delete Producto o Servicio');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (56, 14, 'view_productoservicio', 'Can view Producto o Servicio');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (57, 15, 'add_configuracionsistema', 'Can add Configuración del Sistema');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (58, 15, 'change_configuracionsistema', 'Can change Configuración del Sistema');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (59, 15, 'delete_configuracionsistema', 'Can delete Configuración del Sistema');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (60, 15, 'view_configuracionsistema', 'Can view Configuración del Sistema');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (61, 16, 'add_cultivo', 'Can add Cultivo');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (62, 16, 'change_cultivo', 'Can change Cultivo');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (63, 16, 'delete_cultivo', 'Can delete Cultivo');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (64, 16, 'view_cultivo', 'Can view Cultivo');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (65, 17, 'add_remision', 'Can add Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (66, 17, 'change_remision', 'Can change Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (67, 17, 'delete_remision', 'Can delete Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (68, 17, 'view_remision', 'Can view Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (69, 18, 'add_remisiondetalle', 'Can add Detalle de Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (70, 18, 'change_remisiondetalle', 'Can change Detalle de Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (71, 18, 'delete_remisiondetalle', 'Can delete Detalle de Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (72, 18, 'view_remisiondetalle', 'Can view Detalle de Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (73, 19, 'add_cuentabancaria', 'Can add Cuenta Bancaria');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (74, 19, 'change_cuentabancaria', 'Can change Cuenta Bancaria');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (75, 19, 'delete_cuentabancaria', 'Can delete Cuenta Bancaria');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (76, 19, 'view_cuentabancaria', 'Can view Cuenta Bancaria');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (77, 20, 'add_pagoremision', 'Can add Pago de Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (78, 20, 'change_pagoremision', 'Can change Pago de Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (79, 20, 'delete_pagoremision', 'Can delete Pago de Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (80, 20, 'view_pagoremision', 'Can view Pago de Remisión');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (81, 21, 'add_presupuestogasto', 'Can add Presupuesto de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (82, 21, 'change_presupuestogasto', 'Can change Presupuesto de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (83, 21, 'delete_presupuestogasto', 'Can delete Presupuesto de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (84, 21, 'view_presupuestogasto', 'Can view Presupuesto de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (85, 22, 'add_presupuesto', 'Can add Presupuesto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (86, 22, 'change_presupuesto', 'Can change Presupuesto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (87, 22, 'delete_presupuesto', 'Can delete Presupuesto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (88, 22, 'view_presupuesto', 'Can view Presupuesto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (89, 23, 'add_presupuestodetalle', 'Can add Detalle de Presupuesto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (90, 23, 'change_presupuestodetalle', 'Can change Detalle de Presupuesto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (91, 23, 'delete_presupuestodetalle', 'Can delete Detalle de Presupuesto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (92, 23, 'view_presupuestodetalle', 'Can view Detalle de Presupuesto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (93, 24, 'add_gasto', 'Can add Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (94, 24, 'change_gasto', 'Can change Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (95, 24, 'delete_gasto', 'Can delete Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (96, 24, 'view_gasto', 'Can view Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (97, 25, 'add_gastodetalle', 'Can add Detalle de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (98, 25, 'change_gastodetalle', 'Can change Detalle de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (99, 25, 'delete_gastodetalle', 'Can delete Detalle de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (100, 25, 'view_gastodetalle', 'Can view Detalle de Gasto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (101, 26, 'add_emisor', 'Can add Emisor');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (102, 26, 'change_emisor', 'Can change Emisor');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (103, 26, 'delete_emisor', 'Can delete Emisor');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (104, 26, 'view_emisor', 'Can view Emisor');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (105, 27, 'add_factura', 'Can add Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (106, 27, 'change_factura', 'Can change Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (107, 27, 'delete_factura', 'Can delete Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (108, 27, 'view_factura', 'Can view Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (109, 28, 'add_facturadetalle', 'Can add Detalle de Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (110, 28, 'change_facturadetalle', 'Can change Detalle de Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (111, 28, 'delete_facturadetalle', 'Can delete Detalle de Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (112, 28, 'view_facturadetalle', 'Can view Detalle de Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (113, 29, 'add_pagofactura', 'Can add Pago de Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (114, 29, 'change_pagofactura', 'Can change Pago de Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (115, 29, 'delete_pagofactura', 'Can delete Pago de Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (116, 29, 'view_pagofactura', 'Can view Pago de Factura');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (117, 30, 'add_empresa', 'Can add empresa');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (118, 30, 'change_empresa', 'Can change empresa');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (119, 30, 'delete_empresa', 'Can delete empresa');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (120, 30, 'view_empresa', 'Can view empresa');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (121, 31, 'add_usuarioadministracion', 'Can add usuario administracion');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (122, 31, 'change_usuarioadministracion', 'Can change usuario administracion');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (123, 31, 'delete_usuarioadministracion', 'Can delete usuario administracion');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (124, 31, 'view_usuarioadministracion', 'Can view usuario administracion');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (125, 32, 'add_impuesto', 'Can add Impuesto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (126, 32, 'change_impuesto', 'Can change Impuesto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (127, 32, 'delete_impuesto', 'Can delete Impuesto');
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES (128, 32, 'view_impuesto', 'Can view Impuesto');

-- Tabla: centros_costo
CREATE TABLE "centros_costo" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "descripcion" varchar(200) NOT NULL, "hectareas" decimal NOT NULL, "observaciones" text NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: clasificaciones_gasto
CREATE TABLE "clasificaciones_gasto" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "descripcion" varchar(200) NOT NULL, "observaciones" text NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: clientes
CREATE TABLE "clientes" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "razon_social" varchar(200) NOT NULL, "codigo_postal" varchar(5) NOT NULL, "rfc" varchar(13) NOT NULL UNIQUE, "domicilio" text NOT NULL, "telefono" varchar(15) NOT NULL, "email_principal" varchar(254) NOT NULL, "email_alterno" varchar(254) NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "regimen_fiscal_id" bigint NOT NULL REFERENCES "regimen_fiscal" ("id") DEFERRABLE INITIALLY DEFERRED, "ciudad" varchar(100) NULL, "direccion_entrega" text NULL, "estado" varchar(100) NULL, "numero_bodega" varchar(50) NULL, "telefono_bodega" varchar(15) NULL);

-- Tabla: configuracion_sistema
CREATE TABLE "configuracion_sistema" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "ciclo_actual" varchar(100) NOT NULL, "nombre_pac" varchar(50) NOT NULL, "contrato" varchar(100) NOT NULL, "usuario_pac" varchar(100) NOT NULL, "password_pac" varchar(100) NOT NULL, "certificado" text NULL, "llave" text NULL, "password_llave" varchar(100) NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "usuario_creacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "certificado_nombre" varchar(255) NULL, "llave_nombre" varchar(255) NULL, "direccion" text NOT NULL, "razon_social" varchar(200) NOT NULL, "rfc" varchar(13) NOT NULL, "telefono" varchar(15) NOT NULL, "logo_empresa" varchar(100) NULL, "ultima_actualizacion_catalogos" datetime NULL);

-- Datos para configuracion_sistema
INSERT INTO configuracion_sistema (id, ciclo_actual, nombre_pac, contrato, usuario_pac, password_pac, certificado, llave, password_llave, fecha_creacion, fecha_modificacion, usuario_creacion_id, usuario_modificacion_id, certificado_nombre, llave_nombre, direccion, razon_social, rfc, telefono, logo_empresa, ultima_actualizacion_catalogos) VALUES (5, '2025-2026', 'PRODIGIA', '1234567', 'usuario@directiva.mx', '123456', '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', '123456', '2025-09-04 22:56:13.467271', '2025-09-23 19:51:15.358621', 1, 1, '00001000000709278691.cer', 'JLD160727T52_20240808_163953.key', 'CD. OBREGÓN, SON.', 'DAVID ANAYA MARISCAL', 'AAM940620IA3', '6441351366', 'logos_empresa/logoAgroDam_tOebQmT.png', '2025-09-18 21:40:56.914852');
INSERT INTO configuracion_sistema (id, ciclo_actual, nombre_pac, contrato, usuario_pac, password_pac, certificado, llave, password_llave, fecha_creacion, fecha_modificacion, usuario_creacion_id, usuario_modificacion_id, certificado_nombre, llave_nombre, direccion, razon_social, rfc, telefono, logo_empresa, ultima_actualizacion_catalogos) VALUES (6, '2024-2025', 'Prodigia', 'PRODIGIA_CONTRATO', 'prodigia_usuario', 'prodigia_password', NULL, NULL, 'prodigia_llave_password', '2025-09-24 22:13:19', '2025-09-24 22:13:19', NULL, NULL, NULL, NULL, 'Dirección Prodigia Test', 'Empresa Prodigia Test', 'PROD123456789', '555-1234', NULL, NULL);
INSERT INTO configuracion_sistema (id, ciclo_actual, nombre_pac, contrato, usuario_pac, password_pac, certificado, llave, password_llave, fecha_creacion, fecha_modificacion, usuario_creacion_id, usuario_modificacion_id, certificado_nombre, llave_nombre, direccion, razon_social, rfc, telefono, logo_empresa, ultima_actualizacion_catalogos) VALUES (7, '2024-2025', 'Prodigia', 'PRODIGIA_CONTRATO', 'prodigia_usuario', 'prodigia_password', NULL, NULL, 'prodigia_llave_password', '2025-09-24 22:13:31', '2025-09-24 22:13:31', NULL, NULL, NULL, NULL, 'Dirección Prodigia Test', 'Empresa Prodigia Test 2', 'PROD123456789', '555-1234', NULL, NULL);
INSERT INTO configuracion_sistema (id, ciclo_actual, nombre_pac, contrato, usuario_pac, password_pac, certificado, llave, password_llave, fecha_creacion, fecha_modificacion, usuario_creacion_id, usuario_modificacion_id, certificado_nombre, llave_nombre, direccion, razon_social, rfc, telefono, logo_empresa, ultima_actualizacion_catalogos) VALUES (8, '2024-2025', 'Prodigia', 'PRODIGIA_CONTRATO', 'prodigia_usuario', 'prodigia_password', NULL, NULL, 'prodigia_llave_password', '2025-09-24 22:13:52', '2025-09-24 22:13:52', NULL, NULL, NULL, NULL, 'Dirección Simple Test', 'Empresa Simple Test', 'SIMP123456789', '555-1234', NULL, NULL);
INSERT INTO configuracion_sistema (id, ciclo_actual, nombre_pac, contrato, usuario_pac, password_pac, certificado, llave, password_llave, fecha_creacion, fecha_modificacion, usuario_creacion_id, usuario_modificacion_id, certificado_nombre, llave_nombre, direccion, razon_social, rfc, telefono, logo_empresa, ultima_actualizacion_catalogos) VALUES (9, '2024-2025', 'Prodigia', 'PRODIGIA_CONTRATO', 'prodigia_usuario', 'prodigia_password', NULL, NULL, 'prodigia_llave_password', '2025-09-24 22:14:08', '2025-09-24 22:14:08', NULL, NULL, NULL, NULL, 'Dirección Final Test', 'Empresa Final Test', 'FINAL123456789', '555-1234', NULL, NULL);
INSERT INTO configuracion_sistema (id, ciclo_actual, nombre_pac, contrato, usuario_pac, password_pac, certificado, llave, password_llave, fecha_creacion, fecha_modificacion, usuario_creacion_id, usuario_modificacion_id, certificado_nombre, llave_nombre, direccion, razon_social, rfc, telefono, logo_empresa, ultima_actualizacion_catalogos) VALUES (10, '2024-2025', 'Prodigia', 'PRODIGIA_CONTRATO', 'prodigia_usuario', 'prodigia_password', NULL, NULL, 'prodigia_llave_password', '2025-09-24 22:14:41', '2025-09-24 22:14:41', NULL, NULL, NULL, NULL, 'Dirección Config Test', 'Empresa Config Test', 'CONF123456789', '555-1234', NULL, NULL);
INSERT INTO configuracion_sistema (id, ciclo_actual, nombre_pac, contrato, usuario_pac, password_pac, certificado, llave, password_llave, fecha_creacion, fecha_modificacion, usuario_creacion_id, usuario_modificacion_id, certificado_nombre, llave_nombre, direccion, razon_social, rfc, telefono, logo_empresa, ultima_actualizacion_catalogos) VALUES (11, '2024-2025', 'Prodigia', 'PRODIGIA_CONTRATO', 'prodigia_usuario', 'prodigia_password', NULL, NULL, 'prodigia_llave_password', '2025-09-24 22:14:59', '2025-09-24 22:14:59', NULL, NULL, NULL, NULL, 'Dirección Final Complete', 'Empresa Final Complete', 'FINAL123456789', '555-1234', NULL, NULL);
INSERT INTO configuracion_sistema (id, ciclo_actual, nombre_pac, contrato, usuario_pac, password_pac, certificado, llave, password_llave, fecha_creacion, fecha_modificacion, usuario_creacion_id, usuario_modificacion_id, certificado_nombre, llave_nombre, direccion, razon_social, rfc, telefono, logo_empresa, ultima_actualizacion_catalogos) VALUES (12, '2024-2025', 'Prodigia', 'PRODIGIA_CONTRATO', 'prodigia_usuario', 'prodigia_password', NULL, NULL, 'prodigia_llave_password', '2025-09-24 22:18:21', '2025-09-24 22:18:21', NULL, NULL, NULL, NULL, 'Dirección Limpia Test', 'Empresa Limpia Test', 'LIMP123456789', '555-1234', NULL, NULL);
INSERT INTO configuracion_sistema (id, ciclo_actual, nombre_pac, contrato, usuario_pac, password_pac, certificado, llave, password_llave, fecha_creacion, fecha_modificacion, usuario_creacion_id, usuario_modificacion_id, certificado_nombre, llave_nombre, direccion, razon_social, rfc, telefono, logo_empresa, ultima_actualizacion_catalogos) VALUES (13, '2024-2025', 'Prodigia', 'PRODIGIA_CONTRATO', 'prodigia_usuario', 'prodigia_password', NULL, NULL, 'prodigia_llave_password', '2025-09-24 22:19:18', '2025-09-24 22:19:18', NULL, NULL, NULL, NULL, 'Dirección Real Test', 'Empresa Real Test', 'REAL123456789', '555-1234', NULL, NULL);

-- Tabla: core_pagoremision
CREATE TABLE "core_pagoremision" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "metodo_pago" varchar(20) NOT NULL, "monto" decimal NOT NULL, "fecha_pago" date NOT NULL, "referencia" varchar(100) NULL, "observaciones" text NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "remision_id" integer NOT NULL REFERENCES "remisiones" ("codigo") DEFERRABLE INITIALLY DEFERRED, "usuario_creacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "cuenta_bancaria_id" integer NULL REFERENCES "cuentas_bancarias" ("codigo") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: cuentas_bancarias
CREATE TABLE "cuentas_bancarias" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "nombre_banco" varchar(200) NOT NULL, "numero_cuenta" varchar(50) NOT NULL, "nombre_corto" varchar(100) NOT NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: cultivos
CREATE TABLE "cultivos" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "nombre" varchar(100) NOT NULL, "variedad" varchar(100) NOT NULL, "observaciones" text NOT NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "usuario_creacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: django_admin_log
CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);

-- Tabla: django_content_type
CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);

-- Datos para django_content_type
INSERT INTO django_content_type (id, app_label, model) VALUES (1, 'admin', 'logentry');
INSERT INTO django_content_type (id, app_label, model) VALUES (2, 'auth', 'permission');
INSERT INTO django_content_type (id, app_label, model) VALUES (3, 'auth', 'group');
INSERT INTO django_content_type (id, app_label, model) VALUES (4, 'contenttypes', 'contenttype');
INSERT INTO django_content_type (id, app_label, model) VALUES (5, 'sessions', 'session');
INSERT INTO django_content_type (id, app_label, model) VALUES (6, 'core', 'usuario');
INSERT INTO django_content_type (id, app_label, model) VALUES (7, 'core', 'regimenfiscal');
INSERT INTO django_content_type (id, app_label, model) VALUES (8, 'core', 'cliente');
INSERT INTO django_content_type (id, app_label, model) VALUES (9, 'core', 'proveedor');
INSERT INTO django_content_type (id, app_label, model) VALUES (10, 'core', 'transportista');
INSERT INTO django_content_type (id, app_label, model) VALUES (11, 'core', 'loteorigen');
INSERT INTO django_content_type (id, app_label, model) VALUES (12, 'core', 'clasificaciongasto');
INSERT INTO django_content_type (id, app_label, model) VALUES (13, 'core', 'centrocosto');
INSERT INTO django_content_type (id, app_label, model) VALUES (14, 'core', 'productoservicio');
INSERT INTO django_content_type (id, app_label, model) VALUES (15, 'core', 'configuracionsistema');
INSERT INTO django_content_type (id, app_label, model) VALUES (16, 'core', 'cultivo');
INSERT INTO django_content_type (id, app_label, model) VALUES (17, 'core', 'remision');
INSERT INTO django_content_type (id, app_label, model) VALUES (18, 'core', 'remisiondetalle');
INSERT INTO django_content_type (id, app_label, model) VALUES (19, 'core', 'cuentabancaria');
INSERT INTO django_content_type (id, app_label, model) VALUES (20, 'core', 'pagoremision');
INSERT INTO django_content_type (id, app_label, model) VALUES (21, 'core', 'presupuestogasto');
INSERT INTO django_content_type (id, app_label, model) VALUES (22, 'core', 'presupuesto');
INSERT INTO django_content_type (id, app_label, model) VALUES (23, 'core', 'presupuestodetalle');
INSERT INTO django_content_type (id, app_label, model) VALUES (24, 'core', 'gasto');
INSERT INTO django_content_type (id, app_label, model) VALUES (25, 'core', 'gastodetalle');
INSERT INTO django_content_type (id, app_label, model) VALUES (26, 'core', 'emisor');
INSERT INTO django_content_type (id, app_label, model) VALUES (27, 'core', 'factura');
INSERT INTO django_content_type (id, app_label, model) VALUES (28, 'core', 'facturadetalle');
INSERT INTO django_content_type (id, app_label, model) VALUES (29, 'core', 'pagofactura');
INSERT INTO django_content_type (id, app_label, model) VALUES (30, 'administracion', 'empresa');
INSERT INTO django_content_type (id, app_label, model) VALUES (31, 'administracion', 'usuarioadministracion');
INSERT INTO django_content_type (id, app_label, model) VALUES (32, 'core', 'impuesto');

-- Tabla: django_migrations
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);

-- Datos para django_migrations
INSERT INTO django_migrations (id, app, name, applied) VALUES (1, 'contenttypes', '0001_initial', '2025-09-04 18:09:09.210005');
INSERT INTO django_migrations (id, app, name, applied) VALUES (2, 'contenttypes', '0002_remove_content_type_name', '2025-09-04 18:09:09.212390');
INSERT INTO django_migrations (id, app, name, applied) VALUES (3, 'auth', '0001_initial', '2025-09-04 18:09:09.216566');
INSERT INTO django_migrations (id, app, name, applied) VALUES (4, 'auth', '0002_alter_permission_name_max_length', '2025-09-04 18:09:09.218842');
INSERT INTO django_migrations (id, app, name, applied) VALUES (5, 'auth', '0003_alter_user_email_max_length', '2025-09-04 18:09:09.220622');
INSERT INTO django_migrations (id, app, name, applied) VALUES (6, 'auth', '0004_alter_user_username_opts', '2025-09-04 18:09:09.224266');
INSERT INTO django_migrations (id, app, name, applied) VALUES (7, 'auth', '0005_alter_user_last_login_null', '2025-09-04 18:09:09.226204');
INSERT INTO django_migrations (id, app, name, applied) VALUES (8, 'auth', '0006_require_contenttypes_0002', '2025-09-04 18:09:09.226754');
INSERT INTO django_migrations (id, app, name, applied) VALUES (9, 'auth', '0007_alter_validators_add_error_messages', '2025-09-04 18:09:09.228202');
INSERT INTO django_migrations (id, app, name, applied) VALUES (10, 'auth', '0008_alter_user_username_max_length', '2025-09-04 18:09:09.230034');
INSERT INTO django_migrations (id, app, name, applied) VALUES (11, 'auth', '0009_alter_user_last_name_max_length', '2025-09-04 18:09:09.231781');
INSERT INTO django_migrations (id, app, name, applied) VALUES (12, 'auth', '0010_alter_group_name_max_length', '2025-09-04 18:09:09.233927');
INSERT INTO django_migrations (id, app, name, applied) VALUES (13, 'auth', '0011_update_proxy_permissions', '2025-09-04 18:09:09.235942');
INSERT INTO django_migrations (id, app, name, applied) VALUES (14, 'auth', '0012_alter_user_first_name_max_length', '2025-09-04 18:09:09.237637');
INSERT INTO django_migrations (id, app, name, applied) VALUES (15, 'core', '0001_initial', '2025-09-04 18:09:09.241703');
INSERT INTO django_migrations (id, app, name, applied) VALUES (16, 'admin', '0001_initial', '2025-09-04 18:09:09.244983');
INSERT INTO django_migrations (id, app, name, applied) VALUES (17, 'admin', '0002_logentry_remove_auto_add', '2025-09-04 18:09:09.248252');
INSERT INTO django_migrations (id, app, name, applied) VALUES (18, 'admin', '0003_logentry_add_action_flag_choices', '2025-09-04 18:09:09.250517');
INSERT INTO django_migrations (id, app, name, applied) VALUES (19, 'core', '0002_regimenfiscal_cliente', '2025-09-04 18:09:09.255322');
INSERT INTO django_migrations (id, app, name, applied) VALUES (20, 'core', '0003_cliente_ciudad_cliente_direccion_entrega_and_more', '2025-09-04 18:09:09.270458');
INSERT INTO django_migrations (id, app, name, applied) VALUES (21, 'core', '0004_proveedor', '2025-09-04 18:09:09.275831');
INSERT INTO django_migrations (id, app, name, applied) VALUES (22, 'core', '0005_transportista', '2025-09-04 18:09:09.280190');
INSERT INTO django_migrations (id, app, name, applied) VALUES (23, 'core', '0006_loteorigen', '2025-09-04 18:09:09.284765');
INSERT INTO django_migrations (id, app, name, applied) VALUES (24, 'core', '0007_clasificaciongasto', '2025-09-04 18:09:09.290590');
INSERT INTO django_migrations (id, app, name, applied) VALUES (25, 'core', '0008_centrocosto', '2025-09-04 18:09:09.295509');
INSERT INTO django_migrations (id, app, name, applied) VALUES (26, 'core', '0009_productoservicio', '2025-09-04 18:09:09.301690');
INSERT INTO django_migrations (id, app, name, applied) VALUES (27, 'core', '0010_alter_productoservicio_unidad_medida', '2025-09-04 18:09:09.308466');
INSERT INTO django_migrations (id, app, name, applied) VALUES (28, 'core', '0011_configuracionsistema', '2025-09-04 18:09:09.313909');
INSERT INTO django_migrations (id, app, name, applied) VALUES (29, 'core', '0012_alter_configuracionsistema_ciclo_actual_and_more', '2025-09-04 18:09:09.333567');
INSERT INTO django_migrations (id, app, name, applied) VALUES (30, 'core', '0013_cultivo', '2025-09-04 18:09:09.340037');
INSERT INTO django_migrations (id, app, name, applied) VALUES (31, 'core', '0014_alter_cultivo_usuario_creacion_and_more', '2025-09-04 18:09:09.349785');
INSERT INTO django_migrations (id, app, name, applied) VALUES (32, 'core', '0015_remision_remisiondetalle_and_more', '2025-09-04 18:09:09.412194');
INSERT INTO django_migrations (id, app, name, applied) VALUES (33, 'core', '0016_fix_peso_promedio_field', '2025-09-04 18:09:09.420427');
INSERT INTO django_migrations (id, app, name, applied) VALUES (34, 'core', '0017_increase_decimal_fields_precision', '2025-09-04 18:09:09.459724');
INSERT INTO django_migrations (id, app, name, applied) VALUES (35, 'core', '0018_round_decimal_fields_to_2_places', '2025-09-04 18:09:09.506126');
INSERT INTO django_migrations (id, app, name, applied) VALUES (36, 'core', '0019_alter_remisiondetalle_peso_promedio', '2025-09-04 18:09:09.514341');
INSERT INTO django_migrations (id, app, name, applied) VALUES (37, 'core', '0020_remision_liquidada', '2025-09-04 18:09:09.523394');
INSERT INTO django_migrations (id, app, name, applied) VALUES (38, 'core', '0021_auto_20250903_1308', '2025-09-04 18:09:09.530672');
INSERT INTO django_migrations (id, app, name, applied) VALUES (39, 'core', '0022_remisiondetalle_fecha_liquidacion_and_more', '2025-09-04 18:09:09.546519');
INSERT INTO django_migrations (id, app, name, applied) VALUES (40, 'core', '0023_remision_cancelada_remision_fecha_cancelacion_and_more', '2025-09-04 18:09:09.579422');
INSERT INTO django_migrations (id, app, name, applied) VALUES (41, 'core', '0024_remision_facturado_remision_pagado', '2025-09-04 18:09:09.597198');
INSERT INTO django_migrations (id, app, name, applied) VALUES (42, 'sessions', '0001_initial', '2025-09-04 18:09:09.598903');
INSERT INTO django_migrations (id, app, name, applied) VALUES (43, 'core', '0025_cuentabancaria', '2025-09-10 00:06:48.444001');
INSERT INTO django_migrations (id, app, name, applied) VALUES (44, 'core', '0026_configuracionsistema_certificado_nombre_and_more', '2025-09-10 00:59:29.032169');
INSERT INTO django_migrations (id, app, name, applied) VALUES (45, 'core', '0027_pagoremision', '2025-09-10 01:05:55.416616');
INSERT INTO django_migrations (id, app, name, applied) VALUES (46, 'core', '0028_remision_fecha_pago', '2025-09-10 01:19:05.255919');
INSERT INTO django_migrations (id, app, name, applied) VALUES (47, 'core', '0029_alter_pagoremision_cuenta_bancaria', '2025-09-10 01:19:29.125020');
INSERT INTO django_migrations (id, app, name, applied) VALUES (48, 'core', '0030_presupuesto_gasto', '2025-09-10 17:06:37.266622');
INSERT INTO django_migrations (id, app, name, applied) VALUES (49, 'core', '0031_alter_presupuestogasto_options_presupuesto_and_more', '2025-09-10 17:59:10.808990');
INSERT INTO django_migrations (id, app, name, applied) VALUES (50, 'core', '0032_gasto_gastodetalle_gasto_gastos_presupu_5346b6_idx_and_more', '2025-09-10 19:01:11.873692');
INSERT INTO django_migrations (id, app, name, applied) VALUES (51, 'core', '0033_add_empresa_fields', '2025-09-10 23:24:04.766898');
INSERT INTO django_migrations (id, app, name, applied) VALUES (52, 'core', '0034_add_logo_empresa_field', '2025-09-10 23:42:49.076505');
INSERT INTO django_migrations (id, app, name, applied) VALUES (53, 'core', '0035_emisor', '2025-09-12 21:14:50.620138');
INSERT INTO django_migrations (id, app, name, applied) VALUES (54, 'core', '0036_emisor_contrato_emisor_nombre_pac_and_more', '2025-09-12 21:38:33.241196');
INSERT INTO django_migrations (id, app, name, applied) VALUES (55, 'core', '0037_add_timbrado_prueba_to_emisor', '2025-09-12 22:18:26.342020');
INSERT INTO django_migrations (id, app, name, applied) VALUES (56, 'core', '0038_add_regimen_fiscal_to_emisor', '2025-09-13 00:00:47.614599');
INSERT INTO django_migrations (id, app, name, applied) VALUES (57, 'core', '0039_add_factura_models', '2025-09-13 00:56:18.654977');
INSERT INTO django_migrations (id, app, name, applied) VALUES (58, 'core', '0040_add_serie_to_emisor', '2025-09-13 01:35:25.677434');
INSERT INTO django_migrations (id, app, name, applied) VALUES (59, 'core', '0041_add_cancelada_to_factura', '2025-09-13 02:02:31.055264');
INSERT INTO django_migrations (id, app, name, applied) VALUES (60, 'core', '0042_add_timbrado_fields_to_factura', '2025-09-17 19:41:26.716364');
INSERT INTO django_migrations (id, app, name, applied) VALUES (61, 'core', '0043_configuracionsistema_ultima_actualizacion_catalogos', '2025-09-17 20:31:40.613578');
INSERT INTO django_migrations (id, app, name, applied) VALUES (62, 'core', '0044_change_certificate_storage', '2025-09-17 21:19:42.214235');
INSERT INTO django_migrations (id, app, name, applied) VALUES (63, 'core', '0045_add_nombre_archivos_emisor', '2025-09-17 22:13:50.192289');
INSERT INTO django_migrations (id, app, name, applied) VALUES (64, 'core', '0046_fix_decimal_places_impuestos', '2025-09-18 00:22:15.416091');
INSERT INTO django_migrations (id, app, name, applied) VALUES (65, 'core', '0047_cfdi_4_0_anexo_20_fields', '2025-09-18 00:34:36.901251');
INSERT INTO django_migrations (id, app, name, applied) VALUES (66, 'core', '0048_fix_cantidad_max_digits', '2025-09-18 00:55:03.020688');
INSERT INTO django_migrations (id, app, name, applied) VALUES (67, 'core', '0049_fix_totales_decimal_places', '2025-09-18 00:57:03.250792');
INSERT INTO django_migrations (id, app, name, applied) VALUES (68, 'core', '0050_update_uso_cfdi_choices', '2025-09-18 21:48:38.966061');
INSERT INTO django_migrations (id, app, name, applied) VALUES (69, 'core', '0051_add_informacion_global_fields', '2025-09-18 21:57:58.394795');
INSERT INTO django_migrations (id, app, name, applied) VALUES (70, 'core', '0052_add_codigo_qr_field', '2025-09-18 23:26:59.116189');
INSERT INTO django_migrations (id, app, name, applied) VALUES (71, 'core', '0053_add_cadena_original_sat_field', '2025-09-18 23:47:07.063545');
INSERT INTO django_migrations (id, app, name, applied) VALUES (72, 'core', '0054_add_pago_factura_model', '2025-09-19 19:24:20.764365');
INSERT INTO django_migrations (id, app, name, applied) VALUES (73, 'core', '0055_add_timbrado_fields_to_pago_factura', '2025-09-22 21:34:16.257585');
INSERT INTO django_migrations (id, app, name, applied) VALUES (74, 'core', '0056_pagofactura_num_parcialidad', '2025-09-23 00:38:15.855301');
INSERT INTO django_migrations (id, app, name, applied) VALUES (75, 'core', '0057_pagofactura_forma_pago', '2025-09-23 00:42:15.693815');
INSERT INTO django_migrations (id, app, name, applied) VALUES (76, 'core', '0058_pagofactura_cadena_original_sat_and_more', '2025-09-23 01:11:51.538435');
INSERT INTO django_migrations (id, app, name, applied) VALUES (77, 'administracion', '0001_initial', '2025-09-24 22:09:13.137269');
INSERT INTO django_migrations (id, app, name, applied) VALUES (78, 'administracion', '0002_usuarioadministracion', '2025-09-24 22:09:13.139424');
INSERT INTO django_migrations (id, app, name, applied) VALUES (79, 'core', '0059_alter_productoservicio_impuesto_impuesto_and_more', '2025-10-01 19:04:36.912424');

-- Tabla: django_session
CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);

-- Datos para django_session
INSERT INTO django_session (session_key, session_data, expire_date) VALUES ('qqqaummk2kallzkr1cmmnybcvuxwmzft', 'eyJlbXByZXNhX2RiIjoiRGlyZWN0aXZhX0FBTUQ5NDA2MjBJQTMifQ:1v459R:86lcqwNeweydqDfj8eAWLu6WAAe-U2xO0vV8BFD5iBg', '2025-10-15 16:18:21.235176');
INSERT INTO django_session (session_key, session_data, expire_date) VALUES ('5mzgv8n6cfrc5pphudp23wik5ww46dov', '.eJxVjL0OgyAURt-FuTFcKyAdGzuarm7kwoVKf7QB7dL03auJi-t3zvm-zL_eyWc0ZNmJNTF5N8UPmubSXkvBNYeu69iBGZyn3szZJxNpMWG_WXQPP6yA7jjcxsKNw5SiLVal2Ggu2pH887y5u4Mec7_UoZbknQhQBoVSKVBcuxKPQTviSHUlKXBSJCp3VGDBSlsCBxdAB6ElZ78_RqNEWg:1v4jXj:AdaN4M7QYvuv9GYD_Rks47clkF_sfD9QkpnaIyVF1m8', '2025-10-17 11:26:07.220310');
INSERT INTO django_session (session_key, session_data, expire_date) VALUES ('ipeb0dk1c680rnkw9wvkes2zzp1we7f6', 'eyJlbXByZXNhX2RiIjoiRGlyZWN0aXZhX0RFTU8yNTA5MDFYWFgifQ:1v4jYt:4sLDai9g5mKOLUpPVEd8dvJ3APk58PXLr-n0uIKXPYU', '2025-10-17 11:27:19.285533');

-- Tabla: emisores
CREATE TABLE "emisores" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "razon_social" varchar(200) NOT NULL, "rfc" varchar(13) NOT NULL, "codigo_postal" varchar(5) NOT NULL, "archivo_certificado" text NULL, "password_llave" varchar(100) NOT NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "contrato" varchar(100) NOT NULL, "nombre_pac" varchar(50) NOT NULL, "password_pac" varchar(100) NOT NULL, "usuario_pac" varchar(100) NOT NULL, "timbrado_prueba" bool NOT NULL, "regimen_fiscal" varchar(3) NOT NULL, "serie" varchar(10) NOT NULL, "archivo_llave" text NULL, "nombre_archivo_certificado" varchar(255) NULL, "nombre_archivo_llave" varchar(255) NULL);

-- Tabla: factura_detalles
CREATE TABLE "factura_detalles" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "no_identificacion" varchar(50) NULL, "concepto" varchar(1000) NOT NULL, "precio" decimal NOT NULL, "clave_prod_serv" varchar(20) NOT NULL, "unidad" varchar(20) NOT NULL, "objeto_impuesto" varchar(2) NOT NULL, "importe" decimal NOT NULL, "impuesto_concepto" decimal NOT NULL, "factura_id" integer NOT NULL REFERENCES "facturas" ("folio") DEFERRABLE INITIALLY DEFERRED, "producto_servicio_id" integer NOT NULL REFERENCES "productos_servicios" ("codigo") DEFERRABLE INITIALLY DEFERRED, "clave_unidad" varchar(3) NOT NULL, "descuento" decimal NULL, "cantidad" decimal NOT NULL);

-- Tabla: facturas
CREATE TABLE "facturas" ("serie" varchar(25) NULL, "folio" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "fecha_emision" datetime NOT NULL, "lugar_expedicion" varchar(5) NOT NULL, "exportacion" varchar(2) NOT NULL, "metodo_pago" varchar(3) NOT NULL, "moneda" varchar(3) NOT NULL, "forma_pago" varchar(2) NOT NULL, "tipo_cambio" decimal NOT NULL, "subtotal" decimal NOT NULL, "impuesto" decimal NOT NULL, "total" decimal NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "emisor_id" integer NOT NULL REFERENCES "emisores" ("codigo") DEFERRABLE INITIALLY DEFERRED, "receptor_id" integer NOT NULL REFERENCES "clientes" ("codigo") DEFERRABLE INITIALLY DEFERRED, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "cancelada" bool NOT NULL, "acuse_cancelacion" text NULL, "errores_validacion" text NULL, "estado_timbrado" varchar(20) NOT NULL, "fecha_cancelacion" datetime NULL, "fecha_timbrado" datetime NULL, "intentos_timbrado" integer unsigned NOT NULL CHECK ("intentos_timbrado" >= 0), "motivo_cancelacion" varchar(500) NULL, "no_cert_sat" varchar(20) NULL, "sello_sat" text NULL, "ultimo_intento" datetime NULL, "uuid" varchar(36) NULL, "xml_original" text NULL, "xml_timbrado" text NULL, "certificado" text NULL, "confirmacion" varchar(2) NULL, "descuento" decimal NULL, "no_certificado" varchar(20) NULL, "sello" text NULL, "tipo_comprobante" varchar(1) NOT NULL, "uso_cfdi" varchar(5) NOT NULL, "año_informacion_global" integer NULL, "meses" varchar(2) NULL, "periodicidad" varchar(2) NULL, "codigo_qr" text NULL, "cadena_original_sat" text NULL);

-- Tabla: gasto_detalles
CREATE TABLE "gasto_detalles" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "factura" varchar(100) NOT NULL, "concepto" varchar(255) NOT NULL, "importe" decimal NOT NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "clasificacion_gasto_id" integer NOT NULL REFERENCES "clasificaciones_gasto" ("codigo") DEFERRABLE INITIALLY DEFERRED, "gasto_id" integer NOT NULL REFERENCES "gastos" ("codigo") DEFERRABLE INITIALLY DEFERRED, "proveedor_id" integer NOT NULL REFERENCES "proveedores" ("codigo") DEFERRABLE INITIALLY DEFERRED, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: gastos
CREATE TABLE "gastos" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "ciclo" varchar(10) NOT NULL, "fecha_gasto" date NOT NULL, "observaciones" text NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "presupuesto_id" integer NOT NULL REFERENCES "presupuestos" ("codigo") DEFERRABLE INITIALLY DEFERRED, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: lotes_origen
CREATE TABLE "lotes_origen" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "nombre" varchar(200) NOT NULL, "observaciones" text NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: pagos_factura
CREATE TABLE "pagos_factura" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "fecha_pago" datetime NOT NULL, "monto_pago" decimal NOT NULL, "tipo_pago" varchar(10) NOT NULL, "referencia_pago" varchar(100) NULL, "observaciones" text NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "factura_id" integer NOT NULL REFERENCES "facturas" ("folio") DEFERRABLE INITIALLY DEFERRED, "usuario_registro_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "fecha_timbrado" varchar(50) NULL, "no_certificado_sat" varchar(20) NULL, "sello" text NULL, "sello_sat" text NULL, "uuid" varchar(36) NULL, "xml_timbrado" text NULL, "num_parcialidad" integer unsigned NOT NULL CHECK ("num_parcialidad" >= 0), "forma_pago" varchar(2) NOT NULL, "cadena_original_sat" text NULL, "codigo_qr" text NULL);

-- Tabla: presupuesto_detalles
CREATE TABLE "presupuesto_detalles" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "importe" decimal NOT NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "clasificacion_gasto_id" integer NOT NULL REFERENCES "clasificaciones_gasto" ("codigo") DEFERRABLE INITIALLY DEFERRED, "presupuesto_id" integer NOT NULL REFERENCES "presupuestos" ("codigo") DEFERRABLE INITIALLY DEFERRED, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: presupuestos
CREATE TABLE "presupuestos" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "ciclo" varchar(100) NOT NULL, "observaciones" text NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "centro_costo_id" integer NOT NULL REFERENCES "centros_costo" ("codigo") DEFERRABLE INITIALLY DEFERRED, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: presupuestos_gasto
CREATE TABLE "presupuestos_gasto" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "ciclo" varchar(100) NOT NULL, "importe" decimal NOT NULL, "observaciones" text NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "centro_costo_id" integer NOT NULL REFERENCES "centros_costo" ("codigo") DEFERRABLE INITIALLY DEFERRED, "clasificacion_gasto_id" integer NOT NULL REFERENCES "clasificaciones_gasto" ("codigo") DEFERRABLE INITIALLY DEFERRED, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: productos_servicios
CREATE TABLE "productos_servicios" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "sku" varchar(50) NOT NULL UNIQUE, "descripcion" varchar(200) NOT NULL, "producto_servicio" bool NOT NULL, "clave_sat" varchar(20) NOT NULL, "impuesto" varchar(20) NOT NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "unidad_medida" varchar(50) NOT NULL, "impuesto_catalogo_id" bigint NULL REFERENCES "tipo_impuesto" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: proveedores
CREATE TABLE "proveedores" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "nombre" varchar(200) NOT NULL, "rfc" varchar(13) NOT NULL UNIQUE, "domicilio" text NOT NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: regimen_fiscal
CREATE TABLE "regimen_fiscal" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "codigo" varchar(10) NOT NULL UNIQUE, "descripcion" varchar(200) NOT NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL);

-- Datos para regimen_fiscal
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (391, '601', 'General de Ley Personas Morales', 1, '2025-09-04 22:37:12.259044', '2025-09-04 22:37:12.259181');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (392, '603', 'Personas Morales con Fines no Lucrativos', 1, '2025-09-04 22:37:12.259700', '2025-09-04 22:37:12.259707');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (393, '605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios', 1, '2025-09-04 22:37:12.260078', '2025-09-04 22:37:12.260083');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (394, '606', 'Arrendamiento', 1, '2025-09-04 22:37:12.260433', '2025-09-04 22:37:12.260437');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (395, '608', 'Demás ingresos', 1, '2025-09-04 22:37:12.260765', '2025-09-04 22:37:12.260769');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (396, '610', 'Residentes en el Extranjero sin Establecimiento Permanente en México', 1, '2025-09-04 22:37:12.261115', '2025-09-04 22:37:12.261118');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (397, '611', 'Ingresos por Dividendos (socios y accionistas)', 1, '2025-09-04 22:37:12.261510', '2025-09-04 22:37:12.261518');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (398, '612', 'Personas Físicas con Actividades Empresariales y Profesionales', 1, '2025-09-04 22:37:12.261870', '2025-09-04 22:37:12.261874');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (399, '614', 'Ingresos por intereses', 1, '2025-09-04 22:37:12.262254', '2025-09-04 22:37:12.262262');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (400, '615', 'Régimen de los ingresos por obtención de premios', 1, '2025-09-04 22:37:12.262709', '2025-09-04 22:37:12.262712');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (401, '616', 'Sin obligaciones fiscales', 1, '2025-09-04 22:37:12.263037', '2025-09-04 22:37:12.263041');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (402, '620', 'Sociedades Cooperativas de Producción que optan por diferir sus ingresos', 1, '2025-09-04 22:37:12.263405', '2025-09-04 22:37:12.263410');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (403, '621', 'Incorporación Fiscal', 1, '2025-09-04 22:37:12.263995', '2025-09-04 22:37:12.263999');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (404, '622', 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras', 1, '2025-09-04 22:37:12.264362', '2025-09-04 22:37:12.264366');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (405, '623', 'Opcional para Grupos de Sociedades', 1, '2025-09-04 22:37:12.264719', '2025-09-04 22:37:12.264723');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (406, '624', 'Coordinados', 1, '2025-09-04 22:37:12.265039', '2025-09-04 22:37:12.265043');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (407, '625', 'Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas', 1, '2025-09-04 22:37:12.265411', '2025-09-04 22:37:12.265418');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (408, '626', 'Régimen Simplificado de Confianza', 1, '2025-09-04 22:37:12.265891', '2025-09-04 22:37:12.265897');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (409, '628', 'Hidrocarburos', 1, '2025-09-04 22:37:12.266247', '2025-09-04 22:37:12.266251');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (410, '629', 'De los Regímenes Fiscales Preferentes y de las Empresas Multinacionales', 1, '2025-09-04 22:37:12.266551', '2025-09-04 22:37:12.266555');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (411, '630', 'Enajenación de acciones en bolsa de valores', 1, '2025-09-04 22:37:12.266849', '2025-09-04 22:37:12.266852');
INSERT INTO regimen_fiscal (id, codigo, descripcion, activo, fecha_creacion, fecha_modificacion) VALUES (412, '631', 'Régimen de los ingresos por obtención de premios', 1, '2025-09-04 22:37:12.267175', '2025-09-04 22:37:12.267180');

-- Tabla: remisiones
CREATE TABLE "remisiones" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "ciclo" varchar(100) NOT NULL, "folio" integer unsigned NOT NULL CHECK ("folio" >= 0), "fecha" date NOT NULL, "costo_flete" decimal NOT NULL, "observaciones" text NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "cliente_id" integer NOT NULL REFERENCES "clientes" ("codigo") DEFERRABLE INITIALLY DEFERRED, "lote_origen_id" integer NOT NULL REFERENCES "lotes_origen" ("codigo") DEFERRABLE INITIALLY DEFERRED, "transportista_id" integer NOT NULL REFERENCES "transportistas" ("codigo") DEFERRABLE INITIALLY DEFERRED, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "cancelada" bool NOT NULL, "fecha_cancelacion" datetime NULL, "folio_sustituto" varchar(50) NULL, "motivo_cancelacion" text NULL, "usuario_cancelacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "facturado" bool NOT NULL, "pagado" bool NOT NULL, "fecha_pago" date NULL);

-- Tabla: remisiones_detalles
CREATE TABLE "remisiones_detalles" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "calidad" varchar(20) NOT NULL, "no_arps" integer unsigned NOT NULL CHECK ("no_arps" >= 0), "kgs_enviados" decimal NOT NULL, "merma_arps" integer unsigned NOT NULL CHECK ("merma_arps" >= 0), "kgs_liquidados" decimal NOT NULL, "kgs_merma" decimal NOT NULL, "precio" decimal NOT NULL, "importe_liquidado" decimal NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "cultivo_id" integer NOT NULL REFERENCES "cultivos" ("codigo") DEFERRABLE INITIALLY DEFERRED, "remision_id" integer NOT NULL REFERENCES "remisiones" ("codigo") DEFERRABLE INITIALLY DEFERRED, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "peso_promedio" decimal NOT NULL, "fecha_liquidacion" datetime NULL, "usuario_liquidacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: sqlite_sequence
CREATE TABLE sqlite_sequence(name,seq);

-- Datos para sqlite_sequence
INSERT INTO sqlite_sequence (name, seq) VALUES ('django_migrations', 79);
INSERT INTO sqlite_sequence (name, seq) VALUES ('django_content_type', 32);
INSERT INTO sqlite_sequence (name, seq) VALUES ('auth_permission', 128);
INSERT INTO sqlite_sequence (name, seq) VALUES ('auth_group', 0);
INSERT INTO sqlite_sequence (name, seq) VALUES ('django_admin_log', 0);
INSERT INTO sqlite_sequence (name, seq) VALUES ('productos_servicios', 1);
INSERT INTO sqlite_sequence (name, seq) VALUES ('remisiones_detalles', 6);
INSERT INTO sqlite_sequence (name, seq) VALUES ('remisiones', 6);
INSERT INTO sqlite_sequence (name, seq) VALUES ('usuarios', 5);
INSERT INTO sqlite_sequence (name, seq) VALUES ('regimen_fiscal', 433);
INSERT INTO sqlite_sequence (name, seq) VALUES ('clientes', 4);
INSERT INTO sqlite_sequence (name, seq) VALUES ('proveedores', 2);
INSERT INTO sqlite_sequence (name, seq) VALUES ('centros_costo', 3);
INSERT INTO sqlite_sequence (name, seq) VALUES ('clasificaciones_gasto', 3);
INSERT INTO sqlite_sequence (name, seq) VALUES ('lotes_origen', 3);
INSERT INTO sqlite_sequence (name, seq) VALUES ('transportistas', 2);
INSERT INTO sqlite_sequence (name, seq) VALUES ('cultivos', 1);
INSERT INTO sqlite_sequence (name, seq) VALUES ('cuentas_bancarias', 16);
INSERT INTO sqlite_sequence (name, seq) VALUES ('core_pagoremision', 13);
INSERT INTO sqlite_sequence (name, seq) VALUES ('presupuestos_gasto', 1);
INSERT INTO sqlite_sequence (name, seq) VALUES ('presupuestos', 5);
INSERT INTO sqlite_sequence (name, seq) VALUES ('presupuesto_detalles', 8);
INSERT INTO sqlite_sequence (name, seq) VALUES ('gastos', 14);
INSERT INTO sqlite_sequence (name, seq) VALUES ('gasto_detalles', 14);
INSERT INTO sqlite_sequence (name, seq) VALUES ('configuracion_sistema', 13);
INSERT INTO sqlite_sequence (name, seq) VALUES ('emisores', 21);
INSERT INTO sqlite_sequence (name, seq) VALUES ('factura_detalles', 58);
INSERT INTO sqlite_sequence (name, seq) VALUES ('facturas', 10031);
INSERT INTO sqlite_sequence (name, seq) VALUES ('pagos_factura', 53);
INSERT INTO sqlite_sequence (name, seq) VALUES ('tipo_impuesto', 2);

-- Tabla: tipo_impuesto
CREATE TABLE "tipo_impuesto" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "codigo" varchar(3) NOT NULL, "nombre" varchar(100) NOT NULL, "tasa" decimal NOT NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL);

-- Datos para tipo_impuesto
INSERT INTO tipo_impuesto (id, codigo, nombre, tasa, activo, fecha_creacion, fecha_modificacion) VALUES (1, '002', 'IVA Tasa 16%', 0.16, 1, '2025-10-01 19:06:19.040422', '2025-10-01 19:06:19.040809');
INSERT INTO tipo_impuesto (id, codigo, nombre, tasa, activo, fecha_creacion, fecha_modificacion) VALUES (2, '002', 'IVA Tasa 0%', 0, 1, '2025-10-01 19:06:19.042263', '2025-10-01 19:06:19.042272');

-- Tabla: transportistas
CREATE TABLE "transportistas" ("codigo" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "nombre_completo" varchar(200) NOT NULL, "licencia" varchar(50) NOT NULL, "domicilio" text NOT NULL, "telefono" varchar(15) NOT NULL, "tipo_camion" varchar(100) NOT NULL, "placas_unidad" varchar(20) NOT NULL, "placas_remolque" varchar(20) NULL, "activo" bool NOT NULL, "fecha_creacion" datetime NOT NULL, "fecha_modificacion" datetime NOT NULL, "usuario_creacion_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_modificacion_id" bigint NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: usuarios
CREATE TABLE "usuarios" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "first_name" varchar(150) NOT NULL, "last_name" varchar(150) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "nombre" varchar(100) NOT NULL, "puesto" varchar(100) NOT NULL, "email" varchar(254) NOT NULL UNIQUE, "is_admin" bool NOT NULL);

-- Datos para usuarios
INSERT INTO usuarios (id, password, last_login, is_superuser, username, first_name, last_name, is_staff, is_active, date_joined, nombre, puesto, email, is_admin) VALUES (1, 'pbkdf2_sha256$1000000$733Xl8hZV7ZPrd7sfX26Bv$OpBQPyxG7GBGlK8RLSe0cxzUSbfCewTDSDkTttlJ9vs=', '2025-10-03 11:26:07.218223', 1, 'supervisor', 'SUPERVISOR', 'SISTEMA', 1, 1, '2025-10-01 23:01:49', 'SUPERVISOR SISTEMA', 'Administrador', 'supervisor@directiva.com', 1);

-- Tabla: usuarios_groups
CREATE TABLE "usuarios_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "usuario_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Tabla: usuarios_user_permissions
CREATE TABLE "usuarios_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "usuario_id" bigint NOT NULL REFERENCES "usuarios" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

