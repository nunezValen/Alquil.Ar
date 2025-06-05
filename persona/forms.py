from django import forms
from .models import Persona, Alquiler
from datetime import date
from django.utils import timezone
from django.core.exceptions import ValidationError

class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['nombre', 'apellido', 'dni', 'email', 'fecha_nacimiento']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre', 'autocomplete': 'off', 'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Apellido', 'autocomplete': 'off', 'class': 'form-control'}),
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
        if dni:
            # Verificar si el DNI ya existe
            if Persona.objects.filter(dni=dni).exists():
                raise forms.ValidationError('El DNI ya se encuentra registrado.')
            
            # Eliminar cualquier espacio en blanco
            dni = dni.strip()
            
            # Verificar que solo contenga números
            if not dni.isdigit():
                raise forms.ValidationError('El DNI debe contener solo números.')
            
            # Verificar la longitud (entre 2 y 7 números)
            if len(dni) < 2 or len(dni) > 7:
                raise forms.ValidationError('El DNI debe tener entre 2 y 7 números.')
        
        return dni

    def save(self, commit=True):
        instance = super().save(commit=False)
        nombre_completo = self.cleaned_data.get('nombre', '').strip()
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

    def __init__(self, *args, maquina=None, **kwargs):
        self.maquina = maquina
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise forms.ValidationError("La fecha de inicio debe ser anterior a la fecha de fin.")
            
            if fecha_inicio < timezone.now().date():
                raise forms.ValidationError("La fecha de inicio no puede ser en el pasado.")
            
            # Verificar si la máquina está disponible para las fechas seleccionadas
            if self.maquina:
                alquileres_existentes = Alquiler.objects.filter(
                    maquina=self.maquina,
                    estado__in=['pendiente', 'confirmado', 'en_curso'],
                    fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio
                )
                
                if alquileres_existentes.exists():
                    raise forms.ValidationError("La máquina no está disponible para las fechas seleccionadas.")
        
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

class CambiarPasswordForm(forms.Form):
    password_actual = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña actual'}),
        label='Contraseña actual'
    )
    password_nuevo = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nueva contraseña'}),
        label='Nueva contraseña'
    )
    password_confirmacion = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar nueva contraseña'}),
        label='Confirmar nueva contraseña'
    )

    def clean_password_nuevo(self):
        password = self.cleaned_data.get('password_nuevo')
        if len(password) < 6:
            raise ValidationError('La contraseña debe tener al menos 6 caracteres.')
        if len(password) > 16:
            raise ValidationError('La contraseña no puede tener más de 16 caracteres.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password_nuevo = cleaned_data.get('password_nuevo')
        password_confirmacion = cleaned_data.get('password_confirmacion')

        if password_nuevo and password_confirmacion:
            if password_nuevo != password_confirmacion:
                raise ValidationError('Las contraseñas no coinciden.')
        return cleaned_data
