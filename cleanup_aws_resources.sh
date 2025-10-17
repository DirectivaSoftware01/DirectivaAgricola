#!/bin/bash

# Script para limpiar recursos AWS manteniendo Elastic IP
# Ejecutar con: bash cleanup_aws_resources.sh

set -e

echo "🧹 Iniciando limpieza de recursos AWS..."
echo "⚠️  Se mantendrá la Elastic IP asignada"

# Configurar región
export AWS_DEFAULT_REGION=us-west-2

# 1. Detener y terminar instancia EC2
echo "📋 Buscando instancias EC2..."
INSTANCES=$(aws ec2 describe-instances --query 'Reservations[*].Instances[?State.Name!=`terminated`].[InstanceId]' --output text)

if [ ! -z "$INSTANCES" ]; then
    echo "🛑 Deteniendo instancias EC2: $INSTANCES"
    for instance in $INSTANCES; do
        echo "   Deteniendo instancia: $instance"
        aws ec2 stop-instances --instance-ids $instance
        sleep 10
        aws ec2 terminate-instances --instance-ids $instance
    done
    echo "✅ Instancias EC2 terminadas"
else
    echo "ℹ️  No se encontraron instancias EC2 activas"
fi

# 2. Eliminar Security Groups (excepto default)
echo "🔒 Eliminando Security Groups..."
SECURITY_GROUPS=$(aws ec2 describe-security-groups --query 'SecurityGroups[?GroupName!=`default`].[GroupId]' --output text)

if [ ! -z "$SECURITY_GROUPS" ]; then
    for sg in $SECURITY_GROUPS; do
        echo "   Eliminando Security Group: $sg"
        aws ec2 delete-security-group --group-id $sg || echo "   ⚠️  No se pudo eliminar $sg (puede tener dependencias)"
    done
    echo "✅ Security Groups eliminados"
else
    echo "ℹ️  No se encontraron Security Groups personalizados"
fi

# 3. Eliminar Key Pairs
echo "🔑 Eliminando Key Pairs..."
KEY_PAIRS=$(aws ec2 describe-key-pairs --query 'KeyPairs[?contains(KeyName, `directiva`)].KeyName' --output text)

if [ ! -z "$KEY_PAIRS" ]; then
    for key in $KEY_PAIRS; do
        echo "   Eliminando Key Pair: $key"
        aws ec2 delete-key-pair --key-name $key
    done
    echo "✅ Key Pairs eliminados"
else
    echo "ℹ️  No se encontraron Key Pairs de Directiva"
fi

# 4. Eliminar volúmenes EBS huérfanos
echo "💾 Eliminando volúmenes EBS huérfanos..."
ORPHANED_VOLUMES=$(aws ec2 describe-volumes --query 'Volumes[?State==`available`].[VolumeId]' --output text)

if [ ! -z "$ORPHANED_VOLUMES" ]; then
    for volume in $ORPHANED_VOLUMES; do
        echo "   Eliminando volumen: $volume"
        aws ec2 delete-volume --volume-id $volume
    done
    echo "✅ Volúmenes EBS eliminados"
else
    echo "ℹ️  No se encontraron volúmenes EBS huérfanos"
fi

# 5. Eliminar instancia RDS
echo "🗄️  Eliminando instancia RDS..."
RDS_INSTANCES=$(aws rds describe-db-instances --query 'DBInstances[?contains(DBInstanceIdentifier, `directiva`)].DBInstanceIdentifier' --output text)

if [ ! -z "$RDS_INSTANCES" ]; then
    for db in $RDS_INSTANCES; do
        echo "   Eliminando instancia RDS: $db"
        aws rds delete-db-instance --db-instance-identifier $db --skip-final-snapshot --delete-automated-backups
    done
    echo "✅ Instancias RDS eliminadas"
else
    echo "ℹ️  No se encontraron instancias RDS de Directiva"
fi

# 6. Eliminar Subnet Groups de RDS
echo "🌐 Eliminando DB Subnet Groups..."
SUBNET_GROUPS=$(aws rds describe-db-subnet-groups --query 'DBSubnetGroups[?contains(DBSubnetGroupName, `directiva`)].DBSubnetGroupName' --output text)

if [ ! -z "$SUBNET_GROUPS" ]; then
    for subnet_group in $SUBNET_GROUPS; do
        echo "   Eliminando DB Subnet Group: $subnet_group"
        aws rds delete-db-subnet-group --db-subnet-group-name $subnet_group
    done
    echo "✅ DB Subnet Groups eliminados"
else
    echo "ℹ️  No se encontraron DB Subnet Groups de Directiva"
fi

# 7. Verificar Elastic IPs
echo "🌍 Verificando Elastic IPs..."
ELASTIC_IPS=$(aws ec2 describe-addresses --query 'Addresses[*].[AllocationId,PublicIp,InstanceId]' --output table)
echo "$ELASTIC_IPS"

echo ""
echo "🎉 Limpieza completada!"
echo "📌 Las Elastic IPs se mantienen activas para uso futuro"
echo "💡 Para verificar el estado de los recursos:"
echo "   aws ec2 describe-instances"
echo "   aws rds describe-db-instances"
echo "   aws ec2 describe-addresses"
