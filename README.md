# Directiva Agricola

Proyecto web desarrollado con Django para la gestión de directivas agrícolas.

## Tecnologías utilizadas

- **Python 3.13**
- **Django 5.2.5**
- **Bootstrap 5** (última versión)
- **SQL Server** como base de datos
- **pyodbc** para conexión a SQL Server

## Configuración del entorno de desarrollo

### 1. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate  # En Windows
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar base de datos
El proyecto está configurado para usar SQL Server con las siguientes credenciales:
- **Host**: directivaservices.cnvvqxmyayiq.us-west-2.rds.amazonaws.com
- **Puerto**: 1433
- **Usuario**: dssupervisor
- **Contraseña**: DSBASM790803
- **Base de datos**: directiva_agricola

### 4. Ejecutar migraciones
```bash
python manage.py migrate
```

### 5. Crear superusuario
```bash
python manage.py createsuperuser
```

### 6. Ejecutar servidor de desarrollo
```bash
python manage.py runserver
```

## Estructura del proyecto

```
DirectivaAgricola/
├── venv/                    # Entorno virtual
├── directiva_agricola/      # Configuración principal del proyecto
│   ├── __init__.py
│   ├── settings.py         # Configuraciones del proyecto
│   ├── urls.py            # URLs principales
│   ├── wsgi.py            # Configuración WSGI
│   └── asgi.py            # Configuración ASGI
├── requirements.txt         # Dependencias del proyecto
├── env_example.txt         # Ejemplo de variables de entorno
└── README.md               # Este archivo
```

## Notas importantes

- Asegúrate de tener instalado el driver ODBC para SQL Server
- El proyecto está configurado en español mexicano
- La zona horaria está configurada para México
- No se han creado templates ni views por el momento

## Próximos pasos

1. Crear aplicaciones Django para diferentes módulos
2. Diseñar modelos de base de datos
3. Crear vistas y templates
4. Implementar autenticación y autorización
5. Diseñar interfaz con Bootstrap
