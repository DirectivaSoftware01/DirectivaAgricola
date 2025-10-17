# Limpieza Manual de Recursos AWS

## ⚠️ Problema con credenciales automáticas

Las credenciales proporcionadas tienen un error de firma. Necesitas ejecutar la limpieza manualmente.

## 🔧 Pasos para limpieza manual:

### 1. Verificar credenciales AWS
```bash
aws sts get-caller-identity
```

### 2. Si las credenciales fallan, configurar nuevas:
```bash
aws configure
# Ingresar credenciales válidas
```

### 3. Ejecutar comandos de limpieza uno por uno:

#### Terminar instancias EC2:
```bash
# Listar instancias
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress]' --output table

# Terminar instancia específica (reemplazar i-1234567890abcdef0)
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0
```

#### Eliminar Security Groups:
```bash
# Listar security groups
aws ec2 describe-security-groups --query 'SecurityGroups[?GroupName!=`default`].[GroupId,GroupName]' --output table

# Eliminar security group específico (reemplazar sg-1234567890abcdef0)
aws ec2 delete-security-group --group-id sg-1234567890abcdef0
```

#### Eliminar Key Pairs:
```bash
# Listar key pairs
aws ec2 describe-key-pairs --query 'KeyPairs[*].[KeyName]' --output table

# Eliminar key pair específico (reemplazar directiva-key)
aws ec2 delete-key-pair --key-name directiva-key
```

#### Eliminar volúmenes EBS huérfanos:
```bash
# Listar volúmenes disponibles
aws ec2 describe-volumes --query 'Volumes[?State==`available`].[VolumeId,Size,VolumeType]' --output table

# Eliminar volumen específico (reemplazar vol-1234567890abcdef0)
aws ec2 delete-volume --volume-id vol-1234567890abcdef0
```

#### Eliminar instancia RDS:
```bash
# Listar instancias RDS
aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus]' --output table

# Eliminar instancia RDS específica (reemplazar directiva-agricola-db)
aws rds delete-db-instance --db-instance-identifier directiva-agricola-db --skip-final-snapshot --delete-automated-backups
```

#### Eliminar DB Subnet Groups:
```bash
# Listar subnet groups
aws rds describe-db-subnet-groups --query 'DBSubnetGroups[*].[DBSubnetGroupName]' --output table

# Eliminar subnet group específico (reemplazar directiva-subnet-group)
aws rds delete-db-subnet-group --db-subnet-group-name directiva-subnet-group
```

### 4. Verificar Elastic IPs (se mantienen):
```bash
aws ec2 describe-addresses --query 'Addresses[*].[AllocationId,PublicIp,InstanceId]' --output table
```

## 🎯 Recursos específicos a buscar y eliminar:

Basándome en nuestro despliegue anterior, busca estos recursos:

- **Instancia EC2**: Con IP `52.38.4.79` o `54.212.80.37`
- **Security Groups**: Que contengan `directiva` en el nombre
- **Key Pair**: `directiva-key` o similar
- **RDS Instance**: `directiva-agricola-db` o similar
- **DB Subnet Group**: Que contenga `directiva` en el nombre

## ⚠️ Importante:
- Las **Elastic IPs se mantienen** para uso futuro
- La eliminación de RDS es **irreversible**
- Algunos recursos pueden tener dependencias que requieren eliminación manual
