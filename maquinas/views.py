from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from persona.views import es_empleado_o_admin
from .forms import MaquinaBaseForm
from .models import MaquinaBase

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
            form.save()
            messages.success(request, 'La máquina base ha sido cargada exitosamente.')
            return redirect('persona:gestion')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = MaquinaBaseForm()
    
    return render(request, 'maquinas/cargar_maquina_base.html', {'form': form})
