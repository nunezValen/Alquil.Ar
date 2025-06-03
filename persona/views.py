from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .models import Persona, Maquina
from maquinas.models import MaquinaBase
from .forms import PersonaForm, EditarPersonaForm
from datetime import date
from django.contrib.auth import authenticate, login, update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import random, string

def es_admin(user):
    """
    Verifica si el usuario es administrador
    """
    return user.is_authenticated and user.is_superuser

def inicio(request):
    maquinas = MaquinaBase.objects.filter(stock__gt=0)[:4]  # Obtener las primeras 4 máquinas con stock
    for maquina in maquinas:
        # Creamos un atributo temporal solo para la vista
        if len(maquina.descripcion_corta) > 300:
            maquina.descripcion_vista = maquina.descripcion_corta[:297] + "..."
        else:
            maquina.descripcion_vista = maquina.descripcion_corta
    return render(request, 'persona/inicio.html', {'maquinas': maquinas})

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
    personas = Persona.objects.all()  # Consulta todas las personas
    return render(request, 'lista_persona.html', {'personas': personas})

@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
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
            persona = form.save(commit=False)
            # Verificar si el usuario quiere registrarse como empleado
            if form.cleaned_data.get('es_empleado'):
                persona.es_empleado = True
                persona.es_cliente = True  # Todo empleado es cliente
            else:
                persona.es_cliente = True
            persona.save()

            email = persona.email
            print('EMAIL CAPTURADO EN REGISTRO:', email)
            if email:
                if User.objects.filter(username=email).exists():
                    error = 'Ya existe un usuario con ese email. Si no recibiste el correo, contacta al administrador.'
                else:
                    try:
                        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                        user = User.objects.create_user(
                            username=email,
                            email=email,
                            password=password,
                            first_name=persona.nombre,
                            last_name=persona.apellido,
                            is_staff=persona.es_empleado  # Si es empleado, darle permisos de staff
                        )

                        # Mensaje personalizado según el tipo de cuenta
                        if persona.es_empleado:
                            subject = 'Tu cuenta de empleado en Alquil.ar'
                            message = f'Hola {persona.nombre},\n\nTu usuario de empleado ha sido creado.\n\nUsuario: {email}\nContraseña: {password}\n\nPor favor, cambia tu contraseña después de iniciar sesión.'
                        else:
                            subject = 'Tu cuenta en Alquil.ar'
                            message = f'Hola {persona.nombre},\n\nTu usuario ha sido creado.\n\nUsuario: {email}\nContraseña: {password}\n\nPor favor, cambia tu contraseña después de iniciar sesión.'

                        send_mail(
                            subject,
                            message,
                            'no-reply@alquilar.com.ar',
                            [email],
                            fail_silently=False,
                        )

                        if persona.es_empleado:
                            messages.success(request, 'Tu cuenta de empleado fue registrada exitosamente. Recibirás tu contraseña por email.')
                        else:
                            messages.success(request, 'El usuario fue registrado exitosamente. Recibirás tu contraseña por email.')
                        return redirect('persona:registrar_persona')
                    except Exception as e:
                        error = f'Error al enviar el correo: {e}'
    else:
        form = PersonaForm()
    return render(request, 'persona/registrar_persona.html', {'form': form, 'error': error})

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
                        return redirect('persona:pagina_principal')
                    elif persona.es_cliente:
                        return redirect('persona:pagina_principal')
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
            return redirect('persona:pagina_principal')
        else:
            error = 'Usuario o contraseña incorrectos.'
    return render(request, 'login_empleado.html', {'error': error})

@login_required
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def cambiar_password(request):
    error = None
    success = None
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            error = 'Las contraseñas no coinciden.'
        elif len(password1) < 8:
            error = 'La contraseña debe tener al menos 8 caracteres.'
        else:
            user = request.user
            user.set_password(password1)
            user.save()
            update_session_auth_hash(request, user)  # Mantiene la sesión activa
            success = 'Contraseña cambiada exitosamente.'

    return render(request, 'cambiar_password.html', {'error': error, 'success': success})

@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def cambiar_password_empleado(request):
    error = None
    success = None
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(username=f"emp_{email}")
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user.set_password(password)
            user.save()
            send_mail(
                'Tu nueva contraseña de empleado en Alquil.ar',
                f'Hola {user.first_name},\n\nTu contraseña ha sido cambiada.\n\nNueva contraseña: {password}\n\nPor favor, cambia tu contraseña después de iniciar sesión.',
                'no-reply@alquilar.com.ar',
                [email],
                fail_silently=False,
            )
            success = 'Se ha enviado una nueva contraseña a tu email.'
        except User.DoesNotExist:
            error = 'No existe una cuenta de empleado con ese email.'
    return render(request, 'cambiar_password_empleado.html', {'error': error, 'success': success})

@login_required
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
        elif len(password1) < 8:
            error = 'La contraseña debe tener al menos 8 caracteres.'
        else:
            user = request.user
            user.set_password(password1)
            user.save()
            update_session_auth_hash(request, user)  # Mantiene la sesión activa
            success = 'Contraseña cambiada exitosamente.'

    return render(request, 'cambiar_password_logueado.html', {'error': error, 'success': success})

@login_required
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
        elif len(password1) < 8:
            error = 'La contraseña debe tener al menos 8 caracteres.'
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
            return redirect('persona:pagina_principal')
    except Persona.DoesNotExist:
        return redirect('persona:pagina_principal')

    if request.method == 'POST':
        email = request.user.email  # El email del empleado actual

        try:
            # Buscar si existe una cuenta Persona con el mismo email
            persona = Persona.objects.get(email=email)

            if persona.es_cliente:
                # Guardar en la sesión que el usuario es un empleado actuando como cliente
                request.session['es_empleado_actuando_como_cliente'] = True
                messages.success(request, 'Has cambiado a tu cuenta personal exitosamente.')
                return redirect('persona:pagina_principal')
            else:
                error = 'No tienes una cuenta personal asociada a este email'
        except Persona.DoesNotExist:
            error = 'No existe una cuenta Persona asociada a este email'

    return render(request, 'login_as_persona.html', {'error': error, 'success': success})

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
                    return redirect('persona:pagina_principal')
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

def es_empleado_o_admin(user):
    # Verificar si el usuario está autenticado
    if not user.is_authenticated:
        return False

    # Obtener el objeto request desde el middleware
    from persona.middleware import get_current_request
    request = get_current_request()

    # Si el usuario es un empleado actuando como cliente, no tiene permisos de empleado
    if request and request.session.get('es_empleado_actuando_como_cliente', False):
        return False

    # Verificar en el modelo Persona
    try:
        persona = Persona.objects.get(email=user.email)
        return persona.es_empleado or persona.es_admin
    except Persona.DoesNotExist:
        return False

@login_required
@user_passes_test(es_empleado_o_admin)
def gestion(request):
    """Vista de gestión accesible para empleados y administradores"""
    return render(request, 'persona/gestion.html')

@login_required
@user_passes_test(es_empleado_o_admin)
def estadisticas(request):
    """Vista de estadísticas accesible para empleados y administradores"""
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
    return redirect('persona:pagina_principal')

def logout_view(request):
    """Vista para cerrar sesión"""
    # Limpiar la variable de sesión que indica que el usuario es un empleado actuando como cliente
    if 'es_empleado_actuando_como_cliente' in request.session:
        del request.session['es_empleado_actuando_como_cliente']
    logout(request)
    return redirect('persona:inicio')

@login_required
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def editar_datos_personales(request):
    """Vista para editar los datos personales del usuario logueado"""
    try:
        # Obtener la persona asociada al usuario logueado
        persona = Persona.objects.get(email=request.user.email)

        if request.method == 'POST':
            form = EditarPersonaForm(request.POST, instance=persona)
            if form.is_valid():
                # Guardar los cambios en el modelo Persona
                form.save()

                # Actualizar también los datos en el modelo User
                user = request.user
                user.first_name = persona.nombre
                user.last_name = persona.apellido
                user.save()

                messages.success(request, 'Datos personales actualizados exitosamente.')
                return redirect('persona:editar_datos_personales')
        else:
            form = EditarPersonaForm(instance=persona)

        return render(request, 'persona/editar_datos_personales.html', {'form': form})
    except Persona.DoesNotExist:
        messages.error(request, 'No se encontró una cuenta asociada a este usuario.')
        return redirect('persona:inicio')

# Create your views here.
