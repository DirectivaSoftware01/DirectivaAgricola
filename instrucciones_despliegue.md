# Instrucciones de Despliegue en AWS EC2

## Prerequisitos
- Instancia EC2 ejecutándose en IP: 54.212.80.37
- Clave SSH: directiva-agricola-key.pem
- RDS PostgreSQL configurado

## Pasos para el Despliegue

### 1. Conectarse a la instancia EC2
```bash
ssh -i directiva-agricola-key.pem ubuntu@54.212.80.37
```

### 2. Ejecutar el script de despliegue
Una vez conectado a la instancia EC2, ejecutar:

```bash
# Descargar y ejecutar el script de despliegue
curl -s https://raw.githubusercontent.com/DirectivaSoftware01/DirectivaAgricola/main/deploy_ec2_direct.sh | bash
```

### 3. Verificar el despliegue
```bash
# Verificar estado del servicio
sudo systemctl status directiva-agricola

# Ver logs
sudo journalctl -u directiva-agricola -f

# Verificar que Nginx esté funcionando
sudo systemctl status nginx

# Probar la aplicación
curl -I http://localhost
```

## Configuración de RDS

### Verificar conectividad con RDS
```bash
# Instalar cliente PostgreSQL
sudo apt install postgresql-client

# Probar conexión
psql -h directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com -U postgres -d postgres
```

### Crear bases de datos
```sql
-- Conectarse a PostgreSQL
psql -h directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com -U postgres -d postgres

-- Crear bases de datos
CREATE DATABASE directiva_administracion;
CREATE DATABASE directiva_agricola;

-- Salir
\q
```

## Credenciales de Acceso

- **Usuario administrador**: admin
- **Contraseña**: Directiva2024!
- **Usuario supervisor**: supervisor  
- **Contraseña**: Directivasbmj1*

## URLs de Acceso

- **Aplicación principal**: http://54.212.80.37
- **Administración de empresas**: http://54.212.80.37/admin-empresas/

## Comandos Útiles

```bash
# Reiniciar aplicación
sudo systemctl restart directiva-agricola

# Ver logs en tiempo real
sudo journalctl -u directiva-agricola -f

# Verificar puertos abiertos
sudo netstat -tlnp

# Verificar configuración de Nginx
sudo nginx -t

# Recargar configuración de Nginx
sudo systemctl reload nginx
```

## Solución de Problemas

### Si la aplicación no inicia
```bash
# Verificar logs de error
sudo journalctl -u directiva-agricola --no-pager -l

# Verificar configuración de Django
cd /var/www/directiva_agricola
source venv/bin/activate
python manage.py check --settings=directiva_agricola.settings_production
```

### Si hay problemas de base de datos
```bash
# Verificar conectividad
psql -h directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com -U postgres -d postgres

# Ejecutar migraciones manualmente
cd /var/www/directiva_agricola
source venv/bin/activate
python manage.py migrate --settings=directiva_agricola.settings_production --database=administracion
python manage.py migrate --settings=directiva_agricola.settings_production --database=default
```

### Si hay problemas de permisos
```bash
# Corregir permisos
sudo chown -R ubuntu:www-data /var/www/directiva_agricola
sudo chmod -R 755 /var/www/directiva_agricola
```
