#!/usr/bin/env python
"""
Script para crear un empleado usando el sistema de registro de Django
que envía la contraseña por email automáticamente.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from django.contrib.auth.models import User
from persona.models import Persona
from django.core.mail import send_mail
from django.conf import settings
import random
import string

def crear_empleado():
    """Crear un empleado usando el proceso estándar del sistema"""
    
    print("=== CREANDO EMPLEADO CON ENVÍO DE EMAIL ===")
    
    # Datos del empleado
    nombre = "Ana María"
    apellido = "Rodriguez"
    email = "ana.rodriguez.empleada@gmail.com"
    dni = "45678912"
    telefono = "11-5678-9012"
    direccion = "Calle Empleado 123, Buenos Aires"
    
    try:
        # Verificar si ya existe el usuario
        if User.objects.filter(username=email).exists():
            print(f"Ya existe un usuario con email: {email}")
            return False
            
        if Persona.objects.filter(email=email).exists():
            print(f"Ya existe una persona con email: {email}")
            return False
        
        # Crear la persona empleado
        persona = Persona.objects.create(
            nombre=nombre,
            apellido=apellido,
            email=email,
            dni=dni,
            telefono=telefono,
            direccion=direccion,
            es_empleado=True,
            es_cliente=True,  # Todo empleado es cliente también
            es_admin=False,
            es_baneado=False
        )
        
        print(f"Persona creada: {persona.nombre} {persona.apellido}")
        
        # Generar contraseña aleatoria
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # Crear usuario de Django
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=nombre,
            last_name=apellido,
            is_staff=True  # Es staff para poder acceder al admin
        )
        
        print(f"Usuario Django creado: {user.username}")
        
        # Enviar email con credenciales
        try:
            send_mail(
                'Tu cuenta de empleado en Alquil.ar',
                f'Hola {persona.nombre},\n\n'
                f'Tu usuario ha sido creado exitosamente.\n\n'
                f'Credenciales de acceso:\n'
                f'• Email: {email}\n'
                f'• Contraseña: {password}\n\n'
                f'Puedes iniciar sesión en: https://nearby-cat-mildly.ngrok-free.app/persona/login-unificado2/\n\n'
                f'Por favor, cambia tu contraseña después de iniciar sesión.\n\n'
                f'Saludos,\n'
                f'Equipo Alquil.ar',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            print(f"✅ Email enviado exitosamente a: {email}")
            print(f"✅ Contraseña enviada por email: {password}")
            
        except Exception as e:
            print(f"❌ Error al enviar email: {str(e)}")
            print(f"📧 Credenciales (usa estas si no llegó el email):")
            print(f"   Email: {email}")
            print(f"   Contraseña: {password}")
        
        print(f"\n=== EMPLEADO CREADO EXITOSAMENTE ===")
        print(f"Nombre: {persona.nombre} {persona.apellido}")
        print(f"Email: {persona.email}")
        print(f"DNI: {persona.dni}")
        print(f"Teléfono: {persona.telefono}")
        print(f"Es empleado: {persona.es_empleado}")
        print(f"Es cliente: {persona.es_cliente}")
        print(f"Usuario Django: {user.username}")
        print(f"Es staff: {user.is_staff}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al crear empleado: {str(e)}")
        return False

if __name__ == "__main__":
    crear_empleado() 