#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from maquinas.models import CalificacionCliente, Alquiler
from persona.models import Persona
from django.contrib.auth.models import User

def test_calificaciones():
    print("=== PROBANDO SISTEMA DE CALIFICACIONES ===")
    
    # Buscar un cliente que tenga alquileres finalizados
    clientes_con_alquileres = Persona.objects.filter(
        alquileres_maquinas__estado='finalizado',
        es_cliente=True
    ).distinct()
    
    print(f"Clientes con alquileres finalizados: {clientes_con_alquileres.count()}")
    
    for cliente in clientes_con_alquileres[:3]:  # Solo los primeros 3
        print(f"\n--- Cliente: {cliente.nombre} {cliente.apellido} ---")
        print(f"Calificación actual: {cliente.calificacion_promedio}")
        
        # Ver sus alquileres finalizados
        alquileres_finalizados = cliente.alquileres_maquinas.filter(estado='finalizado')
        print(f"Alquileres finalizados: {alquileres_finalizados.count()}")
        
        # Ver calificaciones existentes
        calificaciones_existentes = CalificacionCliente.objects.filter(cliente=cliente)
        print(f"Calificaciones existentes: {calificaciones_existentes.count()}")
        
        for cal in calificaciones_existentes:
            print(f"  - Alquiler {cal.alquiler.numero}: {cal.calificacion} estrellas")
        
        # Calcular promedio manual
        if calificaciones_existentes.exists():
            promedio_manual = sum(c.calificacion for c in calificaciones_existentes) / calificaciones_existentes.count()
            print(f"Promedio manual: {promedio_manual:.2f}")
            print(f"Promedio en BD: {cliente.calificacion_promedio}")
            
            if abs(float(cliente.calificacion_promedio) - promedio_manual) > 0.01:
                print("❌ EL PROMEDIO NO COINCIDE - ACTUALIZANDO...")
                cliente.calificacion_promedio = round(promedio_manual, 2)
                cliente.save()
                print(f"✅ Promedio actualizado a: {cliente.calificacion_promedio}")
            else:
                print("✅ Promedio correcto")

if __name__ == "__main__":
    test_calificaciones() 