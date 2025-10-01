-- Script de datos básicos para nuevas empresas
-- Incluye catálogos del SAT y configuración inicial
-- Fecha: 2025-01-01

-- Insertar regímenes fiscales básicos
INSERT OR IGNORE INTO regimen_fiscal (codigo, descripcion, fisica, moral, activo, fecha_creacion) VALUES
('601', 'General de Ley Personas Morales', 0, 1, 1, '2025-01-01 00:00:00'),
('603', 'Personas Morales con Fines no Lucrativos', 0, 1, 1, '2025-01-01 00:00:00'),
('605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios', 1, 0, 1, '2025-01-01 00:00:00'),
('606', 'Arrendamiento', 1, 0, 1, '2025-01-01 00:00:00'),
('608', 'Demás ingresos', 1, 0, 1, '2025-01-01 00:00:00'),
('610', 'Residentes en el Extranjero sin Establecimiento Permanente en México', 1, 1, 1, '2025-01-01 00:00:00'),
('611', 'Ingresos por Dividendos (socios y accionistas)', 1, 0, 1, '2025-01-01 00:00:00'),
('612', 'Personas Físicas con Actividades Empresariales y Profesionales', 1, 0, 1, '2025-01-01 00:00:00'),
('615', 'Régimen de los ingresos por obtención de premios', 1, 0, 1, '2025-01-01 00:00:00'),
('616', 'Sin obligaciones fiscales', 1, 0, 1, '2025-01-01 00:00:00'),
('620', 'Sociedades Cooperativas de Producción que optan por diferir sus ingresos', 0, 1, 1, '2025-01-01 00:00:00'),
('621', 'Incorporación Fiscal', 1, 0, 1, '2025-01-01 00:00:00'),
('622', 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras', 1, 1, 1, '2025-01-01 00:00:00'),
('623', 'Opcional para Grupos de Sociedades', 0, 1, 1, '2025-01-01 00:00:00'),
('624', 'Coordinados', 1, 1, 1, '2025-01-01 00:00:00'),
('625', 'Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas', 1, 0, 1, '2025-01-01 00:00:00'),
('626', 'Régimen Simplificado de Confianza', 1, 0, 1, '2025-01-01 00:00:00');

-- Insertar usos de CFDI básicos
INSERT OR IGNORE INTO uso_cfdi (codigo, descripcion, aplica_fisica, aplica_moral, activo, fecha_creacion) VALUES
('G01', 'Adquisición de mercancías', 1, 1, 1, '2025-01-01 00:00:00'),
('G02', 'Devoluciones, descuentos o bonificaciones', 1, 1, 1, '2025-01-01 00:00:00'),
('G03', 'Gastos en general', 1, 1, 1, '2025-01-01 00:00:00'),
('I01', 'Construcciones', 1, 1, 1, '2025-01-01 00:00:00'),
('I02', 'Mobilario y equipo de oficina por inversiones', 1, 1, 1, '2025-01-01 00:00:00'),
('I03', 'Equipo de transporte', 1, 1, 1, '2025-01-01 00:00:00'),
('I04', 'Equipo de computo y accesorios', 1, 1, 1, '2025-01-01 00:00:00'),
('I05', 'Dados, troqueles, moldes, matrices y herramental', 1, 1, 1, '2025-01-01 00:00:00'),
('I06', 'Comunicaciones telefónicas', 1, 1, 1, '2025-01-01 00:00:00'),
('I07', 'Comunicaciones satelitales', 1, 1, 1, '2025-01-01 00:00:00'),
('I08', 'Otra maquinaria y equipo', 1, 1, 1, '2025-01-01 00:00:00'),
('D01', 'Honorarios médicos, dentales y gastos hospitalarios', 1, 0, 1, '2025-01-01 00:00:00'),
('D02', 'Gastos médicos por incapacidad o discapacidad', 1, 0, 1, '2025-01-01 00:00:00'),
('D03', 'Gastos funerales', 1, 0, 1, '2025-01-01 00:00:00'),
('D04', 'Donativos', 1, 0, 1, '2025-01-01 00:00:00'),
('D05', 'Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)', 1, 0, 1, '2025-01-01 00:00:00'),
('D06', 'Aportaciones voluntarias al SAR', 1, 0, 1, '2025-01-01 00:00:00'),
('D07', 'Primas por seguros de gastos médicos', 1, 0, 1, '2025-01-01 00:00:00'),
('D08', 'Gastos de transportación escolar obligatoria', 1, 0, 1, '2025-01-01 00:00:00'),
('D09', 'Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones', 1, 0, 1, '2025-01-01 00:00:00'),
('D10', 'Pagos por servicios educativos (colegiaturas)', 1, 0, 1, '2025-01-01 00:00:00'),
('P01', 'Por definir', 1, 1, 1, '2025-01-01 00:00:00');

-- Insertar métodos de pago básicos
INSERT OR IGNORE INTO metodo_pago (codigo, descripcion, activo, fecha_creacion) VALUES
('PUE', 'Pago en una exhibición', 1, '2025-01-01 00:00:00'),
('PPD', 'Pago en parcialidades o diferido', 1, '2025-01-01 00:00:00');

-- Insertar formas de pago básicas
INSERT OR IGNORE INTO forma_pago (codigo, descripcion, activo, fecha_creacion) VALUES
('01', 'Efectivo', 1, '2025-01-01 00:00:00'),
('02', 'Cheque nominativo', 1, '2025-01-01 00:00:00'),
('03', 'Transferencia electrónica de fondos', 1, '2025-01-01 00:00:00'),
('04', 'Tarjeta de crédito', 1, '2025-01-01 00:00:00'),
('05', 'Monedero electrónico', 1, '2025-01-01 00:00:00'),
('06', 'Dinero electrónico', 1, '2025-01-01 00:00:00'),
('08', 'Vales de despensa', 1, '2025-01-01 00:00:00'),
('12', 'Dación en pago', 1, '2025-01-01 00:00:00'),
('13', 'Pago por subrogación', 1, '2025-01-01 00:00:00'),
('14', 'Pago por consignación', 1, '2025-01-01 00:00:00'),
('15', 'Condonación', 1, '2025-01-01 00:00:00'),
('17', 'Compensación', 1, '2025-01-01 00:00:00'),
('23', 'Novación', 1, '2025-01-01 00:00:00'),
('24', 'Confusión', 1, '2025-01-01 00:00:00'),
('25', 'Remisión de deuda', 1, '2025-01-01 00:00:00'),
('26', 'Prescripción o caducidad', 1, '2025-01-01 00:00:00'),
('27', 'A satisfacción del acreedor', 1, '2025-01-01 00:00:00'),
('28', 'Tarjeta de débito', 1, '2025-01-01 00:00:00'),
('29', 'Tarjeta de servicios', 1, '2025-01-01 00:00:00'),
('30', 'Aplicación de anticipos', 1, '2025-01-01 00:00:00'),
('31', 'Intermediario pagos', 1, '2025-01-01 00:00:00'),
('99', 'Por definir', 1, '2025-01-01 00:00:00');

-- Insertar tipos de impuesto básicos
INSERT OR IGNORE INTO tipo_impuesto (codigo, nombre, tasa, activo, fecha_creacion, fecha_modificacion) VALUES
('002', 'IVA Tasa 16%', 0.1600, 1, '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
('003', 'IVA Tasa 0%', 0.0000, 1, '2025-01-01 00:00:00', '2025-01-01 00:00:00');

-- Insertar usuario supervisor (contraseña: Directivasbmj1*)
-- NOTA: La contraseña debe ser hasheada usando Django's make_password()
-- Este es un placeholder que debe ser reemplazado por el comando de gestión
INSERT OR IGNORE INTO usuarios (
    password, last_login, is_superuser, username, first_name, last_name, 
    email, is_staff, is_active, date_joined
) VALUES (
    'pbkdf2_sha256$1000000$PLACEHOLDER$PLACEHOLDER', -- Debe ser reemplazado
    NULL,
    1, -- is_superuser
    'supervisor',
    'SUPERVISOR',
    'SISTEMA',
    'supervisor@sistema.com',
    1, -- is_staff
    1, -- is_active
    '2025-01-01 00:00:00'
);

-- Insertar configuración del sistema (placeholder)
-- NOTA: Los valores deben ser reemplazados por el comando de gestión
INSERT OR IGNORE INTO configuracion_sistema (
    razon_social, rfc, direccion, telefono, ciclo_actual,
    certificado_nombre, certificado_password, certificado_ruta,
    pac_usuario, pac_password, pac_url, pac_produccion,
    fecha_creacion, fecha_modificacion
) VALUES (
    'EMPRESA_PLACEHOLDER', -- Debe ser reemplazado
    'RFC_PLACEHOLDER', -- Debe ser reemplazado
    'DIRECCION_PLACEHOLDER', -- Debe ser reemplazado
    'TELEFONO_PLACEHOLDER', -- Debe ser reemplazado
    '2025', -- ciclo_actual
    '', -- certificado_nombre
    '', -- certificado_password
    '', -- certificado_ruta
    '', -- pac_usuario
    '', -- pac_password
    '', -- pac_url
    0, -- pac_produccion
    '2025-01-01 00:00:00',
    '2025-01-01 00:00:00'
);
