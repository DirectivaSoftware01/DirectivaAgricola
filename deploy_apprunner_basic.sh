#!/bin/bash

# Script de despliegue básico para AWS App Runner
# Configuración básica
APP_NAME="directiva-agricola"
DB_INSTANCE_ID="directiva-agricola-db"
DB_NAME="directiva_agricola"
ADMIN_DB_NAME="directiva_administracion"
DB_USERNAME="postgres"
DB_PASSWORD="Directiva2024!"
AWS_REGION="us-west-2"
DOMAIN_NAME="agricola.directiva.mx"

echo "🚀 Iniciando despliegue básico en AWS App Runner..."
echo "📱 Aplicación: $APP_NAME"
echo "🌐 Dominio: $DOMAIN_NAME"
echo "🗄️ Región: $AWS_REGION"

# 1. Crear base de datos RDS PostgreSQL
echo "🗄️ Creando base de datos RDS PostgreSQL..."
DB_EXISTS=$(aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null)

if [ "$DB_EXISTS" == "available" ]; then
    echo "✅ Base de datos '$DB_INSTANCE_ID' ya existe y está disponible."
elif [ "$DB_EXISTS" == "None" ] || [ "$DB_EXISTS" == "" ]; then
    echo "📦 Creando nueva base de datos RDS..."
    aws rds create-db-instance \
        --db-instance-identifier $DB_INSTANCE_ID \
        --db-instance-class db.t3.micro \
        --engine postgres \
        --engine-version 15.2 \
        --master-username $DB_USERNAME \
        --master-user-password $DB_PASSWORD \
        --allocated-storage 20 \
        --storage-type gp2 \
        --vpc-security-group-ids default \
        --backup-retention-period 7 \
        --storage-encrypted \
        --region $AWS_REGION

    echo "⏳ Esperando a que la base de datos esté disponible..."
    aws rds wait db-instance-available --db-instance-identifier $DB_INSTANCE_ID --region $AWS_REGION
    echo "✅ Base de datos RDS creada y disponible."
else
    echo "⏳ Base de datos existe pero no está disponible ($DB_EXISTS), esperando..."
    aws rds wait db-instance-available --db-instance-identifier $DB_INSTANCE_ID --region $AWS_REGION
    echo "✅ Base de datos RDS disponible."
fi

# Obtener endpoint de la base de datos
DB_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --query 'DBInstances[0].Endpoint.Address' --output text --region $AWS_REGION)
echo "🗄️ Endpoint BD: $DB_ENDPOINT"

# 2. Crear bucket S3 para archivos estáticos
S3_BUCKET_NAME="directiva-agricola-static-$(date +%s)"
echo "🪣 Creando bucket S3 para archivos estáticos: $S3_BUCKET_NAME..."
aws s3 mb s3://$S3_BUCKET_NAME --region $AWS_REGION

echo "✅ Bucket S3 creado: $S3_BUCKET_NAME"

# 3. Crear servicio de App Runner usando imagen pública
echo "🚀 Creando servicio de App Runner..."

# Verificar si el servicio ya existe
SERVICE_EXISTS=$(aws apprunner describe-service --service-arn "arn:aws:apprunner:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):service/$APP_NAME" --query 'Service.ServiceName' --output text 2>/dev/null)

if [ "$SERVICE_EXISTS" == "None" ] || [ "$SERVICE_EXISTS" == "" ]; then
    echo "📋 Información del despliegue:"
    echo "• Base de datos: $DB_ENDPOINT"
    echo "• Bucket S3: $S3_BUCKET_NAME"
    echo "• Región: $AWS_REGION"
    echo ""
    echo "⚠️  Para completar el despliegue necesitas:"
    echo "1. Permisos adicionales para App Runner"
    echo "2. Crear el servicio manualmente desde AWS Console"
    echo ""
    echo "🔧 Configuración necesaria para App Runner:"
    echo "• Imagen: public.ecr.aws/docker/library/python:3.11-slim"
    echo "• Puerto: 8000"
    echo "• Variables de entorno:"
    echo "  - DJANGO_SETTINGS_MODULE=directiva_agricola.settings_production"
    echo "  - RDS_DB_NAME=$DB_NAME"
    echo "  - RDS_ADMIN_DB_NAME=$ADMIN_DB_NAME"
    echo "  - RDS_USERNAME=$DB_USERNAME"
    echo "  - RDS_PASSWORD=$DB_PASSWORD"
    echo "  - RDS_HOSTNAME=$DB_ENDPOINT"
    echo "  - RDS_PORT=5432"
    echo "  - AWS_STORAGE_BUCKET_NAME=$S3_BUCKET_NAME"
    echo "  - AWS_S3_REGION_NAME=$AWS_REGION"
    echo "  - SECRET_KEY=$(openssl rand -base64 32)"
    echo ""
    echo "📖 Pasos para crear el servicio:"
    echo "1. Ve a AWS Console > App Runner"
    echo "2. Crea un nuevo servicio"
    echo "3. Selecciona 'Container image'"
    echo "4. Usa la imagen: public.ecr.aws/docker/library/python:3.11-slim"
    echo "5. Configura las variables de entorno listadas arriba"
    echo "6. Puerto: 8000"
    echo "7. CPU: 0.25 vCPU, Memoria: 0.5 GB"
else
    echo "✅ Servicio de App Runner ya existe."
fi

echo ""
echo "✅ Preparación completada!"
echo "💰 Costo estimado: ~$20-30/mes (App Runner + RDS + S3)"
echo ""
echo "📋 Próximos pasos:"
echo "1. Crear servicio de App Runner desde AWS Console"
echo "2. Configurar DNS de tu dominio"
echo "3. Verificar que la aplicación funcione correctamente"
echo ""
echo "🔑 Credenciales de acceso:"
echo "• Usuario: supervisor"
echo "• Contraseña: Directivasbmj1*"
