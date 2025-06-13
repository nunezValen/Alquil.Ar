from django.urls import path
from . import views

app_name = 'maquinas'

urlpatterns = [
    path('', views.lista_maquinas, name='lista_maquinas'),
    path('maquina/<int:maquina_id>/', views.detalle_maquina, name='detalle_maquina'),
    path('maquina/<int:maquina_id>/alquilar/', views.alquilar_maquina, name='alquilar_maquina'),
    path('checkout/<int:alquiler_id>/', views.checkout_mp, name='checkout_mp'),
    path('webhook-mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
    path('catalogo/', views.catalogo_publico, name='catalogo_publico'),
    path('maquina/cargar/', views.cargar_maquina_base, name='cargar_maquina_base'),
    path('maquina/<int:maquina_id>/eliminar/', views.eliminar_maquina_base, name='eliminar_maquina_base'),
    path('confirmar-alquiler/', views.confirmar_alquiler, name='confirmar_alquiler'),
    path('error-pago/', views.error_pago, name='error_pago'),
    path('pago-pendiente/', views.pago_pendiente, name='pago_pendiente'),
    path('unidades/', views.lista_unidades, name='lista_unidades'),
    path('unidad/cargar/', views.cargar_unidad, name='cargar_unidad'),
    path('unidad/<int:unidad_id>/eliminar/', views.eliminar_unidad, name='eliminar_unidad'),
    path('eliminar_unidad/<int:pk>/', views.eliminar_unidad, name='eliminar_unidad'),
    path('editar_maquina_base/<int:pk>/', views.editar_maquina_base, name='editar_maquina_base'),
    path('editar_unidad/<int:pk>/', views.editar_unidad, name='editar_unidad'),
    path('unidad/<int:pk>/toggle_visibilidad/', views.toggle_visibilidad_unidad, name='toggle_visibilidad_unidad'),
    path('unidad/<int:pk>/toggle_mantenimiento/', views.toggle_mantenimiento_unidad, name='toggle_mantenimiento_unidad'),
    path('cancelar-alquiler/<int:alquiler_id>/', views.cancelar_alquiler, name='cancelar_alquiler'),
    path('maquina/<int:maquina_id>/desocultar/', views.desocultar_maquina_base, name='desocultar_maquina_base'),
] 