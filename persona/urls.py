from django.urls import path
from .views import lista_personas, lista_maquinas, lista_empleados, login_view, inicio_blanco, registrar_empleado, login_empleado, cambiar_password, cambiar_password_empleado, cambiar_password_logueado, cambiar_password_empleado_logueado
from . import views

urlpatterns = [
    path('personas/', lista_personas, name='lista_personas'),
    path('maquinas/', lista_maquinas, name='lista_maquinas'),
    path('empleados/', lista_empleados, name='lista_empleados'),
    path('registrar/', views.registrar_persona, name='registrar_persona'),
    path('registrar-empleado/', views.registrar_empleado, name='registrar_empleado'),
    path('login/', login_view, name='login'),
    path('login-empleado/', login_empleado, name='login_empleado'),
    path('inicio/', inicio_blanco, name='inicio_blanco'),
    path('cambiar-password/', cambiar_password, name='cambiar_password'),
    path('cambiar-password-empleado/', cambiar_password_empleado, name='cambiar_password_empleado'),
    path('cambiar-password-logueado/', cambiar_password_logueado, name='cambiar_password_logueado'),
    path('cambiar-password-empleado-logueado/', cambiar_password_empleado_logueado, name='cambiar_password_empleado_logueado'),
]


