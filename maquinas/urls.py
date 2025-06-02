from django.urls import path
from . import views

app_name = 'maquinas'

urlpatterns = [
    path('cargar-maquina-base/', views.cargar_maquina_base, name='cargar_maquina_base'),
    path('detalle/<int:maquina_id>/', views.detalle_maquina, name='detalle_maquina'),
    path('eliminar/<int:maquina_id>/', views.eliminar_maquina_base, name='eliminar_maquina_base'),
    path('gestion/', views.lista_maquinas, name='lista_maquinas'),
    path('lista-unidades/', views.lista_unidades, name='lista_unidades'),
    path('cargar-unidad/', views.cargar_unidad, name='cargar_unidad'),
    path('eliminar-unidad/<int:unidad_id>/', views.eliminar_unidad, name='eliminar_unidad'),
] 