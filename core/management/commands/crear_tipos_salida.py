from django.core.management.base import BaseCommand
from core.models import TipoSalida


class Command(BaseCommand):
    help = 'Crear tipos de salida por defecto'

    def handle(self, *args, **options):
        tipos_salida = [
            'Consumo interno',
            'Venta',
            'Transferencia',
            'Merma',
            'Donación',
            'Devolución',
            'Mantenimiento',
            'Producción',
            'Investigación',
            'Capacitación'
        ]

        creados = 0
        for tipo in tipos_salida:
            tipo_obj, created = TipoSalida.objects.get_or_create(
                descripcion=tipo,
                defaults={'activo': True}
            )
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Creado tipo de salida: {tipo}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Se crearon {creados} tipos de salida nuevos.')
        )
