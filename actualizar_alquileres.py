#!/usr/bin/env python
"""
Script para actualizar los alquileres existentes con el campo cantidad_dias
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from maquinas.models import Alquiler

def actualizar_cantidad_dias():
    """Actualizar campo cantidad_dias para alquileres existentes"""
    alquileres = Alquiler.objects.filter(cantidad_dias=1)  # Los que tienen el valor por defecto
    
    print(f"Encontrados {alquileres.count()} alquileres para actualizar...")
    
    for alquiler in alquileres:
        if alquiler.fecha_inicio and alquiler.fecha_fin:
            dias_calculados = (alquiler.fecha_fin - alquiler.fecha_inicio).days + 1
            if dias_calculados != alquiler.cantidad_dias:
                alquiler.cantidad_dias = dias_calculados
                alquiler.save()
                print(f"Actualizado alquiler {alquiler.numero}: {dias_calculados} días")
    
    print("Actualización completada!")

if __name__ == '__main__':
    actualizar_cantidad_dias() 