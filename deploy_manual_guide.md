# 🚀 Guía de Despliegue Manual

Como hay un problema de permisos SSH, aquí tienes una guía paso a paso para desplegar manualmente:

## 📋 Opción 1: Conexión SSH Manual

### 1. Conectar al servidor
```bash
ssh root@89.116.51.217
# O si tienes un usuario específico:
ssh tu_usuario@89.116.51.217
```

### 2. Ir al directorio del proyecto
```bash
cd /var/www/directiva_agricola
```

### 3. Actualizar código desde Git
```bash
git pull origin main
```

### 4. Activar entorno virtual
```bash
source venv/bin/activate
```

### 5. Ejecutar migraciones
```bash
python manage.py migrate --settings=directiva_agricola.settings_production
```

### 6. Recopilar archivos estáticos
```bash
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production
```

### 7. Reiniciar aplicación
```bash
systemctl restart directiva-agricola
```

### 8. Verificar estado
```bash
systemctl status directiva-agricola
```

## 📋 Opción 2: Subir Archivos Manualmente

Si no tienes acceso SSH, puedes usar el panel de control de Hostinger:

### 1. Archivos a Subir (en orden de prioridad):

**Templates (más importantes):**
- `templates/core/presupuesto_list.html`
- `templates/core/presupuesto_detail.html`
- `templates/core/presupuesto_gastos_reporte.html`
- `templates/core/remision_liquidacion.html`
- `templates/core/remision_detail.html`
- `templates/core/remision_form.html`
- `templates/core/remision_imprimir.html`

**Modelos y Vistas:**
- `core/models.py`
- `core/views/main_views.py`
- `core/catalogos_ajax_views.py`
- `core/admin.py`
- `core/urls.py`

**Configuración:**
- `requirements.txt`

### 2. Pasos en el Panel de Hostinger:

1. **Acceder al File Manager** en el panel de Hostinger
2. **Navegar a** `/public_html/` o `/var/www/directiva_agricola/`
3. **Subir archivos** uno por uno manteniendo la estructura de carpetas
4. **Ejecutar comandos** en el terminal del panel:
   ```bash
   cd /var/www/directiva_agricola
   source venv/bin/activate
   python manage.py migrate --settings=directiva_agricola.settings_production
   python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production
   systemctl restart directiva-agricola
   ```

## 📋 Opción 3: Configurar SSH (Recomendado)

### 1. Generar clave SSH (en tu máquina local)
```bash
ssh-keygen -t rsa -b 4096 -C "tu_email@ejemplo.com"
```

### 2. Copiar clave pública al servidor
```bash
ssh-copy-id root@89.116.51.217
```

### 3. Probar conexión
```bash
ssh root@89.116.51.217
```

### 4. Ejecutar script de despliegue
```bash
./deploy_changes.sh
```

## 🔧 Verificación Post-Despliegue

Después de cualquier método, verifica:

1. **Estado de la aplicación:**
   ```bash
   systemctl status directiva-agricola
   ```

2. **Logs de la aplicación:**
   ```bash
   journalctl -u directiva-agricola -f
   ```

3. **Acceso web:**
   - Abrir: `http://89.116.51.217`
   - Verificar que cargue correctamente
   - Probar funcionalidades principales

## 🆘 Solución de Problemas

### Error de Permisos SSH
- Verificar que el usuario tenga acceso SSH
- Configurar autenticación por clave
- Contactar soporte de Hostinger

### Error 502 Bad Gateway
```bash
systemctl restart directiva-agricola
systemctl restart nginx
```

### Error de Base de Datos
```bash
python manage.py migrate --settings=directiva_agricola.settings_production
```

## 📞 ¿Cuál Opción Prefieres?

1. **SSH Manual** - Si tienes acceso SSH
2. **Panel de Hostinger** - Si no tienes SSH
3. **Configurar SSH** - Para futuros despliegues

¡Dime cuál opción prefieres y te ayudo con los pasos específicos!
