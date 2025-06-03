from django.db import models
from django.utils import timezone

class Persona(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    
    # Nuevos campos booleanos para roles
    es_cliente = models.BooleanField(default=False)
    es_empleado = models.BooleanField(default=False)
    es_admin = models.BooleanField(default=False)
    es_baneado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Si es empleado, automáticamente es cliente también
        if self.es_empleado:
            self.es_cliente = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"

class Maquina(models.Model):
    nombre = models.CharField(max_length=100)  # Campo de texto con longitud máxima de 100 caracteres.
    tipo = models.CharField(max_length=100)  # Campo de texto con longitud máxima de 100 caracteres.
    modelo = models.IntegerField()  # Campo para un número entero (edad).

    def __str__(self):
        return f"Nombre: {self.nombre}. Tipo: {self.tipo}. Modelo: {self.modelo} "

# Create your models here.
