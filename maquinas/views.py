from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from persona.views import es_empleado_o_admin
from .forms import MaquinaBaseForm
from .models import MaquinaBase
from .models import Unidad
from .forms import UnidadForm

def es_admin(user):
    return user.is_authenticated and user.is_staff

def detalle_maquina(request, maquina_id):
    maquina = get_object_or_404(MaquinaBase, id=maquina_id)
    return render(request, 'maquinas/detalle_maquina.html', {'maquina': maquina})

@login_required
@user_passes_test(es_empleado_o_admin)
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
@user_passes_test(es_empleado_o_admin)
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
            return redirect('maquinas:detalle_maquina', maquina_id=maquina_id)
    
    return render(request, 'maquinas/eliminar_maquina_base.html', {'maquina': maquina})

@login_required
@user_passes_test(es_empleado_o_admin)
def lista_maquinas(request):
    maquinas = MaquinaBase.objects.all().order_by('nombre')
    return render(request, 'maquinas/lista_maquinas.html', {'maquinas': maquinas})

@login_required
@user_passes_test(es_empleado_o_admin)
def lista_unidades(request):
    unidades = Unidad.objects.select_related('maquina_base', 'sucursal').all().order_by('maquina_base__nombre', 'patente')
    return render(request, 'maquinas/lista_unidades.html', {
        'unidades': unidades
    })

@login_required
@user_passes_test(es_empleado_o_admin)
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
@user_passes_test(es_empleado_o_admin)
def eliminar_unidad(request, unidad_id):
    unidad = get_object_or_404(Unidad, id=unidad_id)
    if request.method == 'POST':
        unidad.delete()
        messages.success(request, f"La unidad '{unidad.patente}' ha sido eliminada con éxito.")
        return redirect('maquinas:lista_unidades')

    return render(request, 'maquinas/eliminar_unidad.html', {
        'unidad': unidad
    })
