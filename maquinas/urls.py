from django.urls import path
from . import views

app_name = 'maquinas'

urlpatterns = [
    path('cargar-maquina-base/', views.cargar_maquina_base, name='cargar_maquina_base'),
    path('detalle/<int:maquina_id>/', views.detalle_maquina, name='detalle_maquina'),
] 