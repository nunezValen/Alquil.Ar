from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import MaquinaBase, Unidad
from sucursales.models import Sucursal
from django.core.exceptions import ValidationError


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
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'marca': forms.Select(attrs={
                'class': 'form-select'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'precio_por_dia': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'descripcion_corta': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'descripcion_larga': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'dias_alquiler_min': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'dias_alquiler_max': forms.NumberInput(attrs={
                'class': 'form-control'
            })
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre de la máquina es obligatorio.',
            },
            'tipo': {
                'required': 'Debe seleccionar un tipo de máquina.',
            },
            'marca': {
                'required': 'Debe seleccionar una marca.',
            },
            'modelo': {
                'required': 'El modelo de la máquina es obligatorio.',
            },
            'precio_por_dia': {
                'required': 'El precio por día es obligatorio.',
                'invalid': 'Por favor, ingrese un precio válido.',
                'min_value': 'El precio debe ser mayor o igual a cero.',
                'max_digits': 'El precio no puede tener más de 10 dígitos.',
                'max_decimal_places': 'El precio no puede tener más de 2 decimales.',
            },
            'descripcion_corta': {
                'required': 'La descripción corta es obligatoria.',
            },
            'descripcion_larga': {
                'required': 'La descripción larga es obligatoria.',
            },
            'imagen': {
                'required': 'Debe subir una imagen de la máquina.',
            },
            'dias_alquiler_min': {
                'required': 'La cantidad mínima de días de alquiler es obligatoria.',
                'min_value': 'La cantidad mínima de días de alquiler debe ser mayor a 0.',
            },
            'dias_alquiler_max': {
                'required': 'La cantidad máxima de días de alquiler es obligatoria.',
                'min_value': 'La cantidad máxima de días de alquiler debe ser mayor a 0.',
            }
        }

    def clean(self):
        cleaned_data = super().clean()
        dias_min = cleaned_data.get('dias_alquiler_min')
        dias_max = cleaned_data.get('dias_alquiler_max')
        
        if dias_min and dias_max and dias_max < dias_min:
            self.add_error('dias_alquiler_max',
                'La cantidad máxima de días de alquiler debe ser mayor o igual a la cantidad mínima.')
        
        return cleaned_data


class UnidadForm(forms.ModelForm):
    class Meta:
        model = Unidad

        fields = [
            'maquina_base',
            'patente',
            'sucursal',
        ]
        widgets = {
            'maquina_base': forms.Select(attrs={'class': 'form-select'}),
            'patente': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 10}),
            'sucursal': forms.Select(attrs={'class': 'form-select'}),
        }
        error_messages = {
            'maquina_base': {
                'required': 'Debe seleccionar una máquina base.',
            },
            'patente': {
                'required': 'La patente es obligatoria.',
                'max_length': 'La patente no puede tener más de 10 caracteres.',
                'unique': 'Ya existe una unidad con esa patente.',
            },
            'sucursal': {
                'required': 'Debe seleccionar una sucursal.',
            },
        }

    # Al instanciar el formulario, se fuerza estado="disponible" y visible=True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el formulario no recibe datos (GET), ya cargamos los valores por defecto
        if not self.instance.pk:
            self.instance.estado = 'disponible'
            self.instance.visible = True

    def clean_patente(self):
        patente = self.cleaned_data.get('patente', '').strip().upper()
        if Unidad.objects.filter(patente__iexact=patente).exists():
            raise ValidationError('Ya existe una unidad registrada con esa patente.')
        return patente

    def save(self, commit=True):
        # Al guardar queda visible=True y estado="disponible"
        unidad = super().save(commit=False)
        unidad.estado = 'disponible'
        unidad.visible = True
        if commit:
            unidad.save()
        return unidad