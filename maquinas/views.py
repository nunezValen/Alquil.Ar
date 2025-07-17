from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
from persona.views import es_empleado_o_admin
from .forms import MaquinaBaseForm, AlquilerForm, CargarUnidadForm
from .models import MaquinaBase, Unidad, Alquiler
from .forms import UnidadForm
from django.conf import settings
import mercadopago
import json
from django.http import HttpResponse, JsonResponse
from datetime import datetime, date, timedelta
from django.urls import reverse
from persona.models import Persona
from django.db.models import Q, Sum
from django.utils.dateparse import parse_date
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from collections import defaultdict
from decimal import Decimal
from .utils import enviar_email_alquiler_simple, enviar_email_alquiler_cancelado
from django.template.loader import render_to_string

def es_admin(user):
    return user.is_authenticated and user.is_superuser

def detalle_maquina(request, maquina_id):
    maquina = get_object_or_404(MaquinaBase, id=maquina_id)
    alquiler = None
    
    if request.method == 'POST':
        form = AlquilerForm(request.POST)
        if form.is_valid():
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            metodo_pago = form.cleaned_data['metodo_pago']
            
            # Validar días mínimos
            dias = (fecha_fin - fecha_inicio).days + 1
            if dias < maquina.dias_alquiler_min:
                form.add_error(None, f"El alquiler mínimo es de {maquina.dias_alquiler_min} días.")
            elif dias > maquina.dias_alquiler_max:
                form.add_error(None, f"El alquiler máximo es de {maquina.dias_alquiler_max} días.")
            else:
                try:
                    # Obtener la persona asociada al usuario
                    try:
                        persona = request.user.persona
                    except:
                        form.add_error(None, "No se encontró tu perfil de persona. Por favor, regístrate primero.")
                        return render(request, 'maquinas/detalle_maquina.html', {
                            'maquina': maquina,
                            'form': form,
                            'mercadopago_public_key': settings.MERCADOPAGO_PUBLIC_KEY
                        })

                    # Verificar si hay unidades disponibles
                    if not maquina.tiene_unidades_disponibles():
                        form.add_error(None, "Lo sentimos, no hay unidades disponibles en este momento.")
                        return render(request, 'maquinas/detalle_maquina.html', {
                            'maquina': maquina,
                            'form': form,
                            'mercadopago_public_key': settings.MERCADOPAGO_PUBLIC_KEY
                        })

                    # Buscar una unidad disponible
                    unidad = Unidad.objects.filter(
                        maquina_base=maquina,
                        estado='disponible',
                        visible=True
                    ).first()

                    # Crear el alquiler
                    alquiler = Alquiler.objects.create(
                        maquina_base=maquina,
                        unidad=unidad,
                        persona=persona,
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                        metodo_pago=metodo_pago,
                        estado='Reservado'
                    )
                    
                    # Esta función detalle_maquina no se usa para procesar pagos
                    # El procesamiento de pagos se hace en alquilar_maquina
                    pass
                        
                except Exception as e:
                    if alquiler:
                        alquiler.delete()
                    form.add_error(None, f"Error al procesar el pago: {str(e)}")
    else:
        form = AlquilerForm()
    
    return render(request, 'maquinas/detalle_maquina.html', {
        'maquina': maquina,
        'form': form,
        'mercadopago_public_key': settings.MERCADOPAGO_PUBLIC_KEY
    })

@login_required
def checkout_mp(request, alquiler_id):
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)
    
    # Verificar que el alquiler pertenece al usuario actual
    if alquiler.persona.email != request.user.email:
        messages.error(request, "No tienes permiso para ver este alquiler.")
        return redirect('maquinas:catalogo_publico')
    
    return render(request, 'maquinas/checkout_mp.html', {
        'maquina': alquiler.maquina_base,
        'alquiler': alquiler,
        'preference_id': alquiler.preference_id,
        'mercadopago_public_key': settings.MERCADOPAGO_PUBLIC_KEY
    })

@login_required
@user_passes_test(es_admin)
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def cargar_maquina_base(request):
    if request.method == 'POST':
        form = MaquinaBaseForm(request.POST, request.FILES)
        if form.is_valid():
            maquina = form.save()
            messages.success(request, f'La máquina base {maquina.nombre} ha sido cargada con éxito.')
            return redirect('maquinas:lista_maquinas')
    else:
        form = MaquinaBaseForm()

    return render(request, 'maquinas/cargar_maquina_base.html', {
        'form': form
    })

@login_required
def eliminar_maquina_base(request, maquina_id):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('maquinas:lista_maquinas')
    maquina = get_object_or_404(MaquinaBase, id=maquina_id)

    if request.method == 'POST':
        nombre_maquina = maquina.nombre
        try:
            if maquina.puede_ser_oculta():
                maquina.visible = False
                maquina.save()
                messages.success(request, f'La máquina base {nombre_maquina} ha sido ocultada exitosamente.')
            else:
                messages.error(request, 'No se puede ocultar la máquina porque tiene unidades visibles. Primero debe ocultar todas sus unidades.')
            return redirect('maquinas:lista_maquinas')
        except Exception as e:
            messages.error(request, f'Error al ocultar la máquina: {str(e)}')
            return redirect('maquinas:lista_maquinas')

    return render(request, 'maquinas/eliminar_maquina_base.html', {'maquina': maquina})

@login_required
@user_passes_test(es_empleado_o_admin)
def lista_maquinas(request):
    maquinas = MaquinaBase.objects.all().order_by('nombre')
    return render(request, 'maquinas/lista_maquinas.html', {'maquinas': maquinas})

@login_required
@user_passes_test(es_empleado_o_admin)
def lista_unidades(request):
    # Mostrar todas las unidades, incluyendo las ocultas
    unidades = Unidad.objects.select_related('maquina_base', 'sucursal').all().order_by('maquina_base__nombre', 'patente')
    return render(request, 'maquinas/lista_unidades.html', {
        'unidades': unidades
    })

@login_required
def toggle_visibilidad_unidad(request, pk):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('maquinas:lista_unidades')
    unidad = get_object_or_404(Unidad, pk=pk)
    maquina_base = unidad.maquina_base
    
    # Si se intenta desocultar una unidad, verificar que su máquina base y sucursal estén visibles
    if not unidad.visible:
        if not maquina_base.visible:
            messages.error(request, f'No se puede desocultar la unidad {unidad.patente} porque su máquina base está oculta.')
            return redirect('maquinas:lista_unidades')
        if not unidad.sucursal.es_visible:
            messages.error(request, f'No se puede desocultar la unidad {unidad.patente} porque su sucursal está oculta.')
            return redirect('maquinas:lista_unidades')

    # Cambiar visibilidad y actualizar stock
    if unidad.visible:
        unidad.visible = False
        maquina_base.stock = max(0, maquina_base.stock - 1)  # Evitar stock negativo
        messages.success(request, f'La unidad {unidad.patente} ha sido ocultada.')
    else:
        unidad.visible = True
        maquina_base.stock += 1
        messages.success(request, f'La unidad {unidad.patente} ha sido desocultada.')
    
    unidad.save()
    maquina_base.save()
    return redirect('maquinas:lista_unidades')



@login_required
@user_passes_test(es_empleado_o_admin)
def cancelar_alquiler(request, alquiler_id):
    """
    Vista para cancelar un alquiler (solo empleados/admins)
    """
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)
    
    if request.method == 'POST':
        try:
            if not alquiler.puede_ser_cancelado():
                messages.error(request, f'El alquiler {alquiler.numero} no puede ser cancelado (estado: {alquiler.get_estado_display()})')
                return redirect('persona:lista_alquileres')
            
            observaciones = request.POST.get('observaciones', '')
            porcentaje, monto = alquiler.cancelar(empleado=request.user, observaciones=observaciones)
            
            # Enviar email de cancelación
            try:
                enviar_email_alquiler_cancelado(alquiler)
                print(f"[INFO] Email de cancelación enviado para alquiler {alquiler.numero}")
            except Exception as e:
                print(f"[ERROR] Error al enviar email de cancelación: {str(e)}")
            
            messages.success(request, 
                f'Alquiler {alquiler.numero} cancelado exitosamente. '
                f'Reembolso: {porcentaje}% (${monto:.2f}). '
                f'Email de notificación enviado al cliente.')
            
        except Exception as e:
            messages.error(request, f'Error al cancelar el alquiler: {str(e)}')
        
        return redirect('persona:lista_alquileres')
    
    # Calcular reembolso para mostrar en el template
    porcentaje, monto = alquiler.calcular_reembolso(es_empleado=True)
    
    return render(request, 'maquinas/cancelar_alquiler.html', {
        'alquiler': alquiler,
        'porcentaje_reembolso': porcentaje,
        'monto_reembolso': monto
    })

@login_required
@user_passes_test(es_admin)
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def cargar_unidad(request):
    if request.method == 'POST':
        form = CargarUnidadForm(request.POST)
        if form.is_valid():
            unidad = form.save()
            messages.success(request, f"La unidad con patente '{unidad.patente}' ha sido cargada con éxito.")
            return redirect('maquinas:lista_unidades')
    else:
        form = CargarUnidadForm()

    return render(request, 'maquinas/cargar_unidad.html', {
        'form': form
    })

@login_required
@user_passes_test(es_admin)
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def eliminar_unidad(request, unidad_id):
    unidad = get_object_or_404(Unidad, id=unidad_id)
    if request.method == 'POST':
        unidad.delete()
        messages.success(request, f"La unidad '{unidad.patente}' ha sido eliminada con éxito.")
        return redirect('maquinas:lista_unidades')

    return render(request, 'maquinas/eliminar_unidad.html', {
        'unidad': unidad
    })

def catalogo_publico(request):
    query = request.GET.get('q', '')
    # Obtener todos los tipos y marcas posibles
    tipos_maquina = MaquinaBase.TIPOS_MAQUINA
    marcas = MaquinaBase.MARCAS

    # Obtener precios mínimo y máximo de todas las máquinas visibles
    precios = MaquinaBase.objects.filter(visible=True)
    precio_min = precios.order_by('precio_por_dia').first().precio_por_dia if precios.exists() else 0
    precio_max = precios.order_by('-precio_por_dia').first().precio_por_dia if precios.exists() else 0

    # Leer filtros seleccionados
    filtros = {
        'tipo': request.GET.getlist('tipo'),
        'marca': request.GET.getlist('marca'),
        'estado': request.GET.getlist('estado'),
        'precio_min': request.GET.get('precio_min', precio_min),
        'precio_max': request.GET.get('precio_max', precio_max),
    }

    # Filtrar máquinas
    maquinas = MaquinaBase.objects.filter(visible=True)
    if filtros['tipo']:
        maquinas = maquinas.filter(tipo__in=filtros['tipo'])
    if filtros['marca']:
        maquinas = maquinas.filter(marca__in=filtros['marca'])
    # Estado: OR global
    if filtros['estado']:
        estados = []
        if 'disponible' in filtros['estado']:
            estados.append(True)
        if 'no_disponible' in filtros['estado']:
            estados.append(False)
        maquinas = [m for m in maquinas if m.tiene_unidades_disponibles() in estados]
    else:
        maquinas = list(maquinas)
    # Filtro de precio
    try:
        pmin = float(filtros['precio_min'])
        pmax = float(filtros['precio_max'])
        maquinas = [m for m in maquinas if pmin <= float(m.precio_por_dia) <= pmax]
    except:
        pass
    # Filtro de búsqueda
    if query:
        maquinas = [m for m in maquinas if query.lower() in m.nombre.lower() or query.lower() in m.modelo.lower() or query.lower() in m.descripcion_corta.lower() or query.lower() in m.descripcion_larga.lower()]
    # Descripción corta recortada
    for maquina in maquinas:
        if len(maquina.descripcion_corta) > 200:
            maquina.descripcion_vista = maquina.descripcion_corta[:197] + "..."
        else:
            maquina.descripcion_vista = maquina.descripcion_corta
    return render(request, 'maquinas/catalogo_publico.html', {
        'maquinas': maquinas,
        'query': query,
        'tipos_maquina': tipos_maquina,
        'marcas': marcas,
        'precio_min': precio_min,
        'precio_max': precio_max,
        'filtros': filtros,
    })

@csrf_exempt
@require_http_methods(["POST"])
def webhook_mercadopago(request):
    if request.method == 'POST':
        try:
            print("=== WEBHOOK MERCADO PAGO RECIBIDO ===")
            # Obtener los datos del webhook
            data = json.loads(request.body)
            print(f"Datos del webhook: {data}")
            
            # Verificar el tipo de notificación
            if data.get('type') == 'payment':
                payment_id = data.get('data', {}).get('id')
                print(f"Payment ID: {payment_id}")
                
                # Para pagos de empleados (QR dinámico), usar las credenciales de empleado
                try:
                    # Intentar primero con credenciales de empleado
                    sdk = mercadopago.SDK(settings.MERCADOPAGO_EMPLOYEE_ACCESS_TOKEN)
                    payment_info = sdk.payment().get(payment_id)
                    print(f"Payment info (empleado): {payment_info}")
                except Exception as e:
                    # Si falla, usar credenciales normales
                    print(f"[WEBHOOK] Error con credenciales de empleado: {str(e)}")
                    try:
                        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                        payment_info = sdk.payment().get(payment_id)
                        print(f"[WEBHOOK] Payment info (normal): {payment_info}")
                    except Exception as e2:
                        print(f"[WEBHOOK] Error con credenciales normales: {str(e2)}")
                        return HttpResponse(status=400)
                
                if payment_info['status'] == 200:
                    payment_data = payment_info['response']
                    external_reference = payment_data.get('external_reference')
                    status = payment_data.get('status')
                    print(f"External reference: {external_reference}, Status: {status}")
                    
                    # El external_reference ahora tiene formato: "maquina_id|persona_id|fecha_inicio|fecha_fin|metodo_pago|total"
                    if '|' in str(external_reference):
                        # Nuevo formato - crear alquiler cuando el pago es aprobado
                        if status == 'approved':
                            try:
                                parts = str(external_reference).split('|')
                                maquina_id, persona_id, fecha_inicio_str, fecha_fin_str, metodo_pago, total = parts
                                
                                # Convertir fechas
                                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
                                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
                                
                                # Obtener objetos
                                maquina = MaquinaBase.objects.get(id=maquina_id)
                                persona = Persona.objects.get(id=persona_id)
                                
                                # IDEMPOTENCIA: Verificar que no existe ya un alquiler ACTIVO para esta referencia
                                alquiler_existente = Alquiler.objects.filter(
                                    external_reference=external_reference,
                                    estado__in=['reservado', 'en_curso']  # Solo alquileres realmente activos
                                ).first()
                                
                                if alquiler_existente:
                                    print(f"[WEBHOOK] Alquiler ya existe: {alquiler_existente.numero}")
                                    return HttpResponse(status=200)
                                
                                # Verificar que no existe un alquiler ACTIVO duplicado por datos
                                alquiler_duplicado = Alquiler.objects.filter(
                                    maquina_base=maquina,
                                    persona=persona,
                                    fecha_inicio=fecha_inicio,
                                    fecha_fin=fecha_fin,
                                    estado__in=['reservado', 'en_curso']  # Solo alquileres realmente activos
                                ).first()
                                
                                if alquiler_duplicado:
                                    print(f"[WEBHOOK] Alquiler duplicado encontrado: {alquiler_duplicado.numero}")
                                    # Actualizar la referencia externa del existente
                                    alquiler_duplicado.external_reference = external_reference
                                    alquiler_duplicado.save()
                                    return HttpResponse(status=200)
                                
                                # Buscar una unidad disponible
                                unidad = Unidad.objects.filter(
                                    maquina_base=maquina,
                                    estado='disponible',
                                    visible=True
                                ).first()
                                
                                if unidad:
                                    # Crear el alquiler 
                                    alquiler = Alquiler.objects.create(
                                        maquina_base=maquina,
                                        persona=persona,
                                        fecha_inicio=fecha_inicio,
                                        fecha_fin=fecha_fin,
                                        metodo_pago=metodo_pago,
                                        estado='reservado',  # Cambiar a reservado
                                        monto_total=total,
                                        external_reference=external_reference
                                    )
                                    
                                    print(f"[WEBHOOK] Alquiler creado: {alquiler.numero}")
                                    
                                    # Enviar mail al cliente
                                    try:
                                        enviar_email_alquiler_simple(alquiler)
                                        print(f"[WEBHOOK] Email enviado correctamente")
                                    except Exception as e:
                                        print(f"[WEBHOOK] Error al enviar email: {str(e)}")
                                else:
                                    print("[WEBHOOK] No hay unidades disponibles")
                                    
                            except Exception as e:
                                print(f"[WEBHOOK] Error procesando pago aprobado: {str(e)}")
                    else:
                        # Formato antiguo - buscar alquiler existente
                        try:
                            alquiler = Alquiler.objects.get(id=external_reference)
                            
                            # Actualizar el estado del alquiler según el estado del pago
                            if status == 'approved':
                                alquiler.estado = 'confirmado'
                                
                            elif status == 'rejected':
                                alquiler.estado = 'rechazado'
                                print("Pago rechazado")
                            elif status == 'pending':
                                alquiler.estado = 'pendiente'
                                print("Pago pendiente")
                            
                            alquiler.save()
                            
                        except Alquiler.DoesNotExist:
                            print(f"Alquiler no encontrado con ID: {external_reference}")
                            return HttpResponse(status=404)
                    
                    return HttpResponse(status=200)
                else:
                    print(f"[WEBHOOK] Error en payment info: {payment_info}")
                    # Si el pago no se encuentra, podría ser porque aún no está disponible
                    # Retornamos 200 para que MercadoPago no reintente
                    if payment_info.get('status') == 404:
                        print(f"[WEBHOOK] Payment not found - MercadoPago aún no lo tiene disponible")
                        return HttpResponse(status=200)
                    return HttpResponse(status=400)
            else:
                print(f"Tipo de notificación no manejado: {data.get('type')}")
                return HttpResponse(status=200)
                
        except Exception as e:
            print(f"Error en webhook: {str(e)}")
            return HttpResponse(status=500)
    
    return HttpResponse(status=405)  # Method Not Allowed

def procesar_pago_empleado_qr_dinamico(request, maquina, persona, fecha_inicio, fecha_fin, dias, total_base, total, porcentaje_recargo, monto_recargo, metodo_pago):
    """
    Procesa pago para empleados usando QR dinámico con nuevas credenciales o Binance
    """
    import requests
    import qrcode
    from io import BytesIO
    import base64
    
    try:
        # Si el método de pago es Binance, NO crear alquiler aún, solo retornar datos para confirmación
        if metodo_pago == 'binance':
            # Preparar external_reference sin crear el alquiler
            external_reference = f"{maquina.id}|{persona.id}|{fecha_inicio.strftime('%Y-%m-%d')}|{fecha_fin.strftime('%Y-%m-%d')}|{metodo_pago}|{total}"
            
            print(f"[OK] Datos preparados para Binance - External reference: {external_reference}")
            
            return JsonResponse({
                'metodo_pago': 'binance',
                'external_reference': external_reference,
                'success': True
            })
        
        # Preparar external_reference con los datos del alquiler
        external_reference = f"{maquina.id}|{persona.id}|{fecha_inicio.strftime('%Y-%m-%d')}|{fecha_fin.strftime('%Y-%m-%d')}|{metodo_pago}|{total}"
        
        # Configurar URL base para ngrok
        base_url = request.build_absolute_uri('/').rstrip('/')
        if 'ngrok-free.app' in base_url:
            base_url = base_url.replace('http://', 'https://')
        
        # Preparar título y descripción con información del recargo
        if porcentaje_recargo > 0:
            titulo = f"Alquiler de {maquina.nombre} (Recargo {porcentaje_recargo}%)"
            descripcion = f"Alquiler de {maquina.nombre} por {dias} días. Base: ${total_base:,.0f} + Recargo {porcentaje_recargo}%: ${monto_recargo:,.0f}"
        else:
            titulo = f"Alquiler de {maquina.nombre}"
            descripcion = f"Alquiler de {maquina.nombre} por {dias} días"
        
        # Datos para crear orden QR dinámico
        url = "https://api.mercadopago.com/instore/orders/qr/seller/collectors/343205143/pos/CAJA001/qrs"
        headers = {
            "Authorization": f"Bearer {settings.MERCADOPAGO_EMPLOYEE_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "external_reference": external_reference,
            "title": titulo,
            "description": descripcion,
            "total_amount": float(total),
            "items": [
                {
                    "title": titulo,
                    "quantity": 1,
                    "unit_price": float(total),
                    "unit_measure": "unit",
                    "total_amount": float(total)
                }
            ],
            "notification_url": f"{base_url}/maquinas/webhook-mercadopago/"
        }
        
        print(f"=== CREANDO QR DINÁMICO ===")
        print(f"URL: {url}")
        print(f"External reference: {external_reference}")
        print(f"Total amount: {total} (tipo: {type(total)})")
        print(f"Payload completo: {payload}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 201:
            data = response.json()
            qr_data = data.get('qr_data')
            
            if qr_data:
                # Generar imagen QR
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convertir a base64
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                img_b64 = base64.b64encode(buffer.getvalue()).decode()
                
                print(f"[OK] QR dinámico creado exitosamente")
                
                return JsonResponse({
                    'qr_code_base64': img_b64,
                    'qr_data': qr_data,
                    'order_id': data.get('in_store_order_id'),
                    'external_reference': external_reference,
                    'success': True
                })
            else:
                return JsonResponse({
                    'error': 'No se pudo generar el código QR'
                }, status=500)
        else:
            error_msg = f"Error al crear orden QR: {response.status_code} - {response.text}"
            print(f"[ERROR] {error_msg}")
            return JsonResponse({
                'error': error_msg
            }, status=500)
            
    except Exception as e:
        print(f"Error en QR dinámico: {str(e)}")
        return JsonResponse({
            'error': f'Error al generar QR dinámico: {str(e)}'
        }, status=500)

def procesar_pago_cliente_normal(request, maquina, persona, fecha_inicio, fecha_fin, dias, total_base, total, porcentaje_recargo, monto_recargo, metodo_pago):
    """
    Procesa pago para clientes usando API normal (preferencias)
    """
    try:
        # Usar credenciales normales para clientes
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        
        # Preparar external_reference con los datos del alquiler
        external_reference = f"{maquina.id}|{persona.id}|{fecha_inicio.strftime('%Y-%m-%d')}|{fecha_fin.strftime('%Y-%m-%d')}|{metodo_pago}|{total}"
        
        # Configurar URL base
        base_url = request.build_absolute_uri('/').rstrip('/')
        if 'ngrok-free.app' in base_url:
            base_url = base_url.replace('http://', 'https://')
        
        webhook_url = f"{base_url}/maquinas/webhook-mercadopago/"
        
        # Preparar título con información del recargo
        if porcentaje_recargo > 0:
            titulo = f"Alquiler de {maquina.nombre} (Recargo {porcentaje_recargo}%)"
        else:
            titulo = f"Alquiler de {maquina.nombre}"
        
        preference_data = {
            "items": [{
                "title": titulo,
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": float(total)
            }],
            "back_urls": {
                "success": f"{base_url}/persona/pago-exitoso/",
                "failure": f"{base_url}/persona/pago-fallido/",
                "pending": f"{base_url}/persona/pago-pendiente/"
            },
            "external_reference": external_reference,
            "notification_url": webhook_url,
            "binary_mode": True,
            "payer": {
                "email": request.user.email
            },
            "payment_methods": {
                "excluded_payment_types": [
                    {"id": "ticket"}
                ],
                "installments": 1
            }
        }
        
        print(f"=== CREANDO PREFERENCIA NORMAL ===")
        print(f"External reference: {external_reference}")
        
        # Crear preferencia
        preference_response = sdk.preference().create(preference_data)
        
        if preference_response["status"] == 201:
            preference = preference_response["response"]
            print(f"[OK] Preferencia creada: {preference['id']}")
            
            return JsonResponse({
                'init_point': preference["init_point"]
            })
        else:
            error_msg = f"Error al crear preferencia: {preference_response.get('message', 'Error desconocido')}"
            return JsonResponse({
                'error': error_msg
            }, status=500)
            
    except Exception as e:
        print(f"Error en pago normal: {str(e)}")
        return JsonResponse({
            'error': f'Error al procesar el pago: {str(e)}'
        }, status=500)

@login_required
def alquilar_maquina(request, maquina_id):
    print(f"=== FUNCIÓN ALQUILAR_MAQUINA EJECUTADA ===")
    print(f"Maquina ID: {maquina_id}")
    print(f"Método: {request.method}")
    print(f"Usuario: {request.user.email}")
    maquina = get_object_or_404(MaquinaBase, id=maquina_id)
    
    if request.method == 'POST':
        try:
            dias = int(request.POST.get('dias'))
            fecha_inicio = request.POST.get('fecha_inicio')
            metodo_pago = request.POST.get('metodo_pago')
            
            # Validar días de alquiler
            if dias < maquina.dias_alquiler_min or dias > maquina.dias_alquiler_max:
                return JsonResponse({
                    'error': f'La cantidad de días debe estar entre {maquina.dias_alquiler_min} y {maquina.dias_alquiler_max}'
                }, status=400)
            
            # Validar fecha de inicio
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            if fecha_inicio < date.today():
                return JsonResponse({
                    'error': 'La fecha de inicio no puede ser anterior a hoy'
                }, status=400)
            
            # Calcular fecha fin
            fecha_fin = fecha_inicio + timedelta(days=dias-1)
            
            # Obtener la persona asociada al usuario
            # Verificar si el empleado está actuando como cliente
            es_empleado_actuando_como_cliente = request.session.get('es_empleado_actuando_como_cliente', False)
            
            if request.user.persona.es_empleado and not es_empleado_actuando_como_cliente:  # Si es empleado trabajando
                cliente_id = request.POST.get('cliente_id')
                persona = get_object_or_404(Persona, id=cliente_id)
            else:
                # Cliente normal o empleado actuando como cliente
                try:
                    persona = Persona.objects.get(email=request.user.email)
                except Persona.DoesNotExist:
                    return JsonResponse({
                        'error': 'No se encontró tu perfil de persona. Por favor, regístrate primero.'
                    }, status=400)
            
            # VALIDACIÓN 1: Verificar que el cliente no tenga alquileres adeudados
            alquileres_adeudados = Alquiler.objects.filter(
                persona=persona,
                estado='adeudado'
            )
            
            if alquileres_adeudados.exists():
                alquiler_adeudado = alquileres_adeudados.first()
                dias_vencido = (date.today() - alquiler_adeudado.fecha_fin).days
                return JsonResponse({
                    'error': f'❌ NO SE PUEDE REALIZAR EL ALQUILER: Hay un alquiler vencido (#{alquiler_adeudado.numero}) asociado a esta personaque debe ser devuelto URGENTEMENTE. '
                            f'Máquina: {alquiler_adeudado.maquina_base.nombre}, '
                            f'vencido hace {dias_vencido} día{"s" if dias_vencido != 1 else ""}. '
                            f'Antes de realizar un nuevo alquiler debe resolverse esta situación. '
                            f'📞 Se recomienda coordinar la devolución a la brevedad.'
                }, status=400)
            
            # VALIDACIÓN 2: Verificar que el cliente no tenga otro alquiler activo/reservado
            alquileres_activos = Alquiler.objects.filter(
                persona=persona,
                estado__in=['reservado', 'en_curso']
            )
            
            if alquileres_activos.exists():
                alquiler_activo = alquileres_activos.first()
                return JsonResponse({
                    'error': f'Ya existe un alquiler activo asociado a esta persona (#{alquiler_activo.numero}). '
                            f'Solo se puede tener un alquiler a la vez. '
                            f'Su alquiler actual: {alquiler_activo.maquina_base.nombre} '
                            f'del {alquiler_activo.fecha_inicio.strftime("%d/%m/%Y")} '
                            f'al {alquiler_activo.fecha_fin.strftime("%d/%m/%Y")}. '
                }, status=400)
            
            # VALIDACIÓN 3: Verificar disponibilidad de unidades para las fechas
            unidades_disponibles = Alquiler.obtener_unidades_disponibles(maquina, fecha_inicio, fecha_fin)
            
            if unidades_disponibles == 0:
                # Verificar si hay unidades de la máquina en general
                total_unidades = maquina.unidades.filter(estado='disponible', visible=True).count()
                if total_unidades == 0:
                    return JsonResponse({
                        'error': f'No hay unidades de {maquina.nombre} disponibles en este momento. '
                                f'Por favor, selecciona otra máquina o contacta al soporte.'
                    }, status=400)
                else:
                    # Buscar próxima fecha disponible
                    proxima_fecha = fecha_inicio
                    while proxima_fecha <= fecha_inicio + timedelta(days=30):  # Buscar hasta 30 días
                        proxima_fecha_fin = proxima_fecha + timedelta(days=dias-1)
                        if Alquiler.obtener_unidades_disponibles(maquina, proxima_fecha, proxima_fecha_fin) > 0:
                            return JsonResponse({
                                'error': f'No hay unidades disponibles para las fechas {fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")}. '
                                        f'La próxima fecha disponible es: {proxima_fecha.strftime("%d/%m/%Y")}. '
                                        f'Por favor, selecciona otras fechas.'
                            }, status=400)
                        proxima_fecha += timedelta(days=1)
                    
                    return JsonResponse({
                        'error': f'No hay unidades disponibles para las fechas seleccionadas. '
                                f'Todas las unidades de {maquina.nombre} están ocupadas en ese período. '
                                f'Por favor, selecciona fechas más adelante o contacta al soporte.'
                    }, status=400)
            
            print(f"=== VALIDACIONES PASADAS ===")
            print(f"Unidades disponibles: {unidades_disponibles}")
            print(f"Cliente: {persona.nombre} {persona.apellido}")
            print(f"Fechas: {fecha_inicio} - {fecha_fin} ({dias} días)")
            
            # Calcular total base
            total_base = dias * maquina.precio_por_dia
            
            # Aplicar recargo si corresponde
            porcentaje_recargo, monto_recargo, total = persona.calcular_recargo(total_base)
            
            # Verificar si el usuario es empleado para usar QR dinámico o API normal
            # Considerar si está actuando como cliente
            try:
                es_empleado_trabajando = request.user.persona.es_empleado and not es_empleado_actuando_como_cliente
            except:
                # Si no tiene persona asociada, buscar por email y asociar
                try:
                    persona_usuario = Persona.objects.get(email=request.user.email)
                    persona_usuario.user = request.user
                    persona_usuario.save()
                    es_empleado_trabajando = persona_usuario.es_empleado and not es_empleado_actuando_como_cliente
                except Persona.DoesNotExist:
                    return JsonResponse({
                        'error': 'No se encontró tu perfil de persona. Por favor, contacta al administrador.'
                    }, status=400)
            
            if es_empleado_trabajando:
                # EMPLEADOS TRABAJANDO: Usar QR dinámico con nuevas credenciales
                return procesar_pago_empleado_qr_dinamico(request, maquina, persona, fecha_inicio, fecha_fin, dias, total_base, total, porcentaje_recargo, monto_recargo, metodo_pago)
            else:
                # CLIENTES (normales o empleados actuando como clientes): Usar API anterior (preferencias normales)
                return procesar_pago_cliente_normal(request, maquina, persona, fecha_inicio, fecha_fin, dias, total_base, total, porcentaje_recargo, monto_recargo, metodo_pago)

        
        except ValueError as e:
            return JsonResponse({
                'error': 'Datos de entrada inválidos. Por favor, verifica la información ingresada.'
            }, status=400)
        except Exception as e:
            print(f"Error en alquilar_maquina: {str(e)}")
            return JsonResponse({
                'error': f'Error al procesar el pago: {str(e)}'
            }, status=500)
    
    # Para GET, devolver los datos necesarios para el modal
    fecha_minima = date.today()
    
    # Obtener información de disponibilidad
    # NOTA: Solo verificar alquileres del usuario si NO es empleado o si es empleado pero no tiene clientes para gestionar
    try:
        persona = Persona.objects.get(email=request.user.email)
        
        # Verificar si el empleado está actuando como cliente
        es_empleado_actuando_como_cliente = request.session.get('es_empleado_actuando_como_cliente', False)
        
        # Si es empleado trabajando, NO verificar sus alquileres personales (puede alquilar para otros)
        if persona.es_empleado and not es_empleado_actuando_como_cliente:
            tiene_alquiler_adeudado = False
            tiene_alquiler_activo = False
        else:
            # Si es cliente normal o empleado actuando como cliente, sí verificar sus alquileres
            tiene_alquiler_adeudado = Alquiler.objects.filter(
                persona=persona,
                estado='adeudado'
            ).exists()
            tiene_alquiler_activo = Alquiler.objects.filter(
                persona=persona,
                estado__in=['reservado', 'en_curso']
            ).exists()
    except:
        tiene_alquiler_adeudado = False
        tiene_alquiler_activo = False
    
    # Obtener lista de clientes si el usuario es empleado TRABAJANDO (no actuando como cliente)
    clientes = []
    try:
        es_empleado_actuando_como_cliente = request.session.get('es_empleado_actuando_como_cliente', False)
        
        if request.user.persona.es_empleado and not es_empleado_actuando_como_cliente:
            # Incluir todas las personas que sean clientes y no estén bloqueadas
            # EXCLUIR al empleado actual para que no pueda alquilar para sí mismo
            clientes_queryset = Persona.objects.filter(
                es_cliente=True,                    # Que sea cliente
                bloqueado_cliente=False             # Que no esté bloqueado como cliente
            ).exclude(
                email=request.user.email            # EXCLUIR al empleado actual
            )
            
            # Agregar información de recargo para cada cliente
            clientes = []
            for cliente in clientes_queryset:
                cliente_data = {
                    'id': cliente.id,
                    'nombre': cliente.nombre,
                    'apellido': cliente.apellido,
                    'email': cliente.email,
                    'dni': cliente.dni,
                    'calificacion_promedio': float(cliente.calificacion_promedio),
                    'tiene_recargo': cliente.tiene_recargo(),
                    'mensaje_recargo': cliente.get_mensaje_recargo(),
                    'tiene_alquiler_adeudado': Alquiler.objects.filter(persona=cliente, estado='adeudado').exists()
                }
                clientes.append(cliente_data)
    except:
        # Si no tiene persona asociada, buscar por email y asociar
        try:
            persona_usuario = Persona.objects.get(email=request.user.email)
            persona_usuario.user = request.user
            persona_usuario.save()
            es_empleado_actuando_como_cliente = request.session.get('es_empleado_actuando_como_cliente', False)
            
            if persona_usuario.es_empleado and not es_empleado_actuando_como_cliente:
                clientes_queryset = Persona.objects.filter(
                    es_cliente=True,                    # Que sea cliente
                    bloqueado_cliente=False             # Que no esté bloqueado como cliente
                ).exclude(
                    email=request.user.email            # EXCLUIR al empleado actual
                )
                
                clientes = []
                for cliente in clientes_queryset:
                    cliente_data = {
                        'id': cliente.id,
                        'nombre': cliente.nombre,
                        'apellido': cliente.apellido,
                        'email': cliente.email,
                        'dni': cliente.dni,
                        'calificacion_promedio': float(cliente.calificacion_promedio),
                        'tiene_recargo': cliente.tiene_recargo(),
                        'mensaje_recargo': cliente.get_mensaje_recargo(),
                        'tiene_alquiler_adeudado': Alquiler.objects.filter(persona=cliente, estado='adeudado').exists()
                    }
                    clientes.append(cliente_data)
        except Persona.DoesNotExist:
            pass
    
    return JsonResponse({
        'maquina': {
            'id': maquina.id,
            'nombre': maquina.nombre,
            'precio_por_dia': maquina.precio_por_dia,
            'dias_min': maquina.dias_alquiler_min,
            'dias_max': maquina.dias_alquiler_max,
            'imagen_url': maquina.imagen.url if maquina.imagen else None,
            'unidades_totales': maquina.unidades.filter(estado='disponible', visible=True).count()
        },
        'fecha_minima': fecha_minima.strftime('%Y-%m-%d'),
        'tiene_alquiler_adeudado': tiene_alquiler_adeudado,
        'tiene_alquiler_activo': tiene_alquiler_activo,
        'clientes': clientes,
        'usuario_email': request.user.email
    })

@login_required
def estado_pago_qr(request):
    """
    Vista para mostrar el estado del pago QR dinámico
    """
    external_reference = request.GET.get('external_reference')
    if not external_reference:
        return JsonResponse({'error': 'External reference requerido'}, status=400)
    
    try:
        # Buscar el alquiler por external_reference
        alquiler = Alquiler.objects.filter(
            external_reference=external_reference
        ).first()
        
        if alquiler:
            return JsonResponse({
                'success': True,
                'alquiler': {
                    'numero': alquiler.numero,
                    'estado': alquiler.estado,
                    'maquina': alquiler.maquina_base.nombre,
                    'cliente': f"{alquiler.persona.nombre} {alquiler.persona.apellido}",
                    'fecha_inicio': alquiler.fecha_inicio.strftime('%d/%m/%Y'),
                    'fecha_fin': alquiler.fecha_fin.strftime('%d/%m/%Y'),
                    'total': float(alquiler.monto_total),
                    'codigo_retiro': alquiler.numero  # Usar el número como código de retiro
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Esperando confirmación del pago...'
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def confirmar_alquiler(request):
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status')
    external_reference = request.GET.get('external_reference')
    
    if status == 'approved':
        # Parsear external_reference
        maquina_id, user_id, dias, fecha_inicio = external_reference.split('_')
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        
        # Crear el alquiler
        alquiler = Alquiler.objects.create(
            maquina_id=maquina_id,
            usuario_id=user_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_inicio + timedelta(days=int(dias)),
            monto_total=float(request.GET.get('amount')),
            estado='confirmado'
        )
        
        messages.success(request, '¡Alquiler confirmado con éxito!')
        return redirect('persona:mis_alquileres')
    
    messages.error(request, 'Hubo un error al procesar el pago')
    return redirect('maquinas:catalogo_publico')

@login_required
def error_pago(request):
    messages.error(request, 'Hubo un error al procesar el pago')
    return redirect('maquinas:catalogo_publico')

@login_required
def pago_pendiente(request):
    messages.warning(request, 'El pago está pendiente de aprobación')
    return redirect('maquinas:catalogo_publico')

@login_required
def editar_maquina_base(request, pk):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('maquinas:lista_maquinas')
    maquina = get_object_or_404(MaquinaBase, pk=pk)
    if request.method == 'POST':
        form = MaquinaBaseForm(request.POST, request.FILES, instance=maquina)
        if form.is_valid():
            maquina = form.save(commit=False)
            # Mantener la imagen original
            maquina.imagen = MaquinaBase.objects.get(pk=pk).imagen
            maquina.save()
            messages.success(request, 'Máquina base actualizada exitosamente.')
            return redirect('maquinas:lista_maquinas')
    else:
        form = MaquinaBaseForm(instance=maquina)
        # Eliminar el campo de imagen del formulario
        if 'imagen' in form.fields:
            del form.fields['imagen']
    
    return render(request, 'maquinas/editar_maquina_base.html', {
        'form': form,
        'maquina': maquina
    })

@login_required
def editar_unidad(request, pk):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('maquinas:lista_unidades')
    unidad = get_object_or_404(Unidad, pk=pk)
    if request.method == 'POST':
        form = UnidadForm(request.POST, instance=unidad, initial={'patente_original': unidad.patente})
        if form.is_valid():
            form.save()
            messages.success(request, f'Unidad {unidad.patente} actualizada correctamente.')
            return redirect('maquinas:lista_unidades')
    else:
        form = UnidadForm(instance=unidad, initial={'patente_original': unidad.patente})
    
    return render(request, 'maquinas/editar_unidad.html', {
        'form': form,
        'unidad': unidad
    })

@login_required
def toggle_mantenimiento_unidad(request, pk):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('maquinas:lista_unidades')
    unidad = get_object_or_404(Unidad, pk=pk)

    # Verificar si la unidad está en un alquiler en curso
    from maquinas.models import Alquiler
    alquiler_en_curso = Alquiler.objects.filter(unidad=unidad, estado='en_curso').exists()
    if alquiler_en_curso:
        messages.error(request, "No se puede poner en mantenimiento una unidad que está en un alquiler en curso.")
        return redirect('maquinas:lista_unidades')

    # Solo permitir cambiar entre disponible y mantenimiento
    if unidad.estado == 'disponible':
        unidad.estado = 'mantenimiento'
        mensaje = f'La unidad {unidad.patente} ha sido puesta en mantenimiento.'
    elif unidad.estado == 'mantenimiento':
        unidad.estado = 'disponible'
        mensaje = f'La unidad {unidad.patente} ha sido marcada como disponible.'
    else:
        messages.error(request, 'Solo se puede cambiar el estado de mantenimiento en unidades disponibles.')
        return redirect('maquinas:lista_unidades')

    unidad.save()
    messages.success(request, mensaje)
    return redirect('maquinas:lista_unidades')

@login_required
def desocultar_maquina_base(request, maquina_id):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('maquinas:lista_maquinas')
    maquina = get_object_or_404(MaquinaBase, id=maquina_id)
    nombre_maquina = maquina.nombre
    try:
        maquina.visible = True
        maquina.save()
        messages.success(request, f'La máquina base {nombre_maquina} ha sido desocultada exitosamente.')
    except Exception as e:
        messages.error(request, f'Error al desocultar la máquina: {str(e)}')
    return redirect('maquinas:lista_maquinas')

@login_required
@csrf_protect
@require_http_methods(["POST"])
def confirmar_pago_binance(request):
    """
    Vista para confirmar el pago de Binance realizado por un empleado
    Ahora crea el alquiler en lugar de solo confirmarlo
    """
    import json
    from datetime import datetime
    
    try:
        # Verificar que el usuario sea empleado
        if not request.user.persona.es_empleado:
            return JsonResponse({
                'error': 'Solo los empleados pueden confirmar pagos de Binance'
            }, status=403)
        
        # Obtener datos del request
        data = json.loads(request.body)
        external_reference = data.get('external_reference')
        
        if not external_reference:
            return JsonResponse({
                'error': 'Referencia externa requerida'
            }, status=400)
        
        # Parsear external_reference
        try:
            parts = external_reference.split('|')
            if len(parts) != 6:
                raise ValueError("Formato de referencia externa inválido")
            
            maquina_id, persona_id, fecha_inicio_str, fecha_fin_str, metodo_pago, total = parts
            
            # Convertir fechas
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            
            # Obtener objetos
            maquina = get_object_or_404(MaquinaBase, id=maquina_id)
            persona = get_object_or_404(Persona, id=persona_id)
            
        except (ValueError, IndexError) as e:
            return JsonResponse({
                'error': f'Error procesando datos del pago: {str(e)}'
            }, status=400)
        
        # IDEMPOTENCIA: Verificar que no existe ya un alquiler ACTIVO para esta referencia
        alquiler_existente = Alquiler.objects.filter(
            external_reference=external_reference,
            estado__in=['reservado', 'en_curso']  # Solo alquileres realmente activos
        ).first()
        
        if alquiler_existente:
            print(f"[OK] Alquiler ya existe para Binance: {alquiler_existente.numero}")
            alquiler = alquiler_existente
        else:
            # Verificar disponibilidad nuevamente
            if not Alquiler.verificar_disponibilidad(maquina, fecha_inicio, fecha_fin):
                return JsonResponse({
                    'error': 'No hay unidades disponibles para las fechas seleccionadas'
                }, status=400)
            
            # Verificar que el cliente no tenga otro alquiler activo
            alquileres_activos = Alquiler.objects.filter(
                persona=persona,
                estado__in=['reservado', 'en_curso']
            )
            
            if alquileres_activos.exists():
                return JsonResponse({
                    'error': 'El cliente ya tiene un alquiler activo'
                }, status=400)
            
            # Buscar unidad disponible
            unidad = Unidad.objects.filter(
                maquina_base=maquina,
                estado='disponible',
                visible=True
            ).first()
            
            if not unidad:
                return JsonResponse({
                    'error': 'No hay unidades disponibles'
                }, status=400)
            
            # Crear el alquiler
            alquiler = Alquiler.objects.create(
                maquina_base=maquina,
                unidad=unidad,
                persona=persona,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                metodo_pago=metodo_pago,
                estado='reservado',
                monto_total=float(total),
                external_reference=external_reference
            )
            
            print(f"[OK] Alquiler Binance creado: {alquiler.numero}")
        
        # Enviar email al cliente
        try:
            from .utils import enviar_email_alquiler_simple
            resultado_email = enviar_email_alquiler_simple(alquiler)
            if resultado_email:
                print(f"[SUCCESS] Email enviado correctamente al cliente {alquiler.persona.email}")
            else:
                print(f"[ERROR] Falló el envío de email al cliente")
        except Exception as e:
            print(f"[ERROR] Error al enviar email de confirmación: {str(e)}")
        
        # Preparar datos del alquiler para la respuesta
        alquiler_data = {
            'id': alquiler.id,
            'numero': alquiler.numero,
            'maquina': alquiler.maquina_base.nombre,
            'cliente': f"{alquiler.persona.nombre} {alquiler.persona.apellido}",
            'fecha_inicio': alquiler.fecha_inicio.strftime('%d/%m/%Y'),
            'fecha_fin': alquiler.fecha_fin.strftime('%d/%m/%Y'),
            'total': float(alquiler.monto_total),
            'estado': alquiler.get_estado_display(),
            'codigo_retiro': alquiler.numero
        }
        
        return JsonResponse({
            'success': True,
            'alquiler': alquiler_data
        })
        
    except Exception as e:
        print(f"Error en confirmar_pago_binance: {str(e)}")
        return JsonResponse({
            'error': f'Error al confirmar el pago: {str(e)}'
        }, status=500)

def nombres_maquinas_base(request):
    nombres = list(MaquinaBase.objects.values_list('nombre', flat=True))
    return JsonResponse({'nombres': nombres})

@require_GET
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def estadisticas_facturacion(request):
    """
    Devuelve datos de facturación agrupados por día, semana, mes o año según el rango de fechas.
    Suma monto_total de alquileres creados en el periodo y resta monto_reembolso de los cancelados en el periodo.
    """
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    if not fecha_inicio or not fecha_fin:
        return JsonResponse({'error': 'Debe especificar fecha de inicio y fin.'}, status=400)

    fecha_inicio = parse_date(fecha_inicio)
    fecha_fin = parse_date(fecha_fin)
    if not fecha_inicio or not fecha_fin:
        return JsonResponse({'error': 'Fechas inválidas.'}, status=400)

    if fecha_inicio > fecha_fin:
        return JsonResponse({'error': 'La fecha de inicio no puede ser posterior a la de fin.'}, status=400)

    dias = (fecha_fin - fecha_inicio).days + 1
    if dias <= 7:
        agrupacion = 'dia'
        formato = '%Y-%m-%d'
    elif dias <= 31:
        agrupacion = 'semana'
        formato = '%Y-%W'
    elif dias <= 366:
        agrupacion = 'mes'
        formato = '%Y-%m'
    else:
        agrupacion = 'anio'
        formato = '%Y'

    # Alquileres creados en el periodo
    alquileres_creados = Alquiler.objects.filter(
        fecha_creacion__date__gte=fecha_inicio,
        fecha_creacion__date__lte=fecha_fin
    )
    # Alquileres cancelados en el periodo
    alquileres_cancelados = Alquiler.objects.filter(
        fecha_cancelacion__date__gte=fecha_inicio,
        fecha_cancelacion__date__lte=fecha_fin,
        estado='cancelado'
    )

    # Agrupación
    if agrupacion == 'dia':
        trunc = TruncDay
    elif agrupacion == 'semana':
        trunc = TruncWeek
    elif agrupacion == 'mes':
        trunc = TruncMonth
    else:
        trunc = TruncYear

    # Sumar monto_total de creados
    creados_agrupados = alquileres_creados.annotate(periodo=trunc('fecha_creacion')).values('periodo').annotate(monto=Sum('monto_total')).order_by('periodo')
    # Sumar monto_reembolso de cancelados
    cancelados_agrupados = alquileres_cancelados.annotate(periodo=trunc('fecha_cancelacion')).values('periodo').annotate(monto=Sum('monto_reembolso')).order_by('periodo')

    # Unir ambos resultados
    datos = defaultdict(lambda: Decimal('0.00'))
    for item in creados_agrupados:
        if item['periodo']:
            datos[item['periodo'].strftime(formato)] += item['monto'] or 0
    for item in cancelados_agrupados:
        if item['periodo']:
            datos[item['periodo'].strftime(formato)] -= item['monto'] or 0

    # Ordenar por periodo
    labels = sorted(datos.keys())
    data = [float(datos[label]) for label in labels]
    total = float(sum(data))

    return JsonResponse({
        'labels': labels,
        'data': data,
        'total': total
    })

def catalogo_grilla_ajax(request):
    # Lógica idéntica a catalogo_publico pero solo devuelve el HTML de la grilla
    query = request.GET.get('q', '')
    tipos_maquina = MaquinaBase.TIPOS_MAQUINA
    marcas = MaquinaBase.MARCAS
    precios = MaquinaBase.objects.filter(visible=True)
    precio_min = precios.order_by('precio_por_dia').first().precio_por_dia if precios.exists() else 0
    precio_max = precios.order_by('-precio_por_dia').first().precio_por_dia if precios.exists() else 0
    filtros = {
        'tipo': request.GET.getlist('tipo'),
        'marca': request.GET.getlist('marca'),
        'estado': request.GET.getlist('estado'),
        'precio_min': request.GET.get('precio_min', precio_min),
        'precio_max': request.GET.get('precio_max', precio_max),
    }
    maquinas = MaquinaBase.objects.filter(visible=True)
    if filtros['tipo']:
        maquinas = maquinas.filter(tipo__in=filtros['tipo'])
    if filtros['marca']:
        maquinas = maquinas.filter(marca__in=filtros['marca'])
    if filtros['estado']:
        estados = []
        if 'disponible' in filtros['estado']:
            estados.append(True)
        if 'no_disponible' in filtros['estado']:
            estados.append(False)
        maquinas = [m for m in maquinas if m.tiene_unidades_disponibles() in estados]
    else:
        maquinas = list(maquinas)
    try:
        pmin = float(filtros['precio_min'])
        pmax = float(filtros['precio_max'])
        maquinas = [m for m in maquinas if pmin <= float(m.precio_por_dia) <= pmax]
    except:
        pass
    if query:
        maquinas = [m for m in maquinas if query.lower() in m.nombre.lower() or query.lower() in m.modelo.lower() or query.lower() in m.descripcion_corta.lower() or query.lower() in m.descripcion_larga.lower()]
    for maquina in maquinas:
        if len(maquina.descripcion_corta) > 200:
            maquina.descripcion_vista = maquina.descripcion_corta[:197] + "..."
        else:
            maquina.descripcion_vista = maquina.descripcion_corta
    html = render_to_string('maquinas/_grilla_maquinas.html', {'maquinas': maquinas, 'request': request})
    return JsonResponse({'html': html})
