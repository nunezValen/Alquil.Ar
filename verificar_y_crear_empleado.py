#!/usr/bin/env python
"""
Script para verificar usuarios y crear empleado con contraseña correctamente hasheada
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from persona.models import Persona

def verificar_usuarios():
    """Verificar usuarios existentes"""
    print("="*60)
    print("👥 USUARIOS EXISTENTES")
    print("="*60)
    
    users = User.objects.all()
    for user in users:
        print(f"👤 Username: {user.username}")
        print(f"📧 Email: {user.email}")
        print(f"👨‍💼 Is staff: {user.is_staff}")
        print(f"🛡️ Is superuser: {user.is_superuser}")
        
        # Buscar persona asociada
        try:
            persona = Persona.objects.get(email=user.email)
            print(f"👤 Persona: {persona.nombre} {persona.apellido}")
            print(f"👨‍💼 Es empleado: {persona.es_empleado}")
            print(f"🛡️ Es admin: {persona.es_admin}")
        except Persona.DoesNotExist:
            print("❌ Sin persona asociada")
        
        print("-" * 40)

def crear_empleado_simple():
    """Crear empleado con credenciales simples"""
    
    # Credenciales simples
    email = "empleado@test.com"
    username = "empleado"
    password = "123456"
    
    # Eliminar si existe
    try:
        User.objects.filter(username=username).delete()
        User.objects.filter(email=email).delete()
        Persona.objects.filter(email=email).delete()
        print("🗑️ Usuario anterior eliminado")
    except:
        pass
    
    try:
        # Crear usuario Django con contraseña correctamente hasheada
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,  # Django hashea automáticamente con create_user
            first_name="Empleado",
            last_name="Test",
            is_staff=True
        )
        
        # Crear persona empleado
        persona = Persona.objects.create(
            nombre="Empleado",
            apellido="Test",
            dni="12345678",
            email=email,
            telefono="1123456789",
            direccion="Calle Test 123",
            es_cliente=True,
            es_empleado=True,
            es_admin=False,
            es_baneado=False
        )
        
        # Verificar que la autenticación funciona
        auth_user = authenticate(username=username, password=password)
        
        print("="*60)
        print("🎉 EMPLEADO CREADO Y VERIFICADO")
        print("="*60)
        print(f"📧 Email/Usuario: {email}")
        print(f"🔑 Contraseña: {password}")
        print(f"👤 Nombre: {persona.nombre} {persona.apellido}")
        print(f"🆔 DNI: {persona.dni}")
        print(f"✅ Autenticación: {'OK' if auth_user else 'ERROR'}")
        print(f"👨‍💼 Es empleado: ✅ Sí")
        print(f"🛡️ Es staff: ✅ Sí")
        print("="*60)
        print("💡 INSTRUCCIONES:")
        print("1. Inicia el servidor: python manage.py runserver")
        print("2. Ve a: http://127.0.0.1:8000/persona/login/")
        print(f"3. Usuario: {username}")
        print(f"4. Contraseña: {password}")
        print("5. Después ve a: http://127.0.0.1:8000/persona/lista-alquileres/")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error al crear empleado: {str(e)}")
        return False

def verificar_credenciales():
    """Verificar si las credenciales funcionan"""
    print("\n🔍 VERIFICANDO CREDENCIALES...")
    
    # Probar con el usuario simple
    auth = authenticate(username="empleado", password="123456")
    print(f"👤 empleado/123456: {'✅ OK' if auth else '❌ FAIL'}")
    
    # Probar con el admin
    auth = authenticate(username="valen", password="1234")
    print(f"🛡️ valen/1234: {'✅ OK' if auth else '❌ FAIL'}")

if __name__ == '__main__':
    print("🔍 Verificando estado actual...")
    verificar_usuarios()
    
    print("\n🆕 Creando empleado simple...")
    crear_empleado_simple()
    
    print("\n🔐 Verificando credenciales...")
    verificar_credenciales() 