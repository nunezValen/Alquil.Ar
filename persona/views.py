from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import Persona, Maquina, Empleado
from .forms import PersonaForm, EmpleadoForm
from datetime import date
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
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
            if email:
                try:
                    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                    empleado.password = password
                    empleado.save()
                    send_mail(
                        'Tu cuenta de empleado en Alquil.ar',
                        f'Hola {empleado.nombre},\n\nTu usuario de empleado ha sido creado.\n\nUsuario: {email}\nContraseña: {password}\n\nPor favor, cambia tu contraseña después de iniciar sesión.',
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

def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Primero buscar en Empleado
        empleado = Empleado.objects.filter(email=username).first()
        if empleado and empleado.password:
            # Verificamos la contraseña (en texto plano, pero deberías usar hash en producción)
            if empleado.password == password:
                request.session['empleado_id'] = empleado.id
                request.session['es_empleado'] = True
                return redirect('inicio_empleado')
            else:
                error = 'Contraseña incorrecta para empleado.'
        else:
            # Si no es empleado, buscar como usuario normal (Persona)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                request.session['es_empleado'] = False
                return redirect('inicio_blanco')
            else:
                error = 'Usuario o contraseña incorrectos.'
    return render(request, 'login.html', {'error': error})

@login_required
def inicio_blanco(request):
    return render(request, 'inicio_blanco.html')

def inicio_empleado(request):
    if not request.session.get('es_empleado'):
        return redirect('login')
    return render(request, 'persona/inicio_empleado.html')

# Create your views here.
