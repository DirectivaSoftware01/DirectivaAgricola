# Cómo Cargar Certificados en Base64

## Método 1: Usando el comando de gestión

### Cargar certificado .cer:
```bash
python3 manage.py cargar_certificado --emisor 1 --tipo cer --archivo /ruta/al/certificado.cer
```

### Cargar llave .key:
```bash
python3 manage.py cargar_certificado --emisor 1 --tipo key --archivo /ruta/a/llave.key
```

### Cargar desde base64 directamente:
```bash
python3 manage.py cargar_certificado --emisor 1 --tipo cer --base64 "MIIFjTCCA3WgAwIBAgI..."
```

## Método 2: Convertir archivos a base64 manualmente

### En Linux/Mac:
```bash
# Convertir .cer a base64
base64 -i certificado.cer -o certificado_base64.txt

# Convertir .key a base64
base64 -i llave.key -o llave_base64.txt
```

### En Python:
```python
import base64

# Leer archivo .cer
with open('certificado.cer', 'rb') as f:
    contenido_cer = f.read()
    base64_cer = base64.b64encode(contenido_cer).decode('utf-8')

# Leer archivo .key
with open('llave.key', 'rb') as f:
    contenido_key = f.read()
    base64_key = base64.b64encode(contenido_key).decode('utf-8')

print("Certificado base64:", base64_cer[:100] + "...")
print("Llave base64:", base64_key[:100] + "...")
```

## Ventajas del almacenamiento en Base64:

1. **Sin problemas de serialización JSON** ✅
2. **Fácil de transferir** entre sistemas
3. **No depende del sistema de archivos** del servidor
4. **Compatible con APIs** y servicios web
5. **Más seguro** para almacenamiento en base de datos

## Notas importantes:

- Los archivos se almacenan como texto en la base de datos
- El tamaño puede ser mayor que los archivos originales (~33% más)
- Los certificados se decodifican automáticamente cuando se necesitan
- Se mantiene toda la funcionalidad de validación y timbrado
