from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
import re

def validar_email(email):
    """Valida que el email tenga un formato válido y un dominio real"""
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValidationError('El formato del email no es válido')

class Persona(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"

class Empleado(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

class Maquina(models.Model):
    nombre = models.CharField(max_length=100)  # Campo de texto con longitud máxima de 100 caracteres.
    tipo = models.CharField(max_length=100)  # Campo de texto con longitud máxima de 100 caracteres.
    modelo = models.IntegerField()  # Campo para un número entero (edad).

    def __str__(self):
        return f"Nombre: {self.nombre}. Tipo: {self.tipo}. Modelo: {self.modelo} "

class Sucursal(models.Model):
    id_sucursal = models.AutoField(
        primary_key=True,
        verbose_name="ID Sucursal"
    )
    direccion = models.CharField(
        max_length=200,
        help_text="Dirección completa de la sucursal"
    )
    latitud = models.FloatField(
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90)
        ],
        help_text="Latitud de la ubicación (entre -90 y 90 grados)"
    )
    longitud = models.FloatField(
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180)
        ],
        help_text="Longitud de la ubicación (entre -180 y 180 grados)"
    )
    telefono = models.CharField(
        max_length=20,
        help_text="Número de teléfono de la sucursal (formato: +54 9 221 123-4567)",
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s-]{10,}$',
                message='Ingrese un número de teléfono válido (mínimo 10 dígitos)'
            )
        ]
    )
    email = models.EmailField(
        help_text="Correo electrónico de contacto",
        validators=[validar_email]
    )
    horario = models.TextField(
        help_text="Horarios de atención de la sucursal"
    )

    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        # Validar que el teléfono tenga el formato correcto
        if self.telefono:
            # Eliminar espacios y guiones para contar dígitos
            digitos = ''.join(filter(str.isdigit, self.telefono))
            if len(digitos) < 10:
                raise ValidationError({
                    'telefono': 'El número de teléfono debe tener al menos 10 dígitos'
                })

    def get_coordenadas(self):
        """Devuelve las coordenadas en formato [latitud, longitud]"""
        return [self.latitud, self.longitud]

    def __str__(self):
        return f"Sucursal #{self.id_sucursal} - {self.direccion}"

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"

# Create your models here.
