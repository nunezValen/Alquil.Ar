# Generated by Django 5.1.7 on 2025-07-07 00:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maquinas', '0010_alquiler_external_reference'),
        ('persona', '0005_persona_calificacion_promedio'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CalificacionCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('calificacion', models.PositiveIntegerField(choices=[(1, '1 Estrella'), (2, '2 Estrellas'), (3, '3 Estrellas'), (4, '4 Estrellas'), (5, '5 Estrellas')], verbose_name='Calificación')),
                ('fecha_calificacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Calificación')),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
                ('alquiler', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='calificacion_cliente', to='maquinas.alquiler', verbose_name='Alquiler')),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calificaciones_recibidas', to='persona.persona', verbose_name='Cliente')),
                ('empleado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='calificaciones_otorgadas', to=settings.AUTH_USER_MODEL, verbose_name='Empleado que Calificó')),
            ],
            options={
                'verbose_name': 'Calificación de Cliente',
                'verbose_name_plural': 'Calificaciones de Clientes',
                'ordering': ['-fecha_calificacion'],
            },
        ),
    ]
