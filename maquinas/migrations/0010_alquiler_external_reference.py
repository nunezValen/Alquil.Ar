# Generated by Django 5.1.7 on 2025-07-06 23:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maquinas', '0009_alter_maquinabase_imagen'),
    ]

    operations = [
        migrations.AddField(
            model_name='alquiler',
            name='external_reference',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Referencia Externa'),
        ),
    ]
