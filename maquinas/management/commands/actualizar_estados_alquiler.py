from django.core.management.base import BaseCommand
from django.utils import timezone
from maquinas.models import Alquiler
from datetime import date

class Command(BaseCommand):
    help = 'Actualiza automáticamente los estados de los alquileres según las fechas'

    def handle(self, *args, **options):
        today = date.today()
        actualizados = 0
        
        # Alquileres reservados que deben pasar a "en_curso"
        alquileres_a_iniciar = Alquiler.objects.filter(
            estado='reservado',
            fecha_inicio=today
        )
        
        for alquiler in alquileres_a_iniciar:
            alquiler.estado = 'en_curso'
            alquiler.save()
            actualizados += 1
            self.stdout.write(f'Alquiler {alquiler.numero} iniciado')
        
        # Alquileres en curso que deben finalizar
        alquileres_a_finalizar = Alquiler.objects.filter(
            estado='en_curso',
            fecha_fin__lt=today
        )
        
        for alquiler in alquileres_a_finalizar:
            alquiler.estado = 'finalizado'
            alquiler.save()
            actualizados += 1
            self.stdout.write(f'Alquiler {alquiler.numero} finalizado')
        
        self.stdout.write(
            self.style.SUCCESS(f'Se actualizaron {actualizados} alquileres')
        ) 