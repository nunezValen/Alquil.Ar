#!/usr/bin/env python
"""
Script para crear un usuario empleado con email random
"""
import os
import sys
import django
import random
import string

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from django.contrib.auth.models import User
from persona.models import Persona

def generar_email_random():
    """Generar un email random"""
    nombres = ['carlos', 'maria', 'juan', 'ana', 'pedro', 'lucia', 'diego', 'sofia', 'pablo', 'laura']
    apellidos = ['garcia', 'rodriguez', 'martinez', 'lopez', 'gonzalez', 'perez', 'sanchez', 'ramirez']
    dominios = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
    
    nombre = random.choice(nombres)
    apellido = random.choice(apellidos)
    dominio = random.choice(dominios)
    numero = random.randint(10, 99)
    
    return f"{nombre}.{apellido}{numero}@{dominio}"

def generar_password():
    """Generar una contraseña simple"""
    return f"empleado{random.randint(100, 999)}"

def generar_dni():
    """Generar un DNI random"""
    return str(random.randint(10000000, 99999999))

def crear_empleado():
    """Crear un usuario empleado"""
    
    # Generar datos
    email = generar_email_random()
    password = generar_password()
    username = email.split('@')[0]
    dni = generar_dni()
    
    # Verificar que no exista
    while User.objects.filter(email=email).exists() or User.objects.filter(username=username).exists() or Persona.objects.filter(email=email).exists() or Persona.objects.filter(dni=dni).exists():
        email = generar_email_random()
        username = email.split('@')[0]
        dni = generar_dni()
    
    try:
        # Crear usuario Django
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=username.split('.')[0].capitalize(),
            last_name=username.split('.')[1].split('0')[0].capitalize() if '.' in username else 'Empleado',
            is_staff=True  # Para que pueda acceder al admin
        )
        
        # Crear persona empleado
        persona = Persona.objects.create(
            nombre=user.first_name,
            apellido=user.last_name,
            dni=dni,
            email=email,
            telefono=f"11{random.randint(10000000, 99999999)}",
            direccion=f"Calle {random.randint(100, 9999)} #{random.randint(10, 999)}",
            es_cliente=True,
            es_empleado=True,
            es_admin=False,
            es_baneado=False
        )
        
        print("="*60)
        print("🎉 EMPLEADO CREADO EXITOSAMENTE")
        print("="*60)
        print(f"📧 Email/Usuario: {email}")
        print(f"🔑 Contraseña: {password}")
        print(f"👤 Nombre: {persona.nombre} {persona.apellido}")
        print(f"🆔 DNI: {persona.dni}")
        print(f"📱 Teléfono: {persona.telefono}")
        print(f"🏠 Dirección: {persona.direccion}")
        print(f"👨‍💼 Es empleado: ✅ Sí")
        print(f"🛡️ Es admin: ❌ No")
        print(f"👤 Es cliente: ✅ Sí")
        print("="*60)
        print("💡 INSTRUCCIONES:")
        print("1. Usa estas credenciales para iniciar sesión")
        print("2. El empleado puede acceder a la gestión de alquileres")
        print("3. Puede ver todos los alquileres de todos los clientes")
        print("4. Puede filtrar y exportar reportes")
        print("5. URL: http://127.0.0.1:8000/persona/lista-alquileres/")
        print("="*60)
        
        return {
            'email': email,
            'password': password,
            'username': username,
            'nombre_completo': f"{persona.nombre} {persona.apellido}",
            'dni': dni
        }
        
    except Exception as e:
        print(f"❌ Error al crear empleado: {str(e)}")
        return None

if __name__ == '__main__':
    crear_empleado() 