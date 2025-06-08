#!/usr/bin/env python
"""
Script para crear un administrador usando el sistema de registro de Django
que envía la contraseña por email automáticamente.
El admin puede cargar máquinas y gestionar todo el sistema.
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

def crear_admin():
    """Crear un administrador usando el proceso estándar del sistema"""
    
    print("=== CREANDO ADMINISTRADOR CON ENVÍO DE EMAIL ===")
    
    # Datos del administrador
    nombre = "Carlos Eduardo"
    apellido = "Mendoza"
    email = "admin.carlos.mendoza@gmail.com"
    dni = "23456789"
    telefono = "11-3456-7890"
    direccion = "Av. Administración 456, Buenos Aires"
    
    try:
        # Verificar si ya existe el usuario
        if User.objects.filter(username=email).exists():
            print(f"Ya existe un usuario con email: {email}")
            return False
            
        if Persona.objects.filter(email=email).exists():
            print(f"Ya existe una persona con email: {email}")
            return False
        
        # Crear la persona administrador
        persona = Persona.objects.create(
            nombre=nombre,
            apellido=apellido,
            email=email,
            dni=dni,
            telefono=telefono,
            direccion=direccion,
            es_empleado=True,   # Los admins también son empleados
            es_cliente=True,    # También pueden actuar como clientes
            es_admin=True,      # Es administrador
            es_baneado=False
        )
        
        print(f"Persona creada: {persona.nombre} {persona.apellido}")
        
        # Generar contraseña aleatoria
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        # Crear usuario de Django con permisos de superusuario
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=nombre,
            last_name=apellido,
            is_staff=True,      # Puede acceder al admin de Django
            is_superuser=True   # Tiene todos los permisos (puede cargar máquinas)
        )
        
        print(f"Usuario Django creado: {user.username}")
        
        # Enviar email con credenciales
        try:
            send_mail(
                '🔐 Tu cuenta de Administrador en Alquil.ar',
                f'¡Hola {persona.nombre}!\n\n'
                f'Tu cuenta de ADMINISTRADOR ha sido creada exitosamente.\n\n'
                f'🔑 CREDENCIALES DE ACCESO:\n'
                f'• Email: {email}\n'
                f'• Contraseña: {password}\n\n'
                f'🌐 ACCESO AL SISTEMA:\n'
                f'• Login: https://nearby-cat-mildly.ngrok-free.app/persona/login-unificado2/\n'
                f'• Panel Admin Django: https://nearby-cat-mildly.ngrok-free.app/admin/\n\n'
                f'⚡ PERMISOS DE ADMINISTRADOR:\n'
                f'• ✅ Cargar y gestionar máquinas\n'
                f'• ✅ Gestionar empleados y clientes\n'
                f'• ✅ Ver estadísticas y reportes\n'
                f'• ✅ Administrar alquileres\n'
                f'• ✅ Acceso completo al panel de Django\n'
                f'• ✅ Permisos de superusuario\n\n'
                f'🔒 SEGURIDAD:\n'
                f'Por favor, cambia tu contraseña después del primer inicio de sesión.\n\n'
                f'¡Bienvenido al equipo de Alquil.ar!\n'
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
        
        print(f"\n=== ADMINISTRADOR CREADO EXITOSAMENTE ===")
        print(f"Nombre: {persona.nombre} {persona.apellido}")
        print(f"Email: {persona.email}")
        print(f"DNI: {persona.dni}")
        print(f"Teléfono: {persona.telefono}")
        print(f"Es empleado: {persona.es_empleado}")
        print(f"Es cliente: {persona.es_cliente}")
        print(f"Es admin: {persona.es_admin}")
        print(f"Usuario Django: {user.username}")
        print(f"Es staff: {user.is_staff}")
        print(f"Es superuser: {user.is_superuser}")
        print(f"\n🎯 PERMISOS ESPECIALES:")
        print(f"• ✅ Puede cargar máquinas")
        print(f"• ✅ Puede gestionar empleados")
        print(f"• ✅ Acceso total al sistema")
        print(f"• ✅ Panel de administración Django")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al crear administrador: {str(e)}")
        return False

if __name__ == "__main__":
    crear_admin() 