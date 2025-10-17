# Guía de Despliegue - Directiva Agrícola

## Configuración de GitHub Actions

### Secrets Requeridos

Para que GitHub Actions funcione correctamente, necesitas configurar los siguientes secrets en tu repositorio:

#### Secrets para Despliegue de Desarrollo
1. **EC2_HOST**: La IP pública de tu instancia EC2
   - Ejemplo: `54.212.80.37`

2. **EC2_SSH_KEY**: La clave privada SSH para conectarse a EC2
   - Contenido del archivo `directiva-agricola-key.pem`

3. **RDS_HOSTNAME**: El endpoint de tu base de datos RDS
   - Ejemplo: `directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com`

4. **RDS_DB_NAME**: Nombre de la base de datos principal
   - Ejemplo: `directiva_agricola`

5. **RDS_ADMIN_DB_NAME**: Nombre de la base de datos de administración
   - Ejemplo: `directiva_administracion`

6. **RDS_USERNAME**: Usuario de la base de datos
   - Ejemplo: `postgres`

7. **RDS_PASSWORD**: Contraseña de la base de datos
   - Ejemplo: `Directiva2024!`

8. **RDS_PORT**: Puerto de la base de datos
   - Ejemplo: `5432`

#### Secrets para Despliegue de Producción (opcional)
- **PROD_EC2_HOST**: IP de la instancia de producción
- **PROD_EC2_SSH_KEY**: Clave SSH de producción
- **PROD_RDS_HOSTNAME**: Endpoint de RDS de producción
- **PROD_RDS_DB_NAME**: Base de datos de producción
- **PROD_RDS_ADMIN_DB_NAME**: Base de datos de administración de producción
- **PROD_RDS_USERNAME**: Usuario de producción
- **PROD_RDS_PASSWORD**: Contraseña de producción
- **PROD_RDS_PORT**: Puerto de producción

### Cómo Configurar los Secrets

1. Ve a tu repositorio en GitHub
2. Haz clic en **Settings** (Configuración)
3. En el menú lateral, haz clic en **Secrets and variables** > **Actions**
4. Haz clic en **New repository secret**
5. Agrega cada secret con su nombre y valor correspondiente

### Workflows Disponibles

#### 1. Test and Lint (`test.yml`)
- Se ejecuta en cada push y pull request
- Ejecuta tests, linting y verificaciones de seguridad
- Compatible con Python 3.9, 3.10 y 3.11

#### 2. Deploy to Development (`deploy-simple.yml`)
- Se ejecuta en push a la rama `main`
- Despliega automáticamente a la instancia EC2 de desarrollo
- Incluye verificaciones de salud de la aplicación

#### 3. Production Deploy (`production-deploy.yml`)
- Se ejecuta cuando se crea un tag de versión (v*)
- Despliega a producción con verificaciones adicionales
- Incluye backup automático antes del despliegue

### Uso de los Workflows

#### Despliegue Automático
```bash
# Hacer push a main para desplegar a desarrollo
git add .
git commit -m "Nueva funcionalidad"
git push origin main
```

#### Despliegue a Producción
```bash
# Crear y push de un tag para desplegar a producción
git tag v1.0.0
git push origin v1.0.0
```

#### Despliegue Manual
1. Ve a la pestaña **Actions** en GitHub
2. Selecciona el workflow que quieres ejecutar
3. Haz clic en **Run workflow**
4. Selecciona la rama y haz clic en **Run workflow**

### Monitoreo del Despliegue

- Los logs de despliegue se guardan en `/var/log/directiva-agricola/deploy.log` en el servidor
- Los backups se guardan en `/opt/backups/directiva-agricola/` en el servidor
- GitHub Actions muestra el estado de cada paso en la interfaz web

### Solución de Problemas

#### El despliegue falla
1. Revisa los logs en GitHub Actions
2. Verifica que todos los secrets estén configurados correctamente
3. Revisa los logs del servidor: `sudo tail -f /var/log/directiva-agricola/deploy.log`

#### La aplicación no responde después del despliegue
1. Verifica el estado de los servicios:
   ```bash
   sudo systemctl status directiva
   sudo systemctl status nginx
   ```
2. Revisa los logs de la aplicación:
   ```bash
   sudo journalctl -u directiva.service -f
   ```

#### Restaurar desde backup
```bash
# Listar backups disponibles
ls -la /opt/backups/directiva-agricola/

# Restaurar desde backup
sudo systemctl stop directiva
sudo rm -rf /opt/directiva-agricola
sudo cp -r /opt/backups/directiva-agricola/backup-YYYYMMDD-HHMMSS /opt/directiva-agricola
sudo chown -R directiva:directiva /opt/directiva-agricola
sudo systemctl start directiva
```

### Estructura de Archivos

```
.github/
├── workflows/
│   ├── test.yml                 # Tests y linting
│   ├── deploy-simple.yml        # Despliegue a desarrollo
│   └── production-deploy.yml    # Despliegue a producción
deploy_script.sh                 # Script de despliegue
DEPLOYMENT.md                    # Esta guía
```

### Notas Importantes

- Los despliegues automáticos solo ocurren en la rama `main`
- Los tags de versión deben seguir el formato `v*` (ej: v1.0.0, v1.2.3)
- Los backups se mantienen por 5 versiones
- El script de despliegue incluye verificaciones de salud de la aplicación
- Todos los despliegues incluyen migraciones automáticas de base de datos