from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from persona.views import es_empleado_o_admin
from .forms import MaquinaBaseForm, AlquilerForm
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
                        estado='pendiente'
                    )
                    
                    # Procesar el pago según el método seleccionado
                    if metodo_pago == 'mercadopago':
                        # Inicializar SDK de Mercado Pago
                        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                        
                        # Configurar preferencia de pago
                        base_url = request.build_absolute_uri('/').rstrip('/')
                        preference_data = {
                            "items": [{
                                "title": f"Alquiler de {maquina.nombre}",
                                "quantity": 1,
                                "currency_id": "ARS",
                                "unit_price": float(maquina.precio_por_dia * dias)
                            }],
                            "back_urls": {
                                "success": f"{base_url}/maquinas/checkout/{alquiler.id}/",
                                "failure": f"{base_url}/maquinas/maquina/{maquina.id}/",
                                "pending": f"{base_url}/maquinas/checkout/{alquiler.id}/"
                            },
                            "external_reference": str(alquiler.id),
                            "notification_url": f"{base_url}/maquinas/webhook/mercadopago/",
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
                            
                            # Guardar el ID de preferencia
                            alquiler.preference_id = preference["id"]
                            alquiler.save()
                            
                            # Redirigir al checkout de Mercado Pago
                            return redirect(preference["init_point"])
                        else:
                            error_msg = f"Error al crear preferencia: {preference_response.get('message', 'Error desconocido')}"
                            raise Exception(error_msg)
                        
                    elif metodo_pago == 'binance':
                        # Implementar lógica de Binance Pay
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
            maquina.delete()
            messages.success(request, f'La máquina base {nombre_maquina} ha sido eliminada exitosamente.')
            return redirect('maquinas:lista_maquinas')
        except Exception as e:
            messages.error(request, 'No se puede eliminar la máquina porque tiene unidades asociadas.')
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
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def toggle_visibilidad_unidad(request, pk):
    unidad = get_object_or_404(Unidad, pk=pk)
    maquina_base = unidad.maquina_base
    
    # Cambiar visibilidad y actualizar stock
    if unidad.visible:
        unidad.visible = False
        maquina_base.stock = max(0, maquina_base.stock - 1)  # Evitar stock negativo
        messages.success(request, f'La unidad {unidad.patente} ahora está oculta.')
    else:
        unidad.visible = True
        maquina_base.stock += 1
        messages.success(request, f'La unidad {unidad.patente} ahora es visible.')
    
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
@user_passes_test(es_admin)
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def cargar_unidad(request):
    if request.method == 'POST':
        form = UnidadForm(request.POST)
        if form.is_valid():
            unidad = form.save()
            messages.success(request, f"La unidad con patente '{unidad.patente}' ha sido cargada con éxito.")
            return redirect('maquinas:lista_unidades')
    else:
        form = UnidadForm()

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

@login_required
@user_passes_test(es_empleado_o_admin)
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def webhook_mercadopago(request):
    if request.method == 'POST':
        try:
            # Obtener los datos del webhook
            data = json.loads(request.body)
            
            # Verificar el tipo de notificación
            if data.get('type') == 'payment':
                payment_id = data.get('data', {}).get('id')
                
                # Inicializar el SDK de MercadoPago
                sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                
                # Obtener información del pago
                payment_info = sdk.payment().get(payment_id)
                
                if payment_info['status'] == 200:
                    payment_data = payment_info['response']
                    external_reference = payment_data.get('external_reference')
                    status = payment_data.get('status')
                    
                    # Buscar el alquiler correspondiente
                    try:
                        alquiler = Alquiler.objects.get(id=external_reference)
                        
                        # Actualizar el estado del alquiler según el estado del pago
                        if status == 'approved':
                            alquiler.estado = 'confirmado'
                            messages.success(request, 'Pago aprobado exitosamente')
                        elif status == 'rejected':
                            alquiler.estado = 'rechazado'
                            messages.error(request, 'El pago fue rechazado')
                        elif status == 'pending':
                            alquiler.estado = 'pendiente'
                            messages.warning(request, 'El pago está pendiente')
                        
                        alquiler.save()
                        
                    except Alquiler.DoesNotExist:
                        return HttpResponse(status=404)
                    
                    return HttpResponse(status=200)
                else:
                    return HttpResponse(status=400)
            else:
                return HttpResponse(status=200)
                
        except Exception as e:
            return HttpResponse(status=500)
    
    return HttpResponse(status=405)  # Method Not Allowed

@login_required
def alquilar_maquina(request, maquina_id):
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
            
            # Calcular total
            total = dias * maquina.precio_por_dia
            
            # Crear el alquiler
            alquiler = Alquiler.objects.create(
                maquina_base=maquina,
                persona=persona,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                metodo_pago=metodo_pago,
                estado='pendiente',
                monto_total=total
            )
            
            # Procesar el pago con Mercado Pago
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            
            # Configurar preferencia de pago
            base_url = request.build_absolute_uri('/').rstrip('/')
            preference_data = {
                "items": [{
                    "title": f"Alquiler de {maquina.nombre}",
                    "quantity": 1,
                    "currency_id": "ARS",
                    "unit_price": float(total + 1)  # +1 para evitar problemas con precio 0
                }],
                "back_urls": {
                    "success": f"{base_url}/maquinas/confirmar-alquiler/",
                    "failure": f"{base_url}/maquinas/error-pago/",
                    "pending": f"{base_url}/maquinas/pago-pendiente/"
                },
                "external_reference": str(alquiler.id),
                "notification_url": f"{base_url}/maquinas/webhook-mercadopago/",
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
                
                # Guardar el ID de preferencia
                alquiler.preference_id = preference["id"]
                alquiler.save()
                
                return JsonResponse({
                    'init_point': preference["init_point"]
                })
            else:
                error_msg = f"Error al crear preferencia: {preference_response.get('message', 'Error desconocido')}"
                alquiler.delete()  # Eliminar el alquiler si falla la creación de la preferencia
                return JsonResponse({
                    'error': error_msg
                }, status=500)
                
        except Exception as e:
            if 'alquiler' in locals():
                alquiler.delete()
            return JsonResponse({
                'error': f'Error al procesar el pago: {str(e)}'
            }, status=500)
    
    # Para GET, devolver los datos necesarios para el modal
    fecha_minima = date.today()
    return JsonResponse({
        'maquina': {
            'id': maquina.id,
            'nombre': maquina.nombre,
            'precio_por_dia': maquina.precio_por_dia,
            'dias_min': maquina.dias_alquiler_min,
            'dias_max': maquina.dias_alquiler_max,
            'imagen_url': maquina.imagen.url if maquina.imagen else None
        },
        'fecha_minima': fecha_minima.strftime('%Y-%m-%d')
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
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def editar_unidad(request, pk):
    unidad = get_object_or_404(Unidad, pk=pk)
    if request.method == 'POST':
        form = UnidadForm(request.POST, request.FILES, instance=unidad)
        if form.is_valid():
            patente_nueva = form.cleaned_data['patente']
            # Buscar si existe otra unidad (diferente a la actual) con la misma patente
            existe_patente = Unidad.objects.filter(patente=patente_nueva).exclude(id=pk).exists()
            
            if existe_patente:
                form.add_error('patente', 'Ya existe otra unidad con esta patente.')
                return render(request, 'maquinas/editar_unidad.html', {
                    'form': form,
                    'unidad': unidad
                })
            
            form.save()
            messages.success(request, 'Unidad actualizada exitosamente.')
            return redirect('maquinas:lista_unidades')
    else:
        form = UnidadForm(instance=unidad)
    
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
