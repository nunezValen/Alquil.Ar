# Generated by Django - Manual migration
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('maquinas', '0011_calificacioncliente'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alquiler',
            name='estado',
            field=models.CharField(
                choices=[
                    ('pendiente', 'Pendiente de Pago'),
                    ('reservado', 'Reservado'),
                    ('en_curso', 'En Curso'),
                    ('finalizado', 'Finalizado'),
                    ('cancelado', 'Cancelado'),
                    ('rechazado', 'Rechazado'),
                    ('adeudado', 'Adeudado'),
                ],
                default='reservado',
                max_length=20
            ),
        ),
    ] 