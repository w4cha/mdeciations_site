# Generated by Django 5.1.1 on 2024-10-13 22:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratorio', '0002_actualizado_campos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='directorgeneral',
            name='laboratorio',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='laboratorio', to='laboratorio.laboratorio', verbose_name='Laboratorio que dirige'),
        ),
        migrations.AlterField(
            model_name='directorgeneral',
            name='nombre',
            field=models.CharField(max_length=30, verbose_name='Nombre del director'),
        ),
        migrations.AlterField(
            model_name='producto',
            name='laboratorio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='laboratorios', to='laboratorio.laboratorio', verbose_name='Laboratorio de origen'),
        ),
    ]
