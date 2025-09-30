#!/bin/bash

# Script para crear recursos AWS necesarios para Directiva Agrícola
# Uso: ./setup_aws_resources.sh

set -e

REGION="us-west-2"
APP_NAME="directiva-agricola"
DB_INSTANCE_ID="directiva-agricola-db"
S3_BUCKET="directiva-agricola-static"

echo "🚀 Configurando recursos AWS para Directiva Agrícola"
echo "🌍 Región: $REGION"

# Verificar que AWS CLI esté configurado
if ! python -m awscli sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS CLI no está configurado o las credenciales son inválidas"
    echo "🔧 Configura AWS CLI con: python -m awscli configure"
    exit 1
fi

echo "✅ AWS CLI configurado correctamente"

# 1. Crear bucket S3 para archivos estáticos
echo "📦 Creando bucket S3 para archivos estáticos..."
if python -m awscli s3api head-bucket --bucket $S3_BUCKET --region $REGION 2>/dev/null; then
    echo "✅ Bucket S3 ya existe: $S3_BUCKET"
else
    python -m awscli s3 mb s3://$S3_BUCKET --region $REGION
    echo "✅ Bucket S3 creado: $S3_BUCKET"
fi

# 2. Configurar bucket S3 para hosting estático
echo "⚙️  Configurando bucket S3 para hosting estático..."
python -m awscli s3api put-bucket-cors --bucket $S3_BUCKET --cors-configuration '{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "HEAD"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": []
        }
    ]
}' --region $REGION

# 3. Crear instancia RDS PostgreSQL
echo "🗄️  Creando instancia RDS PostgreSQL..."
if python -m awscli rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --region $REGION &> /dev/null; then
    echo "✅ Instancia RDS ya existe: $DB_INSTANCE_ID"
else
    python -m awscli rds create-db-instance \
        --db-instance-identifier $DB_INSTANCE_ID \
        --db-instance-class db.t3.micro \
        --engine postgres \
        --master-username postgres \
        --master-user-password "Directiva2024!" \
        --allocated-storage 20 \
        --vpc-security-group-ids default \
        --backup-retention-period 7 \
        --multi-az \
        --publicly-accessible \
        --storage-encrypted \
        --region $REGION
    
    echo "⏳ Esperando a que la instancia RDS esté disponible (esto puede tomar varios minutos)..."
    python -m awscli rds wait db-instance-available --db-instance-identifier $DB_INSTANCE_ID --region $REGION
    echo "✅ Instancia RDS creada: $DB_INSTANCE_ID"
fi

# 4. Obtener endpoint de RDS
echo "🔍 Obteniendo información de la base de datos..."
DB_ENDPOINT=$(python -m awscli rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --region $REGION --query 'DBInstances[0].Endpoint.Address' --output text)
echo "📍 Endpoint de RDS: $DB_ENDPOINT"

# 5. Crear archivo de configuración con las variables reales
echo "📝 Creando archivo de configuración con variables reales..."
cat > .ebextensions/04_environment_real.config << EOF
option_settings:
  aws:elasticbeanstalk:application:environment:
    # Base de datos
    RDS_DB_NAME: directiva_agricola
    RDS_ADMIN_DB_NAME: directiva_administracion
    RDS_USERNAME: postgres
    RDS_PASSWORD: "Directiva2024!"
    RDS_HOSTNAME: "$DB_ENDPOINT"
    RDS_PORT: "5432"
    
    # AWS S3
    AWS_ACCESS_KEY_ID: "$(python -m awscli configure get aws_access_key_id)"
    AWS_SECRET_ACCESS_KEY: "$(python -m awscli configure get aws_secret_access_key)"
    AWS_STORAGE_BUCKET_NAME: "$S3_BUCKET"
    
    # Email (configurar con tus valores reales)
    EMAIL_HOST: "smtp.gmail.com"
    EMAIL_PORT: "587"
    EMAIL_HOST_USER: "noreply@directiva.mx"
    EMAIL_HOST_PASSWORD: "your-email-password"
    DEFAULT_FROM_EMAIL: "noreply@directiva.mx"
    
    # Django
    SECRET_KEY: "$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
    DEBUG: "False"
EOF

echo "✅ Archivo de configuración creado: .ebextensions/04_environment_real.config"

echo ""
echo "🎉 ¡Recursos AWS creados exitosamente!"
echo "📋 Resumen:"
echo "   • Bucket S3: $S3_BUCKET"
echo "   • Base de datos RDS: $DB_INSTANCE_ID"
echo "   • Endpoint RDS: $DB_ENDPOINT"
echo "   • Región: $REGION"
echo ""
echo "🚀 Ahora puedes desplegar la aplicación con:"
echo "   ./deploy.sh"
