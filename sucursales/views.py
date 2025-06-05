from django.shortcuts import render

# Create your views here.

def lista_sucursales(request):
    # Puedes reemplazar esto por una consulta real a la base de datos
    sucursales = [
        {'nombre': 'Sucursal Centro', 'direccion': 'Av. Principal 123', 'telefono': '+54 11 1234-5678'},
        {'nombre': 'Sucursal Norte', 'direccion': 'Calle Falsa 456', 'telefono': '+54 11 8765-4321'},
    ]
    return render(request, 'sucursales/lista_sucursales.html', {'sucursales': sucursales})
