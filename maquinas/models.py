from django.db import models
from django.core.validators import MinValueValidator
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
        error_messages={
            'max_digits': 'El precio no puede tener más de 10 dígitos enteros.',
            'decimal_places': 'El precio no puede tener más de 2 decimales.',
            'invalid': 'Por favor, ingrese un precio válido.',
            'max_whole_digits': 'La parte entera del precio no puede tener más de 10 dígitos.'
        }
    )
    descripcion_corta = models.TextField()
    descripcion_larga = models.TextField()
    imagen = models.ImageField(upload_to='maquinas/')
    dias_alquiler_min = models.PositiveIntegerField(
        verbose_name='Cantidad mínima de días de alquiler',
        validators=[MinValueValidator(1)]
    )
    dias_alquiler_max = models.PositiveIntegerField(
        verbose_name='Cantidad máxima de días de alquiler',
        validators=[MinValueValidator(1)]
    )
    stock = models.IntegerField(default=0, editable=False)

    def clean(self):
        super().clean()
        if self.dias_alquiler_min is not None and self.dias_alquiler_max is not None:
            if self.dias_alquiler_max < self.dias_alquiler_min:
                raise ValidationError({
                    'dias_alquiler_max': 'La cantidad máxima de días debe ser mayor o igual a la cantidad mínima.'
                })

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
        'sucursales.Sucursal',
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