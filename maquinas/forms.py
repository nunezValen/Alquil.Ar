from django import forms
from .models import MaquinaBase

class MaquinaBaseForm(forms.ModelForm):
    class Meta:
        model = MaquinaBase
        fields = [
            'nombre',
            'tipo',
            'marca',
            'modelo',
            'precio_por_dia',
            'descripcion_corta',
            'descripcion_larga',
            'imagen',
            'dias_alquiler_min',
            'dias_alquiler_max',
        ]
        
    def clean(self):
        cleaned_data = super().clean()
        dias_min = cleaned_data.get('dias_alquiler_min')
        dias_max = cleaned_data.get('dias_alquiler_max')
        
        if dias_min and dias_max and dias_max < dias_min:
            raise forms.ValidationError('La cantidad máxima de días debe ser mayor o igual a la cantidad mínima.') 