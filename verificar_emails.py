#!/usr/bin/env python
"""
Script para verificar que el sistema de emails esté funcionando correctamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from django.conf import settings
from maquinas.models import Alquiler
from maquinas.utils import enviar_email_alquiler_simple
from django.core.mail import send_mail

def verificar_configuracion_email():
    """Verificar la configuración de email"""
    print("=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN DE EMAIL")
    print("=" * 60)
    
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD)}")
    print()

def test_email_simple():
    """Probar envío de email simple"""
    print("=" * 60)
    print("PRUEBA DE EMAIL SIMPLE")
    print("=" * 60)
    
    try:
        send_mail(
            'Test de Sistema ALQUIL.AR',
            'Este es un email de prueba del sistema ALQUIL.AR.',
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],  # Enviar a la misma cuenta
            fail_silently=False,
        )
        print("[SUCCESS] Email simple enviado correctamente")
        return True
    except Exception as e:
        print(f"[ERROR] Error al enviar email simple: {str(e)}")
        return False

def test_email_alquiler():
    """Probar envío de email de alquiler"""
    print("=" * 60)
    print("PRUEBA DE EMAIL DE ALQUILER")
    print("=" * 60)
    
    try:
        # Obtener el último alquiler
        alquiler = Alquiler.objects.order_by('-id').first()
        
        if not alquiler:
            print("[WARNING] No hay alquileres en el sistema para probar")
            return False
        
        print(f"Probando con alquiler: {alquiler.numero}")
        print(f"Email destino: {alquiler.persona.email}")
        
        # Intentar enviar el email
        resultado = enviar_email_alquiler_simple(alquiler)
        
        if resultado:
            print("[SUCCESS] Email de alquiler enviado correctamente")
            return True
        else:
            print("[ERROR] Falló el envío del email de alquiler")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error al probar email de alquiler: {str(e)}")
        return False

def main():
    """Función principal"""
    print("\n🔧 VERIFICADOR DE SISTEMA DE EMAILS - ALQUIL.AR")
    print("Este script verifica que el sistema de emails esté funcionando correctamente")
    print()
    
    # Verificar configuración
    verificar_configuracion_email()
    
    # Probar email simple
    test_simple_ok = test_email_simple()
    
    # Probar email de alquiler
    test_alquiler_ok = test_email_alquiler()
    
    # Resumen final
    print("=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"Configuración de email: [OK]")
    print(f"Email simple: [{'OK' if test_simple_ok else 'ERROR'}]")
    print(f"Email de alquiler: [{'OK' if test_alquiler_ok else 'ERROR'}]")
    print()
    
    if test_simple_ok and test_alquiler_ok:
        print("[SUCCESS] ¡Todos los tests pasaron! El sistema de emails está funcionando correctamente.")
        print()
        print("SOLUCIÓN AL PROBLEMA:")
        print("- El problema era que los emojis en los mensajes de print() no se podían")
        print("  codificar en la consola de Windows (error 'charmap' codec)")
        print("- Se reemplazaron todos los emojis por etiquetas de texto: [INFO], [SUCCESS], [ERROR]")
        print("- Ahora el sistema de emails funciona sin problemas")
    else:
        print("[ERROR] Algunos tests fallaron. Revisa la configuración de emails.")
        
    print()
    print("💡 TIPS PARA EL FUTURO:")
    print("- Evita usar emojis en mensajes de print() en Windows")
    print("- Si necesitas emojis, configura la consola para UTF-8")
    print("- Los emails HTML pueden usar emojis sin problemas")
    print()

if __name__ == "__main__":
    main() 