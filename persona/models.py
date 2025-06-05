from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

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
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('alquilada', 'Alquilada'),
        ('mantenimiento', 'En Mantenimiento'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100)
    modelo = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    precio_dia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    dias_minimos = models.IntegerField(default=1)
    descripcion = models.TextField(default="Sin descripción disponible")
    imagen = models.ImageField(upload_to='maquinas/', null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

    class Meta:
        verbose_name = "Máquina"
        verbose_name_plural = "Máquinas"

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
    maquina = models.ForeignKey(Maquina, on_delete=models.CASCADE)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, null=True, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    preference_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Alquiler {self.numero} - {self.maquina.nombre}"

    class Meta:
        verbose_name = "Alquiler"
        verbose_name_plural = "Alquileres"

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
        if not self.monto_total and self.maquina and self.fecha_inicio and self.fecha_fin:
            dias = (self.fecha_fin - self.fecha_inicio).days + 1
            self.monto_total = self.maquina.precio_dia * dias
            
        super().save(*args, **kwargs)

# Create your models here.
