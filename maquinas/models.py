from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class MaquinaBase(models.Model):
    TIPOS = [
        ('bordeadora', 'Bordeadora'),
        ('aplanadora', 'Aplanadora'),
        ('excavadora', 'Excavadora'),
        ('retroexcavadora', 'Retroexcavadora'),
    ]

    MARCAS = [
        ('caterpillar', 'Caterpillar'),
        ('john_deere', 'John Deere'),
        ('bobcat', 'Bobcat'),
    ]

    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    tipo = models.CharField(
        max_length=50, 
        verbose_name='Tipo',
        choices=TIPOS
    )
    marca = models.CharField(
        max_length=50, 
        verbose_name='Marca',
        choices=MARCAS
    )
    modelo = models.CharField(max_length=50, verbose_name='Modelo')
    precio_por_dia = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Precio por día',
        validators=[MinValueValidator(0)]
    )
    descripcion_corta = models.TextField(verbose_name='Descripción corta')
    descripcion_larga = models.TextField(verbose_name='Descripción larga')
    imagen = models.ImageField(upload_to='maquinas/', verbose_name='Imagen')
    dias_alquiler_min = models.PositiveIntegerField(
        verbose_name='Cantidad mínima de días de alquiler',
        validators=[MinValueValidator(1)]
    )
    dias_alquiler_max = models.PositiveIntegerField(
        verbose_name='Cantidad máxima de días de alquiler',
        validators=[MinValueValidator(1)]
    )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.dias_alquiler_max < self.dias_alquiler_min:
            raise ValidationError('La cantidad máxima de días debe ser mayor o igual a la cantidad mínima')

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.tipo}"

    class Meta:
        verbose_name = 'Máquina Base'
        verbose_name_plural = 'Máquinas Base'

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
