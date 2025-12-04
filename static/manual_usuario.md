# Manual de Usuario
## Sistema Directiva Agrícola

**Versión:** 1.0  
**Fecha:** 2025  
**Sistema de Gestión Agrícola Integral**

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Acceso al Sistema](#acceso-al-sistema)
3. [Dashboard](#dashboard)
4. [Módulos Principales](#módulos-principales)
   - [Remisiones](#remisiones)
   - [Preliquidación](#preliquidación)
   - [Cobranza](#cobranza)
   - [Facturación](#facturación)
   - [Compras](#compras)
   - [Inventario](#inventario)
   - [Presupuestos](#presupuestos)
   - [Gastos](#gastos)
5. [Catálogos](#catálogos)
6. [Reportes](#reportes)
7. [Configuración](#configuración)

---

## Introducción

El Sistema Directiva Agrícola es una plataforma integral diseñada para la gestión completa de operaciones agrícolas, incluyendo:

- Gestión de remisiones y preliquidación
- Control de inventario y almacenes
- Facturación electrónica (CFDI 4.0)
- Gestión de compras y pagos
- Control de presupuestos y gastos
- Reportes y análisis estadísticos

### Requisitos del Sistema

- Navegador web moderno (Chrome, Firefox, Edge, Safari)
- Conexión a Internet
- Permisos de usuario asignados por el administrador

---

## Acceso al Sistema

### Inicio de Sesión

1. Accede a la URL del sistema proporcionada por el administrador
2. Ingresa tu **usuario** y **contraseña**
3. Haz clic en el botón **"Iniciar Sesión"**

**[IMAGEN: Pantalla de login con campos de usuario y contraseña]**

### Recuperación de Contraseña

Si olvidaste tu contraseña, contacta al administrador del sistema para su restablecimiento.

### Cerrar Sesión

Para cerrar sesión, haz clic en el botón **"Cerrar Sesión"** ubicado en la esquina superior derecha del sistema.

---

## Dashboard

El Dashboard es la pantalla principal del sistema y muestra un resumen general de las operaciones.

**[IMAGEN: Vista del Dashboard con gráficas y estadísticas]**

### Tarjetas de Resumen

El Dashboard incluye tarjetas informativas que muestran:

- **Total de Remisiones**: Número total de remisiones registradas
- **Remisiones Pendientes**: Remisiones que aún no han sido preliquidadas
- **Remisiones Preliquidadas**: Remisiones que ya fueron preliquidadas
- **Clientes Activos**: Número de clientes activos en el sistema

### Gráficas de Análisis

El Dashboard incluye varias gráficas interactivas:

#### 1. Análisis de Kgs Enviados vs Liquidados
Muestra la comparación entre kilogramos enviados y liquidados por cliente.

**[IMAGEN: Gráfica de barras comparando kgs enviados vs liquidados]**

#### 2. Análisis por Calidad de Producto
Analiza los kilogramos netos enviados vs liquidados por calidad de producto.

**[IMAGEN: Gráfica de análisis de calidad de producto]**

#### 3. Análisis de Merma
Muestra el análisis de merma enviada vs preliquidada por calidad de producto.

**[IMAGEN: Gráfica de análisis de merma]**

#### 4. Ranking de Clientes
Muestra el ranking de clientes por importe liquidado.

**[IMAGEN: Gráfica de ranking de clientes]**

#### 5. Análisis de Importes
Compara importes enviados vs liquidados.

**[IMAGEN: Gráfica de análisis de importes]**

### Filtros del Dashboard

Puedes filtrar las gráficas por:
- **Cliente**: Selecciona un cliente específico
- **Lote - Origen**: Selecciona uno o varios lotes de origen
- **Rango de Fechas**: Define un período específico

---

## Módulos Principales

### Remisiones

El módulo de Remisiones permite gestionar todas las remisiones de productos agrícolas.

#### Listado de Remisiones

**[IMAGEN: Listado de remisiones con tabla y filtros]**

**Acceso:** Menú principal → Remisiones → Listado de Remisiones

**Funcionalidades:**
- Ver todas las remisiones registradas
- Filtrar remisiones por:
  - Cliente
  - Lote - Origen (selección múltiple)
  - Transportista
  - Estado (Pendiente/Preliquidada)
  - Rango de fechas
- Buscar remisiones por ciclo, folio o cliente
- Ver detalles de cada remisión
- Imprimir formato de remisión
- Editar o eliminar remisiones (según permisos)

#### Crear Nueva Remisión

**[IMAGEN: Formulario de creación de remisión]**

**Pasos para crear una remisión:**

1. Haz clic en el botón **"Nueva Remisión"**
2. Completa los siguientes campos:
   - **Ciclo**: Se asigna automáticamente según la configuración
   - **Folio**: Se genera automáticamente
   - **Fecha**: Selecciona la fecha de la remisión
   - **Cliente**: Selecciona el cliente
   - **Lote - Origen**: Selecciona el lote de origen
   - **Transportista**: Selecciona el transportista
   - **Costo de Flete**: Ingresa el costo del flete
   - **Peso Bruto de Embarque**: Ingresa el peso bruto
   - **Merma/Arps Global**: Ingresa la merma global
   - **Observaciones**: (Opcional) Agrega observaciones
3. Haz clic en **"Guardar"**

#### Agregar Detalles de Remisión

Después de crear la remisión, puedes agregar los detalles de productos:

1. En la vista de detalle de la remisión, haz clic en **"Agregar Detalle"**
2. Completa los campos:
   - **Cultivo**: Selecciona el cultivo
   - **Variedad**: Selecciona la variedad
   - **No. Arps Enviados**: Número de arps enviados
   - **Kgs Enviados**: Kilogramos enviados
   - **Merma/Arps Enviados**: Merma por arps enviados
   - **Kgs Merma Enviados**: Kilogramos de merma enviados
   - **Precio por Kg Enviado**: Precio por kilogramo enviado
   - **Importe Enviado**: Se calcula automáticamente
3. Haz clic en **"Guardar"**

**[IMAGEN: Formulario de detalle de remisión]**

#### Imprimir Remisión

Para imprimir una remisión:

1. Ve al listado de remisiones
2. Haz clic en el botón **"Imprimir"** de la remisión deseada
3. Se abrirá una nueva ventana con el formato de impresión
4. Usa la función de impresión de tu navegador (Ctrl+P o Cmd+P)

**[IMAGEN: Formato de impresión de remisión]**

### Preliquidación

La preliquidación permite registrar los datos reales de recepción de productos.

#### Acceder a Preliquidación

1. Ve al listado de remisiones
2. Haz clic en el botón **"Preliquidar"** de la remisión deseada

**[IMAGEN: Pantalla de preliquidación]**

#### Proceso de Preliquidación

1. **Datos Generales**: Se muestran los datos de la remisión
2. **Detalles de Productos**: Para cada producto:
   - **No. Arps Liquidados**: Ingresa el número de arps recibidos
   - **Kgs Merma Liquidados**: Ingresa los kgs de merma recibidos
   - **Peso Promedio Liquidado**: Se calcula automáticamente
   - **Kgs Liquidados**: Se calcula automáticamente
   - **Precio por Kg**: Ingresa el precio por kilogramo liquidado
   - **Importe Liquidado**: Se calcula automáticamente

3. **Agregar Nuevos Cultivos**: Si se recibieron cultivos adicionales:
   - Haz clic en **"Agregar Cultivo"**
   - Completa los campos (solo datos de liquidación, los enviados quedan en cero)
   - Haz clic en **"Guardar"**

4. **Guardar Preliquidación**: Haz clic en **"Guardar Preliquidación"**

**[IMAGEN: Formulario de preliquidación con campos completados]**

### Cobranza

El módulo de Cobranza permite gestionar los pagos de las remisiones.

#### Listado de Cobranza

**[IMAGEN: Listado de cobranza con remisiones y estados de pago]**

**Acceso:** Menú principal → Cobranza

**Funcionalidades:**
- Ver remisiones con saldo pendiente
- Filtrar por cliente, estado de facturación, estado de pago y fechas
- Ver detalles de cada remisión
- Capturar pagos
- Imprimir reporte de cobranza

#### Capturar Pago

1. En el listado de cobranza, haz clic en **"Capturar Pago"** de la remisión deseada
2. Se abrirá un modal con los siguientes campos:
   - **Remisión**: Se muestra automáticamente
   - **Saldo Pendiente**: Se muestra automáticamente
   - **Facturar este pago**: Marca si deseas facturar el pago
   - **Monto del Pago**: Ingresa el monto
   - **Método de Pago**: Selecciona (Efectivo, Transferencia Bancaria, Cheque)
   - **Cuenta Bancaria**: (Solo para transferencia y cheque)
   - **Fecha de Pago**: Selecciona la fecha
   - **Referencia/Comprobante**: Ingresa la referencia
   - **Observaciones**: (Opcional)
3. Haz clic en **"Confirmar"**

**[IMAGEN: Modal de captura de pago]**

### Facturación

El módulo de Facturación permite generar facturas electrónicas (CFDI 4.0).

#### Crear Factura

**[IMAGEN: Pantalla de facturación con formulario]**

**Acceso:** Menú principal → Facturación

**Pasos para crear una factura:**

1. Selecciona el **Emisor** (empresa que factura)
2. Selecciona el **Cliente**
3. Completa los datos generales:
   - **Método de Pago**: PUE (Pago en una sola exhibición) o PPD (Pago en parcialidades)
   - **Forma de Pago**: Selecciona del catálogo SAT
   - **Moneda**: Generalmente MXN
   - **Tipo de Cambio**: (Solo si la moneda no es MXN)
   - **Condiciones de Pago**: (Opcional)
   - **Lugar de Expedición**: Se obtiene del emisor
4. Agrega los productos/servicios:
   - Haz clic en **"Agregar Producto"**
   - Selecciona el producto o servicio
   - Ingresa la cantidad, unidad de medida y precio
   - El importe se calcula automáticamente
5. Revisa el resumen de la factura
6. Haz clic en **"Guardar Factura"**

#### Timbrar Factura

Después de guardar la factura:

1. Haz clic en **"Timbrar Factura"**
2. El sistema validará la factura
3. Si es válida, se timbrará con el PAC (Proveedor Autorizado de Certificación)
4. Se generará el XML y PDF de la factura

**[IMAGEN: Factura timbrada con QR y datos fiscales]**

#### Listado de Facturas

**[IMAGEN: Listado de facturas con estados]**

Puedes ver todas las facturas y:
- Ver detalles
- Descargar PDF
- Descargar XML
- Cancelar factura (si aplica)

### Compras

El módulo de Compras permite gestionar las compras realizadas a proveedores.

#### Listado de Compras

**[IMAGEN: Listado de compras]**

**Acceso:** Menú principal → Compras

**Funcionalidades:**
- Ver todas las compras
- Filtrar por proveedor, almacén, forma de pago y fechas
- Crear nueva compra
- Ver detalles de compra
- Editar o eliminar compras

#### Crear Nueva Compra

1. Haz clic en **"Nueva Compra"**
2. Completa los datos:
   - **Proveedor**: Selecciona el proveedor
   - **Almacén**: Selecciona el almacén de destino
   - **Fecha**: Selecciona la fecha de compra
   - **Forma de Pago**: Selecciona del catálogo SAT
   - **Factura**: Ingresa el número de factura del proveedor
   - **Observaciones**: (Opcional)
3. Agrega los productos:
   - Haz clic en **"Agregar Producto"**
   - Selecciona el producto
   - Ingresa cantidad, precio unitario y descuento (si aplica)
4. Haz clic en **"Guardar Compra"**

**[IMAGEN: Formulario de creación de compra]**

### Inventario

El módulo de Inventario permite controlar las existencias de productos.

#### Existencias

**[IMAGEN: Listado de existencias por almacén]**

**Acceso:** Menú principal → Inventario → Existencias

Muestra las existencias de productos por almacén con:
- Código y descripción del producto
- Unidad de medida
- Existencia actual
- Costo promedio
- Valor total

**Filtros disponibles:**
- Almacén
- Producto/Servicio
- Clasificación de Gasto

#### Kardex

**[IMAGEN: Vista de kardex de un producto]**

**Acceso:** Menú principal → Inventario → Kardex

El Kardex muestra el historial de movimientos de un producto en un almacén específico:
- Entradas
- Salidas
- Existencias
- Costos

#### Salidas de Inventario

**[IMAGEN: Listado de salidas de inventario]**

Permite registrar salidas de productos del inventario:
- Tipo de salida
- Almacén
- Productos y cantidades
- Observaciones

### Presupuestos

El módulo de Presupuestos permite gestionar presupuestos de gastos.

#### Listado de Presupuestos

**[IMAGEN: Listado de presupuestos]**

**Acceso:** Menú principal → Presupuestos

**Funcionalidades:**
- Ver todos los presupuestos
- Crear nuevo presupuesto
- Ver detalles y gastos del presupuesto
- Editar o eliminar presupuestos (solo administradores)

#### Crear Presupuesto

1. Haz clic en **"Nuevo Presupuesto"**
2. Completa los datos:
   - **Ciclo**: Selecciona el ciclo
   - **Descripción**: Ingresa una descripción
   - **Fecha Inicio**: Fecha de inicio del presupuesto
   - **Fecha Fin**: Fecha de fin del presupuesto
3. Agrega los detalles:
   - **Proveedor**: Selecciona el proveedor
   - **Factura**: Número de factura
   - **Clasificación de Gasto**: Selecciona la clasificación
   - **Concepto**: Descripción del gasto
   - **Forma de Pago**: Selecciona del catálogo SAT
   - **Importe**: Ingresa el importe
4. Haz clic en **"Guardar Presupuesto"**

**[IMAGEN: Formulario de creación de presupuesto]**

### Gastos

El módulo de Gastos permite registrar gastos realizados.

#### Listado de Gastos

**[IMAGEN: Listado de gastos]**

**Acceso:** Menú principal → Gastos

**Funcionalidades:**
- Ver todos los gastos
- Filtrar por proveedor, clasificación, centro de costo y fechas
- Crear nuevo gasto
- Ver detalles de gasto
- Editar, eliminar o cancelar gastos

#### Crear Gasto

1. Haz clic en **"Nuevo Gasto"**
2. Completa los datos similares a la creación de presupuesto
3. Agrega los detalles del gasto
4. Haz clic en **"Guardar Gasto"**

---

## Catálogos

El sistema incluye varios catálogos que deben ser configurados antes de usar los módulos principales.

### Clientes

**[IMAGEN: Listado de clientes]**

**Acceso:** Menú principal → Catálogos → Clientes

**Funcionalidades:**
- Ver todos los clientes
- Crear nuevo cliente
- Editar cliente existente
- Ver detalles del cliente
- Activar/Desactivar clientes

**Campos principales:**
- Razón Social
- RFC
- Régimen Fiscal
- Dirección
- Contacto

### Proveedores

**[IMAGEN: Listado de proveedores]**

Similar a clientes, pero para proveedores.

### Transportistas

**[IMAGEN: Listado de transportistas]**

Gestiona los transportistas con:
- Nombre
- Teléfono
- Placas de unidad
- Observaciones

### Lotes - Origen

**[IMAGEN: Listado de lotes de origen]**

Gestiona los lotes de origen de los productos.

### Productos y Servicios

**[IMAGEN: Listado de productos y servicios]**

Catálogo completo de productos y servicios con:
- SKU
- Descripción
- Unidad de medida
- Clasificación de gasto
- Ingrediente activo
- Tipo de producto (Fungicida, Bactericida, Insecticida, Nutrición, Otro)

### Cultivos

**[IMAGEN: Listado de cultivos]**

Gestiona los tipos de cultivos disponibles.

### Otros Catálogos

- **Régimen Fiscal**: Catálogo de regímenes fiscales
- **Clasificación de Gastos**: Clasificaciones para gastos
- **Centro de Costos**: Centros de costo para asignación
- **Almacenes**: Almacenes del sistema
- **Usuarios**: Gestión de usuarios (solo administradores)

---

## Reportes

El sistema incluye varios reportes imprimibles:

### Reportes de Remisiones

- **Formato de Remisión**: Formato oficial de remisión
- **Estadísticas de Preliquidación**: Análisis de diferencias
- **Análisis de Kgs**: Comparación de kilogramos
- **Análisis de Calidad**: Análisis por calidad de producto
- **Análisis de Merma**: Análisis de merma enviada vs preliquidada
- **Ranking de Clientes**: Ranking por importe liquidado
- **Análisis de Importes**: Comparación de importes

### Reportes de Inventario

- **Existencias**: Reporte de existencias por almacén

### Reportes de Cobranza

- **Reporte de Cobranza**: Listado de remisiones con estado de pago
- **Reporte de Pagos**: Historial de pagos

### Reportes de Facturación

- **Factura PDF**: PDF de factura timbrada
- **XML de Factura**: Archivo XML del CFDI

---

## Configuración

### Configuración del Sistema

**[IMAGEN: Pantalla de configuración del sistema]**

**Acceso:** Menú principal → Configuración → Sistema

Permite configurar:
- **Ciclo Actual**: Ciclo de producción actual
- **Empresa**: Datos de la empresa
- **Configuraciones generales**

### Gestión de Usuarios

**[IMAGEN: Listado de usuarios]**

**Acceso:** Menú principal → Configuración → Usuarios

Solo disponible para administradores. Permite:
- Crear nuevos usuarios
- Editar usuarios existentes
- Asignar permisos
- Activar/Desactivar usuarios

---

## Consejos y Mejores Prácticas

### Seguridad

- No compartas tu contraseña
- Cierra sesión cuando termines de trabajar
- Reporta cualquier actividad sospechosa

### Uso del Sistema

- Completa todos los campos obligatorios
- Verifica los datos antes de guardar
- Usa los filtros para encontrar información rápidamente
- Revisa los reportes antes de imprimir

### Soporte

Para soporte técnico o consultas, contacta al administrador del sistema.

---

## Glosario de Términos

- **Remisión**: Documento que registra el envío de productos
- **Preliquidación**: Proceso de registrar los datos reales de recepción
- **Arps**: Unidad de medida (arpillas)
- **Merma**: Pérdida de producto durante el transporte
- **CFDI**: Comprobante Fiscal Digital por Internet
- **PAC**: Proveedor Autorizado de Certificación
- **Kardex**: Registro de movimientos de inventario

---

**Fin del Manual**

*Este manual fue generado automáticamente. Para actualizaciones, contacta al administrador del sistema.*

