# Generated by Django 5.2.1 on 2025-06-05 02:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('persona', '0006_merge_20250604_2214'),
    ]

    operations = [
        migrations.AlterField(
            model_name='persona',
            name='direccion',
            field=models.TextField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='persona',
            name='telefono',
            field=models.CharField(blank=True, editable=False, max_length=20, null=True),
        ),
    ]
