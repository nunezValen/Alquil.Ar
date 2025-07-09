from django import forms
from .models import Persona, Alquiler, Sucursal
from datetime import date
from django.utils import timezone
from django.core.exceptions import ValidationError

class PersonaForm(forms.ModelForm):
    es_cliente = forms.BooleanField(required=False, label='Cliente', initial=False)
    es_empleado = forms.BooleanField(required=False, label='Empleado', initial=False)

    class Meta:
        model = Persona
        fields = ['nombre', 'apellido', 'dni', 'email', 'fecha_nacimiento', 'es_cliente', 'es_empleado']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre', 'autocomplete': 'off', 'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Apellido', 'autocomplete': 'off', 'class': 'form-control'}),
            'dni': forms.NumberInput(attrs={
                'placeholder': 'DNI', 
                'autocomplete': 'off', 
                'class': 'form-control',
                'type': 'number',
                'min': '1000000',  # 7 dígitos mínimo
                'max': '999999999',  # 9 dígitos máximo
                'oninput': 'javascript: if (this.value.length > 9) this.value = this.value.slice(0, 9);'
            }),
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'autocomplete': 'off', 'class': 'form-control', 'required': True}),
            'fecha_nacimiento': forms.DateInput(attrs={'placeholder': 'Fecha de Nacimiento', 'type': 'date', 'class': 'form-control', 'autocomplete': 'off'}),
        }
        error_messages = {
            'email': {
                'required': 'El email es obligatorio.',
                'invalid': 'Por favor, ingresa una dirección de email válida.',
                'unique': 'Este email ya está registrado.'
            }
        }

    def clean(self):
        cleaned_data = super().clean()
        es_cliente = cleaned_data.get('es_cliente')
        es_empleado = cleaned_data.get('es_empleado')

        if not es_cliente and not es_empleado:
            raise ValidationError('Debes seleccionar al menos un tipo de usuario (Cliente o Empleado).')

        return cleaned_data

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
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['nombre'].initial = self.instance.nombre
            self.fields['apellido'].initial = self.instance.apellido

    def save(self, commit=True):
        instance = super().save(commit=False)
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

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['nombre', 'apellido', 'dni', 'email', 'fecha_nacimiento']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Nombre', 
                'autocomplete': 'off', 
                'class': 'form-control',
                'minlength': '2',
                'maxlength': '50'
            }),
            'apellido': forms.TextInput(attrs={
                'placeholder': 'Apellido', 
                'autocomplete': 'off', 
                'class': 'form-control',
                'minlength': '2',
                'maxlength': '50'
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
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'autocomplete': 'off', 'class': 'form-control', 'required': True}),
            'fecha_nacimiento': forms.DateInput(attrs={'placeholder': 'Fecha de Nacimiento', 'type': 'date', 'class': 'form-control', 'autocomplete': 'off', 'required': True}),
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre es obligatorio.'
            },
            'apellido': {
                'required': 'El apellido es obligatorio.'
            },
            'dni': {
                'required': 'El DNI es obligatorio.'
            },
            'email': {
                'required': 'El email es obligatorio.',
                'invalid': 'Por favor, ingresa una dirección de email válida.',
                'unique': 'Este email ya está registrado.'
            },
            'fecha_nacimiento': {
                'required': 'La fecha de nacimiento es obligatoria.'
            }
        }

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if not fecha:
            raise forms.ValidationError('La fecha de nacimiento es obligatoria.')
        hoy = date.today()
        edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
        if edad < 18:
            raise forms.ValidationError('No cumple con la mayoría de edad.')
        return fecha

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
        instance.es_cliente = True
        instance.es_empleado = False
        if commit:
            instance.save()
        return instance

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['nombre', 'apellido', 'dni', 'email', 'fecha_nacimiento']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Nombre', 
                'autocomplete': 'off', 
                'class': 'form-control',
                'minlength': '2',
                'maxlength': '50'
            }),
            'apellido': forms.TextInput(attrs={
                'placeholder': 'Apellido', 
                'autocomplete': 'off', 
                'class': 'form-control',
                'minlength': '2',
                'maxlength': '50'
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
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'autocomplete': 'off', 'class': 'form-control', 'required': True}),
            'fecha_nacimiento': forms.DateInput(attrs={'placeholder': 'Fecha de Nacimiento', 'type': 'date', 'class': 'form-control', 'autocomplete': 'off', 'required': True}),
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre es obligatorio.'
            },
            'apellido': {
                'required': 'El apellido es obligatorio.'
            },
            'dni': {
                'required': 'El DNI es obligatorio.'
            },
            'email': {
                'required': 'El email es obligatorio.',
                'invalid': 'Por favor, ingresa una dirección de email válida.',
                'unique': 'Este email ya está registrado.'
            },
            'fecha_nacimiento': {
                'required': 'La fecha de nacimiento es obligatoria.'
            }
        }

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if not fecha:
            raise forms.ValidationError('La fecha de nacimiento es obligatoria.')
        hoy = date.today()
        edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
        if edad < 18:
            raise forms.ValidationError('No cumple con la mayoría de edad.')
        return fecha

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
        instance.es_empleado = True
        instance.es_cliente = False
        if commit:
            instance.save()
        return instance

class ModificarDatosPersonalesForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['nombre', 'apellido']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su nombre',
                'autocomplete': 'off',
                'minlength': '2',
                'maxlength': '50'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su apellido',
                'autocomplete': 'off',
                'minlength': '2',
                'maxlength': '50'
            })
        }
        labels = {
            'nombre': 'Nombre',
            'apellido': 'Apellido'
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre es obligatorio.'
            },
            'apellido': {
                'required': 'El apellido es obligatorio.'
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['nombre'].initial = self.instance.nombre
            self.fields['apellido'].initial = self.instance.apellido

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
        persona = super().save(commit=False)
        if commit:
            persona.save()
        return persona

class SucursalForm(forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = ['direccion', 'latitud', 'longitud', 'telefono', 'email', 'horario']
        widgets = {
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección completa'}),
            'latitud': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Latitud'}),
            'longitud': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Longitud'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'horario': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Horario de atención', 'rows': 3}),
        }
        error_messages = {
            'direccion': {
                'required': 'La dirección es obligatoria.',
                'max_length': 'La dirección no puede tener más de 200 caracteres.',
            },
            'telefono': {
                'required': 'El teléfono es obligatorio.',
                'max_length': 'El teléfono no puede tener más de 20 caracteres.',
            },
            'latitud': {
                'required': 'Debe seleccionar una ubicación en el mapa.',
            },
            'longitud': {
                'required': 'Debe seleccionar una ubicación en el mapa.',
            },
            'horario': {
                'required': 'El horario es obligatorio.',
            },
            'email': {
                'required': 'El email es obligatorio.',
                'invalid': 'Por favor, ingresa una dirección de email válida.',
            }
        }

    def clean_direccion(self):
        """Valida que la dirección ingresada no exista en otra sucursal y respete longitud."""
        direccion = self.cleaned_data.get('direccion', '').strip()
        if not direccion:
            raise forms.ValidationError('La dirección es obligatoria.')

        if len(direccion) > 200:
            raise forms.ValidationError('La dirección no puede tener más de 200 caracteres.')

        # Búsqueda case-insensitive de direcciones duplicadas sólo entre sucursales visibles
        qs = Sucursal.objects.filter(direccion__iexact=direccion, es_visible=True)
        # Excluir la instancia actual si estamos editando
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError('Ya existe una sucursal registrada con esta dirección.')
        return direccion

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if not telefono:
            raise forms.ValidationError('El teléfono es obligatorio.')
        if len(telefono) > 20:
            raise forms.ValidationError('El teléfono no puede tener más de 20 caracteres.')
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        # Validar que los demás campos no queden vacíos
        campos_requeridos = ['latitud', 'longitud', 'telefono', 'email', 'horario']
        for campo in campos_requeridos:
            valor = cleaned_data.get(campo)
            # Para los float, 0 puede ser un valor válido; por eso sólo se verifica None o cadena vacía
            if valor is None or valor == '':
                # Mensaje específico para ubicación
                if campo in ['latitud', 'longitud']:
                    self.add_error(campo, 'Debe seleccionar una ubicación en el mapa.')
                else:
                    self.add_error(campo, 'Este campo es obligatorio.')
        return cleaned_data

class ModificarSucursalForm(SucursalForm):
    class Meta(SucursalForm.Meta):
        exclude = ['direccion', 'latitud', 'longitud']

    def clean(self):
        # Llama al método clean() de la clase base para obtener los datos limpios
        cleaned_data = super(SucursalForm, self).clean()
        
        # Como latitud y longitud no son parte de este formulario,
        # no se necesita la validación que está en SucursalForm.clean().
        # Aquí solo se realizan las validaciones de los campos que sí están presentes.
        
        return cleaned_data
