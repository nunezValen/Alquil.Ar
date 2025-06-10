from django.contrib import admin
from .models import Persona, Maquina, Sucursal

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('direccion', 'telefono', 'email', 'horario')
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
    )

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'email', 'es_cliente', 'es_empleado', 'es_admin', 'es_baneado')
    list_filter = ('es_cliente', 'es_empleado', 'es_admin', 'es_baneado')
    search_fields = ('nombre', 'apellido', 'email')

# Registramos los demás modelos si no están ya registrados
admin.site.register(Maquina)
