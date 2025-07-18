from django.contrib import admin
from .models import Persona, Maquina, Sucursal

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('direccion', 'telefono', 'email', 'horario', 'es_visible')
    search_fields = ('direccion', 'telefono', 'email', 'horario')
    fieldsets = (
        ('Ubicación', {
            'fields': ('direccion', 'latitud', 'longitud')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email')
        }),
        ('Horarios', {
            'fields': ('horario',)
        }),
        ('Visibilidad', {
            'fields': ('es_visible',)
        }),
    )

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'email', 'es_cliente', 'es_empleado', 'es_admin', 'bloqueado_cliente', 'bloqueado_empleado')
    list_filter = ('es_cliente', 'es_empleado', 'es_admin', 'bloqueado_cliente', 'bloqueado_empleado')
    search_fields = ('nombre', 'apellido', 'email')

# Registramos los demás modelos si no están ya registrados
admin.site.register(Maquina)
