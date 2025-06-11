from django.contrib import admin
from .models import MaquinaBase, Unidad, Alquiler, Reembolso
from django import forms
from django.core.exceptions import ValidationError

@admin.register(MaquinaBase)
class MaquinaBaseAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'marca', 'modelo', 'precio_por_dia', 'stock')
    list_filter = ('tipo', 'marca')
    search_fields = ('nombre', 'modelo')

@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'maquina_base', 'sucursal', 'estado', 'visible')
    list_filter = ('sucursal', 'estado', 'visible')
    search_fields = ('patente', 'maquina_base__nombre')

class AlquilerAdminForm(forms.ModelForm):
    class Meta:
        model = Alquiler
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        estado = cleaned_data.get("estado")
        calificacion = cleaned_data.get("calificacion")

        if estado == "finalizado" and calificacion is None:
            raise ValidationError(
                "La calificación es obligatoria cuando un alquiler está finalizado."
            )
        return cleaned_data

@admin.register(Alquiler)
class AlquilerAdmin(admin.ModelAdmin):
    form = AlquilerAdminForm
    list_display = ('numero', 'persona', 'maquina_base', 'fecha_inicio', 'fecha_fin', 'estado', 'monto_total', 'calificacion')
    list_filter = ('estado', 'metodo_pago', 'fecha_inicio')
    search_fields = ('numero', 'persona__nombre', 'persona__apellido', 'persona__email', 'maquina_base__nombre')
    autocomplete_fields = ('persona', 'maquina_base', 'unidad')

    readonly_fields = ('numero', 'cantidad_dias', 'monto_total', 'codigo_retiro', 'fecha_creacion', 'fecha_actualizacion')

    fieldsets = (
        (None, {
            'fields': ('persona', 'maquina_base', 'unidad', 'estado', 'metodo_pago')
        }),
        ('Periodo y Calificación', {
            'fields': ('fecha_inicio', 'fecha_fin', 'calificacion')
        }),
        ('Valores Calculados', {
            'fields': ('numero', 'cantidad_dias', 'monto_total', 'codigo_retiro')
        }),
        ('Información de Cancelación', {
            'classes': ('collapse',),
            'fields': ('fecha_cancelacion', 'cancelado_por_empleado', 'empleado_que_cancelo', 'monto_reembolso', 'porcentaje_reembolso', 'observaciones_cancelacion')
        }),
        ('Metadatos', {
            'classes': ('collapse',),
            'fields': ('preference_id', 'fecha_creacion', 'fecha_actualizacion')
        }),
    )

@admin.register(Reembolso)
class ReembolsoAdmin(admin.ModelAdmin):
    list_display = ('alquiler', 'monto', 'estado', 'fecha_creacion', 'fecha_pago')
    list_filter = ('estado',)
    search_fields = ('alquiler__numero',)
