from django import forms
from .models import Persona, Empleado
from datetime import date

class PersonaForm(forms.ModelForm):
    nombre_completo = forms.CharField(
        max_length=200,
        label='',
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre Completo',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = Persona
        fields = ['nombre_completo', 'dni', 'email', 'fecha_nacimiento']
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

class EmpleadoForm(forms.ModelForm):
    nombre_completo = forms.CharField(
        max_length=200,
        label='',
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre Completo',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = Empleado
        fields = ['nombre_completo', 'dni', 'email', 'fecha_nacimiento']
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
        if email:
            if Empleado.objects.filter(email=email).exists():
                raise forms.ValidationError('El email ya se encuentra registrado como empleado.')
        return email

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni and Empleado.objects.filter(dni=dni).exists():
            raise forms.ValidationError('El DNI ya se encuentra registrado como empleado.')
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