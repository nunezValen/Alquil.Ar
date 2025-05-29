from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from .models import Persona, Maquina, Empleado, Alquiler
from .forms import PersonaForm, AlquilerForm
from datetime import date, datetime
import random, string
import mercadopago
import binance
from pyngrok import ngrok
import json
from django.urls import reverse

def inicio(request):
    return HttpResponse("<h1>Bienvenido a nuestra página de inicio</h1>")

@login_required
def catalogo_maquinas(request):
    maquinas = Maquina.objects.filter(estado='disponible')
    return render(request, 'persona/catalogo_maquinas.html', {'maquinas': maquinas})

@login_required
def detalle_maquina(request, maquina_id):
    maquina = get_object_or_404(Maquina, id=maquina_id)
    alquiler = None
    
    if request.method == 'POST':
        print(">>> POST recibido en detalle_maquina")
        form = AlquilerForm(request.POST)
        if form.is_valid():
            print(">>> Formulario válido")
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            metodo_pago = form.cleaned_data['metodo_pago']
            
            # Validar días mínimos
            dias = (fecha_fin - fecha_inicio).days + 1
            if dias < maquina.dias_minimos:
                form.add_error(None, f"El alquiler mínimo es de {maquina.dias_minimos} días.")
            else:
                try:
                    # Obtener la persona asociada al usuario
                    try:
                        persona = Persona.objects.get(email=request.user.email)
                        print(f">>> Persona encontrada: {persona.email}")
                    except Persona.DoesNotExist:
                        print(">>> Error: No se encontró la persona")
                        form.add_error(None, "No se encontró tu perfil de persona. Por favor, regístrate primero.")
                        return render(request, 'persona/detalle_maquina.html', {
                            'maquina': maquina,
                            'form': form,
                            'mercadopago_public_key': settings.MERCADOPAGO_PUBLIC_KEY
                        })

                    # Crear el alquiler
                    alquiler = Alquiler.objects.create(
                        maquina=maquina,
                        persona=persona,
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                        metodo_pago=metodo_pago,
                        estado='pendiente'
                    )
                    print(f">>> Alquiler creado con ID: {alquiler.id}")
                    
                    # Procesar el pago según el método seleccionado
                    if metodo_pago == 'mercadopago':
                        print(">>> Iniciando proceso de pago con Mercado Pago")
                        # Inicializar SDK de Mercado Pago
                        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                        print(f">>> SDK inicializado con token: {settings.MERCADOPAGO_ACCESS_TOKEN[:10]}...")
                        
                        # Configurar preferencia de pago
                        base_url = request.build_absolute_uri('/').rstrip('/')
                        preference_data = {
                            "items": [{
                                "title": f"Alquiler de {maquina.nombre}",
                                "quantity": 1,
                                "currency_id": "ARS",
                                "unit_price": float(maquina.precio_dia * dias + 1) #+1 para que el precio sea el correcto porque si no da el precio por ser precio 0
                            }],
                            "back_urls": {
                                "success": f"{base_url}/persona/checkout/{alquiler.id}/",
                                "failure": f"{base_url}/persona/maquina/{maquina.id}/",
                                "pending": f"{base_url}/persona/checkout/{alquiler.id}/"
                            },
                            "external_reference": str(alquiler.id),
                            "notification_url": f"{base_url}/persona/webhook/mercadopago/",
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
                        print(f">>> Datos de preferencia: {preference_data}")
                        
                        # Crear preferencia
                        preference_response = sdk.preference().create(preference_data)
                        print(f">>> Respuesta de Mercado Pago: {preference_response}")
                        
                        if preference_response["status"] == 201:
                            preference = preference_response["response"]
                            print(f">>> Preferencia creada con ID: {preference['id']}")
                            print(f">>> URL de redirección: {preference['init_point']}")
                            
                            # Guardar el ID de preferencia
                            alquiler.preference_id = preference["id"]
                            alquiler.save()
                            
                            # Redirigir al checkout de Mercado Pago
                            return redirect(preference["init_point"])
                        else:
                            error_msg = f"Error al crear preferencia: {preference_response.get('message', 'Error desconocido')}"
                            print(f">>> {error_msg}")
                            raise Exception(error_msg)
                        
                    elif metodo_pago == 'binance':
                        # Implementar lógica de Binance Pay
                        pass
                        
                except Exception as e:
                    print(f">>> Error en el proceso: {str(e)}")
                    if alquiler:
                        alquiler.delete()
                    form.add_error(None, f"Error al procesar el pago: {str(e)}")
        else:
            print(f">>> Errores en el formulario: {form.errors}")
    else:
        form = AlquilerForm()
    
    return render(request, 'persona/detalle_maquina.html', {
        'maquina': maquina,
        'form': form,
        'mercadopago_public_key': settings.MERCADOPAGO_PUBLIC_KEY
    })

@login_required
def mis_alquileres(request):
    alquileres = Alquiler.objects.filter(cliente=request.user).order_by('-fecha_creacion')
    return render(request, 'persona/mis_alquileres.html', {'alquileres': alquileres})

def lista_maquinas(request):
    maquinas = Maquina.objects.all()
    return render(request, 'lista_maquina.html', {'maquinas': maquinas})

def lista_empleados(request):
    empleados = Empleado.objects.all()
    return render(request, 'lista_empleado.html', {'empleados': empleados})

def lista_personas(request):
    personas = Persona.objects.all()
    return render(request, 'lista_persona.html', {'personas': personas})

def registrar_persona(request):
    error = None
    if request.method == 'POST':
        post = request.POST.copy()
        dia = post.get('fecha_dia')
        mes = post.get('fecha_mes')
        anio = post.get('fecha_anio')
        if dia and mes and anio:
            post['fecha_nacimiento'] = f"{anio}-{mes.zfill(2)}-{dia.zfill(2)}"
        form = PersonaForm(post)
        if form.is_valid():
            persona = form.save()
            email = persona.email
            print('EMAIL CAPTURADO EN REGISTRO:', email)
            if email:
                if User.objects.filter(username=email).exists():
                    error = 'Ya existe un usuario con ese email. Si no recibiste el correo, contacta al administrador.'
                else:
                    try:
                        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                        user = User.objects.create_user(username=email, email=email, password=password,
                            first_name=persona.nombre, last_name=persona.apellido)
                        send_mail(
                            'Tu cuenta en Alquil.ar',
                            f'Hola {persona.nombre},\n\nTu usuario ha sido creado.\n\nUsuario: {email}\nContraseña: {password}\n\nPor favor, cambia tu contraseña después de iniciar sesión.',
                            'no-reply@alquilar.com.ar',
                            [email],
                            fail_silently=False,
                        )
                        messages.success(request, 'Persona registrada exitosamente. Recibirás tu contraseña por email.')
                        return redirect('registrar_persona')
                    except Exception as e:
                        error = f'Error al enviar el correo: {e}'
    else:
        form = PersonaForm()
    return render(request, 'persona/registrar_persona.html', {'form': form, 'error': error})

def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('inicio_blanco')
        else:
            error = 'Usuario o contraseña incorrectos.'
    return render(request, 'login.html', {'error': error})

@login_required
def inicio_blanco(request):
    return render(request, 'inicio_blanco.html')

@login_required
def webhook_mercadopago(request):
    if request.method == 'POST':
        try:
            # Obtener los datos del webhook
            data = json.loads(request.body)
            print(f"Webhook recibido: {data}")
            
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
                    
                    print(f"External reference: {external_reference}")
                    print(f"Status: {status}")
                    
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
                        print(f"Alquiler actualizado: {alquiler.id} - Estado: {alquiler.estado}")
                        
                    except Alquiler.DoesNotExist:
                        print(f"Alquiler no encontrado: {external_reference}")
                        return HttpResponse(status=404)
                    
                    return HttpResponse(status=200)
                else:
                    print(f"Error al obtener información del pago: {payment_info}")
                    return HttpResponse(status=400)
            else:
                print(f"Tipo de notificación no manejado: {data.get('type')}")
                return HttpResponse(status=200)
                
        except Exception as e:
            print(f"Error en webhook: {str(e)}")
            return HttpResponse(status=500)
    
    return HttpResponse(status=405)  # Method Not Allowed

@login_required
def checkout_mp(request, alquiler_id):
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)
    
    # Verificar que el alquiler pertenece al usuario actual
    if alquiler.persona.email != request.user.email:
        messages.error(request, "No tienes permiso para ver este alquiler.")
        return redirect('catalogo_maquinas')
    
    return render(request, 'persona/checkout_mp.html', {
        'maquina': alquiler.maquina,
        'alquiler': alquiler,
        'preference_id': alquiler.preference_id,
        'mercadopago_public_key': settings.MERCADOPAGO_PUBLIC_KEY
    })

# Create your views here.
