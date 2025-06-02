import re
from django.core.exceptions import ValidationError
from django.db import models

def validar_coordenadas_dms(value):
    patron = (
        r'^'                          # inicio de cadena
        r'(-?\d{1,3})°'               # grados lat (–999 a 999, luego validamos rangos)
        r'(\d{1,2})\''                # minutos lat (00–59)
        r'(\d{1,2}\.\d+)"'            # segundos lat (00.0–59.999…)
        r'([NS])'                     # cardinal lat: N o S
        r'\s+'                        # al menos un espacio
        r'(-?\d{1,3})°'               # grados lon
        r'(\d{1,2})\''                # minutos lon
        r'(\d{1,2}\.\d+)"'            # segundos lon
        r'([EO])'                     # cardinal lon: E u O
        r'$'                          # fin de cadena
    )
    match = re.match(patron, value)
    if not match:
        raise ValidationError(
            'El formato debe ser: '
            '[Grados]°[Minutos]\'[Segundos.decimal]"[N/S] '
            '[Grados]°[Minutos]\'[Segundos.decimal]"[E/O] '
            '(ej.: 34°36\'00.000"S 058°22\'00.000"O).'
        )
    
    lat_grados   = int(match.group(1))
    lat_minutos  = int(match.group(2))
    lat_segundos = float(match.group(3))
    lat_cardinal = match.group(4)  # 'N' o 'S'
    
    lon_grados   = int(match.group(5))
    lon_minutos  = int(match.group(6))
    lon_segundos = float(match.group(7))
    lon_cardinal = match.group(8)  # 'E' o 'O'
    
    # Validar rangos numéricos
    if not (-90 <= lat_grados <= 90):
        raise ValidationError('La latitud debe estar entre –90° y 90°')
    if not (-180 <= lon_grados <= 180):
        raise ValidationError('La longitud debe estar entre –180° y 180°')
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
        max_length=50,
        verbose_name='Dirección (DMS)',
        help_text=(
            'Formato DMS: '
            '[Grados]°[Minutos]\'[Segundos.decimal]"[N/S] '
            '[Grados]°[Minutos]\'[Segundos.decimal]"[E/O] '
            '(p. ej.: 34°36\'00.000"S 058°22\'00.000"O)'
        ),
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
