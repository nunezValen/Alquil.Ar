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
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie, csrf_exempt
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
from django.db.models import Q, Count
from django.core.paginator import Paginator
from maquinas.models import Alquiler, MaquinaBase
from maquinas.utils import enviar_email_alquiler_simple

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
    """Vista de inicio con manejo de retorno de MercadoPago"""
    
    # Obtener datos para mostrar en la página
    empleados_emails = None
    es_empleado_actuando_como_cliente = False
    
    if request.user.is_authenticated:
        try:
            persona = Persona.objects.get(email=request.user.email)
            es_empleado_actuando_como_cliente = request.session.get('es_empleado_actuando_como_cliente', False)
            
            if es_empleado_actuando_como_cliente or persona.es_empleado:
                empleados_emails = Persona.objects.filter(es_empleado=True).values_list('email', flat=True)
        except Persona.DoesNotExist:
            pass
    
    # Manejar retorno de MercadoPago (fallback si el webhook no funciona)
    status = request.GET.get('status')
    external_reference = request.GET.get('external_reference')
    
    if status and external_reference and request.user.is_authenticated:
        print(f"=== PROCESANDO RETORNO DE MERCADOPAGO ===")
        print(f"Status: {status}")
        print(f"External reference: {external_reference}")
        
        if status == 'approved':
            try:
                # Parsear los datos del external_reference
                # Formato: "maquina_id|persona_id|fecha_inicio|fecha_fin|metodo_pago|total"
                datos = external_reference.split('|')
                if len(datos) == 6:
                    from datetime import datetime
                    
                    maquina_id, persona_id, fecha_inicio_str, fecha_fin_str, metodo_pago, total = datos
                    
                    # Convertir fechas
                    fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
                    fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
                    
                    # Obtener objetos
                    maquina_base = MaquinaBase.objects.get(id=maquina_id)
                    persona = Persona.objects.get(id=persona_id)
                    
                    # Verificar que el usuario actual es el mismo que hizo el pago
                    persona_actual = Persona.objects.get(email=request.user.email)
                    if persona.id == persona_actual.id:
                        
                        # Verificar que no existe ya un alquiler para estos datos
                        alquiler_existente = Alquiler.objects.filter(
                            persona=persona,
                            maquina_base=maquina_base,
                            fecha_inicio=fecha_inicio,
                            fecha_fin=fecha_fin
                        ).first()
                        
                        if not alquiler_existente:
                            # Verificar disponibilidad nuevamente
                            if Alquiler.verificar_disponibilidad(maquina_base, fecha_inicio, fecha_fin):
                                # Verificar que el cliente no tenga otro alquiler activo
                                alquileres_activos = Alquiler.objects.filter(
                                    persona=persona,
                                    estado__in=['reservado', 'en_curso']
                                )
                                
                                if not alquileres_activos.exists():
                                    # Crear el alquiler
                                    alquiler = Alquiler.objects.create(
                                        maquina_base=maquina_base,
                                        persona=persona,
                                        fecha_inicio=fecha_inicio,
                                        fecha_fin=fecha_fin,
                                        metodo_pago=metodo_pago,
                                        estado='reservado',
                                        monto_total=float(total),
                                        preference_id=request.GET.get('preference_id')
                                    )
                                    
                                    print(f"=== ALQUILER CREADO VIA RETORNO ===")
                                    print(f"ID: {alquiler.id}")
                                    print(f"Número: {alquiler.numero}")
                                    print(f"Código de retiro: {alquiler.codigo_retiro}")
                                    
                                    # Enviar email con PDF al cliente
                                    try:
                                        print(f"🔄 Intentando enviar email desde persona webhook...")
                                        resultado_email = enviar_email_alquiler_simple(alquiler)
                                        if resultado_email:
                                            print(f"✅ Email enviado correctamente desde persona webhook")
                                        else:
                                            print(f"❌ Falló el envío de email desde persona webhook")
                                    except Exception as e:
                                        print(f"❌ Error al enviar email desde persona webhook: {str(e)}")
                                        import traceback
                                        traceback.print_exc()
                                    
                                    messages.success(request, f'¡Pago exitoso! Tu número de alquiler es: {alquiler.numero}. Código de retiro: {alquiler.codigo_retiro}')
                        else:
                            print(f"Alquiler ya existe: {alquiler_existente.numero}")
                            messages.success(request, f'Alquiler ya confirmado: {alquiler_existente.numero}')
            except Exception as e:
                print(f"Error al procesar retorno de pago: {str(e)}")
                messages.error(request, 'Hubo un error al procesar el pago.')

    # Obtener máquinas para mostrar en la página de inicio
    maquinas = MaquinaBase.objects.filter(stock__gt=0)[:4]  # Obtener las primeras 4 máquinas con stock
    for maquina in maquinas:
        if len(maquina.descripcion_corta) > 100:
            maquina.descripcion_vista = maquina.descripcion_corta[:100] + "..."
        else:
            maquina.descripcion_vista = maquina.descripcion_corta
     
    return render(request, 'persona/inicio.html', {
        'maquinas': maquinas,
        'empleados_emails': empleados_emails,
        'es_empleado_actuando_como_cliente': es_empleado_actuando_como_cliente
    })

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
    """
    Vista para que los clientes vean su historial de alquileres
    Accesible para clientes y empleados actuando como clientes
    """
    # Verificar que el usuario sea cliente o empleado actuando como cliente
    es_empleado_actuando_como_cliente = request.session.get('es_empleado_actuando_como_cliente', False)
    if es_empleado_o_admin(request.user) and not es_empleado_actuando_como_cliente:
        messages.error(request, 'Esta sección es solo para clientes. Los empleados no pueden alquilar máquinas.')
        return redirect('persona:gestion')
    
    try:
        persona = Persona.objects.get(email=request.user.email)
        
        # Obtener todos los alquileres del cliente, ordenados por fecha de creación
        alquileres = Alquiler.objects.filter(persona=persona).order_by('-fecha_creacion')
        
        # Agregar información adicional para cada alquiler
        for alquiler in alquileres:
            # Calcular días restantes si está en curso o reservado
            if alquiler.estado in ['reservado', 'en_curso'] and alquiler.fecha_inicio:
                from datetime import date
                dias_hasta_inicio = (alquiler.fecha_inicio - date.today()).days
                if dias_hasta_inicio > 0:
                    alquiler.dias_hasta_inicio = dias_hasta_inicio
                elif alquiler.fecha_fin:
                    dias_hasta_fin = (alquiler.fecha_fin - date.today()).days
                    if dias_hasta_fin >= 0:
                        alquiler.dias_hasta_fin = dias_hasta_fin
            
            # Calcular reembolso potencial si puede cancelar
            if alquiler.puede_ser_cancelado():
                porcentaje, monto = alquiler.calcular_reembolso(es_empleado=False)
                alquiler.porcentaje_reembolso_cliente = porcentaje
                alquiler.monto_reembolso_cliente = monto
        
        # Calcular estadísticas del resumen
        from django.db.models import Count, Q
        stats = {
            'total': alquileres.count(),
            'activos': alquileres.filter(estado__in=['reservado', 'en_curso']).count(),
            'finalizados': alquileres.filter(estado='finalizado').count(),
            'cancelados': alquileres.filter(estado='cancelado').count()
        }
        
        return render(request, 'persona/mis_alquileres.html', {
            'alquileres': alquileres,
            'persona': persona,
            'stats': stats
        })
        
    except Persona.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil de cliente.')
        return redirect('persona:inicio')

@login_required 
def cancelar_mi_alquiler(request, alquiler_id):
    """
    Vista para que los clientes cancelen sus propios alquileres
    Accesible para clientes y empleados actuando como clientes
    """
    # Verificar que el usuario sea cliente o empleado actuando como cliente
    es_empleado_actuando_como_cliente = request.session.get('es_empleado_actuando_como_cliente', False)
    if es_empleado_o_admin(request.user) and not es_empleado_actuando_como_cliente:
        messages.error(request, 'Los empleados no pueden usar esta función. Usa la gestión de alquileres.')
        return redirect('persona:gestion')
    
    try:
        persona = Persona.objects.get(email=request.user.email)
        alquiler = get_object_or_404(Alquiler, id=alquiler_id, persona=persona)
        
        if request.method == 'POST':
            try:
                if not alquiler.puede_ser_cancelado():
                    messages.error(request, f'El alquiler {alquiler.numero} no puede ser cancelado (estado: {alquiler.get_estado_display()})')
                    return redirect('persona:mis_alquileres')
                
                observaciones = request.POST.get('observaciones', 'Cancelado por el cliente')
                porcentaje, monto = alquiler.cancelar(empleado=None, observaciones=observaciones)
                
                if porcentaje > 0:
                    messages.success(request, 
                        f'Alquiler {alquiler.numero} cancelado exitosamente. '
                        f'Tienes derecho a un reembolso del {porcentaje}% (${monto:.2f}). '
                        f'Acércate a la tienda el próximo mes para cobrarlo.')
                else:
                    messages.success(request, 
                        f'Alquiler {alquiler.numero} cancelado exitosamente. '
                        f'No corresponde reembolso según la política de cancelación.')
                
            except Exception as e:
                messages.error(request, f'Error al cancelar el alquiler: {str(e)}')
            
            return redirect('persona:mis_alquileres')
        
        # Calcular reembolso para mostrar en el template
        porcentaje, monto = alquiler.calcular_reembolso(es_empleado=False)
        
        return render(request, 'persona/cancelar_mi_alquiler.html', {
            'alquiler': alquiler,
            'porcentaje_reembolso': porcentaje,
            'monto_reembolso': monto,
            'persona': persona
        })
        
    except Persona.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil de cliente.')
        return redirect('persona:inicio')

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
            
            # Si el usuario que registra no es admin, forzar registro como cliente
            if not request.user.is_superuser:
                persona.es_cliente = True
                persona.es_empleado = False
            
            # Verificar que el email exista
            if not persona.email:
                form.add_error('email', 'El email es obligatorio para registrar un usuario.')
                return render(request, 'persona/registrar_persona.html', {'form': form, 'is_admin': request.user.is_superuser})
            
            # Generar contraseña aleatoria
            password = generar_password_random()
            
            try:
                # Crear usuario en Django
                user = User.objects.create_user(
                    username=persona.email,
                    email=persona.email,
                    password=password,
                    first_name=persona.nombre,
                    last_name=persona.apellido,
                    is_staff=form.cleaned_data['es_empleado'] if request.user.is_superuser else False  # Solo admins pueden crear empleados
                )
                
                persona.save()
                
                # Enviar email con la contraseña
                send_mail(
                    'Bienvenido a Alquil.Ar - Tu contraseña',
                    f'Hola {persona.nombre},\n\n'
                    f'Tu cuenta ha sido creada exitosamente.\n\n'
                    f'Credenciales de acceso:\n'
                    f'• Email: {persona.email}\n'
                    f'• Contraseña: {password}\n\n'
                    f'Por favor, cambia tu contraseña la próxima vez que inicies sesión.\n\n'
                    f'Tipo de usuario: {"Empleado y Cliente" if persona.es_empleado and persona.es_cliente else "Empleado" if persona.es_empleado else "Cliente"}\n\n'
                    f'Saludos,\n'
                    f'Equipo Alquil.Ar',
                    settings.DEFAULT_FROM_EMAIL,
                    [persona.email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Usuario registrado exitosamente. Por favor, revisa tu email para obtener tu contraseña.')
                return redirect('persona:login_unificado2')
            except Exception as e:
                # Si algo falla, eliminar el usuario si fue creado
                if 'user' in locals():
                    user.delete()
                form.add_error(None, f'Error al crear el usuario: {str(e)}')
                return render(request, 'persona/registrar_persona.html', {'form': form, 'is_admin': request.user.is_superuser})
    else:
        form = PersonaForm()
    return render(request, 'persona/registrar_persona.html', {'form': form, 'is_admin': request.user.is_superuser})

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
            # El administrador decide si el empleado también es cliente
            persona.es_cliente = form.cleaned_data.get('es_cliente', False)
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
        paso = request.POST.get('paso')
        
        if paso == 'verificar':
            password_actual = request.POST.get('password_actual')
            
            # Verificar la contraseña actual
            user = request.user
            if not user.check_password(password_actual):
                messages.error(request, 'La contraseña actual es incorrecta.')
                return render(request, 'persona/cambiar_password.html', {'password_verificada': False})
            
            # Si la contraseña es correcta, mostrar el formulario de cambio
            return render(request, 'persona/cambiar_password.html', {'password_verificada': True})
            
        elif paso == 'cambiar':
            password_nuevo = request.POST.get('password_nuevo')
            password_confirmacion = request.POST.get('password_confirmacion')
            
            # Validar longitud de la nueva contraseña
            if len(password_nuevo) < 6:
                messages.error(request, 'La nueva contraseña debe tener al menos 6 caracteres.')
                return render(request, 'persona/cambiar_password.html', {'password_verificada': True})
            
            if len(password_nuevo) > 16:
                messages.error(request, 'La nueva contraseña no puede tener más de 16 caracteres.')
                return render(request, 'persona/cambiar_password.html', {'password_verificada': True})
            
            # Validar que las contraseñas coincidan
            if password_nuevo != password_confirmacion:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'persona/cambiar_password.html', {'password_verificada': True})
            
            # Cambiar la contraseña
            user = request.user
            user.set_password(password_nuevo)
            user.save()
            
            # Actualizar la sesión para que el usuario no tenga que volver a iniciar sesión
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
            return redirect('persona:inicio')
    
    return render(request, 'persona/cambiar_password.html', {'password_verificada': False})

@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def cambiar_password_empleado_logueado(request):
    error = None
    success = None
    password_verificada = False
    
    if request.method == 'POST':
        paso = request.POST.get('paso')
        
        if paso == 'verificar':
            password_actual = request.POST.get('password_actual', '')
            
            if not password_actual:
                error = 'Debe ingresar su contraseña actual.'
            else:
                # Verificar la contraseña actual
                user = request.user
                if not user.check_password(password_actual):
                    error = 'La contraseña actual es incorrecta.'
                else:
                    password_verificada = True
                
        elif paso == 'cambiar':
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')

            if not password1 or not password2:
                error = 'Debe completar todos los campos.'
                password_verificada = True
            elif password1 != password2:
                error = 'Las contraseñas no coinciden.'
                password_verificada = True
            elif len(password1) < 6:
                error = 'La contraseña debe tener al menos 6 caracteres.'
                password_verificada = True
            elif len(password1) > 16:
                error = 'La contraseña no puede tener más de 16 caracteres.'
                password_verificada = True
            else:
                user = request.user
                user.set_password(password1)
                user.save()
                update_session_auth_hash(request, user)  # Mantiene la sesión activa
                success = 'Contraseña cambiada exitosamente.'
                return redirect('persona:inicio')
        else:
            # Si no se especifica el paso, asumimos que es una solicitud GET
            password_verificada = False

    return render(request, 'persona/cambiar_password_empleado_logueado.html', {
        'error': error,
        'success': success,
        'password_verificada': password_verificada
    })

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
        if not persona.es_empleado:
            messages.error(request, 'Solo los empleados pueden acceder a esta función.')
            return redirect('persona:inicio')

        if request.method == 'POST':
            # Verificar que el empleado tenga permiso para actuar como cliente
            if not persona.es_cliente:
                messages.error(request, 'No tienes permiso para actuar como cliente. Contacta al administrador.')
                return redirect('persona:inicio')

            # Guardar en la sesión que el usuario es un empleado actuando como cliente
            request.session['es_empleado_actuando_como_cliente'] = True
            messages.success(request, 'Has cambiado a tu cuenta personal exitosamente.')
            return redirect('persona:inicio')

    except Persona.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil de empleado.')
        return redirect('persona:inicio')

    return render(request, 'login_as_persona.html', {
        'error': error, 
        'success': success,
        'persona': persona
    })

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
                    
                    # Verificar roles en orden específico
                    if persona.es_empleado:
                        messages.success(request, 'Has iniciado sesión como empleado')
                        return redirect('persona:inicio')
                    elif persona.es_cliente:
                        messages.success(request, 'Has iniciado sesión como cliente')
                        return redirect('persona:inicio')
                    else:
                        return render(request, 'persona/login_unificado2.html', {
                            'error': 'No tienes cuenta activa. Contacta al administrador.'
                        })
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

@csrf_exempt
def webhook_mercadopago(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"=== WEBHOOK MERCADOPAGO RECIBIDO ===")
            print(f"Data: {data}")
            
            # Obtener el ID del pago
            if data.get('type') == 'payment' and data.get('data', {}).get('id'):
                payment_id = data['data']['id']
                
                # Configurar SDK
                sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                
                # Obtener información del pago
                payment_info = sdk.payment().get(payment_id)
                
                if payment_info['status'] == 200:
                    payment = payment_info['response']
                    status = payment.get('status')
                    external_reference = payment.get('external_reference')
                    
                    print(f"Payment ID: {payment_id}")
                    print(f"Status: {status}")
                    print(f"External Reference: {external_reference}")
                    
                    if status == 'approved' and external_reference:
                        # Parsear external_reference
                        # Formato: "maquina_id|persona_id|fecha_inicio|fecha_fin|metodo_pago|total"
                        try:
                            datos = external_reference.split('|')
                            if len(datos) == 6:
                                from datetime import datetime
                                
                                maquina_id, persona_id, fecha_inicio_str, fecha_fin_str, metodo_pago, total = datos
                                
                                # Convertir fechas
                                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
                                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
                                
                                # Obtener objetos
                                maquina_base = MaquinaBase.objects.get(id=maquina_id)
                                persona = Persona.objects.get(id=persona_id)
                                
                                # Verificar que no existe ya un alquiler para estos datos
                                alquiler_existente = Alquiler.objects.filter(
                                    persona=persona,
                                    maquina_base=maquina_base,
                                    fecha_inicio=fecha_inicio,
                                    fecha_fin=fecha_fin
                                ).first()
                                
                                if not alquiler_existente:
                                    # Verificar disponibilidad nuevamente
                                    if Alquiler.verificar_disponibilidad(maquina_base, fecha_inicio, fecha_fin):
                                        # Verificar que el cliente no tenga otro alquiler activo
                                        alquileres_activos = Alquiler.objects.filter(
                                            persona=persona,
                                            estado__in=['reservado', 'en_curso']
                                        )
                                        
                                        if not alquileres_activos.exists():
                                            # Crear el alquiler
                                            alquiler = Alquiler.objects.create(
                                                maquina_base=maquina_base,
                                                persona=persona,
                                                fecha_inicio=fecha_inicio,
                                                fecha_fin=fecha_fin,
                                                metodo_pago=metodo_pago,
                                                estado='reservado',
                                                monto_total=float(total),
                                                preference_id=payment.get('order', {}).get('id')
                                            )
                                            
                                            print(f"Alquiler creado: {alquiler.numero}")
                                            
                                            # Enviar mail al cliente
                                            try:
                                                send_mail(
                                                    'Alquiler confirmado - ALQUIL.AR',
                                                    f'Alquiler confirmado, gracias por alquilar con ALQUIL.AR.\n'
                                                    f'Aquí te dejamos tu número de retiro: {alquiler.numero}',
                                                    settings.DEFAULT_FROM_EMAIL,
                                                    [persona.email],
                                                    fail_silently=False,
                                                )
                                                print(f"Email enviado exitosamente a: {persona.email}")
                                            except Exception as e:
                                                print(f"Error al enviar email: {str(e)}")
                                            
                                            print(f"=== ALQUILER CREADO VIA WEBHOOK ===")
                                            print(f"ID: {alquiler.id}")
                                            print(f"Número: {alquiler.numero}")
                                            
                                            # Actualizar estado de la máquina si es necesaria
                                            if alquiler.unidad:
                                                maquina = Maquina.objects.filter(
                                                    patente=alquiler.unidad.patente
                                                ).first()
                                                if maquina:
                                                    maquina.estado = 'alquilada'
                                                    maquina.save()
                                                    print(f"Máquina actualizada: {maquina.id} - Estado: {maquina.estado}")
                                else:
                                    print(f"Alquiler ya existe: {alquiler_existente.numero}")
                                    
                        except Exception as e:
                            print(f"Error al procesar webhook: {str(e)}")
                            
            return HttpResponse(status=200)
            
        except Exception as e:
            print(f"Error en webhook: {str(e)}")
            return HttpResponse(status=500)
            
    return HttpResponse(status=405)

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

@user_passes_test(es_empleado_o_admin)
def lista_alquileres(request):
    """Vista completa de gestión de alquileres para empleados y admins"""
    # Obtener todos los alquileres inicialmente
    alquileres = Alquiler.objects.select_related(
        'maquina_base', 'unidad', 'persona', 'unidad__sucursal'
    ).all()
    
    # Aplicar filtros
    estado_filtro = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cliente_filtro = request.GET.get('cliente')
    sucursal_filtro = request.GET.get('sucursal')
    
    if estado_filtro:
        alquileres = alquileres.filter(estado=estado_filtro)
    
    if fecha_desde:
        try:
            from datetime import datetime
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            alquileres = alquileres.filter(fecha_inicio__gte=fecha_desde_obj)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            from datetime import datetime
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            alquileres = alquileres.filter(fecha_fin__lte=fecha_hasta_obj)
        except ValueError:
            pass
    
    if cliente_filtro:
        alquileres = alquileres.filter(
            Q(persona__nombre__icontains=cliente_filtro) |
            Q(persona__apellido__icontains=cliente_filtro) |
            Q(persona__email__icontains=cliente_filtro) |
            Q(persona__dni__icontains=cliente_filtro)
        )
    
    if sucursal_filtro:
        alquileres = alquileres.filter(unidad__sucursal_id=sucursal_filtro)
    
    # Ordenar por fecha de creación más reciente
    alquileres = alquileres.order_by('-fecha_creacion')
    
    # Calcular estadísticas
    stats = Alquiler.objects.aggregate(
        reservados=Count('id', filter=Q(estado='reservado')),
        en_curso=Count('id', filter=Q(estado='en_curso')),
        finalizados=Count('id', filter=Q(estado='finalizado')),
        cancelados=Count('id', filter=Q(estado='cancelado'))
    )
    
    # Obtener sucursales para el filtro
    sucursales = Sucursal.objects.all().order_by('direccion')
    
    # Paginación
    paginator = Paginator(alquileres, 25)  # 25 alquileres por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Verificar si se solicita exportación
    if request.GET.get('export') == 'xlsx':
        return exportar_alquileres_xlsx(alquileres)
    
    # Mostrar mensaje si no hay resultados
    mensaje_sin_resultados = None
    if not alquileres.exists() and any([estado_filtro, fecha_desde, fecha_hasta, cliente_filtro, sucursal_filtro]):
        mensaje_sin_resultados = "No se encontraron alquileres con los filtros aplicados."
    
    context = {
        'alquileres': page_obj,
        'stats': stats,
        'sucursales': sucursales,
        'mensaje_sin_resultados': mensaje_sin_resultados,
        'filtros': {
            'estado': estado_filtro,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'cliente': cliente_filtro,
            'sucursal': sucursal_filtro,
        }
    }
    
    return render(request, 'persona/lista_alquileres.html', context)

def exportar_alquileres_xlsx(alquileres):
    """Exportar alquileres a Excel"""
    try:
        import openpyxl
        from django.http import HttpResponse
        from datetime import datetime
        
        # Crear workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Alquileres"
        
        # Encabezados
        headers = [
            'Número', 'Cliente', 'Email', 'Teléfono', 'Máquina', 'Marca', 'Modelo',
            'Unidad', 'Sucursal', 'Fecha Inicio', 'Fecha Fin', 'Días', 'Estado',
            'Método Pago', 'Monto', 'Código Retiro', 'Fecha Creación'
        ]
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        
        # Datos
        for row, alquiler in enumerate(alquileres, 2):
            ws.cell(row=row, column=1, value=alquiler.numero)
            ws.cell(row=row, column=2, value=f"{alquiler.persona.nombre} {alquiler.persona.apellido}" if alquiler.persona else "N/A")
            ws.cell(row=row, column=3, value=alquiler.persona.email if alquiler.persona else "N/A")
            ws.cell(row=row, column=4, value=alquiler.persona.telefono if alquiler.persona else "N/A")
            ws.cell(row=row, column=5, value=alquiler.maquina_base.nombre)
            ws.cell(row=row, column=6, value=alquiler.maquina_base.get_marca_display())
            ws.cell(row=row, column=7, value=alquiler.maquina_base.modelo)
            ws.cell(row=row, column=8, value=alquiler.unidad.patente if alquiler.unidad else "Sin asignar")
            ws.cell(row=row, column=9, value=alquiler.unidad.sucursal.direccion if alquiler.unidad else "N/A")
            ws.cell(row=row, column=10, value=alquiler.fecha_inicio.strftime('%d/%m/%Y'))
            ws.cell(row=row, column=11, value=alquiler.fecha_fin.strftime('%d/%m/%Y'))
            ws.cell(row=row, column=12, value=alquiler.cantidad_dias)
            ws.cell(row=row, column=13, value=alquiler.get_estado_display())
            ws.cell(row=row, column=14, value=alquiler.get_metodo_pago_display())
            ws.cell(row=row, column=15, value=float(alquiler.monto_total) if alquiler.monto_total else 0)
            ws.cell(row=row, column=16, value=alquiler.codigo_retiro)
            ws.cell(row=row, column=17, value=alquiler.fecha_creacion.strftime('%d/%m/%Y %H:%M'))
        
        # Crear respuesta HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="alquileres_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx"'
        
        wb.save(response)
        return response
        
    except ImportError:
        messages.error(request, 'No se pudo exportar a Excel. Instala openpyxl.')
        return redirect('persona:lista_alquileres')

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

@login_required
def pago_exitoso(request):
    """Página de pago exitoso con confetis"""
    # Obtener datos del pago si están disponibles
    external_reference = request.GET.get('external_reference')
    payment_id = request.GET.get('payment_id')
    
    alquiler = None
    
    print(f"=== PAGO EXITOSO - PROCESANDO RETORNO ===")
    print(f"External reference: {external_reference}")
    print(f"Payment ID: {payment_id}")
    
    # Procesar el pago si tenemos external_reference (usuario viene de MercadoPago)
    if external_reference:
        try:
            datos = external_reference.split('|')
            if len(datos) == 6:
                from datetime import datetime
                
                maquina_id, persona_id, fecha_inicio_str, fecha_fin_str, metodo_pago, total = datos
                
                # Convertir fechas
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
                
                # Obtener objetos
                maquina_base = MaquinaBase.objects.get(id=maquina_id)
                persona = Persona.objects.get(id=persona_id)
                
                # Verificar que el usuario actual es el mismo que hizo el pago
                try:
                    persona_actual = Persona.objects.get(email=request.user.email)
                    if persona.id != persona_actual.id:
                        messages.error(request, "Error de validación de usuario.")
                        return redirect('persona:inicio')
                except Persona.DoesNotExist:
                    messages.error(request, "Usuario no encontrado.")
                    return redirect('persona:inicio')
                
                # Verificar que no existe ya un alquiler para estos datos
                alquiler_existente = Alquiler.objects.filter(
                    persona=persona,
                    maquina_base=maquina_base,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                ).first()
                
                if not alquiler_existente:
                    # Verificar disponibilidad nuevamente
                    if Alquiler.verificar_disponibilidad(maquina_base, fecha_inicio, fecha_fin):
                        # Verificar que el cliente no tenga otro alquiler activo
                        alquileres_activos = Alquiler.objects.filter(
                            persona=persona,
                            estado__in=['reservado', 'en_curso']
                        )
                        
                        if not alquileres_activos.exists():
                            # Crear el alquiler
                            alquiler = Alquiler.objects.create(
                                maquina_base=maquina_base,
                                persona=persona,
                                fecha_inicio=fecha_inicio,
                                fecha_fin=fecha_fin,
                                metodo_pago=metodo_pago,
                                estado='reservado',
                                monto_total=float(total)
                            )
                            
                            print(f"=== ALQUILER CREADO VIA FALLBACK ===")
                            print(f"ID: {alquiler.id}")
                            print(f"Número: {alquiler.numero}")
                            print(f"Código de retiro: {alquiler.codigo_retiro}")
                            
                            # Enviar email con PDF al cliente
                            try:
                                print(f"🔄 Intentando enviar email desde fallback...")
                                resultado_email = enviar_email_alquiler_simple(alquiler)
                                if resultado_email:
                                    print(f"✅ Email enviado correctamente desde fallback")
                                else:
                                    print(f"❌ Falló el envío de email desde fallback")
                            except Exception as e:
                                print(f"❌ Error al enviar email desde fallback: {str(e)}")
                                import traceback
                                traceback.print_exc()
                        else:
                            print(f"Cliente ya tiene alquiler activo")
                            messages.warning(request, 'Ya tienes un alquiler activo.')
                    else:
                        print(f"No hay disponibilidad")
                        messages.error(request, 'No hay unidades disponibles para las fechas seleccionadas.')
                else:
                    print(f"Alquiler ya existe: {alquiler_existente.numero}")
                    alquiler = alquiler_existente
                    
        except Exception as e:
            print(f"Error al procesar retorno de pago: {str(e)}")
            messages.error(request, 'Hubo un error al procesar tu pago. Contacta al soporte.')
    
    # Si no encontramos el alquiler específico, buscar el más reciente del usuario
    if not alquiler:
        try:
            persona = Persona.objects.get(email=request.user.email)
            alquiler = Alquiler.objects.filter(
                persona=persona
            ).order_by('-fecha_creacion').first()
        except:
            pass
    
    return render(request, 'persona/pago_exitoso.html', {
        'alquiler': alquiler
    })

@login_required 
def pago_fallido(request):
    """Página de pago fallido"""
    return render(request, 'persona/pago_fallido.html')

@login_required
def pago_pendiente(request):
    """Página para notificar que el pago está pendiente"""
    return render(request, 'persona/pago_pendiente.html')

@login_required
@user_passes_test(es_empleado_o_admin)
def lista_reembolsos(request):
    """Vista para gestionar reembolsos pendientes y pagados"""
    from maquinas.models import Reembolso
    from django.db.models import Q
    from django.core.paginator import Paginator
    
    # Obtener todos los reembolsos
    reembolsos = Reembolso.objects.select_related(
        'alquiler', 'alquiler__persona', 'alquiler__maquina_base', 
        'empleado_que_marco_pagado'
    ).all()
    
    # Aplicar filtros
    estado_filtro = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cliente_filtro = request.GET.get('cliente')
    
    # Filtrar por estado (solo pendiente y pagado)
    if estado_filtro and estado_filtro in ['pendiente', 'pagado']:
        reembolsos = reembolsos.filter(estado=estado_filtro)
    
    # Filtrar por fechas
    if fecha_desde:
        try:
            from datetime import datetime
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            reembolsos = reembolsos.filter(fecha_creacion__date__gte=fecha_desde_obj)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            from datetime import datetime
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            reembolsos = reembolsos.filter(fecha_creacion__date__lte=fecha_hasta_obj)
        except ValueError:
            pass
    
    # Filtrar por cliente
    if cliente_filtro:
        reembolsos = reembolsos.filter(
            Q(alquiler__persona__nombre__icontains=cliente_filtro) |
            Q(alquiler__persona__apellido__icontains=cliente_filtro) |
            Q(alquiler__persona__email__icontains=cliente_filtro) |
            Q(alquiler__persona__dni__icontains=cliente_filtro)
        )
    
    # Ordenar por fecha de creación más reciente
    reembolsos = reembolsos.order_by('-fecha_creacion')
    
    # Calcular estadísticas
    from django.db.models import Count, Sum
    stats = Reembolso.objects.aggregate(
        pendientes=Count('id', filter=Q(estado='pendiente')),
        pagados=Count('id', filter=Q(estado='pagado')),
        total_pendiente=Sum('monto', filter=Q(estado='pendiente')),
        total_pagado=Sum('monto', filter=Q(estado='pagado'))
    )
    
    # Paginación
    paginator = Paginator(reembolsos, 25)  # 25 reembolsos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reembolsos': page_obj,
        'stats': stats,
        'filtros': {
            'estado': estado_filtro,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'cliente': cliente_filtro,
        }
    }
    
    return render(request, 'persona/lista_reembolsos.html', context)

@login_required
@user_passes_test(es_empleado_o_admin)
def marcar_reembolso_pagado(request, reembolso_id):
    """Vista para marcar un reembolso como pagado"""
    from maquinas.models import Reembolso
    
    reembolso = get_object_or_404(Reembolso, id=reembolso_id)
    
    if request.method == 'POST':
        try:
            if reembolso.estado != 'pendiente':
                messages.error(request, f'El reembolso ya está {reembolso.get_estado_display().lower()}')
                return redirect('persona:lista_reembolsos')
            
            observaciones = request.POST.get('observaciones', '')
            reembolso.marcar_como_pagado(empleado=request.user, observaciones=observaciones)
            
            messages.success(request, 
                f'Reembolso del alquiler {reembolso.alquiler.numero} marcado como pagado exitosamente. '
                f'Monto: ${reembolso.monto}')
            
        except Exception as e:
            messages.error(request, f'Error al marcar el reembolso como pagado: {str(e)}')
        
        return redirect('persona:lista_reembolsos')
    
    return render(request, 'persona/marcar_reembolso_pagado.html', {
        'reembolso': reembolso
    })

def buscar_clientes_json(request):
    """API endpoint para buscar clientes dinámicamente - SOLO POR EMAIL Y DNI - SIN AUTENTICACIÓN"""
    from django.http import JsonResponse
    from django.db.models import Q
    
    query = request.GET.get('q', '').strip()
    
    print(f"🔍 API BÚSQUEDA: '{query}' (longitud: {len(query)})")
    print(f"📊 Usuario: {request.user} - Autenticado: {request.user.is_authenticated}")
    
    if len(query) < 2:  # Mínimo 2 caracteres para buscar
        print("❌ Búsqueda muy corta, devolviendo lista vacía")
        return JsonResponse({'clientes': []})
    
    # Buscar SOLO por email y DNI en todas las personas (excluir empleados)
    print(f"📊 Total personas en BD: {Persona.objects.count()}")
    
    clientes = Persona.objects.filter(
        Q(email__icontains=query) | Q(dni__icontains=query),
        es_empleado=False  # Excluir empleados
    ).order_by('apellido', 'nombre')[:10]  # Limitar a 10 resultados
    
    print(f"🔍 Total encontrados: {clientes.count()}")
    
    resultados = []
    for cliente in clientes:
        display_text = f"{cliente.apellido}, {cliente.nombre} - {cliente.email}"
        if cliente.dni:
            display_text += f" (DNI: {cliente.dni})"
            
        resultados.append({
            'id': cliente.id,
            'nombre_completo': f"{cliente.nombre} {cliente.apellido}",
            'email': cliente.email,
            'dni': cliente.dni if cliente.dni else '',
            'display_text': display_text
        })
        print(f"   📄 Cliente: {cliente.email} - DNI: {cliente.dni}")
    
    print(f"📤 Devolviendo {len(resultados)} resultados")
    return JsonResponse({'clientes': resultados})

# Create your views here.
