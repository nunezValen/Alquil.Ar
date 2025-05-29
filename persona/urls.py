from django.urls import path
from .views import (
    lista_personas, lista_maquinas, lista_empleados, login_view, 
    inicio_blanco, registrar_persona, catalogo_maquinas, 
    detalle_maquina, mis_alquileres, webhook_mercadopago, checkout_mp
)

urlpatterns = [
    path('personas/', lista_personas, name='lista_personas'),
    path('maquinas/', lista_maquinas, name='lista_maquinas'),
    path('empleados/', lista_empleados, name='lista_empleados'),
    path('registrar/', registrar_persona, name='registrar_persona'),
    path('login/', login_view, name='login'),
    path('inicio/', inicio_blanco, name='inicio_blanco'),
    path('catalogo/', catalogo_maquinas, name='catalogo_maquinas'),
    path('maquina/<int:maquina_id>/', detalle_maquina, name='detalle_maquina'),
    path('checkout/<int:alquiler_id>/', checkout_mp, name='checkout_mp'),
    path('mis-alquileres/', mis_alquileres, name='mis_alquileres'),
    path('webhook/mercadopago/', webhook_mercadopago, name='webhook_mercadopago'),
]


