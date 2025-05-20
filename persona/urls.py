from django.urls import path
from .views import lista_personas, lista_maquinas, lista_empleados, login_view, inicio_blanco
from . import views

urlpatterns = [
    path('personas/', lista_personas, name='lista_personas'),
    path('maquinas/', lista_maquinas, name='lista_maquinas'),
    path('empleados/', lista_empleados, name='lista_empleados'),
    path('registrar/', views.registrar_persona, name='registrar_persona'),
    path('login/', login_view, name='login'),
    path('inicio/', inicio_blanco, name='inicio_blanco'),
]


