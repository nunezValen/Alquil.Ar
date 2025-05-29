from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_default_admins(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Empleado = apps.get_model('persona', 'Empleado')

    # Crear usuario Mario
    mario_user = User.objects.create(
        username='emp_mario@alquilar.com',
        email='mario@alquilar.com',
        password=make_password('MarioBro123!'),
        first_name='Mario',
        last_name='Bro',
        is_staff=True,
        is_superuser=True,
        is_active=True
    )

    # Crear empleado Mario
    Empleado.objects.create(
        nombre='Mario',
        apellido='Bro',
        dni='20123456',
        email='mario@alquilar.com',
    )

    # Crear usuario Luigi
    luigi_user = User.objects.create(
        username='emp_luigi@alquilar.com',
        email='luigi@alquilar.com',
        password=make_password('LuigiBro123!'),
        first_name='Luigi',
        last_name='Bro',
        is_staff=True,
        is_superuser=True,
        is_active=True
    )

    # Crear empleado Luigi
    Empleado.objects.create(
        nombre='Luigi',
        apellido='Bro',
        dni='20123457',
        email='luigi@alquilar.com',
    )

def delete_default_admins(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Empleado = apps.get_model('persona', 'Empleado')
    
    User.objects.filter(email__in=['mario@alquilar.com', 'luigi@alquilar.com']).delete()
    Empleado.objects.filter(email__in=['mario@alquilar.com', 'luigi@alquilar.com']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('persona', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_admins, delete_default_admins),
    ] 