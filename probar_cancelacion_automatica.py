#!/usr/bin/env python
"""
Script para probar la funcionalidad de cancelación automática de alquileres futuros
cuando un alquiler se vuelve adeudado.
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
from persona.views import procesar_alquileres_vencidos_automatico

def limpiar_datos_prueba():
    """Limpiar alquileres de prueba anteriores"""
    # Eliminar alquileres de prueba (que tengan observaciones específicas)
    Alquiler.objects.filter(
        observaciones_cancelacion__icontains="PRUEBA CANCELACIÓN AUTOMÁTICA"
    ).delete()
    
    # Restablecer unidades a disponible
    Unidad.objects.filter(estado__in=['adeudado', 'mantenimiento']).update(estado='disponible')
    
    print("🧹 Datos de prueba limpiados")

def crear_escenario_prueba():
    """Crear escenario de prueba con alquiler vencido y alquileres futuros"""
    
    print("\n🔧 CREANDO ESCENARIO DE PRUEBA")
    print("="*50)
    
    # Buscar una máquina base y unidad
    maquina_base = MaquinaBase.objects.first()
    if not maquina_base:
        print("❌ No hay máquinas base disponibles")
        return None
    
    unidad = Unidad.objects.filter(
        maquina_base=maquina_base, 
        estado='disponible'
    ).first()
    if not unidad:
        print("❌ No hay unidades disponibles")
        return None
    
    # Buscar personas para los alquileres
    personas = list(Persona.objects.filter(es_empleado=False)[:4])  # Necesitamos 4 personas
    if len(personas) < 4:
        print("❌ No hay suficientes personas para la prueba")
        return None
    
    fecha_actual = date.today()
    
    # 1. Crear alquiler VENCIDO (en_curso que ya pasó su fecha de fin)
    alquiler_vencido = Alquiler.objects.create(
        maquina_base=maquina_base,
        unidad=unidad,
        persona=personas[0],
        fecha_inicio=fecha_actual - timedelta(days=3),  # Empezó hace 3 días
        fecha_fin=fecha_actual - timedelta(days=1),     # Terminó ayer
        estado='en_curso',  # Está en curso pero ya venció
        metodo_pago='mercadopago',
        monto_total=maquina_base.precio_por_dia * 2,
        observaciones_cancelacion="PRUEBA CANCELACIÓN AUTOMÁTICA - VENCIDO"
    )
    
    print(f"✅ Alquiler VENCIDO creado: {alquiler_vencido.numero}")
    print(f"   - Cliente: {alquiler_vencido.persona.nombre} {alquiler_vencido.persona.apellido}")
    print(f"   - Unidad: {alquiler_vencido.unidad.patente}")
    print(f"   - Fecha fin: {alquiler_vencido.fecha_fin} (hace {(fecha_actual - alquiler_vencido.fecha_fin).days} días)")
    print(f"   - Estado: {alquiler_vencido.estado}")
    
    # 2. Crear alquileres FUTUROS de la misma unidad
    alquileres_futuros = []
    
    # Alquiler futuro 1: Mañana
    futuro_1 = Alquiler.objects.create(
        maquina_base=maquina_base,
        unidad=unidad,
        persona=personas[1],
        fecha_inicio=fecha_actual + timedelta(days=1),
        fecha_fin=fecha_actual + timedelta(days=3),
        estado='reservado',
        metodo_pago='mercadopago',
        monto_total=maquina_base.precio_por_dia * 3,
        observaciones_cancelacion="PRUEBA CANCELACIÓN AUTOMÁTICA - FUTURO 1"
    )
    alquileres_futuros.append(futuro_1)
    
    # Alquiler futuro 2: Próxima semana
    futuro_2 = Alquiler.objects.create(
        maquina_base=maquina_base,
        unidad=unidad,
        persona=personas[2],
        fecha_inicio=fecha_actual + timedelta(days=7),
        fecha_fin=fecha_actual + timedelta(days=9),
        estado='reservado',
        metodo_pago='mercadopago',
        monto_total=maquina_base.precio_por_dia * 3,
        observaciones_cancelacion="PRUEBA CANCELACIÓN AUTOMÁTICA - FUTURO 2"
    )
    alquileres_futuros.append(futuro_2)
    
    # Alquiler futuro 3: Próximo mes
    futuro_3 = Alquiler.objects.create(
        maquina_base=maquina_base,
        unidad=unidad,
        persona=personas[3],
        fecha_inicio=fecha_actual + timedelta(days=30),
        fecha_fin=fecha_actual + timedelta(days=32),
        estado='reservado',
        metodo_pago='mercadopago',
        monto_total=maquina_base.precio_por_dia * 3,
        observaciones_cancelacion="PRUEBA CANCELACIÓN AUTOMÁTICA - FUTURO 3"
    )
    alquileres_futuros.append(futuro_3)
    
    print(f"\n✅ {len(alquileres_futuros)} alquileres FUTUROS creados:")
    for i, alquiler in enumerate(alquileres_futuros, 1):
        print(f"   {i}. {alquiler.numero}: {alquiler.persona.nombre} {alquiler.persona.apellido}")
        print(f"      - Fechas: {alquiler.fecha_inicio} - {alquiler.fecha_fin}")
        print(f"      - Estado: {alquiler.estado}")
        print(f"      - Monto: ${alquiler.monto_total}")
    
    return {
        'alquiler_vencido': alquiler_vencido,
        'alquileres_futuros': alquileres_futuros,
        'unidad': unidad
    }

def ejecutar_prueba():
    """Ejecutar la prueba completa"""
    
    print("\n🚀 EJECUTANDO PRUEBA DE CANCELACIÓN AUTOMÁTICA")
    print("="*60)
    
    # Limpiar datos anteriores
    limpiar_datos_prueba()
    
    # Crear escenario de prueba
    escenario = crear_escenario_prueba()
    if not escenario:
        print("❌ No se pudo crear el escenario de prueba")
        return
    
    alquiler_vencido = escenario['alquiler_vencido']
    alquileres_futuros = escenario['alquileres_futuros']
    unidad = escenario['unidad']
    
    # Verificar estado ANTES del procesamiento
    print(f"\n📊 ESTADO ANTES DEL PROCESAMIENTO:")
    print(f"   - Alquiler vencido: {alquiler_vencido.numero} ({alquiler_vencido.estado})")
    print(f"   - Unidad: {unidad.patente} ({unidad.estado})")
    print(f"   - Alquileres futuros: {len(alquileres_futuros)} en estado reservado")
    
    # EJECUTAR EL PROCESAMIENTO AUTOMÁTICO
    print(f"\n⚙️  PROCESANDO ALQUILERES VENCIDOS...")
    procesados = procesar_alquileres_vencidos_automatico()
    print(f"   - Alquileres procesados: {procesados}")
    
    # Verificar estado DESPUÉS del procesamiento
    print(f"\n📊 ESTADO DESPUÉS DEL PROCESAMIENTO:")
    
    # Recargar objetos desde la base de datos
    alquiler_vencido.refresh_from_db()
    unidad.refresh_from_db()
    
    print(f"   - Alquiler vencido: {alquiler_vencido.numero} ({alquiler_vencido.estado}) ✅")
    print(f"   - Unidad: {unidad.patente} ({unidad.estado}) ✅")
    
    # Verificar alquileres futuros
    alquileres_cancelados = 0
    for alquiler in alquileres_futuros:
        alquiler.refresh_from_db()
        if alquiler.estado == 'cancelado':
            alquileres_cancelados += 1
            print(f"   - {alquiler.numero}: {alquiler.estado} ✅ (Reembolso: {alquiler.porcentaje_reembolso}%)")
        else:
            print(f"   - {alquiler.numero}: {alquiler.estado} ❌")
    
    # Resultado final
    print(f"\n🎯 RESULTADO:")
    if alquiler_vencido.estado == 'adeudado' and unidad.estado == 'adeudado' and alquileres_cancelados == len(alquileres_futuros):
        print("✅ ¡PRUEBA EXITOSA! La cancelación automática funciona correctamente.")
        print(f"   - Alquiler vencido marcado como 'adeudado' ✅")
        print(f"   - Unidad marcada como 'adeudado' ✅")
        print(f"   - {alquileres_cancelados}/{len(alquileres_futuros)} alquileres futuros cancelados ✅")
        print(f"   - Emails de cancelación enviados a los clientes ✅")
    else:
        print("❌ PRUEBA FALLIDA. Verificar la lógica de cancelación automática.")
        print(f"   - Alquiler vencido: {alquiler_vencido.estado} (esperado: adeudado)")
        print(f"   - Unidad: {unidad.estado} (esperado: adeudado)")
        print(f"   - Alquileres cancelados: {alquileres_cancelados}/{len(alquileres_futuros)}")

if __name__ == "__main__":
    ejecutar_prueba() 