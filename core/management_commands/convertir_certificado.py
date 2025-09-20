"""
Comando para convertir certificados a base64 correctamente
"""

import base64
import os
from django.core.management.base import BaseCommand, CommandError
from core.models import Emisor


class Command(BaseCommand):
    help = 'Convierte archivos de certificado a base64 y los carga en un emisor'

    def add_arguments(self, parser):
        parser.add_argument('--emisor', type=str, required=True, help='Código del emisor')
        parser.add_argument('--certificado', type=str, help='Ruta del archivo .cer')
        parser.add_argument('--llave', type=str, help='Ruta del archivo .key')
        parser.add_argument('--password', type=str, help='Contraseña de la llave privada')

    def handle(self, *args, **options):
        emisor_codigo = options['emisor']
        cert_path = options.get('certificado')
        key_path = options.get('llave')
        password = options.get('password')

        try:
            emisor = Emisor.objects.get(codigo=emisor_codigo)
        except Emisor.DoesNotExist:
            raise CommandError(f'Emisor con código {emisor_codigo} no encontrado')

        # Procesar certificado
        if cert_path:
            if not os.path.exists(cert_path):
                raise CommandError(f'Archivo de certificado {cert_path} no encontrado')
            
            self.stdout.write(f'Procesando certificado: {cert_path}')
            cert_b64 = self.convertir_archivo_a_base64(cert_path)
            emisor.archivo_certificado = cert_b64
            self.stdout.write(self.style.SUCCESS(f'Certificado cargado: {len(cert_b64)} caracteres'))

        # Procesar llave
        if key_path:
            if not os.path.exists(key_path):
                raise CommandError(f'Archivo de llave {key_path} no encontrado')
            
            self.stdout.write(f'Procesando llave: {key_path}')
            key_b64 = self.convertir_archivo_a_base64(key_path)
            emisor.archivo_llave = key_b64
            self.stdout.write(self.style.SUCCESS(f'Llave cargada: {len(key_b64)} caracteres'))

        # Actualizar contraseña si se proporciona
        if password:
            emisor.password_llave = password
            self.stdout.write(self.style.SUCCESS('Contraseña actualizada'))

        # Guardar cambios
        emisor.save()
        self.stdout.write(
            self.style.SUCCESS(f'Emisor {emisor.razon_social} actualizado exitosamente')
        )

    def convertir_archivo_a_base64(self, archivo_path):
        """Convierte un archivo a base64"""
        try:
            with open(archivo_path, 'rb') as f:
                contenido = f.read()
            
            # Validar que el archivo no esté vacío
            if len(contenido) == 0:
                raise CommandError(f'El archivo {archivo_path} está vacío')
            
            # Convertir a base64
            base64_content = base64.b64encode(contenido).decode('utf-8')
            
            # Validar que la conversión fue exitosa
            try:
                base64.b64decode(base64_content)
            except Exception as e:
                raise CommandError(f'Error validando base64: {e}')
            
            return base64_content
            
        except Exception as e:
            raise CommandError(f'Error procesando archivo {archivo_path}: {e}')
