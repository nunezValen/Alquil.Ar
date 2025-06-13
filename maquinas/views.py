from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_http_methods
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
from django.db.models import Q
from django.core.mail import send_mail
from .utils import enviar_email_alquiler_simple, enviar_email_alquiler_cancelado

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
@user_passes_test(es_admin)
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def eliminar_maquina_base(request, maquina_id):
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
@user_passes_test(es_admin)
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
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def toggle_visibilidad_unidad(request, pk):
    unidad = get_object_or_404(Unidad, pk=pk)
    maquina_base = unidad.maquina_base
    
    # Si se intenta desocultar una unidad, verificar que su máquina base esté visible
    if not unidad.visible and not maquina_base.visible:
        messages.error(request, f'No se puede desocultar la unidad {unidad.patente} porque su máquina base está oculta.')
        return redirect('maquinas:lista_unidades')
    
    # Cambiar visibilidad y actualizar stock
    if unidad.visible:
        unidad.visible = False
        maquina_base.stock = max(0, maquina_base.stock - 1)  # Evitar stock negativo
        messages.success(request, f'La unidad {unidad.patente} ha sido ocultada.')
    else:
        unidad.visible = True
        maquina_base.stock += 1
        messages.success(request, f'La unidad {unidad.patente} ha sido desoculta.')
    
    unidad.save()
    maquina_base.save()
    return redirect('maquinas:lista_unidades')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def toggle_mantenimiento_unidad(request, pk):
    unidad = get_object_or_404(Unidad, pk=pk)
    
    # Solo permitir cambiar entre disponible y mantenimiento
    if unidad.estado == 'disponible':
        unidad.estado = 'mantenimiento'
        mensaje = f'La unidad {unidad.patente} ha sido puesta en mantenimiento.'
    elif unidad.estado == 'mantenimiento':
        unidad.estado = 'disponible'
        mensaje = f'La unidad {unidad.patente} ha sido marcada como disponible.'
    else:
        messages.error(request, 'Solo se puede cambiar el estado de unidades disponibles o en mantenimiento.')
        return redirect('maquinas:lista_unidades')
    
    unidad.save()
    messages.success(request, mensaje)
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
    maquinas = MaquinaBase.objects.filter(stock__gt=0).order_by('nombre')
    
    if query:
        maquinas = maquinas.filter(
            Q(nombre__icontains=query) |
            Q(tipo__icontains=query) |
            Q(marca__icontains=query) |
            Q(modelo__icontains=query) |
            Q(descripcion_corta__icontains=query) |
            Q(descripcion_larga__icontains=query)
        ).distinct()

    for maquina in maquinas:
        if len(maquina.descripcion_corta) > 200:
            maquina.descripcion_vista = maquina.descripcion_corta[:197] + "..."
        else:
            maquina.descripcion_vista = maquina.descripcion_corta
    
    return render(request, 'maquinas/catalogo_publico.html', {
        'maquinas': maquinas,
        'query': query
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
                
                # Inicializar el SDK de MercadoPago
                sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                
                # Obtener información del pago
                payment_info = sdk.payment().get(payment_id)
                print(f"Payment info: {payment_info}")
                
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
                                        monto_total=total
                                    )
                                    
                                    # NO marcar la unidad como alquilada hasta que comience el alquiler
                                    # El sistema manejará automáticamente las unidades disponibles por fechas
                                    
                                    print(f"Alquiler creado: {alquiler.numero}")
                                    
                                    # Enviar mail al cliente
                                    try:
                                        enviar_email_alquiler_simple(alquiler)
                                    except Exception as e:
                                        print(f"Error al enviar email: {str(e)}")
                                else:
                                    print("No hay unidades disponibles")
                                    
                            except Exception as e:
                                print(f"Error procesando pago aprobado: {str(e)}")
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
                    print(f"Error en payment info: {payment_info}")
                    return HttpResponse(status=400)
            else:
                print(f"Tipo de notificación no manejado: {data.get('type')}")
                return HttpResponse(status=200)
                
        except Exception as e:
            print(f"Error en webhook: {str(e)}")
            return HttpResponse(status=500)
    
    return HttpResponse(status=405)  # Method Not Allowed

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
            try:
                persona = Persona.objects.get(email=request.user.email)
            except Persona.DoesNotExist:
                return JsonResponse({
                    'error': 'No se encontró tu perfil de persona. Por favor, regístrate primero.'
                }, status=400)
            
            # VALIDACIÓN 1: Verificar que el cliente no tenga otro alquiler activo/reservado
            # UN CLIENTE SOLO PUEDE TENER UN ALQUILER A LA VEZ (sin importar fechas)
            alquileres_activos = Alquiler.objects.filter(
                persona=persona,
                estado__in=['reservado', 'en_curso']
            )
            
            if alquileres_activos.exists():
                alquiler_activo = alquileres_activos.first()
                return JsonResponse({
                    'error': f'Ya tienes un alquiler activo (#{alquiler_activo.numero}). '
                            f'Solo puedes tener un alquiler a la vez. '
                            f'Tu alquiler actual: {alquiler_activo.maquina_base.nombre} '
                            f'del {alquiler_activo.fecha_inicio.strftime("%d/%m/%Y")} '
                            f'al {alquiler_activo.fecha_fin.strftime("%d/%m/%Y")}. '
                            f'Contacta al soporte si necesitas cancelarlo.'
                }, status=400)
            
            # VALIDACIÓN 2: Verificar disponibilidad de unidades para las fechas
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
            
            # Calcular total
            total = dias * maquina.precio_por_dia
            
            # Procesar el pago con Mercado Pago SIN crear el alquiler aún
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            
            # Configurar preferencia de pago
            base_url = request.build_absolute_uri('/').rstrip('/')
            
            # Forzar HTTPS para ngrok
            if 'ngrok-free.app' in base_url:
                base_url = base_url.replace('http://', 'https://')
            
            # Preparar external_reference con los datos del alquiler
            # Formato: "maquina_id|persona_id|fecha_inicio|fecha_fin|metodo_pago|total"
            external_reference = f"{maquina.id}|{persona.id}|{fecha_inicio.strftime('%Y-%m-%d')}|{fecha_fin.strftime('%Y-%m-%d')}|{metodo_pago}|{total}"
            
            webhook_url = f"{base_url}/maquinas/webhook-mercadopago/"
            print(f"=== CONFIGURANDO PREFERENCIA ===")
            print(f"Base URL: {base_url}")
            print(f"Webhook URL: {webhook_url}")
            print(f"External reference: {external_reference}")
            
            preference_data = {
                "items": [{
                    "title": f"Alquiler de {maquina.nombre}",
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
            
            # Crear preferencia
            preference_response = sdk.preference().create(preference_data)
            
            if preference_response["status"] == 201:
                preference = preference_response["response"]
                
                print(f"=== PREFERENCIA CREADA ===")
                print(f"External reference: {external_reference}")
                print(f"Preference ID: {preference['id']}")
                
                return JsonResponse({
                    'init_point': preference["init_point"]
                })
            else:
                error_msg = f"Error al crear preferencia: {preference_response.get('message', 'Error desconocido')}"
                return JsonResponse({
                    'error': error_msg
                }, status=500)
                
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
    try:
        persona = Persona.objects.get(email=request.user.email)
        # Verificar si tiene cualquier alquiler activo (reservado o en curso)
        tiene_alquiler_activo = Alquiler.objects.filter(
            persona=persona,
            estado__in=['reservado', 'en_curso']
        ).exists()
    except:
        tiene_alquiler_activo = False
    
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
        'tiene_alquiler_activo': tiene_alquiler_activo
    })

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
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def editar_maquina_base(request, pk):
    maquina = get_object_or_404(MaquinaBase, pk=pk)
    if request.method == 'POST':
        form = MaquinaBaseForm(request.POST, instance=maquina)
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
@user_passes_test(es_admin)
def editar_unidad(request, pk):
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
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def toggle_mantenimiento_unidad(request, pk):
    unidad = get_object_or_404(Unidad, pk=pk)
    
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
@user_passes_test(es_admin)
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["POST"])
def desocultar_maquina_base(request, maquina_id):
    maquina = get_object_or_404(MaquinaBase, id=maquina_id)
    nombre_maquina = maquina.nombre
    try:
        maquina.visible = True
        maquina.save()
        messages.success(request, f'La máquina base {nombre_maquina} ha sido desocultada exitosamente.')
    except Exception as e:
        messages.error(request, f'Error al desocultar la máquina: {str(e)}')
    return redirect('maquinas:lista_maquinas')
