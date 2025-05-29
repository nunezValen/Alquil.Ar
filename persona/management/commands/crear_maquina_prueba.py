from django.core.management.base import BaseCommand
from persona.models import Maquina

class Command(BaseCommand):
    help = 'Crea una máquina de prueba con precio 0'

    def handle(self, *args, **kwargs):
        maquina = Maquina.objects.create(
            nombre="Máquina de Prueba",
            tipo="Herramienta",
            modelo=2024,
            estado="disponible",
            precio_dia=0,
            dias_minimos=1,
            descripcion="Esta es una máquina de prueba para testing. No tiene costo de alquiler."
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Se creó la máquina de prueba con ID: {maquina.id}')
        ) 