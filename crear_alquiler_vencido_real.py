#!/usr/bin/env python
"""
Script para crear un alquiler vencido que funcione con la fecha actual
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from maquinas.models import Alquiler, MaquinaBase, Unidad
from persona.models import Persona

def crear_alquiler_reservado_vencido():
    """Crear un alquiler reservado vencido (que nunca se retiró)"""
    
    # Buscar una máquina base
    maquina_base = MaquinaBase.objects.first()
    if not maquina_base:
        print("❌ No hay máquinas base disponibles")
        return
    
    # Buscar una unidad disponible
    unidad = Unidad.objects.filter(maquina_base=maquina_base, estado='disponible').first()
    if not unidad:
        print("❌ No hay unidades disponibles")
        return
    
    # Buscar una persona
    persona = Persona.objects.filter(es_empleado=False).first()
    if not persona:
        print("❌ No hay personas disponibles")
        return
    
    # Crear fechas: que haya comenzado hace 2 días (para fecha de inicio vencida)
    fecha_actual = date.today()
    fecha_inicio = fecha_actual - timedelta(days=2)  # Hace 2 días
    fecha_fin = fecha_inicio + timedelta(days=1)     # 1 día de duración
    
    try:
        # Crear el alquiler reservado vencido
        alquiler = Alquiler.objects.create(
            maquina_base=maquina_base,
            unidad=unidad,
            persona=persona,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            cantidad_dias=2,
            estado='reservado',  # Reservado pero nunca se retiró
            metodo_pago='mercadopago',
            monto_total=maquina_base.precio_por_dia * 2
        )
        
        print(f"✅ Alquiler reservado vencido creado exitosamente:")
        print(f"   - Número: {alquiler.numero}")
        print(f"   - Cliente: {alquiler.persona.nombre} {alquiler.persona.apellido}")
        print(f"   - Máquina: {alquiler.maquina_base.nombre}")
        print(f"   - Unidad: {alquiler.unidad.patente}")
        print(f"   - Fecha inicio: {alquiler.fecha_inicio} (hace {(fecha_actual - fecha_inicio).days} días)")
        print(f"   - Fecha fin: {alquiler.fecha_fin}")
        print(f"   - Estado: {alquiler.estado}")
        print(f"   - Debería cancelarse automáticamente por no retirar")
        
    except Exception as e:
        print(f"❌ Error creando alquiler vencido: {str(e)}")

def crear_alquiler_en_curso_vencido():
    """Crear un alquiler en curso vencido (que no se devolvió)"""
    
    # Buscar una máquina base
    maquina_base = MaquinaBase.objects.first()
    if not maquina_base:
        print("❌ No hay máquinas base disponibles")
        return
    
    # Buscar una unidad disponible
    unidad = Unidad.objects.filter(maquina_base=maquina_base, estado='disponible').first()
    if not unidad:
        print("❌ No hay unidades disponibles")
        return
    
    # Buscar una persona
    persona = Persona.objects.filter(es_empleado=False).first()
    if not persona:
        print("❌ No hay personas disponibles")
        return
    
    # Crear fechas: que haya terminado hace 1 día (para fecha de fin vencida)
    fecha_actual = date.today()
    fecha_fin = fecha_actual - timedelta(days=1)     # Terminó ayer
    fecha_inicio = fecha_fin - timedelta(days=1)     # Comenzó hace 2 días
    
    try:
        # Crear el alquiler en curso vencido
        alquiler = Alquiler.objects.create(
            maquina_base=maquina_base,
            unidad=unidad,
            persona=persona,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            cantidad_dias=2,
            estado='en_curso',  # En curso pero ya venció
            metodo_pago='mercadopago',
            monto_total=maquina_base.precio_por_dia * 2
        )
        
        print(f"✅ Alquiler en curso vencido creado exitosamente:")
        print(f"   - Número: {alquiler.numero}")
        print(f"   - Cliente: {alquiler.persona.nombre} {alquiler.persona.apellido}")
        print(f"   - Máquina: {alquiler.maquina_base.nombre}")
        print(f"   - Unidad: {alquiler.unidad.patente}")
        print(f"   - Fecha inicio: {alquiler.fecha_inicio}")
        print(f"   - Fecha fin: {alquiler.fecha_fin} (hace {(fecha_actual - fecha_fin).days} días)")
        print(f"   - Estado: {alquiler.estado}")
        print(f"   - Debería marcarse como adeudado automáticamente")
        
    except Exception as e:
        print(f"❌ Error creando alquiler vencido: {str(e)}")

if __name__ == '__main__':
    print("Creando alquileres de prueba vencidos...")
    print("\n1. Alquiler reservado que nunca se retiró:")
    crear_alquiler_reservado_vencido()
    print("\n2. Alquiler en curso que no se devolvió:")
    crear_alquiler_en_curso_vencido() 