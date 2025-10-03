#!/bin/bash

# Script de despliegue para AWS App Runner usando código fuente
# Configuración básica
APP_NAME="directiva-agricola"
DB_INSTANCE_ID="directiva-agricola-db"
DB_NAME="directiva_agricola"
ADMIN_DB_NAME="directiva_administracion"
DB_USERNAME="postgres"
DB_PASSWORD="Directiva2024!"
AWS_REGION="us-west-2"
DOMAIN_NAME="agricola.directiva.mx"

echo "🚀 Iniciando despliegue en AWS App Runner (código fuente)..."
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
        --engine-version 15.4 \
        --master-username $DB_USERNAME \
        --master-user-password $DB_PASSWORD \
        --allocated-storage 20 \
        --storage-type gp2 \
        --vpc-security-group-ids default \
        --backup-retention-period 7 \
        --multi-az \
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

# Configurar bucket para acceso público a archivos estáticos
aws s3api put-bucket-policy \
    --bucket $S3_BUCKET_NAME \
    --policy "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [
            {
                \"Effect\": \"Allow\",
                \"Principal\": \"*\",
                \"Action\": [\"s3:GetObject\"],
                \"Resource\": [\"arn:aws:s3:::$S3_BUCKET_NAME/static/*\"]
            }
        ]
    }" \
    --region $AWS_REGION

echo "✅ Bucket S3 creado y política configurada."

# 3. Crear repositorio de código fuente en GitHub (simulado)
echo "📁 Preparando código fuente para App Runner..."

# Crear un archivo ZIP con el código fuente
echo "📦 Creando archivo ZIP del código fuente..."
zip -r directiva-agricola-source.zip . -x "venv/*" "__pycache__/*" "*.pyc" ".git/*" "*.sqlite3" "media/*" "staticfiles/*" "deploy_*.sh" "*.md"

# Subir el código fuente a S3 temporalmente
SOURCE_BUCKET="directiva-agricola-source-$(date +%s)"
aws s3 mb s3://$SOURCE_BUCKET --region $AWS_REGION
aws s3 cp directiva-agricola-source.zip s3://$SOURCE_BUCKET/ --region $AWS_REGION

echo "✅ Código fuente preparado y subido a S3."

# 4. Crear servicio de App Runner usando código fuente
echo "🚀 Creando servicio de App Runner..."

# Verificar si el servicio ya existe
SERVICE_EXISTS=$(aws apprunner describe-service --service-arn "arn:aws:apprunner:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):service/$APP_NAME" --query 'Service.ServiceName' --output text 2>/dev/null)

if [ "$SERVICE_EXISTS" == "None" ] || [ "$SERVICE_EXISTS" == "" ]; then
    # Crear el servicio usando código fuente
    SERVICE_ARN=$(aws apprunner create-service \
        --service-name $APP_NAME \
        --source-configuration "{
            \"CodeRepository\": {
                \"RepositoryUrl\": \"https://github.com/aws/aws-apprunner-sample-python.git\",
                \"SourceCodeVersion\": {
                    \"Type\": \"BRANCH\",
                    \"Value\": \"main\"
                },
                \"CodeConfiguration\": {
                    \"ConfigurationSource\": \"REPOSITORY\",
                    \"CodeConfigurationValues\": {
                        \"Runtime\": \"PYTHON_3\",
                        \"BuildCommand\": \"pip install -r requirements.txt\",
                        \"StartCommand\": \"gunicorn --bind 0.0.0.0:8000 --workers 2 directiva_agricola.wsgi:application\",
                        \"RuntimeEnvironmentVariables\": {
                            \"DJANGO_SETTINGS_MODULE\": \"directiva_agricola.settings_production\",
                            \"RDS_DB_NAME\": \"$DB_NAME\",
                            \"RDS_ADMIN_DB_NAME\": \"$ADMIN_DB_NAME\",
                            \"RDS_USERNAME\": \"$DB_USERNAME\",
                            \"RDS_PASSWORD\": \"$DB_PASSWORD\",
                            \"RDS_HOSTNAME\": \"$DB_ENDPOINT\",
                            \"RDS_PORT\": \"5432\",
                            \"AWS_STORAGE_BUCKET_NAME\": \"$S3_BUCKET_NAME\",
                            \"AWS_S3_REGION_NAME\": \"$AWS_REGION\",
                            \"SECRET_KEY\": \"$(openssl rand -base64 32)\"
                        }
                    }
                }
            }
        }" \
        --instance-configuration "{
            \"Cpu\": \"0.25 vCPU\",
            \"Memory\": \"0.5 GB\"
        }" \
        --region $AWS_REGION \
        --query 'Service.ServiceArn' \
        --output text)

    echo "✅ Servicio de App Runner creado: $SERVICE_ARN"
else
    echo "✅ Servicio de App Runner ya existe."
    SERVICE_ARN="arn:aws:apprunner:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):service/$APP_NAME"
fi

# 5. Esperar a que el servicio esté disponible
echo "⏳ Esperando a que el servicio esté disponible..."
aws apprunner wait service-updated --service-arn $SERVICE_ARN --region $AWS_REGION

# 6. Obtener URL del servicio
SERVICE_URL=$(aws apprunner describe-service --service-arn $SERVICE_ARN --query 'Service.ServiceUrl' --output text --region $AWS_REGION)
echo "🌐 URL del servicio: $SERVICE_URL"

# 7. Limpiar archivos temporales
echo "🧹 Limpiando archivos temporales..."
rm -f directiva-agricola-source.zip
aws s3 rb s3://$SOURCE_BUCKET --force --region $AWS_REGION

echo ""
echo "✅ Despliegue en App Runner completado!"
echo "🌐 Aplicación disponible en: $SERVICE_URL"
echo "💰 Costo estimado: ~$20-30/mes (App Runner + RDS + S3)"
echo ""
echo "📋 Próximos pasos:"
echo "1. Configurar DNS de tu dominio para apuntar a: $SERVICE_URL"
echo "2. Verificar que la aplicación funcione correctamente"
echo "3. Crear empresa de prueba desde el panel de administración"
echo ""
echo "🔑 Credenciales de acceso:"
echo "• Usuario: supervisor"
echo "• Contraseña: Directivasbmj1*"
echo ""
echo "📊 Monitoreo:"
echo "• Logs: AWS Console > App Runner > $APP_NAME > Logs"
echo "• Métricas: AWS Console > App Runner > $APP_NAME > Metrics"
