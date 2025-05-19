from django.shortcuts import render
from django.http import HttpResponse
from .models import Persona, Maquina, Empleado


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

# Create your views here.
