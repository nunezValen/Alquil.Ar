from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from datetime import date
import string
import random

class MaquinaBase(models.Model):
    TIPOS_MAQUINA = [
        ('excavadora', 'Excavadora'),
        ('retroexcavadora', 'Retroexcavadora'),
        ('cargadora', 'Cargadora'),
        ('compactadora', 'Compactadora'),
        ('motoniveladora', 'Motoniveladora'),
        ('pavimentadora', 'Pavimentadora'),
        ('grua', 'Grúa'),
        ('hormigonera', 'Hormigonera'),
        ('dumper', 'Dumper'),
        ('manipulador', 'Manipulador Telescópico'),
    ]

    MARCAS = [
        ('caterpillar', 'Caterpillar'),
        ('komatsu', 'Komatsu'),
        ('volvo', 'Volvo'),
        ('hitachi', 'Hitachi'),
        ('liebherr', 'Liebherr'),
        ('jcb', 'JCB'),
        ('case', 'Case'),
        ('doosan', 'Doosan'),
        ('john_deere', 'John Deere'),
        ('kubota', 'Kubota'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS_MAQUINA)
    marca = models.CharField(max_length=20, choices=MARCAS)
    modelo = models.CharField(max_length=50)
    precio_por_dia = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='El precio debe ingresarse sin puntos. Puede utilizar comas para separar decimales.'
    )
    descripcion_corta = models.TextField()
    descripcion_larga = models.TextField()
    imagen = models.ImageField(
        upload_to='maquinas/',
        null=True,
        blank=True,
    )
    dias_alquiler_min = models.PositiveIntegerField(
        verbose_name='Cantidad mínima de días de alquiler',
        validators=[MinValueValidator(1)]
    )
    dias_alquiler_max = models.PositiveIntegerField(
        verbose_name='Cantidad máxima de días de alquiler',
        validators=[MinValueValidator(1)]
    )
    stock = models.IntegerField(default=0, editable=False)

    # Campos para política de cancelación
    dias_cancelacion_total = models.PositiveIntegerField(
        verbose_name='Días mínimos para reembolso total',
        help_text='Número de días antes del inicio del alquiler para obtener reembolso total',
        validators=[MinValueValidator(1)],
        default=10
    )
    dias_cancelacion_parcial = models.PositiveIntegerField(
        verbose_name='Días mínimos para reembolso parcial',
        help_text='Número de días antes del inicio del alquiler para obtener reembolso parcial',
        validators=[MinValueValidator(1)],
        default=5
    )
    porcentaje_reembolso_parcial = models.PositiveIntegerField(
        verbose_name='Porcentaje de reembolso parcial',
        help_text='Porcentaje del monto total que se reembolsará en caso de cancelación parcial',
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        default=50
    )

    def clean(self):
        super().clean()
        if self.dias_alquiler_min is not None and self.dias_alquiler_max is not None:
            if self.dias_alquiler_max < self.dias_alquiler_min:
                raise ValidationError({
                    'dias_alquiler_max': 'La cantidad máxima de días debe ser mayor o igual a la cantidad mínima.'
                })
        
        # Validar que los días de cancelación parcial sean menores a los de cancelación total
        if self.dias_cancelacion_parcial is not None and self.dias_cancelacion_total is not None:
            if self.dias_cancelacion_parcial >= self.dias_cancelacion_total:
                raise ValidationError({
                    'dias_cancelacion_parcial': 'Los días para reembolso parcial deben ser menores a los días para reembolso total.'
                })

    def tiene_unidades_disponibles(self):
        return self.unidades.filter(estado='disponible', visible=True).exists()

    def __str__(self):
        return f"{self.nombre} ({self.get_marca_display()} {self.modelo})"

    class Meta:
        verbose_name = "Máquina Base"
        verbose_name_plural = "Máquinas Base"
        ordering = ['nombre']

@receiver(post_save, sender=MaquinaBase)
def actualizar_stock_maquina_base(sender, instance, created, **kwargs):
    if created:
        instance.stock = 0
        instance.save()

class Unidad(models.Model):
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('alquilada', 'Alquilada'),
        ('mantenimiento', 'En Mantenimiento'),
        ('adeudada', 'Adeudada'),
    ]

    maquina_base = models.ForeignKey(
        MaquinaBase, 
        on_delete=models.PROTECT, 
        verbose_name='Máquina base',
        related_name='unidades'
    )
    patente = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name='Patente'
    )
    sucursal = models.ForeignKey(
        'persona.Sucursal',
        on_delete=models.PROTECT,
        verbose_name='Sucursal'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='disponible',
        verbose_name='Estado'
    )
    visible = models.BooleanField(
        default=True,
        verbose_name='Visible',
        help_text='Indica si la unidad es visible en el sistema'
    )

    def __str__(self):
        return f"{self.maquina_base} - Patente: {self.patente}"

    class Meta:
        verbose_name = 'Unidad'
        verbose_name_plural = 'Unidades'

@receiver(post_save, sender=Unidad)
def actualizar_stock_maquina(sender, instance, created, **kwargs):
    if created:  # Solo si es una nueva unidad
        maquina = instance.maquina_base
        maquina.stock = maquina.stock + 1
        maquina.save()

@receiver(post_delete, sender=Unidad)
def restar_stock_maquina(sender, instance, **kwargs):
    maquina = instance.maquina_base
    if maquina.stock > 0:
        maquina.stock -= 1
        maquina.save()

class Alquiler(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente de Pago'),
        ('reservado', 'Reservado'),
        ('en_curso', 'En Curso'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
        ('rechazado', 'Rechazado'),
    ]
    
    METODOS_PAGO = [
        ('mercadopago', 'Mercado Pago'),
        ('binance', 'Binance Pay'),
    ]

    numero = models.CharField(max_length=10, unique=True, blank=True)
    maquina_base = models.ForeignKey(MaquinaBase, on_delete=models.PROTECT)
    unidad = models.ForeignKey(Unidad, on_delete=models.PROTECT, null=True, blank=True)
    persona = models.ForeignKey('persona.Persona', on_delete=models.PROTECT, related_name='alquileres_maquinas')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    cantidad_dias = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='reservado')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    codigo_retiro = models.CharField(max_length=8, unique=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    preference_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Campos para cancelación y reembolso
    fecha_cancelacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Cancelación')
    cancelado_por_empleado = models.BooleanField(default=False, verbose_name='Cancelado por Empleado')
    empleado_que_cancelo = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='Empleado que Canceló',
        related_name='alquileres_cancelados'
    )
    monto_reembolso = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Monto a Reembolsar')
    porcentaje_reembolso = models.PositiveIntegerField(null=True, blank=True, verbose_name='Porcentaje de Reembolso')
    observaciones_cancelacion = models.TextField(blank=True, verbose_name='Observaciones de Cancelación')
    
    calificacion = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        verbose_name='Calificación',
        help_text='Calificación del servicio por parte del cliente (1 a 5)'
    )

    def clean(self):
        super().clean()
        
        # Validar fechas
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio >= self.fecha_fin:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
                
            # No permitir fechas en el pasado
            if self.fecha_inicio < date.today():
                raise ValidationError('La fecha de inicio no puede ser en el pasado.')
                
            # Verificar que el cliente no tenga otro alquiler activo
            if self.persona_id:
                alquileres_activos = Alquiler.objects.filter(
                    persona=self.persona,
                    estado__in=['reservado', 'en_curso']
                ).exclude(id=self.id)
                
                if alquileres_activos.exists():
                    raise ValidationError('Este cliente ya tiene un alquiler activo. Solo puede tener un alquiler a la vez.')
    
    @staticmethod
    def verificar_disponibilidad(maquina_base, fecha_inicio, fecha_fin, excluir_alquiler_id=None):
        """
        Verifica si hay disponibilidad para una máquina en las fechas especificadas
        """
        # Obtener alquileres que se superponen con el período solicitado
        alquileres_superpuestos = Alquiler.objects.filter(
            maquina_base=maquina_base,
            estado__in=['reservado', 'en_curso'],
            fecha_inicio__lte=fecha_fin,
            fecha_fin__gte=fecha_inicio
        )
        
        if excluir_alquiler_id:
            alquileres_superpuestos = alquileres_superpuestos.exclude(id=excluir_alquiler_id)
        
        # Contar cuántas unidades están ocupadas en esas fechas
        unidades_ocupadas = alquileres_superpuestos.count()
        
        # Contar unidades disponibles
        unidades_disponibles = maquina_base.unidades.filter(
            estado='disponible',
            visible=True
        ).count()
        
        return unidades_ocupadas < unidades_disponibles
    
    @staticmethod
    def obtener_unidades_disponibles(maquina_base, fecha_inicio, fecha_fin):
        """
        Obtiene el número de unidades disponibles para una máquina en las fechas especificadas
        """
        # Obtener alquileres que se superponen
        alquileres_superpuestos = Alquiler.objects.filter(
            maquina_base=maquina_base,
            estado__in=['reservado', 'en_curso'],
            fecha_inicio__lte=fecha_fin,
            fecha_fin__gte=fecha_inicio
        )
        
        unidades_ocupadas = alquileres_superpuestos.count()
        unidades_totales = maquina_base.unidades.filter(
            estado='disponible',
            visible=True
        ).count()
        
        return max(0, unidades_totales - unidades_ocupadas)
    
    def asignar_unidad_disponible(self):
        """
        Asigna automáticamente una unidad disponible que no esté ocupada en las fechas del alquiler
        """
        # Obtener todas las unidades de la máquina base
        unidades_maquina = self.maquina_base.unidades.filter(
            estado='disponible',
            visible=True
        )
        
        # Obtener unidades ya ocupadas en las fechas del alquiler
        unidades_ocupadas = Alquiler.objects.filter(
            maquina_base=self.maquina_base,
            estado__in=['reservado', 'en_curso'],
            fecha_inicio__lte=self.fecha_fin,
            fecha_fin__gte=self.fecha_inicio
        ).exclude(id=self.id).values_list('unidad_id', flat=True)
        
        # Buscar la primera unidad disponible
        unidad_disponible = unidades_maquina.exclude(id__in=unidades_ocupadas).first()
        
        if unidad_disponible:
            self.unidad = unidad_disponible
            return True
        return False

    def calcular_reembolso(self, es_empleado=False):
        """
        Calcula el porcentaje y monto de reembolso según la política de cancelación
        """
        if es_empleado:
            return 100, self.monto_total
        
        if not self.fecha_inicio:
            return 0, 0
            
        from datetime import date
        dias_anticipacion = (self.fecha_inicio - date.today()).days
        
        if dias_anticipacion < 0:
            # Ya comenzó el alquiler, no hay reembolso
            return 0, 0
        elif dias_anticipacion >= self.maquina_base.dias_cancelacion_total:
            # Reembolso total
            return 100, self.monto_total
        elif dias_anticipacion >= self.maquina_base.dias_cancelacion_parcial:
            # Reembolso parcial
            porcentaje = self.maquina_base.porcentaje_reembolso_parcial
            monto = (self.monto_total * porcentaje / 100)
            return porcentaje, monto
        else:
            # Sin reembolso
            return 0, 0
    
    def cancelar(self, empleado=None, observaciones=""):
        """
        Cancela el alquiler y calcula el reembolso correspondiente
        """
        from django.utils import timezone
        
        if self.estado in ['cancelado', 'finalizado']:
            raise ValueError("No se puede cancelar un alquiler ya cancelado o finalizado")
        
        es_empleado = empleado is not None
        porcentaje, monto = self.calcular_reembolso(es_empleado)
        
        self.estado = 'cancelado'
        self.fecha_cancelacion = timezone.now()
        self.cancelado_por_empleado = es_empleado
        self.empleado_que_cancelo = empleado if es_empleado else None
        self.porcentaje_reembolso = porcentaje
        self.monto_reembolso = monto
        self.observaciones_cancelacion = observaciones
        
        self.save()
        
        return porcentaje, monto
    
    def puede_ser_cancelado(self):
        """
        Verifica si el alquiler puede ser cancelado
        """
        return self.estado in ['reservado', 'en_curso']
    
    def __str__(self):
        return f"Alquiler {self.numero} - {self.maquina_base.nombre}"

    class Meta:
        verbose_name = "Alquiler"
        verbose_name_plural = "Alquileres"
        ordering = ['-fecha_creacion']

    def save(self, *args, **kwargs):
        # Generar número de alquiler único con formato A-0001
        if not self.numero:
            ultimo_alquiler = Alquiler.objects.order_by('-id').first()
            if ultimo_alquiler:
                try:
                    ultimo_numero = int(ultimo_alquiler.numero.split('-')[1])
                    nuevo_numero = ultimo_numero + 1
                except (ValueError, IndexError):
                    nuevo_numero = 1
            else:
                nuevo_numero = 1
            self.numero = f"A-{nuevo_numero:04d}"
        
        # Generar código de retiro único
        if not self.codigo_retiro:
            while True:
                codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Alquiler.objects.filter(codigo_retiro=codigo).exists():
                    self.codigo_retiro = codigo
                    break
        
        # Calcular cantidad de días
        if self.fecha_inicio and self.fecha_fin:
            self.cantidad_dias = (self.fecha_fin - self.fecha_inicio).days + 1
            
        # Calcular monto total si no está establecido
        if not self.monto_total and self.maquina_base and self.cantidad_dias:
            self.monto_total = self.maquina_base.precio_por_dia * self.cantidad_dias
        
        # Asignar unidad disponible si no tiene una asignada
        if not self.unidad and self.maquina_base:
            self.asignar_unidad_disponible()
            
        super().save(*args, **kwargs)

    def migrar_desde_persona(self, alquiler_persona):
        """Método para migrar un alquiler desde la app persona"""
        self.maquina_base = alquiler_persona.maquina
        self.persona = alquiler_persona.persona
        self.fecha_inicio = alquiler_persona.fecha_inicio
        self.fecha_fin = alquiler_persona.fecha_fin
        self.estado = alquiler_persona.estado
        self.metodo_pago = alquiler_persona.metodo_pago
        self.monto_total = alquiler_persona.monto_total
        self.preference_id = alquiler_persona.preference_id
        self.save()

class Reembolso(models.Model):
    """
    Modelo para gestionar los reembolsos de alquileres cancelados
    """
    ESTADOS = [
        ('pendiente', 'Pendiente de Pago'),
        ('pagado', 'Pagado'),
        ('rechazado', 'Rechazado'),
    ]
    
    alquiler = models.OneToOneField(
        Alquiler,
        on_delete=models.PROTECT,
        verbose_name='Alquiler',
        related_name='reembolso'
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Monto a Reembolsar'
    )
    porcentaje = models.PositiveIntegerField(
        verbose_name='Porcentaje de Reembolso'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente',
        verbose_name='Estado'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    fecha_pago = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Pago'
    )
    empleado_que_marco_pagado = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Empleado que Marcó como Pagado',
        related_name='reembolsos_marcados_pagados'
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    def marcar_como_pagado(self, empleado=None, observaciones=""):
        """
        Marca el reembolso como pagado
        """
        from django.utils import timezone
        
        self.estado = 'pagado'
        self.fecha_pago = timezone.now()
        self.empleado_que_marco_pagado = empleado
        if observaciones:
            self.observaciones = observaciones
        self.save()
    
    def __str__(self):
        return f"Reembolso {self.alquiler.numero} - ${self.monto} ({self.get_estado_display()})"
    
    class Meta:
        verbose_name = "Reembolso"
        verbose_name_plural = "Reembolsos"
        ordering = ['-fecha_creacion']

@receiver(post_save, sender=Alquiler)
def crear_reembolso_automatico(sender, instance, created, **kwargs):
    """
    Crea automáticamente un reembolso cuando se cancela un alquiler con monto > 0
    """
    if (instance.estado == 'cancelado' and 
        instance.monto_reembolso and 
        instance.monto_reembolso > 0 and
        not hasattr(instance, 'reembolso')):
        
        Reembolso.objects.create(
            alquiler=instance,
            monto=instance.monto_reembolso,
            porcentaje=instance.porcentaje_reembolso or 0
        )