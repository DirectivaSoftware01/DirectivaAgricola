"""
Comando de gestión para cargar certificados en base64
"""

import base64
import os
from django.core.management.base import BaseCommand, CommandError
from core.models import Emisor


class Command(BaseCommand):
    help = 'Carga un certificado .cer o .key en base64 para un emisor'

    def add_arguments(self, parser):
        parser.add_argument('--emisor', type=str, help='Código del emisor')
        parser.add_argument('--tipo', type=str, choices=['cer', 'key'], help='Tipo de archivo (cer o key)')
        parser.add_argument('--archivo', type=str, help='Ruta del archivo a cargar')
        parser.add_argument('--base64', type=str, help='Contenido base64 del archivo')

    def handle(self, *args, **options):
        emisor_codigo = options['emisor']
        tipo = options['tipo']
        archivo_path = options.get('archivo')
        base64_content = options.get('base64')

        try:
            emisor = Emisor.objects.get(codigo=emisor_codigo)
        except Emisor.DoesNotExist:
            raise CommandError(f'Emisor con código {emisor_codigo} no encontrado')

        # Obtener contenido base64
        if archivo_path:
            if not os.path.exists(archivo_path):
                raise CommandError(f'Archivo {archivo_path} no encontrado')
            
            with open(archivo_path, 'rb') as f:
                contenido = f.read()
            base64_content = base64.b64encode(contenido).decode('utf-8')
        elif base64_content:
            # Validar que sea base64 válido
            try:
                base64.b64decode(base64_content)
            except Exception:
                raise CommandError('El contenido base64 no es válido')
        else:
            raise CommandError('Debe proporcionar --archivo o --base64')

        # Guardar en el emisor
        if tipo == 'cer':
            emisor.archivo_certificado = base64_content
            self.stdout.write(f'Certificado .cer cargado para emisor {emisor.razon_social}')
        elif tipo == 'key':
            emisor.archivo_llave = base64_content
            self.stdout.write(f'Llave .key cargada para emisor {emisor.razon_social}')

        emisor.save()
        self.stdout.write(
            self.style.SUCCESS(f'Archivo {tipo} cargado exitosamente para {emisor.razon_social}')
        )
