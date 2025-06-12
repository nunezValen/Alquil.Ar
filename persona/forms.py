from django import forms
from .models import Persona, Alquiler
from datetime import date
from django.utils import timezone
from django.core.exceptions import ValidationError

class PersonaForm(forms.ModelForm):
    es_cliente = forms.BooleanField(required=False, label='Cliente', initial=False)
    es_empleado = forms.BooleanField(required=False, label='Empleado', initial=False)
    fecha_nacimiento = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'placeholder': 'Fecha de Nacimiento', 
            'type': 'date', 
            'class': 'form-control', 
            'autocomplete': 'off',
            'required': True
        })
    )

    class Meta:
        model = Persona
        fields = ['nombre', 'apellido', 'dni', 'email', 'fecha_nacimiento', 'es_cliente', 'es_empleado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Nombre', 
                'autocomplete': 'off', 
                'class': 'form-control',
                'required': True
            }),
            'apellido': forms.TextInput(attrs={
                'placeholder': 'Apellido', 
                'autocomplete': 'off', 
                'class': 'form-control',
                'required': True
            }),
            'dni': forms.NumberInput(attrs={
                'placeholder': 'DNI', 
                'autocomplete': 'off', 
                'class': 'form-control',
                'type': 'number',
                'min': '1000000',  # 7 dígitos mínimo
                'max': '999999999',  # 9 dígitos máximo
                'oninput': 'javascript: if (this.value.length > 9) this.value = this.value.slice(0, 9);'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Email', 
                'autocomplete': 'off', 
                'class': 'form-control', 
                'required': True
            })
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre es obligatorio.',
                'max_length': 'El nombre no puede tener más de 100 caracteres.'
            },
            'apellido': {
                'required': 'El apellido es obligatorio.',
                'max_length': 'El apellido no puede tener más de 100 caracteres.'
            },
            'dni': {
                'required': 'El DNI es obligatorio.',
                'unique': 'Ya existe una persona registrada con este DNI.'
            },
            'email': {
                'required': 'El email es obligatorio.',
                'unique': 'Ya existe una persona registrada con este email.',
                'invalid': 'Por favor, ingrese un email válido.'
            }
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre es obligatorio.')
        return nombre

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '').strip()
        if not apellido:
            raise forms.ValidationError('El apellido es obligatorio.')
        return apellido

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if not fecha_nacimiento:
            raise ValidationError('La fecha de nacimiento es obligatoria.')
        
        # Verificar que la fecha no sea futura
        if fecha_nacimiento > date.today():
            raise ValidationError('La fecha de nacimiento no puede ser futura.')
        
        # Verificar que la persona sea mayor de 18 años
        edad = (date.today() - fecha_nacimiento).days / 365.25
        if edad < 18:
            raise ValidationError('Debe ser mayor de 18 años para registrarse.')
        
        return fecha_nacimiento

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get('nombre')
        apellido = cleaned_data.get('apellido')
        
        if nombre and not nombre.strip():
            self.add_error('nombre', 'El nombre no puede estar vacío.')
        
        if apellido and not apellido.strip():
            self.add_error('apellido', 'El apellido no puede estar vacío.')
        
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('El email es obligatorio.')
        if Persona.objects.filter(email=email).exists():
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
            
            # Verificar la longitud (entre 7 y 9 números)
            if len(dni) < 7 or len(dni) > 9:
                raise forms.ValidationError('El DNI debe tener entre 7 y 9 números.')
        
        return dni

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Limpiar espacios en blanco de nombre y apellido
        if instance.nombre:
            instance.nombre = instance.nombre.strip()
        if instance.apellido:
            instance.apellido = instance.apellido.strip()
            
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
        fields = ['nombre', 'apellido']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'minlength': '2',
                'maxlength': '50'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'minlength': '2',
                'maxlength': '50'
            }),
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre es obligatorio.',
                'max_length': 'El nombre no puede tener más de 50 caracteres.',
                'min_length': 'El nombre debe tener al menos 2 caracteres.'
            },
            'apellido': {
                'required': 'El apellido es obligatorio.',
                'max_length': 'El apellido no puede tener más de 50 caracteres.',
                'min_length': 'El apellido debe tener al menos 2 caracteres.'
            }
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre es obligatorio.')
        if len(nombre) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
        if len(nombre) > 50:
            raise forms.ValidationError('El nombre no puede tener más de 50 caracteres.')
        return nombre

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '').strip()
        if not apellido:
            raise forms.ValidationError('El apellido es obligatorio.')
        if len(apellido) < 2:
            raise forms.ValidationError('El apellido debe tener al menos 2 caracteres.')
        if len(apellido) > 50:
            raise forms.ValidationError('El apellido no puede tener más de 50 caracteres.')
        return apellido

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Limpiar espacios en blanco
        if instance.nombre:
            instance.nombre = instance.nombre.strip()
        if instance.apellido:
            instance.apellido = instance.apellido.strip()
            
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
