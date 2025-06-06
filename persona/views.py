from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, update_session_auth_hash, logout
from .models import Persona, Maquina, Sucursal
from .forms import PersonaForm
from datetime import date
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import Persona, Maquina, Alquiler
from maquinas.models import MaquinaBase
from .forms import PersonaForm, EditarPersonaForm, AlquilerForm, CambiarPasswordForm
from datetime import date, datetime
from django.contrib.auth.forms import PasswordChangeForm
import random, string
import mercadopago
import binance
from pyngrok import ngrok
import json
from .utils import generar_password_random

def es_admin(user):
    """
    Verifica si el usuario es administrador
    """
    return user.is_authenticated and user.is_superuser

def es_empleado_o_admin(user):
    """Verifica si el usuario es empleado o administrador"""
    if not user.is_authenticated:
        return False
    try:
        persona = Persona.objects.get(email=user.email)
        return persona.es_empleado or user.is_superuser
    except Persona.DoesNotExist:
        return user.is_superuser

def inicio(request):
    maquinas = MaquinaBase.objects.filter(stock__gt=0)[:4]  # Obtener las primeras 4 máquinas con stock
    for maquina in maquinas:
        # Creamos un atributo temporal solo para la vista
        if len(maquina.descripcion_corta) > 300:
            maquina.descripcion_vista = maquina.descripcion_corta[:297] + "..."
        else:
            maquina.descripcion_vista = maquina.descripcion_corta
    return render(request, 'persona/inicio.html', {'maquinas': maquinas})

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
        form = AlquilerForm(request.POST, maquina=maquina)
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
                                "unit_price": float(maquina.precio_dia * dias + 1)
                            }],
                            "back_urls": {
                                "success": f"{base_url}/persona/checkout/{alquiler.id}/?status=approved",
                                "failure": f"{base_url}/persona/checkout/{alquiler.id}/?status=failure",
                                "pending": f"{base_url}/persona/checkout/{alquiler.id}/?status=pending"
                            },
                            "auto_return": "approved",
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
                            
                            # Retornar la URL de MercadoPago
                            return JsonResponse({
                                'status': 'success',
                                'redirect_url': preference["init_point"]
                            })
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
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e)
                    }, status=400)
        else:
            print(f">>> Errores en el formulario: {form.errors}")
            return JsonResponse({
                'status': 'error',
                'message': 'Formulario inválido',
                'errors': dict(form.errors)
            }, status=400)
    else:
        form = AlquilerForm(maquina=maquina)
    
    return render(request, 'persona/detalle_maquina.html', {
        'maquina': maquina,
        'form': form,
        'mercadopago_public_key': settings.MERCADOPAGO_PUBLIC_KEY
    })

@login_required
def mis_alquileres(request):
    alquileres = Alquiler.objects.filter(persona__email=request.user.email).order_by('-fecha_creacion')
    return render(request, 'persona/mis_alquileres.html', {'alquileres': alquileres})

def lista_maquinas(request):
    search_query = request.GET.get('q', '')
    maquinas = MaquinaBase.objects.filter(stock__gt=0)  # Solo máquinas con stock

    if search_query:
        maquinas = maquinas.filter(nombre__icontains=search_query)

    for maquina in maquinas:
        if len(maquina.descripcion_corta) > 200:
            maquina.descripcion_vista = maquina.descripcion_corta[:197] + "..."
        else:
            maquina.descripcion_vista = maquina.descripcion_corta

    return render(request, 'persona/catalogo.html', {'maquinas': maquinas})

def lista_empleados(request):
    empleados = Persona.objects.filter(es_empleado=True)  # Consulta todos los empleados
    return render(request, 'lista_empleado.html', {'empleados': empleados})

def lista_personas(request):
    personas = Persona.objects.all()
    personas = Persona.objects.all()  # Consulta todas las personas
    return render(request, 'lista_persona.html', {'personas': personas})

@login_required
@user_passes_test(es_empleado_o_admin)
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def registrar_persona(request):
    if request.method == 'POST':
        form = PersonaForm(request.POST)
        if form.is_valid():
            persona = form.save(commit=False)
            persona.es_cliente = True
            
            # Verificar que el email exista
            if not persona.email:
                form.add_error('email', 'El email es obligatorio para registrar un cliente.')
                return render(request, 'persona/registrar_persona.html', {'form': form})
            
            # Generar contraseña aleatoria
            password = generar_password_random()
            
            try:
                # Crear usuario en Django
                user = User.objects.create_user(
                    username=persona.email,
                    email=persona.email,
                    password=password,
                    first_name=persona.nombre,
                    last_name=persona.apellido
                )
                
                persona.save()
                
                # Enviar email con la contraseña
                send_mail(
                    'Bienvenido a Alquil.Ar - Tu contraseña',
                    f'Hola {persona.nombre},\n\nTu cuenta ha sido creada exitosamente. Tu contraseña es: {password}\n\nPor favor, cambia tu contraseña la próxima vez que inicies sesión.\n\nSaludos,\nEquipo Alquil.Ar',
                    settings.DEFAULT_FROM_EMAIL,
                    [persona.email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Te has registrado exitosamente. Por favor, revisa tu email para obtener tu contraseña.')
                return redirect('persona:login_unificado2')
            except Exception as e:
                # Si algo falla, eliminar el usuario si fue creado
                if 'user' in locals():
                    user.delete()
                form.add_error(None, f'Error al crear el usuario: {str(e)}')
                return render(request, 'persona/registrar_persona.html', {'form': form})
    else:
        form = PersonaForm()
    return render(request, 'persona/registrar_persona.html', {'form': form})

@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def login_view(request):
    error = None
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')

        try:
            persona = Persona.objects.get(email=email)
            if persona.es_baneado:
                error = 'Tu cuenta está suspendida. Contacta al administrador.'
            else:
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    login(request, user)
                    if persona.es_empleado or persona.es_admin:
                        return redirect('persona:inicio')
                    elif persona.es_cliente:
                        return redirect('persona:inicio')
                    else:
                        error = 'No tienes permisos para acceder.'
                else:
                    error = 'Email o contraseña incorrectos'
        except Persona.DoesNotExist:
            error = 'Email o contraseña incorrectos'

    return render(request, 'login.html', {'error': error})

@login_required
def pagina_principal(request):
    return redirect('persona:inicio')

@login_required
@user_passes_test(es_admin)
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def registrar_empleado(request):
    if request.method == 'POST':
        form = PersonaForm(request.POST)
        if form.is_valid():
            persona = form.save(commit=False)
            persona.es_empleado = True
            persona.es_cliente = True  # Todo empleado es cliente
            persona.save()

            email = persona.email
            if email:
                if User.objects.filter(username=email).exists():
                    messages.error(request, 'Ya existe un usuario con ese email.')
                else:
                    try:
                        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                        user = User.objects.create_user(
                            username=email,
                            email=email,
                            password=password,
                            first_name=persona.nombre,
                            last_name=persona.apellido,
                            is_staff=True
                        )
                        send_mail(
                            'Tu cuenta de empleado en Alquil.ar',
                            f'Hola {persona.nombre},\n\nTu usuario ha sido creado.\n\nUsuario: {email}\nContraseña: {password}\n\nPor favor, cambia tu contraseña después de iniciar sesión.',
                            'no-reply@alquilar.com.ar',
                            [email],
                            fail_silently=False,
                        )
                        messages.success(request, 'Empleado registrado exitosamente. Recibirá su contraseña por email.')
                        return redirect('persona:registrar_empleado')
                    except Exception as e:
                        messages.error(request, f'Error al enviar el correo: {e}')
    else:
        form = PersonaForm()

    return render(request, 'persona/registrar_empleado.html', {'form': form})

@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def login_empleado(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Agregamos el prefijo emp_ al username para buscar el usuario correcto
        user = authenticate(request, username=f"emp_{username}", password=password)
        if user is not None:
            login(request, user)
            return redirect('persona:inicio')
        else:
            error = 'Usuario o contraseña incorrectos.'
    return render(request, 'login_empleado.html', {'error': error})

@login_required
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def cambiar_password(request):
    if request.method == 'POST':
        password_actual = request.POST.get('password_actual')
        password_nuevo = request.POST.get('password_nuevo')
        password_confirmacion = request.POST.get('password_confirmacion')
        
        # Validar longitud de la nueva contraseña
        if len(password_nuevo) < 6:
            messages.error(request, 'La nueva contraseña debe tener al menos 6 caracteres.')
            return redirect('persona:cambiar_password')
        
        if len(password_nuevo) > 16:
            messages.error(request, 'La nueva contraseña no puede tener más de 16 caracteres.')
            return redirect('persona:cambiar_password')
        
        # Validar que las contraseñas coincidan
        if password_nuevo != password_confirmacion:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('persona:cambiar_password')
        
        # Verificar la contraseña actual
        user = request.user
        if not user.check_password(password_actual):
            messages.error(request, 'La contraseña actual es incorrecta.')
            return redirect('persona:cambiar_password')
        
        # Cambiar la contraseña
        user.set_password(password_nuevo)
        user.save()
        
        # Actualizar la sesión para que el usuario no tenga que volver a iniciar sesión
        update_session_auth_hash(request, user)
        
        messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
        return redirect('persona:inicio')
    
    return render(request, 'persona/cambiar_password.html')

@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def cambiar_password_empleado(request):
    error = None
    success = None
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            error = 'Las contraseñas no coinciden.'
        elif len(password1) < 6:
            error = 'La contraseña debe tener al menos 6 caracteres.'
        elif len(password1) > 16:
            error = 'La contraseña no puede tener más de 16 caracteres.'
        else:
            user = request.user
            user.set_password(password1)
            user.save()
            update_session_auth_hash(request, user)  # Mantiene la sesión activa
            success = 'Contraseña cambiada exitosamente.'

    return render(request, 'cambiar_password_empleado.html', {'error': error, 'success': success})

@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def cambiar_password_logueado(request):
    error = None
    success = None
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            error = 'Las contraseñas no coinciden.'
        elif len(password1) < 6:
            error = 'La contraseña debe tener al menos 6 caracteres.'
        elif len(password1) > 16:
            error = 'La contraseña no puede tener más de 16 caracteres.'
        else:
            user = request.user
            user.set_password(password1)
            user.save()
            update_session_auth_hash(request, user)  # Mantiene la sesión activa
            success = 'Contraseña cambiada exitosamente.'

    return render(request, 'cambiar_password_logueado.html', {'error': error, 'success': success})

@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def cambiar_password_empleado_logueado(request):
    error = None
    success = None
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            error = 'Las contraseñas no coinciden.'
        elif len(password1) < 6:
            error = 'La contraseña debe tener al menos 6 caracteres.'
        elif len(password1) > 16:
            error = 'La contraseña no puede tener más de 16 caracteres.'
        else:
            user = request.user
            user.set_password(password1)
            user.save()
            update_session_auth_hash(request, user)  # Mantiene la sesión activa
            success = 'Contraseña cambiada exitosamente.'

    return render(request, 'cambiar_password_empleado_logueado.html', {'error': error, 'success': success})

@login_required
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def login_as_persona(request):
    error = None
    success = None

    # Verificar que el usuario actual es un empleado
    try:
        persona = Persona.objects.get(email=request.user.email)
        if not persona.es_empleado and not request.user.is_staff:
            return redirect('persona:inicio')
    except Persona.DoesNotExist:
        return redirect('persona:inicio')

    if request.method == 'POST':
        email = request.user.email  # El email del empleado actual

        try:
            # Buscar si existe una cuenta Persona con el mismo email
            persona = Persona.objects.get(email=email)

            if persona.es_cliente:
                # Guardar en la sesión que el usuario es un empleado actuando como cliente
                request.session['es_empleado_actuando_como_cliente'] = True
                messages.success(request, 'Has cambiado a tu cuenta personal exitosamente.')
                return redirect('persona:inicio')
            else:
                error = 'No tienes una cuenta personal asociada a este email'
        except Persona.DoesNotExist:
            error = 'No existe una cuenta Persona asociada a este email'

    return render(request, 'login_as_persona.html', {'error': error, 'success': success})

@login_required
def inicio_blanco(request):
    maquinas = MaquinaBase.objects.filter(stock__gt=0)[:4]  # Obtener las primeras 4 máquinas con stock
    for maquina in maquinas:
        # Creamos un atributo temporal solo para la vista
        if len(maquina.descripcion_corta) > 300:
            maquina.descripcion_vista = maquina.descripcion_corta[:297] + "..."
        else:
            maquina.descripcion_vista = maquina.descripcion_corta
    return render(request, 'persona/inicio_blanco.html', {'maquinas': maquinas})

@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def login_unificado2(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # 1. Buscar en modelo Persona
        try:
            persona = Persona.objects.get(email=email)
            if persona.es_baneado:
                return render(request, 'persona/login_unificado2.html', {
                    'error': 'Tu cuenta está suspendida. Contacta al administrador.'
                })
            else:
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('persona:inicio')
                else:
                    return render(request, 'persona/login_unificado2.html', {
                        'error': 'Email o contraseña incorrectos'
                    })
        except Persona.DoesNotExist:
            return render(request, 'persona/login_unificado2.html', {
                'error': 'Email o contraseña incorrectos'
            })

    # Si es GET, mostrar el formulario
    return render(request, 'persona/login_unificado2.html')

@login_required
@user_passes_test(es_empleado_o_admin)
def gestion(request):
    """Vista de gestión accesible para empleados y administradores"""
    return render(request, 'persona/gestion.html')

@login_required
@user_passes_test(es_admin)
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def estadisticas(request):
    """Vista de estadísticas accesible solo para administradores"""
    return render(request, 'persona/estadisticas.html')

def empleados_processor(request):
    """Context processor que agrega la lista de emails de empleados al contexto de todos los templates."""
    empleados_emails = list(Persona.objects.filter(es_empleado=True).values_list('email', flat=True))

    # Agregar la variable de sesión al contexto
    es_empleado_actuando_como_cliente = request.session.get('es_empleado_actuando_como_cliente', False)

    return {
        'empleados_emails': empleados_emails,
        'es_empleado_actuando_como_cliente': es_empleado_actuando_como_cliente
    }

@login_required
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def switch_back_to_employee(request):
    """Vista para volver a la cuenta de empleado desde la cuenta personal"""
    # Verificar si el usuario está actuando como cliente pero es empleado
    if request.session.get('es_empleado_actuando_como_cliente', False):
        # Eliminar la variable de sesión
        del request.session['es_empleado_actuando_como_cliente']
        messages.success(request, 'Has vuelto a tu cuenta de empleado exitosamente.')
    return redirect('persona:inicio')

def logout_view(request):
    """Vista para cerrar sesión"""
    # Limpiar la variable de sesión que indica que el usuario es un empleado actuando como cliente
    if 'es_empleado_actuando_como_cliente' in request.session:
        del request.session['es_empleado_actuando_como_cliente']
    logout(request)
    messages.success(request, 'Cierre de sesión exitoso')
    return redirect('persona:inicio')

@login_required
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def editar_datos_personales(request):
    return redirect('persona:inicio')

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
                            # Actualizar el estado de la máquina a 'alquilada'
                            maquina = alquiler.maquina
                            maquina.estado = 'alquilada'
                            maquina.save()
                            print(f"Máquina actualizada: {maquina.id} - Estado: {maquina.estado}")
                            messages.success(request, 'Pago aprobado exitosamente')
                        elif status == 'rejected':
                            alquiler.estado = 'cancelado'
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
def checkout(request, alquiler_id):
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)
    status = request.GET.get('status')
    
    # Verificar que el alquiler pertenece al usuario actual
    if alquiler.persona.email != request.user.email:
        messages.error(request, "No tienes permiso para acceder a este alquiler.")
        return redirect('persona:mis_alquileres')
    
    if status == 'approved':
        # Actualizar el estado del alquiler
        alquiler.estado = 'confirmado'
        alquiler.save()
        
        # Marcar la máquina como alquilada
        maquina = alquiler.maquina
        maquina.estado = 'alquilada'
        maquina.save()
        
        messages.success(request, "¡Pago exitoso! Tu alquiler ha sido confirmado.")
    elif status == 'pending':
        alquiler.estado = 'pendiente'
        alquiler.save()
        messages.info(request, "El pago está pendiente de confirmación.")
    else:
        alquiler.estado = 'fallido'
        alquiler.save()
        messages.error(request, "El pago no pudo ser procesado. Por favor, intenta nuevamente.")
    
    return redirect('persona:mis_alquileres')

@login_required
@user_passes_test(es_empleado_o_admin)
def lista_alquileres(request):
    alquileres = Alquiler.objects.all().order_by('-fecha_creacion')
    return render(request, 'persona/lista_alquileres.html', {'alquileres': alquileres})

def recuperar_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            # Buscar la persona por email
            persona = Persona.objects.get(email=email)
            
            # Buscar todos los usuarios asociados
            users = User.objects.filter(email=email)
            if users.exists():
                # Generar nueva contraseña aleatoria
                nueva_password = generar_password_random()
                
                # Actualizar la contraseña de todos los usuarios con ese email
                for user in users:
                    user.set_password(nueva_password)
                    user.save()
                
                # Enviar email con la nueva contraseña
                send_mail(
                    'Alquil.Ar - Tu nueva contraseña',
                    f'Hola {persona.nombre},\n\n'
                    f'Has solicitado una nueva contraseña.\n\n'
                    f'Tu nueva contraseña es: {nueva_password}\n\n'
                    f'Por favor, cambia tu contraseña la próxima vez que inicies sesión.\n\n'
                    f'Saludos,\n'
                    f'Equipo Alquil.Ar',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
            
        except (Persona.DoesNotExist, User.DoesNotExist, Exception):
            # Si el email no existe o hay algún error, simplemente continuamos
            pass
        
        # Siempre mostramos mensaje de éxito
        messages.success(request, 'Se ha enviado una nueva contraseña a tu email.')
        return redirect('persona:login_unificado2')
    
    return render(request, 'persona/recuperar_password.html')

def mapa_sucursales(request):
    try:
        sucursales = Sucursal.objects.all()
        
        # Validar que las coordenadas sean válidas
        for sucursal in sucursales:
            if not (-90 <= sucursal.latitud <= 90) or not (-180 <= sucursal.longitud <= 180):
                raise ValueError(f'Coordenadas inválidas en sucursal {sucursal.id_sucursal}')
        
        return render(request, 'mapa_sucursales.html', {
            'sucursales': sucursales,
            'centro_mapa': [-34.9214, -57.9544]  # Coordenadas de La Plata
        })
    except ValueError as e:
        messages.error(request, f'Error en las coordenadas: {str(e)}')
        return redirect('persona:inicio')
    except Exception as e:
        messages.error(request, 'Ocurrió un error al cargar el mapa de sucursales')
        return redirect('persona:inicio')

# Create your views here.
