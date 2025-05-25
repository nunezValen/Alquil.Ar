from django.db import migrations, models
from django.utils import timezone
from datetime import date

def eliminar_registros_nulos(apps, schema_editor):
    Persona = apps.get_model('persona', 'Persona')
    # Eliminamos registros con email o fecha_nacimiento nulos
    Persona.objects.filter(email__isnull=True).delete()
    Persona.objects.filter(fecha_nacimiento__isnull=True).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('persona', '0003_remove_persona_direccion_and_more'),
    ]

    operations = [
        migrations.RunPython(eliminar_registros_nulos),
        migrations.AlterField(
            model_name='persona',
            name='email',
            field=models.EmailField(
                max_length=254,
                unique=True,
                help_text="Ingrese un correo electrónico válido"
            ),
        ),
        migrations.AlterField(
            model_name='persona',
            name='fecha_nacimiento',
            field=models.DateField(
                help_text="Ingrese su fecha de nacimiento"
            ),
        ),
    ] 