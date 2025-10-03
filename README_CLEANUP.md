# Limpieza de Recursos AWS

## Instrucciones para eliminar recursos AWS manteniendo Elastic IP

### Prerrequisitos
1. AWS CLI instalado y configurado
2. Credenciales AWS válidas con permisos para EC2 y RDS

### Pasos

1. **Configurar credenciales AWS** (si no están configuradas):
   ```bash
   aws configure
   # Ingresar:
   # AWS Access Key ID: [TU_ACCESS_KEY_ID]
   # AWS Secret Access Key: [TU_SECRET_ACCESS_KEY]
   # Default region name: us-west-2
   # Default output format: json
   ```

2. **Ejecutar script de limpieza**:
   ```bash
   bash cleanup_aws_resources.sh
   ```

### Recursos que se eliminarán:
- ✅ Instancias EC2 (terminadas)
- ✅ Security Groups personalizados
- ✅ Key Pairs de Directiva
- ✅ Volúmenes EBS huérfanos
- ✅ Instancias RDS de Directiva
- ✅ DB Subnet Groups de Directiva

### Recursos que se mantienen:
- 🌍 **Elastic IPs** (para uso futuro)
- 🌐 **Route 53** (si tienes configurado el subdominio)

### Verificación post-limpieza:
```bash
# Verificar que no quedan instancias activas
aws ec2 describe-instances

# Verificar que no quedan instancias RDS
aws rds describe-db-instances

# Verificar Elastic IPs (deben mantenerse)
aws ec2 describe-addresses
```

### Notas importantes:
- ⚠️ La eliminación de RDS es **irreversible** (sin snapshot)
- 🔒 Las Elastic IPs se mantienen activas y seguirán generando costos mínimos
- 📋 Si hay errores de dependencias, algunos recursos pueden requerir eliminación manual
