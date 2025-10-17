#!/usr/bin/env python3
"""
Script para adaptar los comandos de creación de empresas para PostgreSQL
Convierte los scripts SQL de SQLite a PostgreSQL
"""

import os
import re

def convert_sqlite_to_postgresql(sqlite_sql):
    """Convertir SQL de SQLite a PostgreSQL"""
    
    # Reemplazos específicos para PostgreSQL
    replacements = [
        # Tipos de datos
        (r'INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY'),
        (r'INTEGER', 'INTEGER'),
        (r'TEXT', 'TEXT'),
        (r'VARCHAR\((\d+)\)', r'VARCHAR(\1)'),
        (r'DECIMAL\((\d+),(\d+)\)', r'DECIMAL(\1,\2)'),
        (r'BOOLEAN', 'BOOLEAN'),
        (r'DATETIME', 'TIMESTAMP WITH TIME ZONE'),
        (r'DEFAULT CURRENT_TIMESTAMP', 'DEFAULT CURRENT_TIMESTAMP'),
        
        # Sintaxis específica
        (r'AUTOINCREMENT', ''),
        (r'INTEGER PRIMARY KEY', 'SERIAL PRIMARY KEY'),
        
        # Constraint names (PostgreSQL requiere nombres únicos)
        (r'CONSTRAINT "([^"]+)"', r'CONSTRAINT \1'),
        
        # Índices
        (r'CREATE INDEX "([^"]+)"', r'CREATE INDEX \1'),
        (r'ON "([^"]+)"', r'ON \1'),
        
        # Nombres de tablas y columnas
        (r'"([^"]+)"', r'\1'),
    ]
    
    postgresql_sql = sqlite_sql
    
    for pattern, replacement in replacements:
        postgresql_sql = re.sub(pattern, replacement, postgresql_sql)
    
    return postgresql_sql

def create_postgresql_empresa_structure():
    """Crear estructura de empresa para PostgreSQL"""
    
    sql = """
-- Estructura de base de datos de empresa para PostgreSQL
-- Generado automáticamente desde SQLite

-- Tabla de usuarios
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

-- Tabla de sesiones de Django
CREATE TABLE IF NOT EXISTS django_session (
    session_key VARCHAR(40) PRIMARY KEY,
    session_data TEXT NOT NULL,
    expire_date TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Tabla de productos/servicios
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

-- Tabla de impuestos
CREATE TABLE IF NOT EXISTS tipo_impuesto (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(3) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    tasa DECIMAL(6,4) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de régimen fiscal
CREATE TABLE IF NOT EXISTS regimen_fiscal (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    descripcion TEXT NOT NULL,
    fisica BOOLEAN DEFAULT FALSE,
    moral BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de usos CFDI
CREATE TABLE IF NOT EXISTS uso_cfdi (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    descripcion TEXT NOT NULL,
    aplica_fisica BOOLEAN DEFAULT TRUE,
    aplica_moral BOOLEAN DEFAULT TRUE,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de métodos de pago
CREATE TABLE IF NOT EXISTS metodo_pago (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    descripcion TEXT NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de formas de pago
CREATE TABLE IF NOT EXISTS forma_pago (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    descripcion TEXT NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de configuración del sistema
CREATE TABLE IF NOT EXISTS configuracion_sistema (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT NOT NULL,
    descripcion TEXT,
    fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de emisores
CREATE TABLE IF NOT EXISTS emisores (
    id SERIAL PRIMARY KEY,
    razon_social VARCHAR(255) NOT NULL,
    rfc VARCHAR(13) UNIQUE NOT NULL,
    regimen_fiscal_id INTEGER,
    direccion TEXT,
    telefono VARCHAR(20),
    email VARCHAR(255),
    serie VARCHAR(10),
    lugar_expedicion VARCHAR(255),
    modo_pruebas BOOLEAN DEFAULT TRUE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    razon_social VARCHAR(255) NOT NULL,
    rfc VARCHAR(13) UNIQUE NOT NULL,
    regimen_fiscal_id INTEGER,
    uso_cfdi_id INTEGER,
    direccion TEXT,
    telefono VARCHAR(20),
    email VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de facturas
CREATE TABLE IF NOT EXISTS facturas (
    id SERIAL PRIMARY KEY,
    folio VARCHAR(20) UNIQUE NOT NULL,
    emisor_id INTEGER NOT NULL,
    cliente_id INTEGER NOT NULL,
    fecha_emision TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_pago TIMESTAMP WITH TIME ZONE,
    subtotal DECIMAL(10,2) NOT NULL,
    total_impuestos DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    metodo_pago_id INTEGER,
    forma_pago_id INTEGER,
    moneda VARCHAR(3) DEFAULT 'MXN',
    tipo_cambio DECIMAL(10,4) DEFAULT 1.0,
    condiciones_pago VARCHAR(100),
    lugar_expedicion VARCHAR(255),
    observaciones TEXT,
    uuid VARCHAR(36),
    estado VARCHAR(20) DEFAULT 'borrador',
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de conceptos de factura
CREATE TABLE IF NOT EXISTS conceptos_factura (
    id SERIAL PRIMARY KEY,
    factura_id INTEGER NOT NULL,
    producto_servicio_id INTEGER,
    cantidad DECIMAL(10,3) NOT NULL,
    unidad VARCHAR(20) NOT NULL,
    descripcion TEXT NOT NULL,
    valor_unitario DECIMAL(10,2) NOT NULL,
    importe DECIMAL(10,2) NOT NULL,
    impuesto_id INTEGER,
    tasa_impuesto DECIMAL(6,4),
    importe_impuesto DECIMAL(10,2),
    orden INTEGER DEFAULT 1
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);
CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios(is_active);
CREATE INDEX IF NOT EXISTS idx_productos_codigo ON productos_servicios(codigo);
CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos_servicios(activo);
CREATE INDEX IF NOT EXISTS idx_session_expire ON django_session(expire_date);
CREATE INDEX IF NOT EXISTS idx_emisores_rfc ON emisores(rfc);
CREATE INDEX IF NOT EXISTS idx_clientes_rfc ON clientes(rfc);
CREATE INDEX IF NOT EXISTS idx_facturas_folio ON facturas(folio);
CREATE INDEX IF NOT EXISTS idx_facturas_fecha ON facturas(fecha_emision);
CREATE INDEX IF NOT EXISTS idx_conceptos_factura ON conceptos_factura(factura_id);
"""
    
    return sql

def create_postgresql_basic_data():
    """Crear datos básicos para PostgreSQL"""
    
    sql = """
-- Datos básicos para nueva empresa en PostgreSQL

-- Insertar usuario supervisor
INSERT INTO usuarios (username, password, first_name, last_name, email, is_superuser, is_staff, is_active, date_joined) VALUES
('supervisor', 'pbkdf2_sha256$600000$hash$hash', 'Supervisor', 'Sistema', 'supervisor@directiva.com', TRUE, TRUE, TRUE, CURRENT_TIMESTAMP)
ON CONFLICT (username) DO NOTHING;

-- Insertar impuestos básicos
INSERT INTO tipo_impuesto (codigo, nombre, tasa, activo) VALUES
('002', 'IVA Tasa 16%', 0.1600, TRUE),
('002', 'IVA Tasa 0%', 0.0000, TRUE)
ON CONFLICT DO NOTHING;

-- Insertar régimen fiscal básico
INSERT INTO regimen_fiscal (codigo, descripcion, fisica, moral, activo) VALUES
('601', 'General de Ley Personas Morales', FALSE, TRUE, TRUE),
('603', 'Personas Morales con Fines no Lucrativos', FALSE, TRUE, TRUE),
('605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios', TRUE, FALSE, TRUE),
('606', 'Arrendamiento', TRUE, FALSE, TRUE)
ON CONFLICT (codigo) DO NOTHING;

-- Insertar usos CFDI básicos
INSERT INTO uso_cfdi (codigo, descripcion, aplica_fisica, aplica_moral, activo) VALUES
('G01', 'Adquisición de mercancías', TRUE, TRUE, TRUE),
('G02', 'Devoluciones, descuentos o bonificaciones', TRUE, TRUE, TRUE),
('G03', 'Gastos en general', TRUE, TRUE, TRUE),
('I01', 'Construcciones', TRUE, TRUE, TRUE),
('I02', 'Mobilario y equipo de oficina por inversiones', TRUE, TRUE, TRUE),
('I03', 'Equipo de transporte', TRUE, TRUE, TRUE),
('I04', 'Equipo de computo y accesorios', TRUE, TRUE, TRUE),
('I05', 'Dados, troqueles, moldes, matrices y herramental', TRUE, TRUE, TRUE),
('I06', 'Comunicaciones telefónicas', TRUE, TRUE, TRUE),
('I07', 'Comunicaciones satelitales', TRUE, TRUE, TRUE),
('I08', 'Otra maquinaria y equipo', TRUE, TRUE, TRUE),
('D01', 'Honorarios médicos, dentales y gastos hospitalarios', TRUE, FALSE, TRUE),
('D02', 'Gastos médicos por incapacidad o discapacidad', TRUE, FALSE, TRUE),
('D03', 'Gastos funerales', TRUE, FALSE, TRUE),
('D04', 'Donativos', TRUE, FALSE, TRUE),
('D05', 'Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)', TRUE, FALSE, TRUE),
('D06', 'Aportaciones voluntarias al SAR', TRUE, FALSE, TRUE),
('D07', 'Primas por seguros de gastos médicos', TRUE, FALSE, TRUE),
('D08', 'Gastos de transportación escolar obligatoria', TRUE, FALSE, TRUE),
('D09', 'Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones', TRUE, FALSE, TRUE),
('D10', 'Pagos por servicios educativos (colegiaturas)', TRUE, FALSE, TRUE),
('P01', 'Por definir', TRUE, TRUE, TRUE)
ON CONFLICT (codigo) DO NOTHING;

-- Insertar métodos de pago básicos
INSERT INTO metodo_pago (codigo, descripcion, activo) VALUES
('PUE', 'Pago en una sola exhibición', TRUE),
('PPD', 'Pago en parcialidades o diferido', TRUE)
ON CONFLICT (codigo) DO NOTHING;

-- Insertar formas de pago básicas
INSERT INTO forma_pago (codigo, descripcion, activo) VALUES
('01', 'Efectivo', TRUE),
('02', 'Cheque nominativo', TRUE),
('03', 'Transferencia electrónica de fondos', TRUE),
('04', 'Tarjeta de crédito', TRUE),
('05', 'Monedero electrónico', TRUE),
('06', 'Dinero electrónico', TRUE),
('08', 'Vales de despensa', TRUE),
('12', 'Dación en pago', TRUE),
('13', 'Pago por subrogación', TRUE),
('14', 'Pago por consignación', TRUE),
('15', 'Condonación', TRUE),
('17', 'Compensación', TRUE),
('23', 'Novación', TRUE),
('24', 'Confusión', TRUE),
('25', 'Remisión de deuda', TRUE),
('26', 'Prescripción o caducidad', TRUE),
('27', 'A satisfacción del acreedor', TRUE),
('28', 'Tarjeta de débito', TRUE),
('29', 'Tarjeta de servicios', TRUE),
('30', 'Aplicación de anticipos', TRUE),
('31', 'Intermediario pagos', TRUE),
('99', 'Por definir', TRUE)
ON CONFLICT (codigo) DO NOTHING;

-- Insertar configuración básica
INSERT INTO configuracion_sistema (clave, valor, descripcion) VALUES
('ciclo_actual', '2025', 'Ciclo fiscal actual'),
('version_sistema', '1.0.0', 'Versión del sistema'),
('moneda', 'MXN', 'Moneda por defecto'),
('lugar_expedicion', 'México', 'Lugar de expedición por defecto')
ON CONFLICT (clave) DO NOTHING;
"""
    
    return sql

def main():
    """Función principal"""
    print("🔄 Adaptando comandos de creación de empresas para PostgreSQL...")
    
    # Crear directorio para scripts PostgreSQL
    os.makedirs('scripts_bd/postgresql', exist_ok=True)
    
    # Crear estructura de empresa para PostgreSQL
    estructura_sql = create_postgresql_empresa_structure()
    with open('scripts_bd/postgresql/estructura_empresa_postgresql.sql', 'w', encoding='utf-8') as f:
        f.write(estructura_sql)
    
    # Crear datos básicos para PostgreSQL
    datos_sql = create_postgresql_basic_data()
    with open('scripts_bd/postgresql/datos_basicos_empresa_postgresql.sql', 'w', encoding='utf-8') as f:
        f.write(datos_sql)
    
    print("✅ Scripts PostgreSQL creados exitosamente:")
    print("   📁 scripts_bd/postgresql/estructura_empresa_postgresql.sql")
    print("   📁 scripts_bd/postgresql/datos_basicos_empresa_postgresql.sql")

if __name__ == "__main__":
    main()
