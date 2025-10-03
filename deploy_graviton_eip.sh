#!/bin/bash

set -euo pipefail

# Orquestador: elimina instancia anterior (manteniendo EIP 54.212.80.37),
# crea t4g.micro AL2023 ARM64, asocia EIP, provisiona con pyenv 3.13.7,
# configura RDS y despliega la app.

REGION="us-west-2"
EIP_PUBLIC_IP="54.212.80.37"
INSTANCE_TYPE="t4g.micro"
KEY_NAME="directiva-agricola-key"
KEY_PATH="/Users/josemanuelbarba/Documents/Directiva Proyectos/DirectivaAgricola/directiva-agricola-key.pem"
SECURITY_GROUP_NAME="directiva-agricola-sg"
VPC_ID=""
SUBNET_ID=""
SSM_PARAM_AMI="/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-arm64"  # no se usará si no hay permisos SSM

APP_DIR="/var/www/directiva_agricola"
LOCAL_PROVISION="/Users/josemanuelbarba/Documents/Directiva Proyectos/DirectivaAgricola/scripts/provision_al2023_clean.sh"

# Dominios (ajusta si es necesario)
DOMAIN_ROOT="agricola.directiva.mx"
DOMAIN_WWW="www.agricola.directiva.mx"

# RDS envs
export DS_DB_NAME="directiva_agricola"
export RDS_ADMIN_DB_NAME="directiva_administracion"
export RDS_USERNAME="postgres"
export RDS_PASSWORD="Directiva2024!"
export RDS_HOSTNAME="directiva-agricola-db.ch0uaaay0qlf.us-west-2.rds.amazonaws.com"
export RDS_PORT="5432"

command -v aws >/dev/null || { echo "Necesitas AWS CLI"; exit 1; }
command -v jq >/dev/null || { echo "Necesitas jq (brew install jq)"; exit 1; }

echo "==> Región: $REGION"
aws configure get region >/dev/null || { echo "Configura AWS CLI (aws configure)"; exit 1; }

echo "==> Obteniendo AllocationId de la EIP $EIP_PUBLIC_IP"
ALLOCATION_ID=$(aws ec2 describe-addresses --region "$REGION" --public-ips "$EIP_PUBLIC_IP" --query 'Addresses[0].AllocationId' --output text || true)
ASSOCIATION_ID="None"
OLD_INSTANCE_ID="None"
if [ "$ALLOCATION_ID" = "None" ] || [ -z "$ALLOCATION_ID" ]; then
  echo "⚠️  La IP $EIP_PUBLIC_IP no es una EIP en esta cuenta. Asignando una nueva EIP..."
  NEW_EIP_JSON=$(aws ec2 allocate-address --region "$REGION" --domain vpc)
  ALLOCATION_ID=$(echo "$NEW_EIP_JSON" | jq -r '.AllocationId')
  EIP_PUBLIC_IP=$(echo "$NEW_EIP_JSON" | jq -r '.PublicIp')
  echo "✅ Nueva EIP asignada: $EIP_PUBLIC_IP (AllocationId=$ALLOCATION_ID)"
else
  ASSOCIATION_ID=$(aws ec2 describe-addresses --region "$REGION" --public-ips "$EIP_PUBLIC_IP" --query 'Addresses[0].AssociationId' --output text)
  OLD_INSTANCE_ID=$(aws ec2 describe-addresses --region "$REGION" --public-ips "$EIP_PUBLIC_IP" --query 'Addresses[0].InstanceId' --output text)
  echo "AllocationId=$ALLOCATION_ID AssociationId=$ASSOCIATION_ID OldInstance=$OLD_INSTANCE_ID"
  if [ "$ASSOCIATION_ID" != "None" ]; then
    echo "==> Desasociando EIP de la instancia antigua..."
    aws ec2 disassociate-address --region "$REGION" --association-id "$ASSOCIATION_ID"
  fi
  if [ "$OLD_INSTANCE_ID" != "None" ]; then
    echo "==> Terminando instancia antigua $OLD_INSTANCE_ID ..."
    aws ec2 terminate-instances --region "$REGION" --instance-ids "$OLD_INSTANCE_ID" >/dev/null
    echo "==> Esperando a que termine..."
    aws ec2 wait instance-terminated --region "$REGION" --instance-ids "$OLD_INSTANCE_ID"
  fi
fi

echo "==> Obteniendo AMI AL2023 ARM64..."
AMI_ID=""
set +e
AMI_ID=$(aws ssm get-parameters --region "$REGION" --names "$SSM_PARAM_AMI" --query 'Parameters[0].Value' --output text 2>/dev/null)
set -e
if [ -z "$AMI_ID" ] || [ "$AMI_ID" = "None" ]; then
  echo "Sin permisos SSM o parámetro no disponible. Usando DescribeImages..."
  AMI_ID=$(aws ec2 describe-images --region "$REGION" \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-*-kernel-6.1-arm64" "Name=state,Values=available" \
    --query 'Images | sort_by(@,&CreationDate)[-1].ImageId' --output text)
fi
echo "AMI_ID=$AMI_ID"

if [ -z "$VPC_ID" ]; then
  VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
fi
if [ -z "$SUBNET_ID" ]; then
  SUBNET_ID=$(aws ec2 describe-subnets --region "$REGION" --filters Name=vpc-id,Values="$VPC_ID" Name=default-for-az,Values=true --query 'Subnets[0].SubnetId' --output text)
fi
echo "VPC_ID=$VPC_ID SUBNET_ID=$SUBNET_ID"

echo "==> Creando/obteniendo Security Group $SECURITY_GROUP_NAME ..."
SG_ID=$(aws ec2 describe-security-groups --region "$REGION" --filters Name=group-name,Values="$SECURITY_GROUP_NAME" Name=vpc-id,Values="$VPC_ID" --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG_ID" = "None" ]; then
  SG_ID=$(aws ec2 create-security-group --region "$REGION" --group-name "$SECURITY_GROUP_NAME" --description "Directiva Agricola SG" --vpc-id "$VPC_ID" --query 'GroupId' --output text)
  aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$SG_ID" --ip-permissions \
    IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges="[{CidrIp=0.0.0.0/0,Description='SSH'}]" \
    IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges="[{CidrIp=0.0.0.0/0,Description='HTTP'}]" \
    IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges="[{CidrIp=0.0.0.0/0,Description='HTTPS'}]"
fi
echo "SG_ID=$SG_ID"

# Asegurar 443 abierto si el SG ya existía
aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$SG_ID" --ip-permissions \
  IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges="[{CidrIp=0.0.0.0/0,Description='HTTPS'}]" || true

if [ ! -f "$KEY_PATH" ]; then
  echo "==> No se encontró PEM en $KEY_PATH"; exit 1;
fi

echo "==> Creando nueva instancia $INSTANCE_TYPE ..."
INSTANCE_JSON=$(aws ec2 run-instances --region "$REGION" \
  --image-id "$AMI_ID" --instance-type "$INSTANCE_TYPE" \
  --key-name "$KEY_NAME" --security-group-ids "$SG_ID" --subnet-id "$SUBNET_ID" \
  --count 1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=directiva-agricola-ec2}]')
NEW_INSTANCE_ID=$(echo "$INSTANCE_JSON" | jq -r '.Instances[0].InstanceId')
echo "NEW_INSTANCE_ID=$NEW_INSTANCE_ID"
echo "==> Esperando a que esté en running..."
aws ec2 wait instance-running --region "$REGION" --instance-ids "$NEW_INSTANCE_ID"

echo "==> Asociando EIP $EIP_PUBLIC_IP ($ALLOCATION_ID) a la nueva instancia..."
aws ec2 associate-address --region "$REGION" --allocation-id "$ALLOCATION_ID" --instance-id "$NEW_INSTANCE_ID" >/dev/null || true

echo "==> Esperando 30s a que SSH esté listo..."
sleep 30

[ -f "$LOCAL_PROVISION" ] || { echo "No existe $LOCAL_PROVISION"; exit 1; }

echo "==> Copiando script de provisionamiento..."
scp -o StrictHostKeyChecking=no -i "$KEY_PATH" "$LOCAL_PROVISION" ec2-user@"$EIP_PUBLIC_IP":/home/ec2-user/
echo "==> Ejecutando provisionamiento..."
ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@"$EIP_PUBLIC_IP" "chmod +x provision_al2023_clean.sh && sudo ./provision_al2023_clean.sh"

echo "==> Configurando aplicación y servicio..."
ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@"$EIP_PUBLIC_IP" 'bash -lc "
set -e
cd '"$APP_DIR"'
sudo tee /etc/systemd/system/directiva-agricola.service > /dev/null <<EOL
[Unit]
Description=Directiva Agricola Gunicorn daemon
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory='"$APP_DIR"'
Environment=PATH='"$APP_DIR"'/venv/bin
Environment=DS_DB_NAME='"$DS_DB_NAME"'
Environment=RDS_ADMIN_DB_NAME='"$RDS_ADMIN_DB_NAME"'
Environment=RDS_USERNAME='"$RDS_USERNAME"'
Environment=RDS_PASSWORD='"$RDS_PASSWORD"'
Environment=RDS_HOSTNAME='"$RDS_HOSTNAME"'
Environment=RDS_PORT='"$RDS_PORT"'
Environment=SECRET_KEY=directiva-secret-key-2024-production
ExecStart='"$APP_DIR"'/venv/bin/gunicorn --config gunicorn.conf.py directiva_agricola.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL

if [ ! -f gunicorn.conf.py ]; then
  cat > gunicorn.conf.py <<GCONF
bind = \"127.0.0.1:8000\"
workers = 3
worker_class = \"sync\"
timeout = 30
keepalive = 2
preload_app = True
GCONF
fi

cat > directiva_agricola/settings_production.py <<'PY'
import os
from .settings import *
DEBUG = False
ALLOWED_HOSTS = ['"$EIP_PUBLIC_IP"']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DS_DB_NAME', 'directiva_agricola'),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', ''),
        'HOST': os.environ.get('RDS_HOSTNAME', ''),
        'PORT': os.environ.get('RDS_PORT', '5432'),
        'ATOMIC_REQUESTS': True,
        'TIME_ZONE': 'America/Mexico_City',
    },
    'administracion': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('RDS_ADMIN_DB_NAME', 'directiva_administracion'),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', ''),
        'HOST': os.environ.get('RDS_HOSTNAME', ''),
        'PORT': os.environ.get('RDS_PORT', '5432'),
        'ATOMIC_REQUESTS': True,
        'TIME_ZONE': 'America/Mexico_City',
    }
}
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
SECRET_KEY = os.environ.get('SECRET_KEY', 'directiva-secret-key-2024-production')
PY

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate --settings=directiva_agricola.settings_production --database=administracion
python manage.py migrate --settings=directiva_agricola.settings_production --database=default
python manage.py collectstatic --noinput --settings=directiva_agricola.settings_production

python manage.py shell --settings=directiva_agricola.settings_production <<'PY'
from django.contrib.auth import get_user_model
from administracion.models import UsuarioAdministracion
User = get_user_model()
admin_user, created = UsuarioAdministracion.objects.using('administracion').get_or_create(
    username='admin',
    defaults={'first_name': 'Administrador','last_name': 'Sistema','email': 'admin@directiva.com','is_staff': True,'is_active': True}
)
if created:
    admin_user.set_password('Directiva2024!')
    admin_user.save()
supervisor_user, created = User.objects.using('default').get_or_create(
    username='supervisor',
    defaults={'first_name': 'Supervisor','last_name': 'Sistema','email': 'supervisor@directiva.com','is_superuser': True,'is_staff': True,'is_active': True}
)
if created:
    supervisor_user.set_password('Directivasbmj1*')
    supervisor_user.save()
PY

sudo systemctl daemon-reload
sudo systemctl enable --now directiva-agricola
sudo systemctl restart nginx

# ================= HTTPS via Let's Encrypt (Certbot) =================
echo "Instalando Certbot via snapd..."
sudo dnf install -y snapd
sudo systemctl enable --now snapd.socket
sudo ln -s /var/lib/snapd/snap /snap || true
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot

# Webroot para ACME challenge
sudo mkdir -p /var/www/letsencrypt
sudo chown ec2-user:ec2-user /var/www/letsencrypt

# Config Nginx temporal para emitir certificados (challenge + sitio en http)
sudo tee /etc/nginx/conf.d/directiva-agricola.conf > /dev/null <<NGHTTP
server {
    listen 80;
    server_name '"$DOMAIN_ROOT"' '"$DOMAIN_WWW"' '"$EIP_PUBLIC_IP"';
    client_max_body_size 100M;

    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }

    location /static/ {
        alias '"$APP_DIR"'/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    location /media/ {
        alias '"$APP_DIR"'/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGHTTP

sudo nginx -t && sudo systemctl reload nginx

# Emitir certificados (solo subdominio principal)
sudo certbot certonly --webroot -w /var/www/letsencrypt -d '"$DOMAIN_ROOT"' -d '"$DOMAIN_WWW"' --agree-tos -m admin@'"$DOMAIN_ROOT"' --non-interactive --no-eff-email || true

# Configuración HTTPS + redirección HTTP -> HTTPS
sudo tee /etc/nginx/conf.d/directiva-agricola-ssl.conf > /dev/null <<NGSSL
server {
    listen 80;
    server_name '"$DOMAIN_ROOT"' '"$DOMAIN_WWW"' '"$EIP_PUBLIC_IP"';
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name '"$DOMAIN_ROOT"' '"$DOMAIN_WWW"';

    ssl_certificate /etc/letsencrypt/live/'"$DOMAIN_ROOT"'/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/'"$DOMAIN_ROOT"'/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    location /static/ {
        alias '"$APP_DIR"'/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    location /media/ {
        alias '"$APP_DIR"'/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGSSL

sudo nginx -t && sudo systemctl reload nginx

# Ampliar ALLOWED_HOSTS para dominios
export EIP='"$EIP_PUBLIC_IP"'
export DOMAIN_ROOT='"$DOMAIN_ROOT"'
export DOMAIN_WWW='"$DOMAIN_WWW"'
python - <<'PY'
import os
from pathlib import Path
import re
f = Path('directiva_agricola/settings_production.py')
text = f.read_text()
eip = os.environ.get('EIP', '').strip()
root = os.environ.get('DOMAIN_ROOT', '').strip()
www = os.environ.get('DOMAIN_WWW', '').strip()
hosts = [h for h in [eip, root, www] if h]
if hosts:
    repl = "ALLOWED_HOSTS = [" + ", ".join(["'"+h+"'" for h in hosts]) + "]"
    text = re.sub(r"ALLOWED_HOSTS\s*=\s*\[[^\]]*\]", repl, text)
f.write_text(text)
PY

"'

echo "==> Verificaciones:"
"'

echo "==> Verificaciones:"
aws ec2 describe-instance-status --region "$REGION" --instance-ids "$NEW_INSTANCE_ID" --query 'InstanceStatuses[0].InstanceState.Name' --output text || true
curl -I --max-time 5 "http://$EIP_PUBLIC_IP" || true
echo "Si los certificados fallaron, asegúrate de que DNS A de $DOMAIN_ROOT y $DOMAIN_WWW apunten a $EIP_PUBLIC_IP y reintenta: sudo certbot renew --dry-run; luego recarga Nginx."

echo "==> Despliegue finalizado. Accede: http://$EIP_PUBLIC_IP"


