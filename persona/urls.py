from django.urls import path
from .views import (
    lista_personas, lista_maquinas, lista_empleados, login_view, 
    inicio_blanco, registrar_persona, catalogo_maquinas, 
    detalle_maquina, mis_alquileres, webhook_mercadopago, checkout_mp
)
from .views import (
    lista_personas, lista_maquinas, lista_empleados,
    pagina_principal, registrar_empleado, cambiar_password,
    cambiar_password_empleado, cambiar_password_logueado,
    cambiar_password_empleado_logueado, login_as_persona,
    login_unificado2, logout_view, switch_back_to_employee,
    editar_datos_personales
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
    path('switch-back-to-employee/', switch_back_to_employee, name='switch_back_to_employee'),
    path('gestion/', views.gestion, name='gestion'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('logout/', logout_view, name='logout'),
    path('editar-datos-personales/', editar_datos_personales, name='editar_datos_personales'),
]
    path('registrar/', registrar_persona, name='registrar_persona'),
    path('login/', login_view, name='login'),
    path('inicio/', inicio_blanco, name='inicio_blanco'),
    path('catalogo/', catalogo_maquinas, name='catalogo_maquinas'),
    path('maquina/<int:maquina_id>/', detalle_maquina, name='detalle_maquina'),
    path('checkout/<int:alquiler_id>/', checkout_mp, name='checkout_mp'),
    path('mis-alquileres/', mis_alquileres, name='mis_alquileres'),
    path('webhook/mercadopago/', webhook_mercadopago, name='webhook_mercadopago'),
]


