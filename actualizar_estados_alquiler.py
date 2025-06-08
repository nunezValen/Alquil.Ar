#!/usr/bin/env python
"""
Script para actualizar los estados de alquileres existentes
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from maquinas.models import Alquiler

def actualizar_estados():
    """Actualizar estados de alquileres existentes"""
    # Mapear estados antiguos a nuevos
    mapeo_estados = {
        'pendiente': 'reservado',
        'confirmado': 'reservado',
        # 'en_curso' se mantiene igual
        # 'finalizado' se mantiene igual
        'cancelado': 'cancelado'
    }
    
    print("Actualizando estados de alquileres...")
    
    total_actualizados = 0
    
    for estado_antiguo, estado_nuevo in mapeo_estados.items():
        alquileres = Alquiler.objects.filter(estado=estado_antiguo)
        count = alquileres.count()
        
        if count > 0:
            alquileres.update(estado=estado_nuevo)
            print(f"Actualizados {count} alquileres de '{estado_antiguo}' a '{estado_nuevo}'")
            total_actualizados += count
    
    # Generar códigos de retiro para alquileres que no los tengan
    alquileres_sin_codigo = Alquiler.objects.filter(codigo_retiro__isnull=True)
    count_sin_codigo = alquileres_sin_codigo.count()
    
    if count_sin_codigo > 0:
        import random
        import string
        
        for alquiler in alquileres_sin_codigo:
            alquiler.codigo_retiro = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            alquiler.save()
        
        print(f"Generados códigos de retiro para {count_sin_codigo} alquileres")
        total_actualizados += count_sin_codigo
    
    print(f"Actualización completada! Total de cambios: {total_actualizados}")

if __name__ == '__main__':
    actualizar_estados() 