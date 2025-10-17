# 🚀 Instrucciones para Actualizar la Aplicación en Hostinger

## 📋 Opciones de Actualización

Tienes **3 opciones** para actualizar tu aplicación en el servidor de Hostinger:

### 1. 🔄 Actualización Completa (Recomendada para cambios importantes)

```bash
# En tu máquina local
./upload_to_hosting.sh
```

**¿Qué hace?**
- Sube todos los archivos al servidor
- Hace backup de la base de datos
- Ejecuta migraciones
- Reinicia todos los servicios

### 2. ⚡ Actualización Rápida (Para cambios menores)

```bash
# Conectar al servidor
ssh root@89.116.51.217

# Ejecutar actualización rápida
cd /var/www/directiva_agricola
sudo ./quick_update.sh
```

**¿Qué hace?**
- Actualiza solo el código
- Ejecuta migraciones
- Reinicia la aplicación

### 3. 🛠️ Actualización Manual (Para control total)

```bash
# Conectar al servidor
ssh root@89.116.51.217

# Ir al directorio del proyecto
cd /var/www/directiva_agricola

# Actualizar código
git pull origin main

# Activar entorno virtual
source venv/bin/activate

# Ejecutar migraciones
python manage.py migrate --settings=directiva_agricola.settings_production

# Recopilar archivos estáticos
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production

# Reiniciar aplicación
systemctl restart directiva-agricola
```

## 🔧 Configuración del Script de Subida

**IMPORTANTE:** Antes de usar `upload_to_hosting.sh`, edita las variables:

```bash
nano upload_to_hosting.sh
```

Cambia estas líneas:
```bash
SERVER_IP="89.116.51.217"  # Tu IP del VPS
SERVER_USER="root"  # Tu usuario del servidor
```

## 📊 Verificación Post-Actualización

Después de cualquier actualización, verifica:

### 1. Estado de la Aplicación
```bash
systemctl status directiva-agricola
```

### 2. Logs de la Aplicación
```bash
journalctl -u directiva-agricola -f
```

### 3. Estado de Nginx
```bash
systemctl status nginx
```

### 4. Acceso Web
- Abre tu navegador y ve a: `http://89.116.51.217`
- Verifica que la aplicación cargue correctamente
- Prueba las funcionalidades principales

## 🆘 Solución de Problemas

### Error 502 Bad Gateway
```bash
# Verificar que Gunicorn esté ejecutándose
systemctl status directiva-agricola

# Reiniciar servicios
systemctl restart directiva-agricola
systemctl restart nginx
```

### Error de Base de Datos
```bash
# Verificar migraciones
cd /var/www/directiva_agricola
source venv/bin/activate
python manage.py showmigrations --settings=directiva_agricola.settings_production
```

### Error de Archivos Estáticos
```bash
# Recopilar archivos estáticos
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production

# Verificar permisos
chown -R www-data:www-data /var/www/directiva_agricola/static/
```

## 📝 Cambios Incluidos en Esta Actualización

### ✅ Mejoras de Diseño
- Títulos de tarjetas con color blanco para mejor contraste
- Diseño unificado entre templates de facturas y presupuestos
- Encabezados de tabla con estilo `table-light`

### ✅ Funcionalidades de Gastos
- Campo "Forma de Pago" en modales de gastos
- Campo "Autorizó" con catálogo dinámico
- Filtros de búsqueda por forma de pago y autorizador
- Botón de cancelación de gastos
- Botones de acción ocultos en impresión

### ✅ Mejoras de Remisiones
- Fórmula corregida para "Kgs Liquidados"
- Columnas "Dif" ocultas pero funcionales
- Nuevas columnas en formato de impresión
- Campos ocultos en modal de nueva remisión

## 🎯 Recomendación

Para esta actualización, te recomiendo usar la **Opción 1 (Actualización Completa)** porque incluye:

- Nuevos modelos de base de datos (`AutorizoGasto`)
- Nuevas migraciones
- Cambios en templates
- Nuevas funcionalidades AJAX

## 📞 Soporte

Si encuentras algún problema:

1. Revisa los logs: `journalctl -u directiva-agricola -f`
2. Verifica el estado: `systemctl status directiva-agricola`
3. Consulta este archivo de instrucciones
4. Contacta al soporte técnico si es necesario

¡Tu aplicación estará actualizada y funcionando perfectamente! 🚀
