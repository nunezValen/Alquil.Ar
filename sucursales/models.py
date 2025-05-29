from django.db import models
from django.core.exceptions import ValidationError
import re

def validar_coordenadas_dms(value):
    patron = r'^(-?\d{1,3})°(\d{1,2})\'(\d{1,2}\.\d+)"[NS]\s(-?\d{1,3})°(\d{1,2})\'(\d{1,2}\.\d+)"[EO]$'
    if not re.match(patron, value):
        raise ValidationError(
            'El formato debe ser: [Grados]°[Minutos]\'[Segundos.decimales]"[N/S] [Grados]°[Minutos]\'[Segundos.decimales]"[E/O]'
        )
    
    # Extraer componentes
    match = re.match(patron, value)
    lat_grados = int(match.group(1))
    lat_minutos = int(match.group(2))
    lat_segundos = float(match.group(3))
    lon_grados = int(match.group(4))
    lon_minutos = int(match.group(5))
    lon_segundos = float(match.group(6))
    
    # Validar rangos
    if not (-90 <= lat_grados <= 90):
        raise ValidationError('La latitud debe estar entre -90° y 90°')
    if not (-180 <= lon_grados <= 180):
        raise ValidationError('La longitud debe estar entre -180° y 180°')
    if not (0 <= lat_minutos < 60 and 0 <= lon_minutos < 60):
        raise ValidationError('Los minutos deben estar entre 0 y 59')
    if not (0 <= lat_segundos < 60 and 0 <= lon_segundos < 60):
        raise ValidationError('Los segundos deben estar entre 0 y 59.999')

class Sucursal(models.Model):
    nombre = models.CharField(
        max_length=100, 
        verbose_name='Nombre',
        unique=True
    )
    direccion = models.CharField(
        max_length=100,
        verbose_name='Dirección (DMS)',
        help_text='Formato: [Grados]°[Minutos]\'[Segundos.decimales]"[N/S] [Grados]°[Minutos]\'[Segundos.decimales]"[E/O]',
        validators=[validar_coordenadas_dms]
    )
    visible = models.BooleanField(
        default=True,
        verbose_name='Visible',
        help_text='Indica si la sucursal es visible en el sistema'
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
