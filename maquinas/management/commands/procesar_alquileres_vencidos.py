from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from maquinas.models import Alquiler

class Command(BaseCommand):
    help = 'Procesa alquileres vencidos, cambiándolos a estado "adeudado" y poniendo las máquinas en mantenimiento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué alquileres se procesarían sin hacer cambios reales',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada del proceso',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        # Obtener la fecha actual
        fecha_actual = date.today()
        
        # Buscar alquileres vencidos que no han sido devueltos
        alquileres_vencidos = Alquiler.objects.filter(
            estado='en_curso',  # Solo alquileres en curso
            fecha_fin__lt=fecha_actual  # Fecha de fin menor a la fecha actual
        )
        
        if not alquileres_vencidos.exists():
            self.stdout.write(
                self.style.SUCCESS('No hay alquileres vencidos para procesar.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Se encontraron {alquileres_vencidos.count()} alquileres vencidos.')
        )
        
        procesados = 0
        errores = 0
        
        for alquiler in alquileres_vencidos:
            try:
                dias_vencido = (fecha_actual - alquiler.fecha_fin).days
                
                if verbose or dry_run:
                    self.stdout.write(
                        f'Procesando alquiler {alquiler.numero}:'
                    )
                    self.stdout.write(
                        f'  - Cliente: {alquiler.persona.nombre} {alquiler.persona.apellido}'
                    )
                    self.stdout.write(
                        f'  - Máquina: {alquiler.maquina_base.nombre}'
                    )
                    self.stdout.write(
                        f'  - Unidad: {alquiler.unidad.patente if alquiler.unidad else "Sin asignar"}'
                    )
                    self.stdout.write(
                        f'  - Fecha vencimiento: {alquiler.fecha_fin.strftime("%d/%m/%Y")}'
                    )
                    self.stdout.write(
                        f'  - Días vencido: {dias_vencido}'
                    )
                    
                if not dry_run:
                    # Cambiar estado del alquiler a "adeudado"
                    alquiler.estado = 'adeudado'
                    alquiler.save()
                    
                    # Poner la máquina en mantenimiento
                    if alquiler.unidad:
                        alquiler.unidad.estado = 'mantenimiento'
                        alquiler.unidad.save()
                        
                        # NUEVA FUNCIONALIDAD: Cancelar automáticamente alquileres futuros de la misma unidad
                        alquileres_futuros = Alquiler.objects.filter(
                            unidad=alquiler.unidad,
                            estado__in=['reservado', 'en_curso'],
                            fecha_inicio__gt=date.today()  # Solo alquileres futuros
                        ).exclude(id=alquiler.id)
                        
                        alquileres_cancelados = []
                        for alquiler_futuro in alquileres_futuros:
                            try:
                                # Cancelar el alquiler futuro
                                observaciones_cancelacion = f"Cancelado automáticamente por alquiler adeudado #{alquiler.numero}. La máquina {alquiler.unidad.patente} no fue devuelto a tiempo."
                                
                                # Crear un usuario del sistema para la cancelación automática
                                from django.contrib.auth.models import User
                                usuario_sistema = User.objects.filter(is_superuser=True).first()
                                
                                porcentaje, monto = alquiler_futuro.cancelar(
                                    empleado=usuario_sistema, 
                                    observaciones=observaciones_cancelacion
                                )
                                
                                # Enviar email de cancelación
                                try:
                                    from maquinas.utils import enviar_email_alquiler_cancelado
                                    enviar_email_alquiler_cancelado(alquiler_futuro)
                                    if verbose:
                                        self.stdout.write(
                                            self.style.SUCCESS(
                                                f'    ✓ Email de cancelación enviado para alquiler {alquiler_futuro.numero}'
                                            )
                                        )
                                except Exception as e:
                                    if verbose:
                                        self.stdout.write(
                                            self.style.ERROR(
                                                f'    ✗ Error al enviar email de cancelación para alquiler {alquiler_futuro.numero}: {str(e)}'
                                            )
                                        )
                                
                                alquileres_cancelados.append({
                                    'numero': alquiler_futuro.numero,
                                    'cliente': f"{alquiler_futuro.persona.nombre} {alquiler_futuro.persona.apellido}",
                                    'monto_reembolso': float(monto) if monto else 0,
                                    'porcentaje_reembolso': porcentaje
                                })
                                
                            except Exception as e:
                                if verbose:
                                    self.stdout.write(
                                        self.style.ERROR(
                                            f'    ✗ Error cancelando alquiler futuro {alquiler_futuro.numero}: {str(e)}'
                                        )
                                    )
                        
                        if verbose:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Alquiler {alquiler.numero} marcado como adeudado'
                                )
                            )
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Unidad {alquiler.unidad.patente} puesta en mantenimiento'
                                )
                            )
                            
                            if alquileres_cancelados:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  ⚠️  Se cancelaron {len(alquileres_cancelados)} alquileres futuros:'
                                    )
                                )
                                for cancelado in alquileres_cancelados:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'    - {cancelado["numero"]}: {cancelado["cliente"]} - Reembolso: {cancelado["porcentaje_reembolso"]}% (${cancelado["monto_reembolso"]})'
                                        )
                                    )
                    else:
                        if verbose:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Alquiler {alquiler.numero} marcado como adeudado (sin unidad asignada)'
                                )
                            )
                else:
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [DRY RUN] Se cambiaría a estado "adeudado" y unidad a mantenimiento'
                            )
                        )
                        
                        # Mostrar qué alquileres se cancelarían en dry-run
                        if alquiler.unidad:
                            alquileres_futuros = Alquiler.objects.filter(
                                unidad=alquiler.unidad,
                                estado__in=['reservado', 'en_curso'],
                                fecha_inicio__gt=date.today()  # Solo alquileres futuros
                            ).exclude(id=alquiler.id)
                            
                            if alquileres_futuros.exists():
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  [DRY RUN] Se cancelarían {alquileres_futuros.count()} alquileres futuros:'
                                    )
                                )
                                for alquiler_futuro in alquileres_futuros:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'    - {alquiler_futuro.numero}: {alquiler_futuro.persona.nombre} {alquiler_futuro.persona.apellido} (${alquiler_futuro.monto_total})'
                                        )
                                    )
                
                procesados += 1
                
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error procesando alquiler {alquiler.numero}: {str(e)}'
                    )
                )
        
        # Resumen final
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[DRY RUN] Se procesarían {procesados} alquileres vencidos.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Procesados {procesados} alquileres vencidos exitosamente.'
                )
            )
            
        if errores > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'✗ Se encontraron {errores} errores durante el procesamiento.'
                )
            )
            
        # Información adicional
        self.stdout.write(
            self.style.WARNING(
                f'\nRecuerda que las máquinas están ahora en mantenimiento y no estarán disponibles para nuevos alquileres.'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f'Los clientes deberán ser contactados para coordinar la devolución y pago de multas si corresponde.'
            )
        ) 