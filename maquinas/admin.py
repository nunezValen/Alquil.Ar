from django.contrib import admin
from .models import MaquinaBase, Unidad

@admin.register(MaquinaBase)
class MaquinaBaseAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'marca', 'modelo', 'precio_por_dia')
    list_filter = ('tipo', 'marca')
    search_fields = ('nombre', 'modelo')

@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ('maquina_base', 'patente', 'sucursal', 'estado', 'visible')
    list_filter = ('estado', 'sucursal', 'visible')
    search_fields = ('patente', 'maquina_base__nombre')
