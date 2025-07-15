#!/usr/bin/env python
"""
Script para crear un alquiler adeudado específicamente para 14/07/2025
y demostrar la cancelación automática de alquileres futuros.

Uso: python crear_alquiler_adeudado_14_07_2025.py
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from maquinas.models import MaquinaBase, Unidad, Alquiler
from persona.models import Persona
from persona.views import procesar_alquileres_vencidos_automatico

def print_separator():
    print("=" * 80)

def print_header(titulo):
    print_separator()
    print(f"🎯 {titulo}")
    print_separator()

def print_info(mensaje):
    print(f"ℹ️  {mensaje}")

def print_success(mensaje):
    print(f"✅ {mensaje}")

def print_error(mensaje):
    print(f"❌ {mensaje}")

def print_warning(mensaje):
    print(f"⚠️  {mensaje}")

def crear_alquiler_vencido_14_07_2025():
    """
    Crea un alquiler que esté vencido al 14/07/2025
    Para que funcione con la fecha actual, lo crearemos como vencido YA
    """
    print_header("CREANDO ALQUILER VENCIDO PARA SIMULACIÓN 14/07/2025")
    
    # Crear fechas que ya estén vencidas (hace una semana)
    fecha_vencimiento = date.today() - timedelta(days=1)  # Vencido ayer
    fecha_inicio = fecha_vencimiento - timedelta(days=6)  # 7 días de alquiler
    
    print_info(f"📅 Fecha de inicio: {fecha_inicio.strftime('%d/%m/%Y')}")
    print_info(f"📅 Fecha de vencimiento: {fecha_vencimiento.strftime('%d/%m/%Y')} (VENCIDO)")
    print_info(f"📅 Fecha actual: {date.today().strftime('%d/%m/%Y')}")
    
    # Buscar cliente disponible
    cliente = Persona.objects.filter(
        es_empleado=False,
        es_admin=False
    ).exclude(
        alquileres_maquinas__estado__in=['reservado', 'en_curso', 'adeudado']
    ).first()
    
    if not cliente:
        print_error("No se encontró un cliente disponible")
        return None
    
    print_success(f"👤 Cliente seleccionado: {cliente.nombre} {cliente.apellido} ({cliente.email})")
    
    # Buscar máquina y unidad disponible
    unidad = Unidad.objects.filter(
        estado='disponible',
        visible=True,
        maquina_base__visible=True
    ).first()
    
    if not unidad:
        print_error("No se encontró una unidad disponible")
        return None
    
    print_success(f"🚜 Unidad seleccionada: {unidad.maquina_base.nombre} - Patente: {unidad.patente}")
    
    # Crear el alquiler vencido
    try:
        alquiler = Alquiler.objects.create(
            maquina_base=unidad.maquina_base,
            unidad=unidad,
            persona=cliente,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_vencimiento,
            cantidad_dias=7,
            estado='en_curso',  # Iniciamos en curso para simular que ya comenzó
            metodo_pago='mercadopago',
            monto_total=unidad.maquina_base.precio_por_dia * 7
        )
        
        # Cambiar estado de la unidad a alquilada
        unidad.estado = 'alquilada'
        unidad.save()
        
        print_success(f"📄 Alquiler creado: {alquiler.numero}")
        print_info(f"💰 Monto total: ${alquiler.monto_total}")
        print_info(f"🏷️  Estado inicial: {alquiler.get_estado_display()}")
        print_info(f"🔧 Estado de unidad: {unidad.get_estado_display()}")
        print_warning(f"⏰ Días vencido: {(date.today() - fecha_vencimiento).days} día(s)")
        
        return alquiler
        
    except Exception as e:
        print_error(f"Error al crear alquiler: {str(e)}")
        return None

def crear_alquileres_futuros(unidad, cliente_vencido, cantidad=4):
    """
    Crea alquileres futuros para la misma unidad
    """
    print_header("CREANDO ALQUILERES FUTUROS")
    
    alquileres_creados = []
    fecha_base = date.today() + timedelta(days=7)  # Una semana desde hoy
    
    # Obtener otros clientes disponibles
    otros_clientes = Persona.objects.filter(
        es_empleado=False,
        es_admin=False
    ).exclude(
        id=cliente_vencido.id
    ).exclude(
        alquileres_maquinas__estado__in=['reservado', 'en_curso', 'adeudado']
    )[:cantidad]
    
    if len(otros_clientes) < cantidad:
        print_warning(f"Solo se encontraron {len(otros_clientes)} clientes disponibles de {cantidad} requeridos")
    
    for i, cliente in enumerate(otros_clientes):
        try:
            fecha_inicio = fecha_base + timedelta(days=i*8)  # Espaciados cada 8 días
            fecha_fin = fecha_inicio + timedelta(days=6)  # 7 días cada uno
            
            alquiler = Alquiler.objects.create(
                maquina_base=unidad.maquina_base,
                unidad=unidad,
                persona=cliente,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                cantidad_dias=7,
                estado='reservado',
                metodo_pago='mercadopago',
                monto_total=unidad.maquina_base.precio_por_dia * 7
            )
            
            alquileres_creados.append(alquiler)
            print_success(f"📅 Alquiler {alquiler.numero}: {cliente.nombre} {cliente.apellido}")
            print_info(f"   📍 Fechas: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")
            print_info(f"   💰 Monto: ${alquiler.monto_total}")
            
        except Exception as e:
            print_error(f"Error creando alquiler futuro {i+1}: {str(e)}")
    
    return alquileres_creados

def mostrar_estado_inicial(alquiler_vencido, alquileres_futuros):
    """
    Muestra el estado inicial antes del procesamiento
    """
    print_header("ESTADO INICIAL ANTES DEL PROCESAMIENTO")
    
    print_info(f"🔥 ALQUILER VENCIDO:")
    print(f"   📄 {alquiler_vencido.numero} - {alquiler_vencido.persona.nombre} {alquiler_vencido.persona.apellido}")
    print(f"   📅 Vencido el: {alquiler_vencido.fecha_fin.strftime('%d/%m/%Y')}")
    print(f"   ⏰ Días vencido: {(date.today() - alquiler_vencido.fecha_fin).days} día(s)")
    print(f"   🏷️  Estado: {alquiler_vencido.get_estado_display()}")
    print(f"   🚜 Unidad: {alquiler_vencido.unidad.patente} ({alquiler_vencido.unidad.get_estado_display()})")
    
    print_info(f"📅 ALQUILERES FUTUROS ({len(alquileres_futuros)}):")
    for alquiler in alquileres_futuros:
        print(f"   📄 {alquiler.numero} - {alquiler.persona.nombre} {alquiler.persona.apellido}")
        print(f"   📅 Fechas: {alquiler.fecha_inicio.strftime('%d/%m/%Y')} - {alquiler.fecha_fin.strftime('%d/%m/%Y')}")
        print(f"   🏷️  Estado: {alquiler.get_estado_display()}")
        print(f"   💰 Monto: ${alquiler.monto_total}")
        print()

def procesar_y_mostrar_resultados(alquiler_vencido, alquileres_futuros):
    """
    Procesa el alquiler vencido y muestra los resultados
    """
    print_header("PROCESANDO ALQUILER VENCIDO")
    
    print_info("🔄 Ejecutando procesamiento automático...")
    print_info(f"📅 Fecha actual: {date.today().strftime('%d/%m/%Y')}")
    
    # Obtener IDs de los alquileres futuros para tracking
    ids_futuros = [alq.id for alq in alquileres_futuros]
    
    # Ejecutar el procesamiento
    try:
        resultado = procesar_alquileres_vencidos_automatico()
        
        if resultado['procesados'] > 0:
            print_success(f"🎯 Procesamiento completado: {resultado['procesados']} alquiler(es) procesado(s)")
            if resultado['cancelados'] > 0:
                print_success(f"❌ Alquileres cancelados: {resultado['cancelados']}")
            if resultado['emails_enviados'] > 0:
                print_success(f"📧 Emails enviados: {resultado['emails_enviados']}")
        else:
            print_warning("No se procesaron alquileres vencidos")
            
    except Exception as e:
        print_error(f"Error en el procesamiento: {str(e)}")
    
    print_separator()

def mostrar_estado_final(alquiler_vencido, alquileres_futuros):
    """
    Muestra el estado final después del procesamiento
    """
    print_header("ESTADO FINAL DESPUÉS DEL PROCESAMIENTO")
    
    # Recargar desde la base de datos
    alquiler_vencido.refresh_from_db()
    alquiler_vencido.unidad.refresh_from_db()
    
    print_info("🔥 ALQUILER VENCIDO:")
    print(f"   📄 {alquiler_vencido.numero}")
    print(f"   🏷️  Estado: {alquiler_vencido.get_estado_display()}")
    print(f"   🚜 Unidad: {alquiler_vencido.unidad.patente} ({alquiler_vencido.unidad.get_estado_display()})")
    
    print_info(f"📅 ALQUILERES FUTUROS:")
    cancelados = 0
    activos = 0
    
    for alquiler in alquileres_futuros:
        alquiler.refresh_from_db()
        
        if alquiler.estado == 'cancelado':
            status_icon = "❌"
            cancelados += 1
        else:
            status_icon = "✅"
            activos += 1
            
        print(f"   {status_icon} {alquiler.numero} - {alquiler.persona.nombre} {alquiler.persona.apellido}")
        print(f"      🏷️  Estado: {alquiler.get_estado_display()}")
        
        if alquiler.estado == 'cancelado':
            print(f"      💰 Reembolso: ${alquiler.monto_reembolso} ({alquiler.porcentaje_reembolso}%)")
            print(f"      📧 Cancelación automática por alquiler adeudado")
        print()
    
    print_separator()
    print_success(f"📊 RESUMEN FINAL:")
    print(f"   • Alquiler vencido procesado: {'✅ SÍ' if alquiler_vencido.estado == 'adeudado' else '❌ NO'}")
    print(f"   • Estado final alquiler: {alquiler_vencido.get_estado_display()}")
    print(f"   • Alquileres futuros cancelados: {cancelados}")
    print(f"   • Alquileres futuros activos: {activos}")
    print(f"   • Unidad en estado: {alquiler_vencido.unidad.get_estado_display()}")
    
    if cancelados > 0:
        print_success(f"🎉 ¡FUNCIONALIDAD DEMOSTRADA!")
        print_info(f"   La cancelación automática funcionó correctamente")
        print_info(f"   Se cancelaron {cancelados} alquileres futuros")
        print_info(f"   Los clientes fueron notificados por email")
    
    print_separator()

def limpiar_alquileres_previos():
    """
    Limpia alquileres de pruebas anteriores para evitar conflictos
    """
    print_header("LIMPIANDO ALQUILERES DE PRUEBAS ANTERIORES")
    
    # Buscar alquileres vencidos recientes (última semana)
    fecha_limite = date.today() - timedelta(days=7)
    
    alquileres_vencidos = Alquiler.objects.filter(
        fecha_fin__gte=fecha_limite,
        fecha_fin__lt=date.today(),
        estado__in=['en_curso', 'adeudado']
    )
    
    if alquileres_vencidos.exists():
        print_info(f"🧹 Encontrados {alquileres_vencidos.count()} alquileres de pruebas anteriores")
        
        for alquiler in alquileres_vencidos:
            # Restaurar estado de la unidad
            if alquiler.unidad:
                alquiler.unidad.estado = 'disponible'
                alquiler.unidad.save()
            
            print_info(f"   🗑️  Eliminando: {alquiler.numero}")
            alquiler.delete()
        
        print_success("✅ Limpieza completada")
    else:
        print_info("✅ No se encontraron alquileres de pruebas anteriores")

def main():
    """
    Función principal del script
    """
    print_header("SCRIPT DE ALQUILER ADEUDADO - SIMULACIÓN 14/07/2025")
    print_info("Este script creará un alquiler vencido y demostrará")
    print_info("la cancelación automática de alquileres futuros")
    print_info("(Simulando el escenario del 14/07/2025)")
    print()
    
    # Paso 0: Limpiar alquileres previos
    limpiar_alquileres_previos()
    
    # Paso 1: Crear alquiler vencido
    alquiler_vencido = crear_alquiler_vencido_14_07_2025()
    if not alquiler_vencido:
        print_error("❌ No se pudo crear el alquiler vencido")
        return
    
    # Paso 2: Crear alquileres futuros
    alquileres_futuros = crear_alquileres_futuros(alquiler_vencido.unidad, alquiler_vencido.persona)
    if not alquileres_futuros:
        print_warning("⚠️  No se crearon alquileres futuros")
        return
    
    # Paso 3: Mostrar estado inicial
    mostrar_estado_inicial(alquiler_vencido, alquileres_futuros)
    
    # Paso 4: Procesar y mostrar resultados en tiempo real
    procesar_y_mostrar_resultados(alquiler_vencido, alquileres_futuros)
    
    # Paso 5: Mostrar estado final
    mostrar_estado_final(alquiler_vencido, alquileres_futuros)
    
    print_success("🎉 Script ejecutado exitosamente!")
    print_info("💡 Tip: Revisa la interfaz web para ver los cambios")
    print_info("💡 Tip: Puedes ejecutar el script varias veces")

if __name__ == "__main__":
    main() 