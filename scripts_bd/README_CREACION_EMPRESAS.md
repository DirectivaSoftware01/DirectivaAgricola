# Sistema de Creación de Empresas

## 📋 Descripción

Este sistema permite crear nuevas empresas de forma automatizada con estructura completa de base de datos, catálogos básicos del SAT y configuración inicial.

## 🏗️ Arquitectura del Sistema

### Archivos Principales

1. **`scripts_bd/estructura_empresa_limpia.sql`**
   - Estructura base de la base de datos
   - Tablas principales del sistema
   - Índices para optimización

2. **`scripts_bd/datos_basicos_empresa.sql`**
   - Catálogos del SAT (regímenes fiscales, usos CFDI, etc.)
   - Datos básicos del sistema
   - Placeholders para datos específicos de la empresa

3. **`administracion/management/commands/crear_empresa_nueva.py`**
   - Comando de gestión para crear empresas
   - Integra los scripts SQL
   - Registra la empresa en administración

## 🚀 Proceso de Creación

### 1. Crear Nueva Empresa

```bash
./venv/bin/python manage.py crear_empresa_nueva \
    --razon-social="NOMBRE DE LA EMPRESA" \
    --rfc="RFC123456789" \
    --direccion="Dirección de la empresa" \
    --telefono="555-0123" \
    --ciclo-actual="2025"
```

### 2. Proceso Automatizado

El comando ejecuta automáticamente:

1. **Verificación**: Comprueba que no exista una empresa con el mismo RFC
2. **Creación de BD**: Crea la base de datos SQLite vacía
3. **Configuración Django**: Configura temporalmente Django para usar la nueva BD
4. **Migraciones**: Aplica todas las migraciones de Django
5. **Estructura**: Ejecuta el script de estructura de base de datos
6. **Catálogos**: Inserta los catálogos básicos del SAT
7. **Datos Empresa**: Inserta datos específicos de la empresa
8. **Registro**: Registra la empresa en la base de datos de administración

### 3. Datos Incluidos

#### Usuario Supervisor
- **Usuario**: `supervisor`
- **Contraseña**: `Directivasbmj1*`
- **Permisos**: Superusuario y administrador

#### Catálogos del SAT
- **17 Regímenes Fiscales** (601, 603, 605, etc.)
- **22 Usos de CFDI** (G01, G02, I01, D01, etc.)
- **2 Métodos de Pago** (PUE, PPD)
- **22 Formas de Pago** (01, 02, 03, etc.)
- **2 Tipos de Impuesto** (IVA 16%, IVA 0%)

#### Configuración del Sistema
- Datos de la empresa (razón social, RFC, dirección, teléfono)
- Ciclo actual
- Configuración de certificados (vacía, lista para configurar)
- Configuración de PAC (vacía, lista para configurar)

## 🔐 Sistema de Login

### Verificación de RFC

El sistema de login funciona de la siguiente manera:

1. **Captura de RFC**: El usuario ingresa su RFC en el formulario de login
2. **Búsqueda en Administración**: El sistema busca el RFC en la base de datos de administración
3. **Obtención de BD**: Si existe, obtiene el nombre de la base de datos de la empresa
4. **Configuración Dinámica**: Configura Django para usar la base de datos de la empresa
5. **Autenticación**: Valida usuario y contraseña contra la base de datos de la empresa

### Flujo de Autenticación

```
Usuario ingresa RFC + Usuario + Contraseña
           ↓
Sistema busca RFC en BD Administración
           ↓
Si existe → Obtiene nombre de BD empresa
           ↓
Configura Django para usar BD empresa
           ↓
Valida usuario/contraseña en BD empresa
           ↓
Si válido → Login exitoso
```

## 📁 Estructura de Archivos

```
scripts_bd/
├── README_CREACION_EMPRESAS.md          # Este archivo
├── estructura_empresa_limpia.sql        # Estructura de BD
├── datos_basicos_empresa.sql            # Catálogos básicos
├── estructura_empresa_completa.sql      # Backup completo
└── estructura_empresa_base.sql          # Estructura básica

administracion/management/commands/
└── crear_empresa_nueva.py               # Comando principal
```

## 🛠️ Mantenimiento

### Actualizar Estructura

Cuando se modifique el sistema:

1. **Actualizar Scripts**: Modificar `estructura_empresa_limpia.sql` y `datos_basicos_empresa.sql`
2. **Probar**: Crear una empresa de prueba para verificar cambios
3. **Documentar**: Actualizar este README si es necesario

### Backup de Estructura

Para crear un backup de la estructura actual:

```bash
sqlite3 Directiva_DEMO250901XXX.sqlite3 ".dump" > scripts_bd/backup_$(date +%Y%m%d).sql
```

## ✅ Verificación

### Comandos de Verificación

```bash
# Listar empresas registradas
./venv/bin/python manage.py shell -c "
from administracion.models import Empresa
for e in Empresa.objects.using('administracion').all():
    print(f'{e.nombre} - {e.rfc} - {e.db_name}')
"

# Verificar estructura de BD empresa
sqlite3 Directiva_NOMBREEMPRESA.sqlite3 ".tables"

# Verificar usuario supervisor
sqlite3 Directiva_NOMBREEMPRESA.sqlite3 "SELECT username, is_staff, is_active FROM usuarios;"

# Verificar catálogos
sqlite3 Directiva_NOMBREEMPRESA.sqlite3 "SELECT COUNT(*) FROM regimen_fiscal;"
```

## 🎯 Beneficios

1. **Automatización Completa**: Creación de empresa en un solo comando
2. **Estructura Consistente**: Todas las empresas tienen la misma estructura
3. **Catálogos Actualizados**: Incluye catálogos oficiales del SAT
4. **Configuración Inicial**: Lista para usar inmediatamente
5. **Escalabilidad**: Fácil mantenimiento y actualización
6. **Seguridad**: Usuario supervisor con permisos completos

## 🚨 Consideraciones

- **RFC Único**: Cada empresa debe tener un RFC único
- **Backup**: Hacer backup antes de modificar scripts
- **Pruebas**: Siempre probar en empresa de prueba antes de producción
- **Contraseñas**: La contraseña del supervisor es fija por seguridad
- **Configuración**: Los certificados y PAC deben configurarse después de la creación
