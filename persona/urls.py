from django.urls import path
from .views import lista_personas, lista_maquinas, lista_empleados

urlpatterns = [
    path('personas/', lista_personas, name='lista_personas'),
    path('maquinas/', lista_maquinas, name='lista_maquinas'),
    path('empleados/', lista_empleados, name='lista_empleados'),

]


