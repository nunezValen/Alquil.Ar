from django.db import models

class Persona(models.Model):
    nombre = models.CharField(max_length=100)
    dni = models.IntegerField()# Campo de texto con longitud máxima de 100 caracteres.
    apollo = models.CharField(max_length=100)  # Campo de texto con longitud máxima de 100 caracteres.
    edad = models.IntegerField()  # Campo para un número entero (edad).

    def __str__(self):
        return f"{self.nombre} {self.apollo} ({self.edad} años)"

class Empleado(models.Model):
    nombre = models.CharField(max_length=100)
    dni = models.IntegerField()# Campo de texto con longitud máxima de 100 caracteres.
    apollo = models.CharField(max_length=100)  # Campo de texto con longitud máxima de 100 caracteres.
    edad = models.IntegerField()  # Campo para un número entero (edad).

    def __str__(self):
        return f"{self.nombre} {self.apollo} ({self.edad} años)"

class Maquina(models.Model):
    nombre = models.CharField(max_length=100)  # Campo de texto con longitud máxima de 100 caracteres.
    tipo = models.CharField(max_length=100)  # Campo de texto con longitud máxima de 100 caracteres.
    modelo = models.IntegerField()  # Campo para un número entero (edad).

    def __str__(self):
        return f"Nombre: {self.nombre}. Tipo: {self.tipo}. Modelo: {self.modelo} "

# Create your models here.
