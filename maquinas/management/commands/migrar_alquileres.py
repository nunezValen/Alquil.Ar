from django.core.management.base import BaseCommand
from maquinas.models import Alquiler
from persona.models import Alquiler as AlquilerPersona

class Command(BaseCommand):
    help = 'Migra los alquileres existentes de la app persona a la app maquinas'

    def handle(self, *args, **options):
        alquileres_persona = AlquilerPersona.objects.all()
        total = alquileres_persona.count()
        migrados = 0
        errores = 0

        self.stdout.write(f"Iniciando migración de {total} alquileres...")

        for alquiler_persona in alquileres_persona:
            try:
                # Verificar si ya existe un alquiler migrado
                if Alquiler.objects.filter(alquiler_original=alquiler_persona).exists():
                    self.stdout.write(f"El alquiler {alquiler_persona.numero} ya fue migrado.")
                    continue

                # Crear nuevo alquiler
                alquiler = Alquiler()
                alquiler.migrar_desde_persona(alquiler_persona)
                migrados += 1
                self.stdout.write(f"Alquiler {alquiler_persona.numero} migrado exitosamente.")

            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(f"Error al migrar alquiler {alquiler_persona.numero}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"""
Migración completada:
- Total de alquileres: {total}
- Migrados exitosamente: {migrados}
- Errores: {errores}
""")) 