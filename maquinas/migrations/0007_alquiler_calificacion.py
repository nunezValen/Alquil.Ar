# Generated by Django 5.1.3 on 2025-06-11 04:26

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maquinas', '0006_reembolso'),
    ]

    operations = [
        migrations.AddField(
            model_name='alquiler',
            name='calificacion',
            field=models.PositiveIntegerField(blank=True, help_text='Calificación del servicio por parte del cliente (1 a 5)', null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Calificación'),
        ),
    ]
