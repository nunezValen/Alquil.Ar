#!/usr/bin/env python
"""
Script para actualizar alquileres existentes con los nuevos campos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from maquinas.models import Alquiler
import string
import random

def actualizar_alquileres():
    """Actualizar alquileres existentes con cantidad_dias y codigo_retiro"""
    
    alquileres = Alquiler.objects.all()
    actualizados = 0
    
    print(f"Encontrados {alquileres.count()} alquileres para actualizar...")
    
    for alquiler in alquileres:
        actualizado = False
        
        # Actualizar cantidad_dias si no está establecido
        if not alquiler.cantidad_dias or alquiler.cantidad_dias == 1:
            if alquiler.fecha_inicio and alquiler.fecha_fin:
                alquiler.cantidad_dias = (alquiler.fecha_fin - alquiler.fecha_inicio).days + 1
                actualizado = True
                print(f"Alquiler {alquiler.numero}: cantidad_dias = {alquiler.cantidad_dias}")
        
        # Generar codigo_retiro si no existe
        if not alquiler.codigo_retiro:
            while True:
                codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Alquiler.objects.filter(codigo_retiro=codigo).exists():
                    alquiler.codigo_retiro = codigo
                    actualizado = True
                    print(f"Alquiler {alquiler.numero}: codigo_retiro = {alquiler.codigo_retiro}")
                    break
        
        # Actualizar monto_total si no está establecido
        if not alquiler.monto_total and alquiler.maquina_base and alquiler.cantidad_dias:
            alquiler.monto_total = alquiler.maquina_base.precio_por_dia * alquiler.cantidad_dias
            actualizado = True
            print(f"Alquiler {alquiler.numero}: monto_total = ${alquiler.monto_total}")
        
        # Asignar unidad si no tiene una
        if not alquiler.unidad and alquiler.maquina_base:
            if alquiler.asignar_unidad_disponible():
                actualizado = True
                print(f"Alquiler {alquiler.numero}: unidad asignada = {alquiler.unidad.patente}")
        
        if actualizado:
            alquiler.save()
            actualizados += 1
    
    print(f"\n✅ Proceso completado. {actualizados} alquileres actualizados.")
    
    # Mostrar resumen
    print("\n📊 RESUMEN DE ALQUILERES:")
    print(f"Total de alquileres: {Alquiler.objects.count()}")
    print(f"Reservados: {Alquiler.objects.filter(estado='reservado').count()}")
    print(f"En curso: {Alquiler.objects.filter(estado='en_curso').count()}")
    print(f"Finalizados: {Alquiler.objects.filter(estado='finalizado').count()}")
    print(f"Cancelados: {Alquiler.objects.filter(estado='cancelado').count()}")

if __name__ == '__main__':
    actualizar_alquileres() 