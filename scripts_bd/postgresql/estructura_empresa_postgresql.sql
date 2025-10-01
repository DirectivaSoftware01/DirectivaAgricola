
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
