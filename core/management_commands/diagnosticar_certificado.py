"""
Comando para diagnosticar problemas con certificados
"""

import base64
import binascii
from django.core.management.base import BaseCommand, CommandError
from core.models import Emisor


class Command(BaseCommand):
    help = 'Diagnostica problemas con certificados de emisores'

    def add_arguments(self, parser):
        parser.add_argument('--emisor', type=str, help='Código del emisor')
        parser.add_argument('--todos', action='store_true', help='Diagnosticar todos los emisores')

    def handle(self, *args, **options):
        if options['todos']:
            emisores = Emisor.objects.all()
        elif options['emisor']:
            try:
                emisores = [Emisor.objects.get(codigo=options['emisor'])]
            except Emisor.DoesNotExist:
                raise CommandError(f'Emisor con código {options["emisor"]} no encontrado')
        else:
            raise CommandError('Debe especificar --emisor o --todos')

        for emisor in emisores:
            self.stdout.write(f'\n=== Diagnóstico para {emisor.razon_social} (Código: {emisor.codigo}) ===')
            
            # Verificar certificado
            if emisor.archivo_certificado:
                self.diagnosticar_certificado(emisor.archivo_certificado, 'Certificado')
            else:
                self.stdout.write(self.style.WARNING('  No hay certificado cargado'))
            
            # Verificar llave
            if emisor.archivo_llave:
                self.diagnosticar_llave(emisor.archivo_llave, 'Llave')
            else:
                self.stdout.write(self.style.WARNING('  No hay llave cargada'))

    def diagnosticar_certificado(self, certificado_b64, tipo):
        """Diagnostica un certificado en base64"""
        try:
            # Verificar que sea base64 válido
            try:
                certificado_data = base64.b64decode(certificado_b64)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  {tipo}: Error decodificando base64: {e}'))
                return
            
            # Información básica
            self.stdout.write(f'  {tipo}: Tamaño decodificado: {len(certificado_data)} bytes')
            
            # Verificar si es DER válido
            try:
                from cryptography import x509
                cert = x509.load_der_x509_certificate(certificado_data)
                self.stdout.write(self.style.SUCCESS(f'  {tipo}: Formato DER válido'))
                self.stdout.write(f'  {tipo}: Número de serie: {cert.serial_number}')
                self.stdout.write(f'  {tipo}: Válido desde: {cert.not_valid_before}')
                self.stdout.write(f'  {tipo}: Válido hasta: {cert.not_valid_after}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  {tipo}: No es un certificado DER válido: {e}'))
                
                # Intentar como PEM
                try:
                    pem_data = base64.b64encode(certificado_data).decode('utf-8')
                    pem_cert = f"-----BEGIN CERTIFICATE-----\n{pem_data}\n-----END CERTIFICATE-----"
                    cert = x509.load_pem_x509_certificate(pem_cert.encode('utf-8'))
                    self.stdout.write(self.style.SUCCESS(f'  {tipo}: Formato PEM válido (convertido)'))
                except Exception as pem_error:
                    self.stdout.write(self.style.ERROR(f'  {tipo}: Tampoco es PEM válido: {pem_error}'))
            
            # Mostrar primeros bytes en hex para debugging
            hex_preview = binascii.hexlify(certificado_data[:20]).decode('utf-8')
            self.stdout.write(f'  {tipo}: Primeros 20 bytes (hex): {hex_preview}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  {tipo}: Error general: {e}'))

    def diagnosticar_llave(self, llave_b64, tipo):
        """Diagnostica una llave en base64"""
        try:
            # Verificar que sea base64 válido
            try:
                llave_data = base64.b64decode(llave_b64)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  {tipo}: Error decodificando base64: {e}'))
                return
            
            # Información básica
            self.stdout.write(f'  {tipo}: Tamaño decodificado: {len(llave_data)} bytes')
            
            # Verificar si es PEM
            if llave_data.startswith(b'-----BEGIN'):
                self.stdout.write(self.style.SUCCESS(f'  {tipo}: Formato PEM detectado'))
            else:
                self.stdout.write(f'  {tipo}: Formato binario (probablemente DER)')
            
            # Mostrar primeros bytes en hex para debugging
            hex_preview = binascii.hexlify(llave_data[:20]).decode('utf-8')
            self.stdout.write(f'  {tipo}: Primeros 20 bytes (hex): {hex_preview}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  {tipo}: Error general: {e}'))
