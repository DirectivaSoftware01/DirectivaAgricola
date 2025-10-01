
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
