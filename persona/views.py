from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import Persona, Maquina, Empleado, Sucursal
from .forms import PersonaForm, EmpleadoForm
from datetime import date
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import random, string


def inicio(request):
    return render(request, 'inicio.html')

def lista_maquinas(request):
    maquinas = Maquina.objects.all()  # Consulta todos los productos.
    return render(request, 'lista_maquina.html', {'maquinas': maquinas})

def lista_empleados(request):
    empleados = Empleado.objects.all()  # Consulta todos los productos.
    return render(request, 'lista_empleado.html', {'empleados': empleados})

def lista_personas(request):
    personas = Persona.objects.all()  # Consulta todas las personas.
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
                        user = User.objects.create_user(
                            username=email,
                            email=email,
                            password=password,
                            first_name=persona.nombre,
                            last_name=persona.apellido
                        )
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

@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def login_view(request):
    error = None
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        
        print(f"Intento de login con email: {email}")  # Debug
        
        # 1. Primero buscar en Empleado
        try:
            empleado = Empleado.objects.get(email=email)
            print(f"Empleado encontrado: {empleado}")  # Debug
            # 1.1 Intentar autenticar como empleado
            username = f"emp_{email}"
            user = authenticate(request, username=username, password=password)
            if user is not None:
                print(f"Autenticación exitosa como empleado: {user}")  # Debug
                login(request, user)
                return redirect('inicio_blanco')
            # 1.2 Si la contraseña no coincide
            else:
                print("Contraseña incorrecta para empleado")  # Debug
                error = 'Email o contraseña incorrectos'
        except Empleado.DoesNotExist:
            print("No se encontró empleado, buscando en Persona")  # Debug
            # 2. Si no existe en Empleado, buscar en Persona
            try:
                persona = Persona.objects.get(email=email)
                print(f"Persona encontrada: {persona}")  # Debug
                # 2.1 Intentar autenticar como persona
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    print(f"Autenticación exitosa como persona: {user}")  # Debug
                    login(request, user)
                    return redirect('inicio_blanco')
                # 2.2 Si la contraseña no coincide
                else:
                    print("Contraseña incorrecta para persona")  # Debug
                    error = 'Email o contraseña incorrectos'
            except Persona.DoesNotExist:
                # 3. Si no existe ni en Empleado ni en Persona
                print("No se encontró ni empleado ni persona")  # Debug
                error = 'Email o contraseña incorrectos'
    
    return render(request, 'login.html', {'error': error})

@login_required
def inicio_blanco(request):
    return render(request, 'inicio_blanco.html')

def registrar_empleado(request):
    error = None
    if request.method == 'POST':
        post = request.POST.copy()
        dia = post.get('fecha_dia')
        mes = post.get('fecha_mes')
        anio = post.get('fecha_anio')
        if dia and mes and anio:
            post['fecha_nacimiento'] = f"{anio}-{mes.zfill(2)}-{dia.zfill(2)}"
        form = EmpleadoForm(post)
        if form.is_valid():
            empleado = form.save()
            email = empleado.email
            print('EMAIL CAPTURADO EN REGISTRO:', email)
            if email:
                try:
                    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                    # Agregamos un prefijo al username para diferenciarlo de los usuarios normales
                    username = f"emp_{email}"
                    if User.objects.filter(username=username).exists():
                        error = 'Ya existe un usuario con ese email. Si no recibiste el correo, contacta al administrador.'
                    else:
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=password,
                            first_name=empleado.nombre,
                            last_name=empleado.apellido
                        )
                        send_mail(
                            'Tu cuenta de empleado en Alquil.ar',
                            f'Hola {empleado.nombre},\n\nTu usuario ha sido creado.\n\nUsuario: {email}\nContraseña: {password}\n\nPor favor, cambia tu contraseña después de iniciar sesión.',
                            'no-reply@alquilar.com.ar',
                            [email],
                            fail_silently=False,
                        )
                        messages.success(request, 'Empleado registrado exitosamente. Recibirás tu contraseña por email.')
                        return redirect('registrar_empleado')
                except Exception as e:
                    error = f'Error al enviar el correo: {e}'
    else:
        form = EmpleadoForm()
    return render(request, 'persona/registrar_empleado.html', {'form': form, 'error': error})

def login_empleado(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Agregamos el prefijo emp_ al username para buscar el usuario correcto
        user = authenticate(request, username=f"emp_{username}", password=password)
        if user is not None:
            login(request, user)
            return redirect('inicio_blanco')
        else:
            error = 'Usuario o contraseña incorrectos.'
    return render(request, 'login_empleado.html', {'error': error})

def cambiar_password(request):
    error = None
    success = None
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(username=email)
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user.set_password(password)
            user.save()
            send_mail(
                'Tu nueva contraseña en Alquil.ar',
                f'Hola {user.first_name},\n\nTu contraseña ha sido cambiada.\n\nNueva contraseña: {password}\n\nPor favor, cambia tu contraseña después de iniciar sesión.',
                'no-reply@alquilar.com.ar',
                [email],
                fail_silently=False,
            )
            success = 'Se ha enviado una nueva contraseña a tu email.'
        except User.DoesNotExist:
            error = 'No existe una cuenta con ese email.'
    return render(request, 'cambiar_password.html', {'error': error, 'success': success})

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
def login_as_persona(request):
    error = None
    success = None
    
    # Verificar que el usuario actual es un empleado
    if not request.user.username.startswith('emp_'):
        return redirect('inicio_blanco')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        email = request.user.email  # El email del empleado actual
        
        try:
            # Buscar si existe una cuenta Persona con el mismo email
            persona = Persona.objects.get(email=email)
            
            # Intentar autenticar como persona
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('inicio_blanco')
            else:
                error = 'Contraseña incorrecta para la cuenta Persona'
        except Persona.DoesNotExist:
            error = 'No existe una cuenta Persona asociada a este email'
    
    return render(request, 'login_as_persona.html', {'error': error, 'success': success})

def login_unificado2(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # 1. Buscar en modelo Empleado
        try:
            empleado = Empleado.objects.get(email=email)
            # 1.1. Intentar autenticar como empleado
            username = f"emp_{email}"
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Si la contraseña coincide
                login(request, user)
                return redirect('inicio_blanco')
            else:
                # 1.2. Si la contraseña no coincide
                return render(request, 'persona/login_unificado2.html', {
                    'error': 'Email o contraseña incorrectos'
                })
        except Empleado.DoesNotExist:
            # 2. Si no existe en Empleado, buscar en Persona
            try:
                persona = Persona.objects.get(email=email)
                # 2.1. Intentar autenticar como persona
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    # Si la contraseña coincide
                    login(request, user)
                    return redirect('inicio_blanco')
                else:
                    # 2.2. Si la contraseña no coincide
                    return render(request, 'persona/login_unificado2.html', {
                        'error': 'Email o contraseña incorrectos'
                    })
            except Persona.DoesNotExist:
                # 3. Si no existe ni en Empleado ni en Persona
                return render(request, 'persona/login_unificado2.html', {
                    'error': 'Email o contraseña incorrectos'
                })
    
    # Si es GET, mostrar el formulario
    return render(request, 'persona/login_unificado2.html')

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
        return redirect('inicio')
    except Exception as e:
        messages.error(request, 'Ocurrió un error al cargar el mapa de sucursales')
        return redirect('inicio')

# Create your views here.
