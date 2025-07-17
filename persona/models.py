from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
import re
import random
import string
from django.contrib.auth.models import User

def validar_email(email):
    """Valida que el email tenga un formato válido y un dominio real"""
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValidationError('El formato del email no es válido')

def generar_codigo():
    """Genera un código aleatorio de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=6))

class CodigoVerificacion(models.Model):
    persona = models.ForeignKey('Persona', on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6, default=generar_codigo)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    usado = models.BooleanField(default=False)

    def __str__(self):
        return f"Código para {self.persona.email}"

    def save(self, *args, **kwargs):
        if not self.fecha_expiracion:
            # El código expira en 10 minutos
            self.fecha_expiracion = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Código de Verificación"
        verbose_name_plural = "Códigos de Verificación"

class Persona(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='persona', null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True, editable=False)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.TextField(null=True, blank=True, editable=False)
    fecha_registro = models.DateTimeField(default=timezone.now)
    
    # Nuevos campos booleanos para roles
    es_cliente = models.BooleanField(default=False)
    es_empleado = models.BooleanField(default=False)
    es_admin = models.BooleanField(default=False)
    bloqueado_cliente = models.BooleanField(default=False, help_text="Si el usuario está bloqueado para actuar como cliente")
    bloqueado_empleado = models.BooleanField(default=False, help_text="Si el usuario está bloqueado para actuar como empleado")
    
    # Campo para el promedio de calificaciones
    calificacion_promedio = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=5.00,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Promedio de calificaciones del cliente (1.00 - 5.00)"
    )

    def calcular_recargo(self, monto_base):
        """
        Calcula el recargo basado en la calificación promedio del cliente.
        
        Reglas (usando redondeo hacia arriba):
        - ≥ 4 estrellas: 0% de recargo
        - = 3 estrellas: 10% de recargo  
        - = 2 estrellas: 20% de recargo
        - = 1 estrella: 30% de recargo
        
        Ejemplos:
        - 3.5 → ceil(3.5) = 4 → 0% recargo
        - 2.5 → ceil(2.5) = 3 → 10% recargo
        - 1.5 → ceil(1.5) = 2 → 20% recargo
        
        Returns:
            tuple: (porcentaje_recargo, monto_recargo, monto_total)
        """
        import math
        
        # Redondear hacia arriba la calificación promedio
        calificacion_redondeada = math.ceil(float(self.calificacion_promedio))
        
        # Aplicar reglas de negocio basadas en la calificación redondeada
        if calificacion_redondeada >= 4:
            porcentaje = 0
        elif calificacion_redondeada == 3:
            porcentaje = 10
        elif calificacion_redondeada == 2:
            porcentaje = 20
        else:  # calificacion_redondeada == 1
            porcentaje = 30
        
        monto_recargo = (monto_base * porcentaje) / 100
        monto_total = monto_base + monto_recargo
        
        return porcentaje, monto_recargo, monto_total
    
    def tiene_recargo(self):
        """
        Verifica si el cliente tiene recargo aplicable.
        Usa redondeo hacia arriba para consistencia.
        Returns: bool
        """
        import math
        calificacion_redondeada = math.ceil(float(self.calificacion_promedio))
        return calificacion_redondeada < 4
    
    def get_mensaje_recargo(self, monto_base=None):
        """
        Obtiene el mensaje explicativo del recargo.
        Returns: str
        """
        if not self.tiene_recargo():
            return "Sin recargo por historial de calificaciones."
        
        porcentaje, monto_recargo, monto_total = self.calcular_recargo(monto_base or 0)
        
        if monto_base:
            return f"Recargo por calificación baja: {porcentaje}% (${monto_recargo:,.0f}). Total a pagar: ${monto_total:,.0f}."
        else:
            return f"Se aplicará un recargo de {porcentaje}% por calificación promedio de {self.calificacion_promedio} estrellas."

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def save(self, *args, **kwargs):
        # Guardar el estado anterior de es_admin si el objeto ya existe
        if self.pk:
            old_instance = Persona.objects.get(pk=self.pk)
            old_es_admin = old_instance.es_admin
        else:
            old_es_admin = False

        # Guardar la persona
        super().save(*args, **kwargs)

        # Si el email existe, actualizar o crear el usuario de Django
        if self.email:
            user, created = User.objects.get_or_create(
                username=self.email,
                defaults={
                    'email': self.email,
                    'first_name': self.nombre,
                    'last_name': self.apellido,
                }
            )

            # Si el usuario ya existía, actualizar sus datos
            if not created:
                user.first_name = self.nombre
                user.last_name = self.apellido
                user.email = self.email

            # Actualizar permisos si es_admin ha cambiado
            if self.es_admin != old_es_admin:
                user.is_staff = self.es_admin
                user.is_superuser = self.es_admin
            
            user.save()

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

    es_visible = models.BooleanField(
        default=True,
        verbose_name="Visible",
        help_text="Indica si la sucursal es visible en listados y mapas"
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
