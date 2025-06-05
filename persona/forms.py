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
            'class': 'form-control',
        })
    )

    password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Contraseña',
            'autocomplete': 'new-password',
            'class': 'form-control',
        })
    )

    password_confirmation = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirmar Contraseña',
            'autocomplete': 'new-password',
            'class': 'form-control',
        })
    )

    class Meta:
        model = Persona
        fields = ['nombre_completo', 'dni', 'email', 'fecha_nacimiento']
        widgets = {
            'dni': forms.TextInput(attrs={'placeholder': 'DNI', 'autocomplete': 'off', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'autocomplete': 'off', 'class': 'form-control'}),
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

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirmation = cleaned_data.get('password_confirmation')

        if password and password_confirmation:
            if password != password_confirmation:
                raise forms.ValidationError('Las contraseñas no coinciden.')
            if len(password) < 8:
                raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
        return cleaned_data

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
    class Meta:
        model = Persona
        fields = ['nombre', 'apellido', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['nombre'].initial = self.instance.nombre
            self.fields['apellido'].initial = self.instance.apellido
            self.fields['email'].initial = self.instance.email

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if edad < 18:
                raise forms.ValidationError('No cumple con la mayoría de edad.')
        return fecha

    def clean_email(self):
        if self.instance and self.instance.pk:
            return self.instance.email
        return self.cleaned_data.get('email')

    def clean_dni(self):
        if self.instance and self.instance.pk:
            return self.instance.dni
        return self.cleaned_data.get('dni')

    def save(self, commit=True):
        instance = super().save(commit=False)
        nombre_completo = self.cleaned_data.get('nombre', '').strip()
        partes = nombre_completo.split(' ', 1)
        instance.nombre = partes[0]
        instance.apellido = partes[1] if len(partes) > 1 else ''
        if commit:
            instance.save()
        return instance
