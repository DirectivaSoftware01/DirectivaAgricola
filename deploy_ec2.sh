#!/bin/bash

# Script de despliegue para EC2 con Docker Compose
# Uso: ./deploy_ec2.sh

set -e

echo "🚀 Iniciando despliegue en EC2..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con color
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

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado. Instalando Docker..."
    
    # Instalar Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    
    print_success "Docker instalado correctamente"
fi

# Verificar que Docker Compose esté instalado
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose no está instalado. Instalando Docker Compose..."
    
    # Instalar Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    print_success "Docker Compose instalado correctamente"
fi

# Crear directorios necesarios
print_status "Creando directorios necesarios..."
mkdir -p media staticfiles logs ssl

# Generar SECRET_KEY si no existe
if [ ! -f .env ]; then
    print_status "Generando archivo de variables de entorno..."
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    
    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
DB_PASSWORD=Directiva2024!
DEBUG=False
ALLOWED_HOSTS=agricola.directiva.mx,localhost,127.0.0.1
EOF
    
    print_success "Archivo .env creado con SECRET_KEY generado"
fi

# Detener contenedores existentes
print_status "Deteniendo contenedores existentes..."
docker-compose -f docker-compose.prod.yml down || true

# Construir y levantar los servicios
print_status "Construyendo y levantando servicios..."
docker-compose -f docker-compose.prod.yml up --build -d

# Esperar a que la base de datos esté lista
print_status "Esperando a que la base de datos esté lista..."
sleep 30

# Ejecutar migraciones
print_status "Ejecutando migraciones..."
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --settings=directiva_agricola.settings_ec2

# Crear superusuario si no existe
print_status "Creando superusuario..."
docker-compose -f docker-compose.prod.yml exec web python manage.py shell --settings=directiva_agricola.settings_ec2 << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@directiva.mx', 'admin123')
    print('Superusuario creado: admin/admin123')
else:
    print('Superusuario ya existe')
EOF

# Recopilar archivos estáticos
print_status "Recopilando archivos estáticos..."
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput --settings=directiva_agricola.settings_ec2

# Verificar que los servicios estén funcionando
print_status "Verificando servicios..."
sleep 10

if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    print_success "✅ Todos los servicios están funcionando correctamente"
    
    echo ""
    echo "🎉 ¡DESPLIEGUE COMPLETADO EXITOSAMENTE!"
    echo ""
    echo "📊 Servicios desplegados:"
    echo "   • Django Web App: http://localhost:8000"
    echo "   • Nginx: http://localhost:80"
    echo "   • PostgreSQL: localhost:5432"
    echo "   • Redis: localhost:6379"
    echo ""
    echo "👤 Credenciales de administrador:"
    echo "   • Usuario: admin"
    echo "   • Contraseña: admin123"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "   • Ver logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "   • Detener: docker-compose -f docker-compose.prod.yml down"
    echo "   • Reiniciar: docker-compose -f docker-compose.prod.yml restart"
    echo ""
    echo "🌐 Para configurar el dominio agricola.directiva.mx:"
    echo "   1. Configurar DNS para apuntar a esta IP"
    echo "   2. Ejecutar: ./setup_ssl.sh"
    echo ""
else
    print_error "❌ Algunos servicios no están funcionando correctamente"
    print_status "Revisando logs..."
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi
