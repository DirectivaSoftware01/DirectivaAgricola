# 🚀 Configuración de CI/CD - Directiva Agrícola

## ✅ Configuración Completada

He configurado un sistema completo de CI/CD con GitHub Actions que incluye:

### 📋 Workflows Configurados

#### 1. **Despliegue Automático** (`deploy-simple.yml`)
- **Trigger**: Push a rama `main`
- **Funciones**:
  - Tests automáticos
  - Despliegue a EC2
  - Verificación de salud de la aplicación
  - Notificaciones de estado

#### 2. **Tests y Calidad** (`test.yml`)
- **Trigger**: Push y Pull Requests
- **Funciones**:
  - Tests en Python 3.9, 3.10, 3.11
  - Linting con flake8
  - Formateo de código con black
  - Ordenamiento de imports con isort
  - Verificaciones de seguridad

#### 3. **Despliegue a Producción** (`production-deploy.yml`)
- **Trigger**: Tags de versión (v*)
- **Funciones**:
  - Despliegue a producción
  - Backup automático antes del despliegue
  - Verificaciones adicionales
  - Notificaciones de estado

#### 4. **Despliegue a Staging** (`staging-deploy.yml`)
- **Trigger**: Push a ramas `develop` o `staging`
- **Funciones**:
  - Despliegue a entorno de staging
  - Tests de humo
  - Notificaciones de estado

#### 5. **Monitoreo de Salud** (`monitor.yml`)
- **Trigger**: Cada 5 minutos + manual
- **Funciones**:
  - Verificación de servicios
  - Verificación de base de datos
  - Monitoreo de recursos
  - Alertas automáticas

#### 6. **Backup Automático** (`backup.yml`)
- **Trigger**: Diario a las 2:00 AM UTC
- **Funciones**:
  - Backup de base de datos
  - Backup de código
  - Limpieza de backups antiguos
  - Notificaciones de estado

#### 7. **Escaneo de Seguridad** (`security-scan.yml`)
- **Trigger**: Push, PRs y semanalmente
- **Funciones**:
  - Verificación de vulnerabilidades
  - Análisis de código con Bandit
  - Escaneo con Semgrep
  - Detección de secretos hardcodeados

#### 8. **Pruebas de Rendimiento** (`performance-test.yml`)
- **Trigger**: Push, PRs y manual
- **Funciones**:
  - Análisis de consultas de BD
  - Pruebas de memoria
  - Pruebas de carga
  - Pruebas de estrés

#### 9. **Limpieza y Mantenimiento** (`cleanup.yml`)
- **Trigger**: Semanalmente + manual
- **Funciones**:
  - Limpieza de logs antiguos
  - Limpieza de backups antiguos
  - Limpieza de archivos temporales
  - Verificación de recursos

#### 10. **Rollback de Despliegues** (`rollback.yml`)
- **Trigger**: Manual
- **Funciones**:
  - Rollback a versión anterior
  - Rollback de emergencia
  - Verificación post-rollback
  - Notificaciones de estado

### 🔧 Configuración Requerida

#### Secrets de GitHub Necesarios

Para que los workflows funcionen, necesitas configurar estos secrets en tu repositorio:

1. **EC2_HOST**: `54.212.80.37`
2. **EC2_SSH_KEY**: Contenido del archivo `directiva-agricola-key.pem`
3. **RDS_HOSTNAME**: `directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com`
4. **RDS_DB_NAME**: `directiva_agricola`
5. **RDS_ADMIN_DB_NAME**: `directiva_administracion`
6. **RDS_USERNAME**: `postgres`
7. **RDS_PASSWORD**: `Directiva2024!`
8. **RDS_PORT**: `5432`

#### Cómo Configurar los Secrets

1. Ve a tu repositorio en GitHub
2. Haz clic en **Settings** (Configuración)
3. En el menú lateral, haz clic en **Secrets and variables** > **Actions**
4. Haz clic en **New repository secret**
5. Agrega cada secret con su nombre y valor correspondiente

### 🚀 Uso de los Workflows

#### Despliegue Automático
```bash
# Hacer push a main para desplegar automáticamente
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

### 📊 Monitoreo y Alertas

#### Verificación de Salud
- **Frecuencia**: Cada 5 minutos
- **Verificaciones**:
  - Estado de servicios (directiva, nginx)
  - Conectividad a base de datos
  - Respuesta de la aplicación
  - Uso de recursos (CPU, memoria, disco)

#### Backup Automático
- **Frecuencia**: Diario a las 2:00 AM UTC
- **Incluye**:
  - Backup de base de datos principal
  - Backup de base de datos de administración
  - Backup de código de la aplicación
  - Limpieza de backups antiguos

#### Limpieza Automática
- **Frecuencia**: Semanalmente los domingos a las 3:00 AM UTC
- **Incluye**:
  - Limpieza de logs antiguos
  - Limpieza de backups antiguos
  - Limpieza de archivos temporales
  - Verificación de recursos

### 🔒 Seguridad

#### Escaneo Automático
- **Frecuencia**: En cada push, PR y semanalmente
- **Incluye**:
  - Verificación de vulnerabilidades
  - Análisis de código con Bandit
  - Escaneo con Semgrep
  - Detección de secretos hardcodeados
  - Verificación de configuraciones de seguridad

#### Pruebas de Rendimiento
- **Frecuencia**: En cada push, PR y manual
- **Incluye**:
  - Análisis de consultas de base de datos
  - Pruebas de uso de memoria
  - Pruebas de carga
  - Pruebas de estrés

### 🛠️ Solución de Problemas

#### El Despliegue Falló
1. Revisa los logs en GitHub Actions
2. Verifica que todos los secrets estén configurados
3. Revisa los logs del servidor: `sudo tail -f /var/log/directiva-agricola/deploy.log`

#### La Aplicación No Responde
1. Verifica el estado de los servicios:
   ```bash
   sudo systemctl status directiva
   sudo systemctl status nginx
   ```
2. Revisa los logs de la aplicación:
   ```bash
   sudo journalctl -u directiva.service -f
   ```

#### Rollback de Emergencia
1. Ve a **Actions** > **Rollback Deployment**
2. Haz clic en **Run workflow**
3. Selecciona el tipo de rollback
4. Escribe **YES** para confirmar
5. Haz clic en **Run workflow**

### 📁 Estructura de Archivos

```
.github/
├── workflows/
│   ├── deploy-simple.yml        # Despliegue automático
│   ├── test.yml                 # Tests y calidad
│   ├── production-deploy.yml    # Despliegue a producción
│   ├── staging-deploy.yml       # Despliegue a staging
│   ├── monitor.yml              # Monitoreo de salud
│   ├── backup.yml               # Backup automático
│   ├── security-scan.yml        # Escaneo de seguridad
│   ├── performance-test.yml     # Pruebas de rendimiento
│   ├── cleanup.yml              # Limpieza y mantenimiento
│   └── rollback.yml             # Rollback de despliegues
deploy_script.sh                 # Script de despliegue
DEPLOYMENT.md                    # Guía de despliegue
CI_CD_SETUP.md                   # Esta guía
```

### 🎯 Próximos Pasos

1. **Configurar los secrets de GitHub** (requerido)
2. **Probar el despliegue automático** con un push a main
3. **Configurar notificaciones** (email, Slack, etc.)
4. **Configurar monitoreo adicional** (CloudWatch, etc.)
5. **Configurar SSL/HTTPS** (próximo paso)

### 📞 Soporte

Si tienes problemas con la configuración de CI/CD:

1. Revisa los logs en GitHub Actions
2. Verifica que todos los secrets estén configurados
3. Revisa la documentación en `DEPLOYMENT.md`
4. Consulta los logs del servidor en `/var/log/directiva-agricola/`

¡El sistema de CI/CD está listo para usar! 🎉
