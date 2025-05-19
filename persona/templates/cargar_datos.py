from django.core.management.base import BaseCommand
from persona.models import Persona, Empleado, Maquina


class Command(BaseCommand):
    help = 'Carga datos iniciales en la base de datos'

    def handle(self, *args, **kwargs):
        # Crear datos para la tabla Persona
        Persona.objects.create(nombre="Juan", apollo="Pérez", dni=12345678, edad=30)
        Persona.objects.create(nombre="Ana", apollo="López", dni=87654321, edad=25)

        # Crear datos para la tabla Empleado
        Empleado.objects.create(nombre="Carlos", apollo="Martínez", dni=72314567, edad=40)
        Empleado.objects.create(nombre="Laura", apollo="Fernández", dni=36985214, edad=28)

        # Crear datos para la tabla Maquina
        Maquina.objects.create(nombre="Excavadora", tipo="Industrial", modelo=2022)
        Maquina.objects.create(nombre="Tractor", tipo="Agrícola", modelo=2020)

        self.stdout.write(self.style.SUCCESS('¡Datos cargados exitosamente!'))
