from django.urls import path
from .views import (
    lista_personas, lista_maquinas, lista_empleados, login_view, 
    registrar_persona, catalogo_maquinas, 
    detalle_maquina, mis_alquileres, webhook_mercadopago,
    pagina_principal, registrar_empleado, cambiar_password,
    cambiar_password_empleado_logueado, login_as_persona,
    login_unificado2, logout_view, switch_back_to_employee,
    modificar_datos_personales, gestion, estadisticas, inicio,
    lista_alquileres, lista_clientes, checkout, recuperar_password, mapa_sucursales,
    pago_exitoso, pago_fallido, pago_pendiente, cancelar_mi_alquiler,
    lista_reembolsos, marcar_reembolso_pagado, buscar_clientes_json,
    enviar_codigo_verificacion, verificar_codigo, cambiar_password_2,
    bloquear_cliente, desbloquear_cliente,
    lista_empleados_gestion, bloquear_empleado, desbloquear_empleado,
    registrar_cliente_nuevo, registrar_empleado_nuevo
)
from maquinas.views import cancelar_alquiler

app_name = 'persona'

urlpatterns = [
    path('', pagina_principal, name='inicio'),
    path('inicio/', inicio, name='inicio'),
    path('personas/', lista_personas, name='lista_personas'),
    path('maquinas/', lista_maquinas, name='lista_maquinas'),
    path('empleados/', lista_empleados, name='lista_empleados'),
    path('registrar/', registrar_persona, name='registrar_persona'),
    path('registrar-empleado/', registrar_empleado, name='registrar_empleado'),
    path('registrar-cliente-nuevo/', registrar_cliente_nuevo, name='registrar_cliente_nuevo'),
    path('registrar-empleado-nuevo/', registrar_empleado_nuevo, name='registrar_empleado_nuevo'),
    path('login-unificado2/', login_unificado2, name='login_unificado2'),
    path('catalogo/', catalogo_maquinas, name='catalogo_maquinas'),
    path('maquina/<int:maquina_id>/', detalle_maquina, name='detalle_maquina'),
    path('checkout/<int:alquiler_id>/', checkout, name='checkout'),
    path('mis-alquileres/', mis_alquileres, name='mis_alquileres'),
    path('cancelar-mi-alquiler/<int:alquiler_id>/', cancelar_mi_alquiler, name='cancelar_mi_alquiler'),
    path('cancelar-alquiler/<int:alquiler_id>/', cancelar_alquiler, name='cancelar_alquiler'),
    path('webhook-mercadopago/', webhook_mercadopago, name='webhook_mercadopago'),
    path('cambiar-password/', cambiar_password, name='cambiar_password'),
    path('cambiar-password-empleado/', cambiar_password_empleado_logueado, name='cambiar_password_empleado'),
    path('cambiar-password-empleado-logueado/', cambiar_password_empleado_logueado, name='cambiar_password_empleado_logueado'),
    path('cambiar-password-2/', cambiar_password_2, name='cambiar_password_2'),
    path('login-as-persona/', login_as_persona, name='login_as_persona'),
    path('switch-back-to-employee/', switch_back_to_employee, name='switch_back_to_employee'),
    path('gestion/', gestion, name='gestion'),
    path('estadisticas/', estadisticas, name='estadisticas'),
    path('logout/', logout_view, name='logout'),
    path('modificar-datos-personales/', modificar_datos_personales, name='modificar_datos_personales'),
    path('alquileres/', lista_alquileres, name='lista_alquileres'),
    path('reembolsos/', lista_reembolsos, name='lista_reembolsos'),
    path('marcar-reembolso-pagado/<int:reembolso_id>/', marcar_reembolso_pagado, name='marcar_reembolso_pagado'),
    path('buscar-clientes-json/', buscar_clientes_json, name='buscar_clientes_json'),
    path('pago-exitoso/', pago_exitoso, name='pago_exitoso'),
    path('pago-fallido/', pago_fallido, name='pago_fallido'),
    path('pago-pendiente/', pago_pendiente, name='pago_pendiente'),
    path('recuperar-password/', recuperar_password, name='recuperar_password'),
    path('sucursales/', mapa_sucursales, name='mapa_sucursales'),
    # URLs para verificación en dos pasos
    path('verificacion/enviar-codigo/', enviar_codigo_verificacion, name='enviar_codigo_verificacion'),
    path('verificacion/verificar-codigo/', verificar_codigo, name='verificar_codigo'),
    path('lista_clientes/', lista_clientes, name='lista_clientes'),
    # Rutas para gestión de clientes (bloqueo/desbloqueo)
    path('clientes/<int:persona_id>/bloquear/', bloquear_cliente, name='bloquear_cliente'),
    path('clientes/<int:persona_id>/desbloquear/', desbloquear_cliente, name='desbloquear_cliente'),
    # Rutas para gestión de empleados (bloqueo/desbloqueo)
    path('gestion/empleados/', lista_empleados_gestion, name='lista_empleados_gestion'),
    path('empleados/<int:persona_id>/bloquear/', bloquear_empleado, name='bloquear_empleado'),
    path('empleados/<int:persona_id>/desbloquear/', desbloquear_empleado, name='desbloquear_empleado'),
]


