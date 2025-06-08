from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError

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
        ('confirmado', 'Confirmado'),
        ('en_curso', 'En Curso'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]
    
    METODOS_PAGO = [
        ('mercadopago', 'Mercado Pago'),
        ('binance', 'Binance Pay'),
    ]

    numero = models.CharField(max_length=10, unique=True)
    maquina_base = models.ForeignKey(MaquinaBase, on_delete=models.PROTECT)
    unidad = models.ForeignKey(Unidad, on_delete=models.PROTECT, null=True, blank=True)
    persona = models.ForeignKey('persona.Persona', on_delete=models.PROTECT, related_name='alquileres_maquinas')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    preference_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Alquiler {self.numero} - {self.maquina_base.nombre}"

    class Meta:
        verbose_name = "Alquiler"
        verbose_name_plural = "Alquileres"
        ordering = ['-fecha_creacion']

    def save(self, *args, **kwargs):
        if not self.numero:
            # Generar número de alquiler único
            ultimo_alquiler = Alquiler.objects.order_by('-id').first()
            if ultimo_alquiler:
                ultimo_numero = int(ultimo_alquiler.numero.split('-')[1])
                self.numero = f"A-{ultimo_numero + 1}"
            else:
                self.numero = "A-1"
        
        # Calcular monto total si no está establecido
        if not self.monto_total and self.maquina_base and self.fecha_inicio and self.fecha_fin:
            dias = (self.fecha_fin - self.fecha_inicio).days + 1
            self.monto_total = self.maquina_base.precio_por_dia * dias
            
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