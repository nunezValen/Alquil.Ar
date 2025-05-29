from django.urls import path
from .views import (
    lista_personas, lista_maquinas, lista_empleados,
    pagina_principal, registrar_empleado, cambiar_password,
    cambiar_password_empleado, cambiar_password_logueado,
    cambiar_password_empleado_logueado, login_as_persona,
    login_unificado2, logout_view
)
from . import views

app_name = 'persona'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('personas/', lista_personas, name='lista_personas'),
    path('maquinas/', lista_maquinas, name='lista_maquinas'),
    path('empleados/', lista_empleados, name='lista_empleados'),
    path('registrar/', views.registrar_persona, name='registrar_persona'),
    path('registrar-empleado/', registrar_empleado, name='registrar_empleado'),
    path('login-unificado2/', login_unificado2, name='login_unificado2'),
    path('inicio/', pagina_principal, name='pagina_principal'),
    path('cambiar-password/', cambiar_password, name='cambiar_password'),
    path('cambiar-password-empleado/', cambiar_password_empleado, name='cambiar_password_empleado'),
    path('cambiar-password-logueado/', cambiar_password_logueado, name='cambiar_password_logueado'),
    path('cambiar-password-empleado-logueado/', cambiar_password_empleado_logueado, name='cambiar_password_empleado_logueado'),
    path('login-as-persona/', login_as_persona, name='login_as_persona'),
    path('gestion/', views.gestion, name='gestion'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('logout/', logout_view, name='logout'),
]


