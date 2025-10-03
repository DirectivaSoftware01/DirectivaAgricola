# Solución para Security Group con Dependencias

## ⚠️ Problema
El Security Group `sg-0edd3aec09a9dbeed` (directiva-agricola-sg) no se puede eliminar porque tiene objetos dependientes.

## 🔍 Estado actual:
- ✅ Instancia EC2 terminada
- ✅ Todas las reglas de entrada eliminadas
- ❌ Security Group aún tiene dependencias

## 🛠️ Soluciones posibles:

### Opción 1: Esperar (Recomendado)
AWS a veces tarda hasta 24 horas en liberar completamente las dependencias de un Security Group después de terminar una instancia. El Security Group se eliminará automáticamente.

### Opción 2: Eliminación manual desde consola AWS
1. Ve a la consola AWS EC2
2. Security Groups → directiva-agricola-sg
3. Verifica qué recursos están usando este Security Group
4. Elimina manualmente las dependencias
5. Elimina el Security Group

### Opción 3: Verificar dependencias específicas
```bash
# Verificar Network Interfaces
aws ec2 describe-network-interfaces --filters "Name=group-id,Values=sg-0edd3aec09a9dbeed"

# Verificar Load Balancers (requiere permisos adicionales)
aws elbv2 describe-load-balancers

# Verificar Auto Scaling Groups
aws autoscaling describe-auto-scaling-groups
```

## 📋 Comando para verificar estado:
```bash
aws ec2 describe-security-groups --query 'SecurityGroups[?GroupName!=`default`].[GroupId,GroupName,Description]' --output table
```

## ⏰ Recomendación:
**Esperar 24 horas** y luego ejecutar:
```bash
aws ec2 delete-security-group --group-id sg-0edd3aec09a9dbeed
```

El Security Group se eliminará automáticamente cuando AWS libere todas las dependencias internas.
