#!/usr/bin/env python
"""
Script para cargar datos de prueba para testear las estadísticas.
Carga múltiples máquinas base y genera alquileres con diferentes fechas y cantidades.
"""
import os
import sys
import django
import random
from datetime import date, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from maquinas.models import MaquinaBase, Unidad, Alquiler
from persona.models import Persona, Sucursal

def cargar_maquinas_prueba():
    """Crear múltiples máquinas base con datos variados"""
    
    print("=== CARGANDO MÁQUINAS DE PRUEBA ===")
    
    # Lista de máquinas a crear
    maquinas_data = [
        {
            'nombre': 'Excavadora CAT 320',
            'tipo': 'excavadora',
            'marca': 'caterpillar',
            'modelo': '320GL',
            'precio_por_dia': Decimal('15000.00'),
            'descripcion_corta': 'Excavadora hidráulica de alta potencia para trabajos pesados de excavación.',
            'descripcion_larga': 'Excavadora hidráulica Caterpillar 320GL con motor de alta eficiencia, sistema hidráulico avanzado y cabina ergonómica. Ideal para excavación, demolición y manejo de materiales.',
            'dias_alquiler_min': 1,
            'dias_alquiler_max': 30,
        },
        {
            'nombre': 'Retroexcavadora JCB 3CX',
            'tipo': 'retroexcavadora',
            'marca': 'jcb',
            'modelo': '3CX-14',
            'precio_por_dia': Decimal('12000.00'),
            'descripcion_corta': 'Retroexcavadora versátil para múltiples aplicaciones en construcción.',
            'descripcion_larga': 'Retroexcavadora JCB 3CX con tracción en las 4 ruedas, brazo extensible y cargador frontal. Perfecta para obras de construcción, excavación y carga de materiales.',
            'dias_alquiler_min': 1,
            'dias_alquiler_max': 25,
        },
        {
            'nombre': 'Cargadora Frontal Volvo L60H',
            'tipo': 'cargadora',
            'marca': 'volvo',
            'modelo': 'L60H',
            'precio_por_dia': Decimal('10000.00'),
            'descripcion_corta': 'Cargadora frontal compacta y eficiente para carga y transporte.',
            'descripcion_larga': 'Cargadora frontal Volvo L60H con motor de bajo consumo, sistema de dirección articulada y balde de alta capacidad. Ideal para trabajos de carga y movimiento de materiales.',
            'dias_alquiler_min': 1,
            'dias_alquiler_max': 20,
        },
        {
            'nombre': 'Compactadora Dynapac CA2500',
            'tipo': 'compactadora',
            'marca': 'case',
            'modelo': 'CA2500',
            'precio_por_dia': Decimal('8000.00'),
            'descripcion_corta': 'Compactadora de rodillo vibratorio para compactación de suelos.',
            'descripcion_larga': 'Compactadora de rodillo vibratorio Dynapac CA2500 con sistema de vibración avanzado y control de compactación. Perfecta para pavimentación y compactación de bases.',
            'dias_alquiler_min': 1,
            'dias_alquiler_max': 15,
        },
        {
            'nombre': 'Motoniveladora Komatsu GD555',
            'tipo': 'motoniveladora',
            'marca': 'komatsu',
            'modelo': 'GD555-5',
            'precio_por_dia': Decimal('18000.00'),
            'descripcion_corta': 'Motoniveladora de precisión para nivelación y acabado de superficies.',
            'descripcion_larga': 'Motoniveladora Komatsu GD555 con cuchilla de alta precisión, sistema de control avanzado y transmisión automática. Ideal para trabajos de nivelación y mantenimiento de caminos.',
            'dias_alquiler_min': 2,
            'dias_alquiler_max': 30,
        },
        {
            'nombre': 'Grúa Móvil Liebherr LTM1030',
            'tipo': 'grua',
            'marca': 'liebherr',
            'modelo': 'LTM1030-2.1',
            'precio_por_dia': Decimal('25000.00'),
            'descripcion_corta': 'Grúa móvil de 30 toneladas para trabajos de elevación y montaje.',
            'descripcion_larga': 'Grúa móvil Liebherr LTM1030 con capacidad de 30 toneladas, pluma telescópica y estabilizadores automáticos. Perfecta para montaje de estructuras y trabajos de elevación.',
            'dias_alquiler_min': 1,
            'dias_alquiler_max': 10,
        },
        {
            'nombre': 'Hormigonera Automezcla Volumétrica',
            'tipo': 'hormigonera',
            'marca': 'volvo',
            'modelo': 'VM-8',
            'precio_por_dia': Decimal('14000.00'),
            'descripcion_corta': 'Camión hormigonera con sistema de mezclado volumétrico.',
            'descripcion_larga': 'Hormigonera automezcla con sistema volumétrico que permite producir hormigón fresco en obra. Capacidad de 8m³ y sistema de descarga por canaleta.',
            'dias_alquiler_min': 1,
            'dias_alquiler_max': 5,
        },
        {
            'nombre': 'Dumper Articulado Volvo A25G',
            'tipo': 'dumper',
            'marca': 'volvo',
            'modelo': 'A25G',
            'precio_por_dia': Decimal('16000.00'),
            'descripcion_corta': 'Dumper articulado de alta capacidad para transporte en terrenos difíciles.',
            'descripcion_larga': 'Dumper articulado Volvo A25G con tracción 6x6, suspensión independiente y tolva basculante. Ideal para transporte de materiales en terrenos complicados.',
            'dias_alquiler_min': 1,
            'dias_alquiler_max': 20,
        },
        {
            'nombre': 'Manipulador Telescópico JCB 540-170',
            'tipo': 'manipulador',
            'marca': 'jcb',
            'modelo': '540-170',
            'precio_por_dia': Decimal('11000.00'),
            'descripcion_corta': 'Manipulador telescópico versátil para carga y elevación.',
            'descripcion_larga': 'Manipulador telescópico JCB 540-170 con brazo telescópico de 17m, sistema de estabilización y múltiples accesorios. Perfecto para construcción y almacenes.',
            'dias_alquiler_min': 1,
            'dias_alquiler_max': 15,
        },
        {
            'nombre': 'Excavadora Compacta Kubota KX080',
            'tipo': 'excavadora',
            'marca': 'kubota',
            'modelo': 'KX080-4',
            'precio_por_dia': Decimal('9000.00'),
            'descripcion_corta': 'Excavadora compacta ideal para espacios reducidos.',
            'descripcion_larga': 'Excavadora compacta Kubota KX080 con radio de giro cero, brazo extensible y múltiples accesorios. Ideal para trabajos en espacios confinados y obras urbanas.',
            'dias_alquiler_min': 1,
            'dias_alquiler_max': 15,
        },
        {
            'nombre': 'Pavimentadora Bituminosa Vogele S1900',
            'tipo': 'pavimentadora',
            'marca': 'case',
            'modelo': 'S1900-3L',
            'precio_por_dia': Decimal('22000.00'),
            'descripcion_corta': 'Pavimentadora de asfalto para trabajos de pavimentación.',
            'descripcion_larga': 'Pavimentadora Vogele S1900 con regla extensible, sistema de calefacción y control automático de espesor. Perfecta para pavimentación de carreteras y calles.',
            'dias_alquiler_min': 3,
            'dias_alquiler_max': 20,
        },
        {
            'nombre': 'Cargadora Compacta Doosan SSL75',
            'tipo': 'cargadora',
            'marca': 'doosan',
            'modelo': 'SSL75',
            'precio_por_dia': Decimal('7500.00'),
            'descripcion_corta': 'Cargadora compacta de dirección deslizante para trabajos precisos.',
            'descripcion_larga': 'Cargadora compacta Doosan SSL75 con dirección deslizante, sistema de acoplamiento rápido y alta maniobrabilidad. Ideal para trabajos de paisajismo y construcción menor.',
            'dias_alquiler_min': 1,
            'dias_alquiler_max': 10,
        },
    ]
    
    maquinas_creadas = []
    
    for data in maquinas_data:
        # Verificar si ya existe una máquina con ese nombre
        if not MaquinaBase.objects.filter(nombre=data['nombre']).exists():
            maquina = MaquinaBase.objects.create(**data)
            maquinas_creadas.append(maquina)
            print(f"[OK] Creada: {maquina.nombre}")
        else:
            print(f"[INFO] Ya existe: {data['nombre']}")
    
    print(f"\nSe crearon {len(maquinas_creadas)} máquinas nuevas")
    return maquinas_creadas

def crear_unidades_para_maquinas():
    """Crear unidades para las máquinas que no tienen"""
    
    print("\n=== CREANDO UNIDADES ===")
    
    # Obtener todas las sucursales
    sucursales = list(Sucursal.objects.filter(es_visible=True))
    if not sucursales:
        print("No hay sucursales disponibles")
        return
    
    maquinas_sin_unidades = MaquinaBase.objects.filter(unidades__isnull=True)
    
    contador = 1000  # Para generar patentes únicas
    
    for maquina in maquinas_sin_unidades:
        # Crear 1-3 unidades por máquina
        num_unidades = random.randint(1, 3)
        
        for i in range(num_unidades):
            patente = f"AB{contador:03d}CD"
            contador += 1
            
            # Verificar que la patente no exista
            while Unidad.objects.filter(patente=patente).exists():
                patente = f"AB{contador:03d}CD"
                contador += 1
            
            sucursal = random.choice(sucursales)
            
            unidad = Unidad.objects.create(
                maquina_base=maquina,
                patente=patente,
                sucursal=sucursal,
                estado='disponible',
                visible=True
            )
            
            print(f"[OK] Unidad {unidad.patente} para {maquina.nombre}")
    
    # Actualizar stock de todas las máquinas
    for maquina in MaquinaBase.objects.all():
        stock = maquina.unidades.filter(visible=True).count()
        maquina.stock = stock
        maquina.save()

def generar_alquileres_prueba():
    """Generar alquileres variados para testear estadísticas"""
    
    print("\n=== GENERANDO ALQUILERES DE PRUEBA ===")
    
    # Obtener clientes
    clientes = list(Persona.objects.filter(es_cliente=True, bloqueado_cliente=False))
    if not clientes:
        print("No hay clientes disponibles")
        return
    
    # Obtener máquinas con unidades
    maquinas = list(MaquinaBase.objects.filter(unidades__estado='disponible').distinct())
    if not maquinas:
        print("No hay máquinas disponibles")
        return
    
    # Definir rangos de fechas para variar los alquileres
    hoy = date.today()
    fecha_inicio_min = hoy - timedelta(days=60)  # 2 meses atrás
    fecha_inicio_max = hoy + timedelta(days=30)  # 1 mes adelante
    
    # Cantidad de alquileres por máquina (para crear distribución variada)
    distribucion_alquileres = {
        'Excavadora CAT 320': 25,           # Top 1
        'Retroexcavadora JCB 3CX': 22,      # Top 2
        'Cargadora Frontal Volvo L60H': 18, # Top 3
        'Compactadora Dynapac CA2500': 15,  # Top 4
        'Motoniveladora Komatsu GD555': 12, # Top 5
        'Grúa Móvil Liebherr LTM1030': 8,   # Otras
        'Hormigonera Automezcla Volumétrica': 6, # Otras
        'Dumper Articulado Volvo A25G': 5,  # Otras
        'Manipulador Telescópico JCB 540-170': 4, # Otras
        'Excavadora Compacta Kubota KX080': 3,    # Otras
        'Pavimentadora Bituminosa Vogele S1900': 2, # Otras
        'Cargadora Compacta Doosan SSL75': 1,     # Otras
    }
    
    contador_alquileres = 0
    
    for maquina in maquinas:
        # Obtener unidades disponibles de esta máquina
        unidades = list(maquina.unidades.filter(estado='disponible'))
        if not unidades:
            continue
        
        # Determinar cuántos alquileres crear para esta máquina
        num_alquileres = distribucion_alquileres.get(maquina.nombre, random.randint(1, 3))
        
        for _ in range(num_alquileres):
            # Seleccionar cliente aleatorio
            cliente = random.choice(clientes)
            
            # Generar fechas aleatorias
            fecha_inicio = fecha_inicio_min + timedelta(
                days=random.randint(0, (fecha_inicio_max - fecha_inicio_min).days)
            )
            
            dias_alquiler = random.randint(maquina.dias_alquiler_min, min(maquina.dias_alquiler_max, 10))
            fecha_fin = fecha_inicio + timedelta(days=dias_alquiler - 1)
            
            # Determinar estado basado en las fechas
            if fecha_fin < hoy:
                estado = 'finalizado'
            elif fecha_inicio <= hoy <= fecha_fin:
                estado = 'en_curso'
            else:
                estado = 'reservado'
            
            # Seleccionar unidad aleatoria
            unidad = random.choice(unidades)
            
            # Calcular monto
            monto_total = maquina.precio_por_dia * dias_alquiler
            
            # Generar número de alquiler único
            numero = f"ALQ{1000 + contador_alquileres}"
            while Alquiler.objects.filter(numero=numero).exists():
                contador_alquileres += 1
                numero = f"ALQ{1000 + contador_alquileres}"
            
            # Crear alquiler
            alquiler = Alquiler.objects.create(
                numero=numero,
                maquina_base=maquina,
                unidad=unidad,
                persona=cliente,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                cantidad_dias=dias_alquiler,
                estado=estado,
                metodo_pago=random.choice(['mercadopago', 'binance']),
                monto_total=monto_total,
                codigo_retiro=f"RET{random.randint(10000, 99999)}"
            )
            
            contador_alquileres += 1
            
            print(f"[OK] Alquiler {alquiler.numero}: {maquina.nombre} - {estado}")
    
    print(f"\nSe generaron {contador_alquileres} alquileres de prueba")

def main():
    """Función principal"""
    print("SCRIPT DE CARGA DE DATOS PARA ESTADÍSTICAS")
    print("=" * 50)
    
    try:
        # Cargar máquinas
        maquinas_creadas = cargar_maquinas_prueba()
        
        # Crear unidades
        crear_unidades_para_maquinas()
        
        # Generar alquileres
        generar_alquileres_prueba()
        
        print("\n" + "=" * 50)
        print("[EXITO] CARGA DE DATOS COMPLETADA EXITOSAMENTE")
        print("\nAhora puedes:")
        print("1. Ir a Estadísticas > Máquinas")
        print("2. Seleccionar un rango de fechas amplio (ej: 01/01/2025 - 31/12/2025)")
        print("3. Ver el gráfico de torta con categoría 'Otras'")
        print("4. Verificar que las top 5 + 'Otras' aparezcan correctamente")
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 