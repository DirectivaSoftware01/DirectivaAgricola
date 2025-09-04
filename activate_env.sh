#!/bin/bash

# Script para activar el entorno virtual del proyecto Directiva Agricola

echo "Activando entorno virtual para Directiva Agricola..."
source venv/bin/activate

echo "Entorno virtual activado!"
echo "Para desactivar, ejecuta: deactivate"
echo ""
echo "Comandos útiles:"
echo "  python manage.py runserver    - Ejecutar servidor de desarrollo"
echo "  python manage.py makemigrations - Crear migraciones"
echo "  python manage.py migrate      - Aplicar migraciones"
echo "  python manage.py createsuperuser - Crear superusuario"
echo "  python manage.py shell        - Abrir shell de Django"
echo ""
echo "Para instalar nuevas dependencias:"
echo "  pip install nombre_paquete"
echo "  pip freeze > requirements.txt"
