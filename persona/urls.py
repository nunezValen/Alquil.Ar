from django.urls import path
from .views import (
    lista_personas, lista_maquinas, lista_empleados,
    inicio_blanco, registrar_empleado, cambiar_password,
    cambiar_password_empleado, cambiar_password_logueado,
    cambiar_password_empleado_logueado, login_as_persona,
    login_unificado2
)
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('personas/', lista_personas, name='lista_personas'),
    path('maquinas/', lista_maquinas, name='lista_maquinas'),
    path('empleados/', lista_empleados, name='lista_empleados'),
    path('registrar/', views.registrar_persona, name='registrar_persona'),
    path('registrar-empleado/', views.registrar_empleado, name='registrar_empleado'),
    path('login2/', login_unificado2, name='login_unificado2'),
    path('inicio/', inicio_blanco, name='inicio_blanco'),
    path('cambiar-password/', cambiar_password, name='cambiar_password'),
    path('cambiar-password-empleado/', cambiar_password_empleado, name='cambiar_password_empleado'),
    path('cambiar-password-logueado/', cambiar_password_logueado, name='cambiar_password_logueado'),
    path('cambiar-password-empleado-logueado/', cambiar_password_empleado_logueado, name='cambiar_password_empleado_logueado'),
    path('login-as-persona/', login_as_persona, name='login_as_persona'),
]


