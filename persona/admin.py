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

# Registramos los demás modelos si no están ya registrados
admin.site.register(Persona)
admin.site.register(Maquina)
