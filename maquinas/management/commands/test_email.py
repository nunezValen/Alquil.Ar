from django.core.management.base import BaseCommand
from maquinas.models import Alquiler
from maquinas.utils import enviar_email_alquiler_simple

class Command(BaseCommand):
    help = 'Probar el envío de email con el último alquiler'

    def handle(self, *args, **options):
        try:
            # Obtener el último alquiler
            alquiler = Alquiler.objects.order_by('-id').first()
            
            if not alquiler:
                self.stdout.write(self.style.ERROR('No hay alquileres en el sistema'))
                return
            
            self.stdout.write(f'Probando email con alquiler: {alquiler.numero}')
            self.stdout.write(f'Email destino: {alquiler.persona.email}')
            self.stdout.write(f'Monto total: {alquiler.monto_total} (tipo: {type(alquiler.monto_total)})')
            
            # Intentar enviar el email
            resultado = enviar_email_alquiler_simple(alquiler)
            
            if resultado:
                self.stdout.write(self.style.SUCCESS('✅ Email enviado exitosamente'))
            else:
                self.stdout.write(self.style.ERROR('❌ Error al enviar email'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 