from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import MaquinaBase, Unidad, Alquiler
from persona.models import Sucursal
from django.core.exceptions import ValidationError
from datetime import date


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
            'dias_cancelacion_total',
            'dias_cancelacion_parcial',
            'porcentaje_reembolso_parcial',
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
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'dias_alquiler_min': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'dias_alquiler_max': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'dias_cancelacion_total': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'dias_cancelacion_parcial': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'porcentaje_reembolso_parcial': forms.NumberInput(attrs={
                'class': 'form-control'
            })
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre de la máquina es obligatorio.',
                'max_length': 'El nombre no puede tener más de 100 caracteres.',
            },
            'tipo': {
                'required': 'Debe seleccionar un tipo.',
            },
            'marca': {
                'required': 'Debe seleccionar una marca.',
            },
            'modelo': {
                'required': 'El modelo de la máquina es obligatorio.',
                'max_length': 'El modelo no puede tener más de 50 caracteres.',
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
                'required': 'La imagen es obligatoria.',
                'invalid': 'Por favor, suba una imagen válida de la máquina.',
            },
            'dias_alquiler_min': {
                'required': 'La cantidad mínima de días de alquiler es obligatoria.',
                'min_value': 'La cantidad mínima de días de alquiler debe ser mayor a 0.',
            },
            'dias_alquiler_max': {
                'required': 'La cantidad máxima de días de alquiler es obligatoria.',
                'min_value': 'La cantidad máxima de días de alquiler debe ser mayor a 0.',
            },
            'dias_cancelacion_total': {
                'required': 'Los días para reembolso total son obligatorios.',
                'min_value': 'Los días para reembolso total deben ser mayores a 0.',
            },
            'dias_cancelacion_parcial': {
                'required': 'Los días para reembolso parcial son obligatorios.',
                'min_value': 'Los días para reembolso parcial deben ser mayores a 0.',
            },
            'porcentaje_reembolso_parcial': {
                'invalid': 'Ingrese un número entero.',
                'required': 'El porcentaje de reembolso parcial es obligatorio.',
                'min_value': 'El porcentaje debe ser mayor a 0.',
                'max_value': 'El porcentaje debe ser menor a 100.',
            }
        }

    def clean(self):
        cleaned_data = super().clean()
        dias_min = cleaned_data.get('dias_alquiler_min')
        dias_max = cleaned_data.get('dias_alquiler_max')
        
        if dias_min and dias_max and dias_max < dias_min:
            self.add_error('dias_alquiler_max',
                'La cantidad máxima de días de alquiler debe ser mayor o igual a la cantidad mínima.')
        
        # Validar que los días de cancelación parcial sean menores a los de cancelación total
        dias_cancelacion_parcial = cleaned_data.get('dias_cancelacion_parcial')
        dias_cancelacion_total = cleaned_data.get('dias_cancelacion_total')
        
        if dias_cancelacion_parcial and dias_cancelacion_total:
            if dias_cancelacion_parcial >= dias_cancelacion_total:
                self.add_error('dias_cancelacion_parcial',
                    'Los días para reembolso parcial deben ser menores a los días para reembolso total.')

        # Validar que se suba una imagen para nuevas máquinas
        if not self.instance.pk and not cleaned_data.get('imagen'):
            self.add_error('imagen', 'Por favor, suba una imagen de la máquina.')
        
        # Si hay error en imagen y es el mensaje en inglés, lo reemplazo
        imagen_errors = self.errors.get('imagen')
        if imagen_errors:
            errores_nuevos = []
            for error in imagen_errors:
                if 'Upload a valid image' in error or 'The file you uploaded was either not an image or a corrupted image.' in error:
                    errores_nuevos.append('')
                else:
                    errores_nuevos.append(error)
            self._errors['imagen'] = self.error_class(errores_nuevos)
        
        return cleaned_data


class UnidadForm(forms.ModelForm):
    patente_original = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Unidad
        fields = ['patente', 'sucursal']
        widgets = {
            'patente': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 10}),
            'sucursal': forms.Select(attrs={'class': 'form-select'}),
        }
        error_messages = {
            'patente': {
                'required': 'La patente es obligatoria.',
                'max_length': 'La patente no puede tener más de 10 caracteres.',
            },
            'sucursal': {
                'required': 'Debe seleccionar una sucursal.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Modificar el queryset de sucursales para mostrar la dirección
        self.fields['sucursal'].queryset = Sucursal.objects.filter(es_visible=True)
        self.fields['sucursal'].label_from_instance = lambda obj: f"{obj.direccion}"

    def clean(self):
        cleaned_data = super().clean()
        nueva_patente = cleaned_data.get('patente', '').strip().upper()
        patente_original = cleaned_data.get('patente_original', '').strip().upper()

        # Si la patente no cambió, no validar duplicados
        if nueva_patente == patente_original:
            return cleaned_data

        # Solo validar si la patente es diferente a la original
        if Unidad.objects.filter(patente__iexact=nueva_patente).exists():
            self.add_error('patente', "Esa patente ya está registrada.")
        
        return cleaned_data


class CargarUnidadForm(forms.ModelForm):
    class Meta:
        model = Unidad
        fields = ['maquina_base', 'patente', 'sucursal']
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el formulario no recibe datos (GET), ya cargamos los valores por defecto
        if not self.instance.pk:
            self.instance.estado = 'disponible'
            self.instance.visible = True
 
        # Solo mostrar sucursales visibles
        self.fields['sucursal'].queryset = Sucursal.objects.filter(es_visible=True)
        self.fields['sucursal'].label_from_instance = lambda obj: f"{obj.direccion}"

    def clean_patente(self):
        patente = self.cleaned_data.get('patente', '').strip().upper()
        if Unidad.objects.filter(patente__iexact=patente).exists():
            raise ValidationError('Ya existe una unidad registrada con esa patente.')
        return patente


class AlquilerForm(forms.Form):
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha de inicio'
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha de fin'
    )
    metodo_pago = forms.ChoiceField(
        choices=Alquiler.METODOS_PAGO,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Método de pago'
    )

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            # Validar que la fecha de inicio no sea en el pasado
            if fecha_inicio < date.today():
                raise forms.ValidationError("La fecha de inicio no puede ser en el pasado.")
            
            # Validar que la fecha de fin sea posterior a la fecha de inicio
            if fecha_fin < fecha_inicio:
                raise forms.ValidationError("La fecha de fin debe ser posterior a la fecha de inicio.")
            
            # Validar que el período no sea mayor a 30 días
            dias = (fecha_fin - fecha_inicio).days + 1
            if dias > 30:
                raise forms.ValidationError("El período máximo de alquiler es de 30 días.")
        
        return cleaned_data