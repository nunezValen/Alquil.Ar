from django import forms
from .models import Persona, Alquiler
from datetime import date
from django.utils import timezone

class PersonaForm(forms.ModelForm):
    nombre_completo = forms.CharField(
        max_length=200,
        label='',
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre Completo',
            'autocomplete': 'off',
        })
    )

    es_empleado = forms.BooleanField(
        required=False,
        label='Registrarme como empleado',
        widget=forms.CheckboxInput(attrs={
            'class': 'employee-checkbox',
        })
    )

    class Meta:
        model = Persona
        fields = ['nombre_completo', 'dni', 'email', 'fecha_nacimiento', 'es_empleado']
        widgets = {
            'dni': forms.TextInput(attrs={'placeholder': 'DNI', 'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'autocomplete': 'off'}),
            'fecha_nacimiento': forms.DateInput(attrs={'placeholder': 'Fecha de Nacimiento', 'type': 'date', 'class': 'form-control', 'autocomplete': 'off'}),
        }

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if edad < 18:
                raise forms.ValidationError('No cumple con la mayoría de edad.')
        return fecha

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Persona.objects.filter(email=email).exists():
            raise forms.ValidationError('El email ya se encuentra registrado.')
        return email

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni and Persona.objects.filter(dni=dni).exists():
            raise forms.ValidationError('El DNI ya se encuentra registrado.')
        return dni

    def save(self, commit=True):
        instance = super().save(commit=False)
        nombre_completo = self.cleaned_data.get('nombre_completo', '').strip()
        partes = nombre_completo.split(' ', 1)
        instance.nombre = partes[0]
        instance.apellido = partes[1] if len(partes) > 1 else ''
        if commit:
            instance.save()
        return instance

class AlquilerForm(forms.ModelForm):
    class Meta:
        model = Alquiler
        fields = ['fecha_inicio', 'fecha_fin', 'metodo_pago']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'metodo_pago': forms.RadioSelect(choices=[
                ('mercadopago', 'Mercado Pago'),
                ('binance', 'Binance Pay')
            ])
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise forms.ValidationError("La fecha de inicio debe ser anterior a la fecha de fin.")
            
            if fecha_inicio < timezone.now().date():
                raise forms.ValidationError("La fecha de inicio no puede ser en el pasado.")
        
        return cleaned_data 

class EditarPersonaForm(forms.ModelForm):
    nombre_completo = forms.CharField(
        max_length=200,
        label='Nombre Completo',
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre Completo',
            'autocomplete': 'off',
            'class': 'form-control',
        })
    )

    class Meta:
        model = Persona
        fields = ['nombre_completo', 'dni', 'email', 'telefono', 'fecha_nacimiento', 'direccion']
        widgets = {
            'dni': forms.TextInput(attrs={'placeholder': 'DNI', 'autocomplete': 'off', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'autocomplete': 'off', 'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Teléfono', 'autocomplete': 'off', 'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'placeholder': 'Fecha de Nacimiento', 'type': 'date', 'class': 'form-control', 'autocomplete': 'off'}),
            'direccion': forms.Textarea(attrs={'placeholder': 'Dirección', 'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.instance_id = kwargs.pop('instance_id', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['nombre_completo'].initial = f"{self.instance.nombre} {self.instance.apellido}"
            # Make DNI and email fields read-only
            self.fields['dni'].widget.attrs['readonly'] = True
            self.fields['email'].widget.attrs['readonly'] = True

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if edad < 18:
                raise forms.ValidationError('No cumple con la mayoría de edad.')
        return fecha

    def clean_email(self):
        # Always return the original email value from the instance
        if self.instance and self.instance.pk:
            return self.instance.email
        return self.cleaned_data.get('email')

    def clean_dni(self):
        # Always return the original DNI value from the instance
        if self.instance and self.instance.pk:
            return self.instance.dni
        return self.cleaned_data.get('dni')

    def save(self, commit=True):
        instance = super().save(commit=False)
        nombre_completo = self.cleaned_data.get('nombre_completo', '').strip()
        partes = nombre_completo.split(' ', 1)
        instance.nombre = partes[0]
        instance.apellido = partes[1] if len(partes) > 1 else ''
        if commit:
            instance.save()
        return instance
