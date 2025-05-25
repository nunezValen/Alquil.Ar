from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from datetime import date

def validar_mayor_edad(fecha_nacimiento):
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    if edad < 18:
        raise ValidationError('Debe ser mayor de 18 años para registrarse.')

class Persona(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(2)],
        help_text="El nombre debe tener entre 2 y 50 caracteres"
    )
    apellido = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(2)],
        help_text="El apellido debe tener entre 2 y 50 caracteres"
    )
    dni = models.CharField(
        max_length=9,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{7,9}$',
                message='El DNI debe tener entre 7 y 9 dígitos numéricos'
            )
        ],
        help_text="Ingrese un DNI de entre 7 y 9 dígitos"
    )
    email = models.EmailField(
        unique=True,
        help_text="Ingrese un correo electrónico válido"
    )
    fecha_nacimiento = models.DateField(
        help_text="Ingrese su fecha de nacimiento (debe ser mayor de 18 años)",
        validators=[validar_mayor_edad]
    )

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"

class Empleado(models.Model):
    nombre = models.CharField(max_length=100)
    dni = models.IntegerField()# Campo de texto con longitud máxima de 100 caracteres.
    apellido = models.CharField(max_length=100)  # Campo de texto con longitud máxima de 100 caracteres.
    edad = models.IntegerField()  # Campo para un número entero (edad).

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.edad} años)"

class Maquina(models.Model):
    nombre = models.CharField(max_length=100)  # Campo de texto con longitud máxima de 100 caracteres.
    tipo = models.CharField(max_length=100)  # Campo de texto con longitud máxima de 100 caracteres.
    modelo = models.IntegerField()  # Campo para un número entero (edad).

    def __str__(self):
        return f"Nombre: {self.nombre}. Tipo: {self.tipo}. Modelo: {self.modelo} "

# Create your models here.
