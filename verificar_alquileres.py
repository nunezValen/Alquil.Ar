#!/usr/bin/env python
"""
Script para verificar alquileres en la base de datos
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from maquinas.models import Alquiler
from persona.models import Persona

def verificar_alquileres():
    """Verificar los alquileres en la base de datos"""
    
    print("=== VERIFICANDO ALQUILERES EN LA BASE DE DATOS ===")
    
    # Contar total de alquileres
    total_alquileres = Alquiler.objects.count()
    print(f"Total de alquileres: {total_alquileres}")
    
    if total_alquileres == 0:
        print("❌ No hay alquileres en la base de datos")
        return
    
    # Mostrar últimos 5 alquileres
    print(f"\n=== ÚLTIMOS 5 ALQUILERES ===")
    alquileres = Alquiler.objects.all().order_by('-fecha_creacion')[:5]
    
    for alquiler in alquileres:
        print(f"ID: {alquiler.id}")
        print(f"Número: {alquiler.numero}")
        print(f"Cliente: {alquiler.persona.nombre} {alquiler.persona.apellido}")
        print(f"Email: {alquiler.persona.email}")
        print(f"Máquina: {alquiler.maquina_base.nombre}")
        print(f"Estado: {alquiler.estado}")
        print(f"Fecha inicio: {alquiler.fecha_inicio}")
        print(f"Fecha fin: {alquiler.fecha_fin}")
        print(f"Monto: ${alquiler.monto_total}")
        print(f"Código retiro: {alquiler.codigo_retiro}")
        print(f"Fecha creación: {alquiler.fecha_creacion}")
        print("-" * 50)
    
    # Estadísticas por estado
    print(f"\n=== ESTADÍSTICAS POR ESTADO ===")
    estados = Alquiler.objects.values_list('estado', flat=True).distinct()
    for estado in estados:
        cantidad = Alquiler.objects.filter(estado=estado).count()
        print(f"{estado}: {cantidad} alquileres")
    
    # Verificar personas
    print(f"\n=== VERIFICANDO PERSONAS ===")
    total_personas = Persona.objects.count()
    print(f"Total de personas: {total_personas}")
    
    if total_personas > 0:
        print(f"Últimas 3 personas registradas:")
        personas = Persona.objects.all().order_by('-fecha_registro')[:3]
        for persona in personas:
            print(f"- {persona.nombre} {persona.apellido} ({persona.email})")
            print(f"  Cliente: {persona.es_cliente}, Empleado: {persona.es_empleado}")

if __name__ == "__main__":
    verificar_alquileres() 