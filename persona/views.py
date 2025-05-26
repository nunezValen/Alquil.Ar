from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import Persona, Maquina, Empleado
from .forms import PersonaForm, EmpleadoForm
from datetime import date
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.auth.forms import PasswordChangeForm
import random, string


def inicio(request):
    return HttpResponse("<h1>Bienvenido a nuestra página de inicio</h1>")

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
                    user = User.objects.create_user(username=username, email=email, password=password,
                        first_name=empleado.nombre, last_name=empleado.apellido)
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

# Create your views here.
