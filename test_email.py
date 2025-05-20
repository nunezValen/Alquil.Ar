from django.core.mail import send_mail
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

send_mail(
    'Prueba de correo desde Django',
    '¡Este es un correo de prueba enviado desde tu proyecto Django!',
    'no-reply@alquilar.com.ar',
    ['contacto.alquilar@gmail.com'],
    fail_silently=False,
)
print('Correo enviado (si no hay error)') 