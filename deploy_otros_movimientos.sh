#!/bin/bash

# Script para desplegar funcionalidad de Otros Movimientos
# Servidor: agricola.directiva.mx
# Usuario: root
# Contraseña: -kNuHf@9G&94BR/d&eA6

echo "=== DESPLEGANDO FUNCIONALIDAD DE OTROS MOVIMIENTOS ==="

# Configuración del servidor
SERVER="agricola.directiva.mx"
USER="root"
PASSWORD="-kNuHf@9G&94BR/d&eA6"
REMOTE_DIR="/home/directiva/directiva_agricola"

echo "1. Conectando al servidor..."

# Crear archivo temporal con comandos
cat > /tmp/deploy_commands.sh << 'EOF'
#!/bin/bash

echo "=== INICIANDO DESPLIEGUE EN SERVIDOR ==="

# Navegar al directorio del proyecto
cd /home/directiva/directiva_agricola

# Activar entorno virtual
source venv/bin/activate

# Hacer backup de la base de datos antes de las migraciones
echo "2. Creando backup de la base de datos..."
mysqldump -u root -p'-kNuHf@9G&94BR/d&eA6' directiva_agricola > backup_$(date +%Y%m%d_%H%M%S).sql

# Aplicar migraciones
echo "3. Aplicando migraciones..."
python manage.py migrate

# Recopilar archivos estáticos
echo "4. Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Reiniciar servicios
echo "5. Reiniciando servicios..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "=== DESPLIEGUE COMPLETADO ==="
EOF

# Subir archivos necesarios
echo "2. Subiendo archivos al servidor..."

# Subir archivos de modelos
scp core/models.py $USER@$SERVER:$REMOTE_DIR/core/

# Subir archivos de vistas
scp core/otros_movimientos_views.py $USER@$SERVER:$REMOTE_DIR/core/

# Subir archivos de formularios
scp core/otros_movimientos_forms.py $USER@$SERVER:$REMOTE_DIR/core/

# Subir archivos de URLs
scp core/urls.py $USER@$SERVER:$REMOTE_DIR/core/

# Subir templates
scp templates/core/otros_movimientos_list.html $USER@$SERVER:$REMOTE_DIR/templates/core/
scp templates/core/otros_movimientos_form.html $USER@$SERVER:$REMOTE_DIR/templates/core/
scp templates/core/otros_movimientos_detail.html $USER@$SERVER:$REMOTE_DIR/templates/core/
scp templates/core/otros_movimientos_confirm_delete.html $USER@$SERVER:$REMOTE_DIR/templates/core/

# Subir template base actualizado
scp templates/base.html $USER@$SERVER:$REMOTE_DIR/templates/

# Subir archivo de comandos
scp /tmp/deploy_commands.sh $USER@$SERVER:$REMOTE_DIR/

# Ejecutar comandos en el servidor
echo "3. Ejecutando comandos en el servidor..."
ssh $USER@$SERVER "chmod +x /home/directiva/directiva_agricola/deploy_commands.sh && /home/directiva/directiva_agricola/deploy_commands.sh"

# Limpiar archivos temporales
rm /tmp/deploy_commands.sh

echo "=== DESPLIEGUE COMPLETADO ==="
echo "La funcionalidad de 'Otros movimientos' ha sido desplegada exitosamente."
echo "Backup de la base de datos creado antes de las migraciones."

