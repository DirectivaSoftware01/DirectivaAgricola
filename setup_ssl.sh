#!/bin/bash

# Script para configurar SSL con Let's Encrypt
# Uso: ./setup_ssl.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

DOMAIN="agricola.directiva.mx"
EMAIL="admin@directiva.mx"

print_status "Configurando SSL para el dominio: $DOMAIN"

# Verificar que el dominio apunte a esta IP
print_status "Verificando que el dominio $DOMAIN apunte a esta IP..."
CURRENT_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)

if [ "$CURRENT_IP" != "$DOMAIN_IP" ]; then
    print_warning "El dominio $DOMAIN no apunta a esta IP ($CURRENT_IP)"
    print_warning "IP del dominio: $DOMAIN_IP"
    print_warning "Por favor, configura el DNS antes de continuar"
    read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Instalar Certbot si no está instalado
if ! command -v certbot &> /dev/null; then
    print_status "Instalando Certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
fi

# Crear directorio para certificados
mkdir -p ssl

# Obtener certificado SSL
print_status "Obteniendo certificado SSL de Let's Encrypt..."
sudo certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --domains $DOMAIN,www.$DOMAIN

# Copiar certificados al directorio del proyecto
print_status "Copiando certificados..."
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/
sudo chown $USER:$USER ssl/*.pem

# Crear script de renovación automática
print_status "Configurando renovación automática..."
cat > renew_ssl.sh << 'EOF'
#!/bin/bash
# Script para renovar certificados SSL
sudo certbot renew --quiet
sudo cp /etc/letsencrypt/live/agricola.directiva.mx/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/agricola.directiva.mx/privkey.pem ssl/
sudo chown $USER:$USER ssl/*.pem
docker-compose -f docker-compose.prod.yml restart nginx
EOF

chmod +x renew_ssl.sh

# Agregar cron job para renovación automática
print_status "Configurando renovación automática con cron..."
(crontab -l 2>/dev/null; echo "0 12 * * * $(pwd)/renew_ssl.sh") | crontab -

# Reiniciar Nginx con SSL
print_status "Reiniciando Nginx con SSL..."
docker-compose -f docker-compose.prod.yml restart nginx

print_success "✅ SSL configurado correctamente"
echo ""
echo "🔒 Certificado SSL instalado para: $DOMAIN"
echo "🔄 Renovación automática configurada"
echo "🌐 Tu sitio ahora está disponible en: https://$DOMAIN"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Verificar que https://$DOMAIN funciona correctamente"
echo "   2. Configurar backup de la base de datos"
echo "   3. Configurar monitoreo del servidor"
echo ""
